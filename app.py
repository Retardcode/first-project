import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from rag_engine import process_and_upload_file, query_rag, get_document_stats
import os

# ==========================================
# 1. PAGE CONFIGURATION & SETUP
# ==========================================
st.set_page_config(page_title="QUANTUM NEXUS | Enterprise", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. ADVANCED MAXIMALIST CSS
# ==========================================
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(14, 15, 30) 0%, rgb(4, 5, 12) 90%);
        color: #e0e6ed;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .title-glow {
        background: linear-gradient(to right, #ff007f, #7928ca, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0px 0px 20px rgba(121, 40, 202, 0.4);
        margin-bottom: 0px;
    }
    .subtitle-glow {
        color: #00f2fe;
        font-size: 1.2rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 4px;
        border-bottom: 2px solid #ff007f;
        padding-bottom: 10px;
        margin-bottom: 30px;
    }
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(20,22,45,0.8) 0%, rgba(10,12,25,0.9) 100%);
        border: 1px solid rgba(0, 242, 254, 0.3);
        border-left: 5px solid #ff007f;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 242, 254, 0.15);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0b15 0%, #130f24 100%) !important;
        border-right: 2px solid #7928ca;
        box-shadow: 5px 0 15px rgba(121,40,202,0.3);
    }
    .stButton>button {
        background: linear-gradient(45deg, #ff007f, #7928ca);
        color: white; border: none; border-radius: 4px; font-weight: bold;
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(255, 0, 127, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6);
        background: linear-gradient(45deg, #7928ca, #00f2fe);
    }
    .stChatMessage {
        background: rgba(20, 22, 45, 0.6) !important;
        border: 1px solid rgba(121, 40, 202, 0.5) !important;
        border-radius: 10px !important;
    }
    .empty-state {
        text-align: center; padding: 50px; background: rgba(255,0,127,0.1); 
        border: 1px dashed #ff007f; border-radius: 10px; color: #ff007f; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "Main Hub"

# Fetch Live Data
raw_stats = get_document_stats()
df_stats = pd.DataFrame(raw_stats) if raw_stats else pd.DataFrame(columns=["id", "category"])
total_docs = len(df_stats)

# Calculate dynamic risk score (0-100)
risk_score = 0
if not df_stats.empty:
    cats = df_stats['category'].unique()
    if 'compliance assets' in cats: risk_score += 35
    if 'regulatory docs' in cats: risk_score += 35
    if 'internal documents' in cats: risk_score += 15
    if 'general knowledge' in cats: risk_score += 15

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("## **NEXUS SYSTEM**")
    st.markdown("---")
    
    page_selection = st.radio(
        "SYSTEM MODULES",
        ["Main Hub", "Risk & Operations Overview", "Data Assimilation", "Neural Terminal"],
        label_visibility="collapsed"
    )
    st.session_state.current_page = page_selection
    
    st.markdown("---")
    st.markdown(f"🟢 **Status:** ONLINE\n\n🛡️ **Risk Score:** {risk_score}/100\n\n💾 **Vector Nodes:** {total_docs}")

# ==========================================
# PAGE 1: MAIN TITLE HUB
# ==========================================
def render_home():
    st.markdown('<p class="title-glow">QUANTUM NEXUS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Enterprise Intelligence Command</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Data Nodes", f"{total_docs}", "Live Vectors", delta_color="off")
    col2.metric("System Readiness", f"{risk_score}%", "Operational Health")
    col3.metric("Auto-Sorting", "Active", "Neural Tagging", delta_color="normal")
    col4.metric("LLM Context Range", "Deep", "Threshold 0.3", delta_color="normal")

    if df_stats.empty:
        st.markdown('<div class="empty-state">SYSTEM EMPTY: AWAITING NEURAL ASSIMILATION</div>', unsafe_allow_html=True)
    else:
        st.markdown("### 🌐 Global Operations Activity Map")
        df_map = pd.DataFrame({
            "lat": np.random.randn(total_docs * 2) / 50 + 37.76,
            "lon": np.random.randn(total_docs * 2) / 50 - 122.4,
            "size": np.random.rand(total_docs * 2) * 100,
        })
        st.map(df_map, color="#ff007f", size="size")

# ==========================================
# PAGE 2: RISK & OPERATIONS OVERVIEW
# ==========================================
def render_risk():
    st.markdown('<p class="title-glow">RISK & OPERATIONS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Live Vector Assessment Matrices</p>', unsafe_allow_html=True)
    
    if df_stats.empty:
        st.markdown('<div class="empty-state">NO DATA DETECTED. Navigate to Data Assimilation to inject payloads.</div>', unsafe_allow_html=True)
        return

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🛡️ Enterprise Security Score")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = risk_score,
            title = {'text': "Security & Policy Readiness", 'font': {'color': 'white'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickcolor': "white"},
                'bar': {'color': "#00f2fe"},
                'steps': [
                    {'range': [0, 40], 'color': "rgba(255,0,127,0.3)"},
                    {'range': [40, 80], 'color': "rgba(121,40,202,0.3)"},
                    {'range': [80, 100], 'color': "rgba(0,242,254,0.3)"}],
            }
        ))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.markdown("### 🗂️ Autonomous Neural Sorting Distribution")
        category_counts = df_stats['category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Node Count']
        fig2 = go.Figure(data=[go.Pie(labels=category_counts['Category'], values=category_counts['Node Count'], hole=.5)])
        fig2.update_traces(
            hoverinfo='label+percent', textfont_size=14,
            marker=dict(colors=['#00f2fe', '#7928ca', '#ff007f', '#ffffff'], line=dict(color='#000000', width=2))
        )
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# PAGE 3: DATA ASSIMILATION (UPLOAD)
# ==========================================
def render_upload():
    st.markdown('<p class="title-glow">DATA ASSIMILATION</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Autonomous Sorting Engine</p>', unsafe_allow_html=True)
    
    st.info("The RAG Engine will read the files, detect the 'CLASSIFICATION' string, and sort them into the database automatically.")
    
    # Payload Generator
    with st.expander("📥 1. Generate Demo Payloads (Click to Download)"):
        st.write("Save these files to your computer, then drag them into the uploader below.")
        
        c_text = "CLASSIFICATION: COMPLIANCE\n\nTITLE: Anti-Money Laundering Framework 2026\nAll transactions over $10,000 must be reported immediately. Failure to comply results in a Level 4 Risk Event."
        r_text = "CLASSIFICATION: REGULATORY\n\nTITLE: SEC Quantum Directive 409\nEffective immediately, all cloud storage must utilize AES-256 or Quantum-Resistant standards. Annual audits required."
        i_text = "CLASSIFICATION: INTERNAL\n\nTITLE: Q3 Engineering Sprint\nThe Nexus servers will undergo a heavy update this weekend. Ensure all backups are pushed to the secondary nodes."
        g_text = "CLASSIFICATION: GENERAL\n\nTITLE: Company Holiday Schedule\nThe office will be closed on November 26th and 27th. Please ensure all tasks are wrapped up prior to the break."

        c1, c2, c3, c4 = st.columns(4)
        c1.download_button("Download Compliance", c_text, file_name="demo_compliance.txt")
        c2.download_button("Download Regulatory", r_text, file_name="demo_regulatory.txt")
        c3.download_button("Download Internal", i_text, file_name="demo_internal.txt")
        c4.download_button("Download General", g_text, file_name="demo_general.txt")

    st.markdown("### 📤 2. Neural Upload Gateway")
    uploaded_file = st.file_uploader("Drop .txt or .pdf files here", type=["pdf", "txt"])
    
    if uploaded_file:
        if st.button("INITIATE ASSIMILATION SEQUENCE"):
            with st.status("Reading & Classifying payload...", expanded=True) as status:
                # Save temp file
                temp_name = "temp" + os.path.splitext(uploaded_file.name)[1]
                with open(temp_name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.write("Extracting linguistic triggers and vectorizing...")
                detected_category = process_and_upload_file(temp_name)
                
                status.update(label="Assimilation Complete!", state="complete", expanded=False)
                st.success(f"Success! System automatically sorted this file into: **{detected_category.upper()}**")

# ==========================================
# PAGE 4: NEURAL TERMINAL (CHAT)
# ==========================================
def render_chat():
    st.markdown('<p class="title-glow">NEURAL TERMINAL</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Direct LLM Knowledge Access</p>', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Enter complex query command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Searching quantum vectors (Broad Context Mode)..."):
                context = query_rag(prompt)
                
            if not context:
                full_response = "Access Denied / Data Not Found. Database empty or query out of bounds."
                message_placeholder.markdown(full_response)
            else:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"You are a highly advanced AI system named NEXUS. Answer the user in deep detail using this context:\n\n{context}"},
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
if st.session_state.current_page == "Main Hub":
    render_home()
elif st.session_state.current_page == "Risk & Operations Overview":
    render_risk()
elif st.session_state.current_page == "Data Assimilation":
    render_upload()
elif st.session_state.current_page == "Neural Terminal":
    render_chat()
