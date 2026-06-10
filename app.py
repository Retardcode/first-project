import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from rag_engine import process_and_upload_file, query_rag, get_document_stats
import os

# ==========================================
# 1. PAGE CONFIGURATION & ADVANCED CSS
# ==========================================
st.set_page_config(page_title="QUANTUM NEXUS | Enterprise", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Dark Radial Background */
    .stApp {
        background: radial-gradient(circle at 50% 0%, rgb(18, 19, 38) 0%, rgb(4, 5, 12) 100%);
        color: #e0e6ed;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Glowing Title Animations */
    @keyframes text-glow {
        0% { text-shadow: 0 0 10px rgba(0, 242, 254, 0.4); }
        50% { text-shadow: 0 0 30px rgba(255, 0, 127, 0.8), 0 0 10px rgba(0, 242, 254, 0.4); }
        100% { text-shadow: 0 0 10px rgba(0, 242, 254, 0.4); }
    }
    .title-glow {
        background: linear-gradient(90deg, #ff007f, #7928ca, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4.2rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 4px;
        animation: text-glow 4s infinite alternate;
        margin-bottom: 0px;
    }
    .subtitle-glow {
        color: #00f2fe;
        font-size: 1.4rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 6px;
        border-bottom: 2px solid #ff007f;
        padding-bottom: 15px;
        margin-bottom: 40px;
        box-shadow: 0 5px 15px -10px #ff007f;
    }

    /* Pulsing Metric Cards */
    @keyframes border-pulse {
        0% { box-shadow: 0 0 10px rgba(0, 242, 254, 0.1); }
        50% { box-shadow: 0 0 25px rgba(0, 242, 254, 0.5); border-color: rgba(0,242,254,0.8); }
        100% { box-shadow: 0 0 10px rgba(0, 242, 254, 0.1); }
    }
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(20,22,45,0.85) 0%, rgba(10,12,25,0.95) 100%);
        border: 1px solid rgba(0, 242, 254, 0.3);
        border-left: 6px solid #ff007f;
        border-radius: 12px;
        padding: 20px;
        animation: border-pulse 4s infinite alternate;
    }
    
    /* Neon Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0b15 0%, #1a153a 100%) !important;
        border-right: 2px solid #00f2fe;
        box-shadow: 5px 0 30px rgba(0, 242, 254, 0.2);
    }
    
    /* Cyber Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #ff007f, #7928ca);
        color: white; border: 1px solid rgba(255,255,255,0.3); 
        border-radius: 8px; font-weight: 800; letter-spacing: 1px;
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(255, 0, 127, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0, 242, 254, 0.7);
        background: linear-gradient(45deg, #7928ca, #00f2fe);
        border: 1px solid #fff;
    }
    
    /* Chat System */
    .stChatMessage {
        background: rgba(20, 22, 45, 0.8) !important;
        border: 1px solid rgba(0, 242, 254, 0.4) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.8) !important;
    }
    .empty-state {
        text-align: center; padding: 60px; background: rgba(255,0,127,0.05); 
        border: 2px dashed #ff007f; border-radius: 15px; color: #ff007f; font-weight: 900;
        letter-spacing: 2px; text-shadow: 0 0 10px rgba(255,0,127,0.5);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SESSION & LIVE DATA FETCHING
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "current_page" not in st.session_state: st.session_state.current_page = "Main Hub"

raw_stats = get_document_stats()
df_stats = pd.DataFrame(raw_stats) if raw_stats else pd.DataFrame(columns=["id", "category", "lat", "lon"])
total_docs = len(df_stats)

# --- INVERTED RISK SCORE ALGORITHM ---
# Base Risk is 100 (Critical Danger). Having documents LOWERS the risk.
risk_score = 100
if not df_stats.empty:
    cats = df_stats['category'].unique()
    if 'COMPLIANCE ASSETS' in cats: risk_score -= 40
    if 'REGULATORY DOCS' in cats: risk_score -= 35
    if 'INTERNAL DOCUMENTS' in cats: risk_score -= 10
    if 'GENERAL KNOWLEDGE' in cats: risk_score -= 5

risk_score = max(5, risk_score) # Cap minimum risk at 5% (Cybersecurity is never 0)

if risk_score > 60:
    risk_status, risk_color = "CRITICAL", "#ff007f"
elif risk_score > 20:
    risk_status, risk_color = "ELEVATED", "#f9a826"
else:
    risk_status, risk_color = "SECURE", "#00f2fe"

# ==========================================
# 3. SIDEBAR CONTROLLER
# ==========================================
with st.sidebar:
    st.markdown("## **NEXUS COMMAND**")
    st.markdown("---")
    
    st.session_state.current_page = st.radio(
        "SYSTEM MODULES",
        ["Main Hub", "Risk & Operations Overview", "Data Assimilation (Multi-Upload)", "Neural Terminal"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(f"🟢 **Status:** ONLINE\n\n⚠️ **Risk Score:** {risk_score}/100\n\n🗄️ **Databases Active:** {len(df_stats['category'].unique()) if not df_stats.empty else 0}/4\n\n💾 **Total Vectors:** {total_docs}")

# ==========================================
# PAGE 1: MAIN TITLE HUB
# ==========================================
def render_home():
    st.markdown('<p class="title-glow">QUANTUM NEXUS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Global Intelligence & Relational Network</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Data Nodes", f"{total_docs}", "Live Vectors", delta_color="off")
    col2.metric("System Risk Score", f"{risk_score}/100", f"Status: {risk_status}", delta_color="inverse" if risk_score > 50 else "normal")
    col3.metric("Auto-Routing", "Active", "Deep SQL Tagging", delta_color="normal")
    col4.metric("Geospatial Scanners", "Online", "Extracting Coordinates", delta_color="normal")

    if df_stats.empty:
        st.markdown('<div class="empty-state">SYSTEM EMPTY: AWAITING NEURAL ASSIMILATION</div>', unsafe_allow_html=True)
    else:
        st.markdown("### 🌐 Global Document Geolocation Map")
        st.info("Dots represent real-world locations extracted directly from your uploaded documents by the RAG Engine.")
        
        # Filter dataframe to only include rows where lat/lon were successfully found
        df_map = df_stats.dropna(subset=['lat', 'lon'])
        
        if df_map.empty:
            st.warning("No geospatial data detected in current documents. Upload files containing city names (e.g., London, Tokyo, New York).")
        else:
            st.map(df_map, color="#00f2fe", size=4000)

# ==========================================
# PAGE 2: RISK & OPERATIONS OVERVIEW
# ==========================================
def render_risk():
    st.markdown('<p class="title-glow">RISK & OPERATIONS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Dynamic Threat & Readiness Matrices</p>', unsafe_allow_html=True)
    
    if df_stats.empty:
        st.markdown('<div class="empty-state">NO VECTORS DETECTED. Navigate to Data Assimilation to inject payloads.</div>', unsafe_allow_html=True)
        return

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚠️ Live Threat Gauge")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = risk_score,
            title = {'text': "100 = CRITICAL DANGER", 'font': {'color': 'white'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickcolor': "white"},
                'bar': {'color': risk_color},
                'steps': [
                    {'range': [0, 20], 'color': "rgba(0,242,254,0.2)"},   # Safe
                    {'range': [20, 60], 'color': "rgba(249,168,38,0.2)"}, # Warn
                    {'range': [60, 100], 'color': "rgba(255,0,127,0.3)"}],# Danger
            }
        ))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.markdown("### 🗂️ Relational Table Distribution")
        category_counts = df_stats['category'].value_counts().reset_index()
        category_counts.columns = ['SQL Table', 'Vector Count']
        fig2 = go.Figure(data=[go.Pie(labels=category_counts['SQL Table'], values=category_counts['Vector Count'], hole=.5)])
        fig2.update_traces(
            hoverinfo='label+percent', textfont_size=14,
            marker=dict(colors=['#00f2fe', '#7928ca', '#ff007f', '#f9a826'], line=dict(color='#000000', width=2))
        )
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# PAGE 3: DATA ASSIMILATION (MULTI-UPLOAD)
# ==========================================
def render_upload():
    st.markdown('<p class="title-glow">DATA ASSIMILATION</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Batch Processing & Geo-Extraction Engine</p>', unsafe_allow_html=True)
    
    with st.expander("📥 1. Generate Location-Tagged Demo Payloads (Click to Download)"):
        st.write("These files contain city names. When uploaded, the engine will extract them and plot them on the Map!")
        
        c_text = "CLASSIFICATION: COMPLIANCE\n\nTITLE: London AML Framework\nAll transactions through the LONDON branch exceeding $10,000 must be reported. Failure to comply results in a Level 4 Risk Event."
        r_text = "CLASSIFICATION: REGULATORY\n\nTITLE: Tokyo Quantum Directive\nEffective immediately, the TOKYO datacenter must utilize AES-256 or Quantum-Resistant standards."
        i_text = "CLASSIFICATION: INTERNAL\n\nTITLE: New York Engineering Sprint\nThe NEW YORK core servers will undergo a heavy update this weekend. Ensure backups are pushed."
        g_text = "CLASSIFICATION: GENERAL\n\nTITLE: Dubai Office Schedule\nThe DUBAI regional office will be closed on Friday. Please ensure all tasks are wrapped up."
        u_text = "TITLE: Frankfurt Data Center Expansion\nThe FRANKFURT nodes are expanding. Hardware deliveries arrive Tuesday."

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.download_button("Compliance", c_text, file_name="demo_compliance.txt")
        c2.download_button("Regulatory", r_text, file_name="demo_regulatory.txt")
        c3.download_button("Internal", i_text, file_name="demo_internal.txt")
        c4.download_button("General", g_text, file_name="demo_general.txt")
        c5.download_button("Untagged", u_text, file_name="demo_untagged.txt")

    st.markdown("### 📤 2. Neural Batch Upload Gateway")
    # MULTI-FILE UPLOAD ENABLED HERE
    uploaded_files = st.file_uploader("Select multiple .txt or .pdf files to assimilate concurrently", type=["pdf", "txt"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("INITIATE BATCH ASSIMILATION SEQUENCE"):
            with st.status(f"Processing {len(uploaded_files)} payloads...", expanded=True) as status:
                for u_file in uploaded_files:
                    st.write(f"Extracting & Geo-tagging: {u_file.name}...")
                    temp_name = "temp_" + u_file.name
                    with open(temp_name, "wb") as f:
                        f.write(u_file.getbuffer())
                    
                    target_table = process_and_upload_file(temp_name)
                    st.success(f"Routed '{u_file.name}' ➜ **{target_table.upper()}**")
                    os.remove(temp_name) # Cleanup temp files
                
                status.update(label="Batch Assimilation Complete!", state="complete", expanded=False)

# ==========================================
# PAGE 4: NEURAL TERMINAL (CHAT)
# ==========================================
def render_chat():
    st.markdown('<p class="title-glow">NEURAL TERMINAL</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Multi-Table Union Queries</p>', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Enter complex query command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Executing Deep UNION ALL Search across 4 Tables..."):
                context = query_rag(prompt)
                
            if not context:
                full_response = "Access Denied / Data Not Found. No relevant data in any of the 4 tables."
                message_placeholder.markdown(full_response)
            else:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"You are a highly advanced AI system named NEXUS. Answer the user in deep detail using this context extracted from our databases:\n\n{context}"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                
                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "█")
                
                message_placeholder.markdown(full_response)
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# ==========================================
# EXECUTION ROUTER
# ==========================================
if st.session_state.current_page == "Main Hub": render_home()
elif st.session_state.current_page == "Risk & Operations Overview": render_risk()
elif st.session_state.current_page == "Data Assimilation (Multi-Upload)": render_upload()
elif st.session_state.current_page == "Neural Terminal": render_chat()
