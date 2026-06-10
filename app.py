import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from rag_engine import process_and_upload_file, query_rag

# ==========================================
# 1. PAGE CONFIGURATION & SETUP
# ==========================================
st.set_page_config(page_title="QUANTUM NEXUS | Enterprise", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. ADVANCED MAXIMALIST CSS
# ==========================================
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(14, 15, 30) 0%, rgb(4, 5, 12) 90%);
        color: #e0e6ed;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Neon Text Gradients */
    .title-glow {
        background: linear-gradient(to right, #ff007f, #7928ca, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0px 0px 20px rgba(121, 40, 202, 0.4);
    }
    
    .subtitle-glow {
        color: #00f2fe;
        font-size: 1.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 4px;
        border-bottom: 2px solid #ff007f;
        padding-bottom: 10px;
        margin-bottom: 30px;
    }

    /* Metric Cards Customization */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(20,22,45,0.8) 0%, rgba(10,12,25,0.9) 100%);
        border: 1px solid rgba(0, 242, 254, 0.3);
        border-left: 5px solid #ff007f;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 242, 254, 0.15);
    }
    
    /* Sidebar Customization */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0b15 0%, #130f24 100%) !important;
        border-right: 2px solid #7928ca;
        box-shadow: 5px 0 15px rgba(121,40,202,0.3);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #ff007f, #7928ca);
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 0, 127, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6);
        background: linear-gradient(45deg, #7928ca, #00f2fe);
    }

    /* Chat Elements */
    .stChatMessage {
        background: rgba(20, 22, 45, 0.6) !important;
        border: 1px solid rgba(121, 40, 202, 0.5) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "Main Hub"

# ==========================================
# 3. SIDEBAR NAVIGATION CONTROLLER
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103322.png", width=60) # Placeholder Tech Icon
    st.markdown("## **NEXUS SYSTEM**")
    st.markdown("---")
    
    # Custom Navigation
    page_selection = st.radio(
        "SYSTEM MODULES",
        ["Main Hub", "Risk & Operations Overview", "Data Assimilation (Upload)", "Neural Terminal (Chat)"],
        label_visibility="collapsed"
    )
    st.session_state.current_page = page_selection
    
    st.markdown("---")
    st.markdown("🟢 **System Status:** ONLINE\n\n🛡️ **Security:** ENCRYPTED\n\n💾 **Vector DB:** CONNECTED")

# ==========================================
# PAGE 1: MAIN TITLE HUB
# ==========================================
def render_home():
    st.markdown('<p class="title-glow">QUANTUM NEXUS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Enterprise Intelligence & Document Automation</p>', unsafe_allow_html=True)
    
    st.write("Welcome to the advanced operations command center. Select a module from the sidebar to begin.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Protocols", "1,024", "+12% efficiency", delta_color="normal")
    col2.metric("Threat Level", "Minimal", "-4.2% risk", delta_color="inverse")
    col3.metric("Data Nodes", "84,302", "Syncing...", delta_color="off")
    col4.metric("Neural Uplink", "99.9%", "Optimal", delta_color="normal")

    st.markdown("---")
    st.markdown("### 🌐 Global Operations Map")
    # Colorful Dummy Map Data
    df_map = pd.DataFrame({
        "lat": np.random.randn(100) / 50 + 37.76,
        "lon": np.random.randn(100) / 50 - 122.4,
        "size": np.random.rand(100) * 100,
        "color": np.random.rand(100)
    })
    st.map(df_map, color="#ff007f", size="size")

# ==========================================
# PAGE 2: RISK & OPERATIONS OVERVIEW
# ==========================================
def render_risk():
    st.markdown('<p class="title-glow">RISK & OPERATIONS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Global Assessment Matrices</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Compliance Radar")
        categories = ['Financial', 'Regulatory', 'Operational', 'Cybersecurity', 'Reputational']
        fig1 = go.Figure()
        fig1.add_trace(go.Scatterpolar(
            r=[80, 95, 75, 85, 90],
            theta=categories,
            fill='toself',
            name='Current Quarter',
            line_color='#00f2fe'
        ))
        fig1.add_trace(go.Scatterpolar(
            r=[70, 80, 60, 90, 75],
            theta=categories,
            fill='toself',
            name='Previous Quarter',
            line_color='#ff007f'
        ))
        fig1.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white")
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("### Operational Threat Distribution")
        labels = ['Internal Policies', 'External Regulations', 'Vendor Risks', 'Market Volatility']
        values = [450, 300, 150, 100]
        fig2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
        fig2.update_traces(
            hoverinfo='label+percent', 
            textfont_size=14,
            marker=dict(colors=['#7928ca', '#ff007f', '#00f2fe', '#f9a826'], line=dict(color='#000000', width=2))
        )
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 📊 Live Risk Event Feed")
    dummy_data = pd.DataFrame({
        "Event ID": ["EVT-901", "EVT-902", "EVT-903", "EVT-904"],
        "Category": ["Compliance", "Cybersecurity", "Regulatory", "Financial"],
        "Severity": ["Critical", "High", "Medium", "Low"],
        "Status": ["Investigating", "Mitigated", "Open", "Closed"]
    })
    st.dataframe(dummy_data, use_container_width=True)

# ==========================================
# PAGE 3: DATA ASSIMILATION (UPLOAD)
# ==========================================
def render_upload():
    st.markdown('<p class="title-glow">DATA ASSIMILATION</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Inject Documents into Vector Space</p>', unsafe_allow_html=True)
    
    st.info("⚠️ Ensure documents are verified before assimilation into the neural network.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        target_category = st.radio(
            "Select Security Classification:",
            ["Compliance Assets", "Regulatory Documents", "Internal Memos", "General Knowledge"]
        )
    
    with col2:
        uploaded_file = st.file_uploader("Drop Secure PDF Payload Here", type=["pdf"])
        
        if uploaded_file:
            if st.button("INITIATE ASSIMILATION SEQUENCE"):
                with st.status(f"Encrypting and Vectorizing into '{target_category}'...", expanded=True) as status:
                    st.write("Extracting linguistic data blocks...")
                    with open("temp.pdf", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    st.write("Connecting to Supabase Vector Core...")
                    process_and_upload_file("temp.pdf", category_name=target_category.lower())
                    
                    status.update(label="Assimilation Complete!", state="complete", expanded=False)
                    st.success("File verified and integrated.")

# ==========================================
# PAGE 4: NEURAL TERMINAL (CHAT)
# ==========================================
def render_chat():
    st.markdown('<p class="title-glow">NEURAL TERMINAL</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Direct LLM Knowledge Access</p>', unsafe_allow_html=True)
    
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("Enter query command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner("Searching quantum vectors..."):
                context = query_rag(prompt)
                
            if not context:
                full_response = "Access Denied / Data Not Found. No relevant files match this query in the current vector space."
                message_placeholder.markdown(full_response)
            else:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"You are a highly advanced AI system named NEXUS. Answer the user strictly using this context:\n\n{context}"},
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
elif st.session_state.current_page == "Data Assimilation (Upload)":
    render_upload()
elif st.session_state.current_page == "Neural Terminal (Chat)":
    render_chat()
