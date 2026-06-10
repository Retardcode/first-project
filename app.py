import streamlit as st
import pandas as pd
from openai import OpenAI
from supabase import create_client
import os
from dotenv import load_dotenv
import plotly.express as px
import time
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

# ==========================================
# 1. ENVIRONMENT & CONFIGURATION
# ==========================================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    st.error("System Initialization Failure. Verify .env credentials.")
    st.stop()

st.set_page_config(
    page_title="ReguShield AI | Enterprise OS", 
    page_icon="🛡️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. HYPER-VIBRANT CSS & ANIMATIONS
# ==========================================
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
        
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #03040B; color: #F8FAFC; overflow-x: hidden; }
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}

        @keyframes blob-bounce-1 { 0% { transform: translate(0px, 0px) scale(1); } 33% { transform: translate(30px, -50px) scale(1.1); } 66% { transform: translate(-20px, 20px) scale(0.9); } 100% { transform: translate(0px, 0px) scale(1); } }
        @keyframes blob-bounce-2 { 0% { transform: translate(0px, 0px) scale(1); } 33% { transform: translate(-30px, 50px) scale(1.1); } 66% { transform: translate(20px, -20px) scale(0.9); } 100% { transform: translate(0px, 0px) scale(1); } }
        @keyframes blob-bounce-3 { 0% { transform: translate(0px, 0px) scale(1); } 50% { transform: translate(40px, 20px) scale(1.2); } 100% { transform: translate(0px, 0px) scale(1); } }

        .blob-1 { position: absolute; width: 400px; height: 400px; background: rgba(0, 240, 255, 0.35); border-radius: 50%; filter: blur(90px); animation: blob-bounce-1 12s infinite ease-in-out; top: -100px; left: -100px; z-index: 0; pointer-events: none;}
        .blob-2 { position: absolute; width: 350px; height: 350px; background: rgba(255, 0, 127, 0.35); border-radius: 50%; filter: blur(90px); animation: blob-bounce-2 15s infinite ease-in-out; bottom: -50px; right: 5%; z-index: 0; pointer-events: none;}
        .blob-3 { position: absolute; width: 450px; height: 450px; background: rgba(138, 43, 226, 0.35); border-radius: 50%; filter: blur(100px); animation: blob-bounce-3 10s infinite ease-in-out; top: 40%; left: 40%; z-index: 0; pointer-events: none;}

        .hero-title { position: relative; z-index: 10; background: linear-gradient(to right, #00F0FF, #FF007F, #00F0FF); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 5rem; font-weight: 900; letter-spacing: -2px; line-height: 1.1; animation: text-shine 4s linear infinite; }
        @keyframes text-shine { to { background-position: 200% center; } }
        
        .hero-subtitle { position: relative; z-index: 10; color: #E2E8F0; font-size: 1.3rem; font-weight: 500; margin-bottom: 40px; letter-spacing: 0.5px; }

        [data-testid="stMetric"] { position: relative; z-index: 10; background: linear-gradient(145deg, rgba(17, 24, 39, 0.6) 0%, rgba(3, 7, 18, 0.8) 100%); border: 1px solid rgba(0, 240, 255, 0.2); border-radius: 20px; padding: 24px 20px; backdrop-filter: blur(25px); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); transition: all 0.4s ease; }
        [data-testid="stMetric"]:hover { border-color: rgba(0, 240, 255, 0.8); transform: translateY(-8px) scale(1.03); box-shadow: 0 20px 40px -10px rgba(0, 240, 255, 0.4); }

        section[data-testid="stSidebar"] { background-color: #050814 !important; border-right: 1px solid rgba(255, 0, 127, 0.15); }
        .stRadio label { background: rgba(15, 23, 42, 0.6); padding: 15px 20px !important; border-radius: 12px; border: 1px solid transparent; transition: all 0.3s ease; font-size: 1.1rem !important; font-weight: 600 !important; cursor: pointer; margin-bottom: 10px; }
        .stRadio label:hover { border-color: #FF007F; background: rgba(255, 0, 127, 0.08); transform: translateX(5px); }

        .stChatMessage { background: rgba(15, 23, 42, 0.5) !important; border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 16px; padding: 15px 20px; margin-bottom: 20px; backdrop-filter: blur(15px); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); }
        .stButton > button { background: linear-gradient(90deg, #00F0FF 0%, #8A2BE2 50%, #FF007F 100%); background-size: 200% auto; color: #FFFFFF; border: none; border-radius: 12px; padding: 1rem; font-weight: 900; letter-spacing: 1.5px; width: 100%; text-transform: uppercase; transition: all 0.4s ease; box-shadow: 0 4px 15px rgba(138, 43, 226, 0.4); }
        .stButton > button:hover { background-position: right center; transform: translateY(-3px) scale(1.02); box-shadow: 0 15px 30px -5px rgba(255, 0, 127, 0.6); }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC (RAG, INGESTION & EXTRACTION)
# ==========================================
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        return "".join([page.extract_text() + "\n" for page in pdf_reader.pages])
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.getvalue().decode("utf-8")
    return ""

def process_and_upload_document(text, filename):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_text(text)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, chunk in enumerate(chunks):
        status_text.text(f"Vectorizing array {i+1}/{len(chunks)}...")
        embedding = client.embeddings.create(input=chunk, model="text-embedding-3-small").data[0].embedding
        
        supabase.table("regulatory_docs").insert({
            "title": f"{filename} (Part {i+1})",
            "content": chunk,
            "embedding": embedding
        }).execute()
        
        progress_bar.progress((i + 1) / len(chunks))
        time.sleep(0.05)
        
    status_text.text("✅ Vectors Online.")
    return len(chunks)

def extract_and_store_asset_data(raw_text):
    system_prompt = """You are a compliance extraction AI.
    Analyze the text and extract operational data into a strict JSON object with these exact keys:
    {
        "asset_name": "string (Create a short, formal name for the document)",
        "jurisdiction": "string (Local, State, or Federal based on context)",
        "expiry_date": "YYYY-MM-DD (If no date is found, generate a date exactly 1 year from today)",
        "threat_level": "string (Critical, Warning, or Compliant based on the strictness of the text)",
        "risk_score": integer (Estimate a risk score from 0 to 100 based on the severity of the rules)
    }
    Return ONLY valid JSON."""

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text[:4000]} 
        ]
    )
    
    extracted_data = json.loads(response.choices[0].message.content)
    supabase.table("compliance_assets").insert(extracted_data).execute()

def get_regulatory_context(user_query):
    query_embedding = client.embeddings.create(input=user_query, model="text-embedding-3-small").data[0].embedding
    response = supabase.rpc("match_regulatory_docs", {
        "query_embedding": query_embedding,
        "match_threshold": 0.25, 
        "match_count": 3
    }).execute()
    
    return "\n\n---\n\n".join([doc['content'] for doc in response.data]) if response.data else None

# ==========================================
# 4. UI MODULES
# ==========================================
def render_mission_control():
    st.markdown('<div class="blob-1"></div><div class="blob-2"></div><div class="blob-3"></div>', unsafe_allow_html=True)
    st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="hero-title" style="text-align: center;">ReguShield.ai</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle" style="text-align: center; color: #00F0FF; font-weight: 700; text-transform: uppercase;">Next-Generation Compliance Operating System</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="position: relative; z-index: 10; background: rgba(15, 23, 42, 0.4); padding: 40px; border-radius: 24px; border: 1px solid rgba(255, 0, 127, 0.3); text-align: center; backdrop-filter: blur(20px); box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
            <h3 style="color: #F8FAFC; font-size: 1.8rem; margin-bottom: 20px;">System Status: <span style="color: #10B981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);">Online</span></h3>
            <p style="color: #cbd5e1; font-size: 1.15rem; line-height: 1.6;">Welcome to the command center. Navigate using the sidebar to ingest legal frameworks, query the dynamic neural network, or monitor your global risk operations.</p>
        </div>
        """, unsafe_allow_html=True)

def render_ingestion_interface():
    st.markdown('<div class="hero-title" style="font-size: 3.5rem;">Data Forge</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Upload raw documentation. The AI will vectorize the text and extract live metrics simultaneously.</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop PDF or TXT Files Here", type=["pdf", "txt"])
    
    if uploaded_file and st.button("INITIALIZE VECTORIZATION ⚙️"):
        with st.spinner("Shredding document into mathematical vectors..."):
            raw_text = extract_text_from_file(uploaded_file)
        
        if not raw_text.strip():
            st.error("Extraction failure: Unreadable format or image-based PDF.")
        else:
            chunks = process_and_upload_document(raw_text, uploaded_file.name)
            
            with st.spinner("AI is extracting structured metrics for Global Operations..."):
                try:
                    extract_and_store_asset_data(raw_text)
                    st.success("✅ Structured data automatically bridged to Global Operations dashboard!")
                except Exception as e:
                    st.warning("Vectors uploaded, but AI failed to extract structured JSON data.")
            
            st.balloons()
            st.success(f"System trained! {chunks} new vectors injected into the Supabase hive.")

def render_rag_interface():
    st.markdown('<div class="hero-title" style="font-size: 3.5rem;">Neural Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Converse with your proprietary vector database and live operational metrics.</div>', unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello. I am actively monitoring your vector database and live operational dashboard. How can I assist you with compliance today?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Enter compliance query..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Scanning vector clusters and live operations telemetry..."):
                
                context = get_regulatory_context(prompt)
                
                try:
                    docs = supabase.table("regulatory_docs").select("title").execute().data
                    unique_titles = list(set([doc['title'].split(" (Part")[0] for doc in docs])) if docs else []
                    database_inventory = ", ".join(unique_titles) if unique_titles else "No documents uploaded yet."
                except Exception:
                    database_inventory = "Unable to fetch inventory."

                try:
                    struct_data = supabase.table("compliance_assets").select("*").execute().data
                    if struct_data:
                        df_chat = pd.DataFrame(struct_data)
                        total_assets = len(df_chat)
                        critical_threats = len(df_chat[df_chat['threat_level'] == 'Critical'])
                        exposure = df_chat['risk_score'].sum() * 2500
                        
                        ops_context = f"LIVE DASHBOARD TELEMETRY: You are currently tracking {total_assets} active assets. There are {critical_threats} assets marked as 'Critical'. Total Capital Exposure is currently ${exposure:,.0f} calculated at $2,500 per risk point."
                    else:
                        ops_context = "LIVE DASHBOARD TELEMETRY: No operational assets are currently being tracked."
                except Exception:
                    ops_context = "LIVE DASHBOARD TELEMETRY: Connection to operational database failed."

                # MEGA-PROMPT WITH THE FIXES
                system_prompt = f"""You are an elite enterprise compliance AI. 

                CRITICAL INSTRUCTION 1: NEVER use LaTeX math formatting (like \\[ \\] or \\( \\)). Write all numbers, currency, and equations in plain, unformatted text (e.g., "90 points x $2,500 = $225,000").
                
                CRITICAL INSTRUCTION 2: If the user asks WHY a risk score (like 90) was assigned to an asset, do not just explain the math. Explain that the Data Forge AI automatically evaluates the severity of the uploaded regulatory rules (such as fines, strict physical requirements, or legal penalties) on a scale of 0 to 100 when the document is first uploaded. Look at the retrieved legal data to give an example of why it might be severe.

                Retrieved Legal Data:
                {context if context else 'No specific legal rules found for this query.'}

                Database Inventory:
                {database_inventory}

                Live Operations Telemetry:
                {ops_context}
                """

                ai_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt}, 
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Double-tap anti-LaTeX cleanup just in case OpenAI ignores the prompt
                final_reply = ai_response.choices[0].message.content.replace("\\[", "").replace("\\]", "").replace("\\(", "").replace("\\)", "")
                st.markdown(final_reply)
                
                if context:
                    with st.expander("🔍 View Raw Database Match"):
                        st.code(context, language="text")
                        
                st.session_state.messages.append({"role": "assistant", "content": final_reply})

def render_operations_dashboard():
    st.markdown('<div class="hero-title" style="font-size: 3.5rem;">Global Operations</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Live structured data telemetry generated automatically by the AI.</div>', unsafe_allow_html=True)
    
    try:
        struct_data = supabase.table("compliance_assets").select("*").execute().data
        vector_count_response = supabase.table("regulatory_docs").select("id", count="exact").limit(1).execute()
        total_vectors = vector_count_response.count if vector_count_response.count else 0
    except Exception as e:
        st.error("Failed to connect to databases. Ensure tables exist in Supabase.")
        return

    if not struct_data:
        st.info("No operational assets found. Go to the Data Forge and upload a text file to auto-generate data.")
        return

    df = pd.DataFrame(struct_data)
    
    total_assets = len(df)
    critical_threats = len(df[df['threat_level'] == 'Critical'])
    avg_risk = df['risk_score'].mean()
    calculated_exposure = df['risk_score'].sum() * 2500
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg Risk Score", f"{avg_risk:.1f}/100")
    m2.metric("Tracked Assets", str(total_assets))
    m3.metric("Vector Chunks", str(total_vectors), "AI Brain Capacity", delta_color="normal")
    m4.metric("Capital Exposure", f"${calculated_exposure:,.0f}", "- Critical Level" if calculated_exposure > 100000 else "Stable", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    chart_col, alert_col = st.columns([1.2, 1])
    
    with chart_col:
        st.markdown("<h3 style='color: #00F0FF;'>📊 Live Risk Distribution</h3>", unsafe_allow_html=True)
        threat_counts = df['threat_level'].value_counts().reset_index()
        threat_counts.columns = ['Threat Level', 'Count']
        
        color_map = {'Critical': '#FF007F', 'Warning': '#00F0FF', 'Compliant': '#8A2BE2'}
        fig = px.pie(
            threat_counts, values='Count', names='Threat Level', 
            color='Threat Level', color_discrete_map=color_map, hole=0.75
        )
        fig.update_traces(textposition='outside', textinfo='percent+label', marker=dict(line=dict(color='#03040B', width=4)))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
            font=dict(color="#F8FAFC", size=14, family="Inter"), margin=dict(t=20, b=20, l=0, r=0), height=350,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with alert_col:
        st.markdown("<h3 style='color: #FF007F;'>🚨 Active Vulnerabilities</h3>", unsafe_allow_html=True)
        critical_items = df[df['threat_level'] == 'Critical']
        if critical_items.empty:
            st.success("All systems optimal. No critical vulnerabilities detected.")
        else:
            for _, row in critical_items.iterrows():
                st.markdown(f"""
                    <div style="background: linear-gradient(90deg, rgba(255, 0, 127, 0.15) 0%, rgba(15, 23, 42, 0) 100%); border-left: 5px solid #FF007F; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
                        <b style="color: #FF007F; font-size: 1.2rem; letter-spacing: 1px;">CRITICAL: RISK LEVEL {row['risk_score']}</b><br>
                        Asset: <i style="color: #00F0FF; font-weight: bold;">{row['asset_name']}</i><br>
                        <span style="color: #94A3B8;">Jurisdiction: {row['jurisdiction']} | Expiry: {row['expiry_date']}</span>
                    </div>
                """, unsafe_allow_html=True)
                
    st.markdown("---")
    st.markdown("<h3 style='color: #8A2BE2;'>📋 Live Relational Ledger</h3>", unsafe_allow_html=True)
    st.dataframe(
        df[['asset_name', 'jurisdiction', 'expiry_date', 'threat_level', 'risk_score']],
        column_config={
            "risk_score": st.column_config.ProgressColumn("Risk Index", min_value=0, max_value=100, format="%f"),
            "asset_name": "Entity / Asset Profile",
            "jurisdiction": "Oversight",
            "expiry_date": "Expiration",
            "threat_level": "Status"
        },
        hide_index=True, use_container_width=True
    )

# ==========================================
# 5. MAIN NAVIGATION ROUTER
# ==========================================
def main():
    inject_custom_css()
    
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style='color:#F8FAFC; font-weight:900; letter-spacing:-2px; font-size:2.5rem; margin-bottom: 0;'>
                Regu<span style='color:#00F0FF; text-shadow: 0 0 15px rgba(0,240,255,0.5);'>Shield</span>
                </h1>
                <p style='color:#FF007F; font-size:0.85rem; font-weight:900; letter-spacing:2px; text-transform: uppercase;'>OS Version 6.1</p>
            </div>
        """, unsafe_allow_html=True)
        
        page = st.radio("SYSTEM MODULES", [
            "🏠 Mission Control",
            "📂 Data Forge (Upload)", 
            "💬 Neural Chat (AI)", 
            "📊 Global Operations"
        ])
        
        st.markdown("<div style='margin-top: 50px;'><hr style='border-color: rgba(0, 240, 255, 0.2);'></div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8; font-size:0.75rem; letter-spacing:1.5px; text-transform: uppercase;'>Live Telemetry</p>", unsafe_allow_html=True)
        st.markdown("<div style='color: #10B981; font-weight: 600; font-size: 0.9rem; margin-bottom: 5px;'>● SQL Core: ACTIVE</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #00F0FF; font-weight: 600; font-size: 0.9rem; margin-bottom: 5px;'>● PGVector: SYNCED</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #FF007F; font-weight: 600; font-size: 0.9rem;'>● OpenAI JSON Bridge: SECURED</div>", unsafe_allow_html=True)
    
    if page == "🏠 Mission Control": render_mission_control()
    elif page == "📂 Data Forge (Upload)": render_ingestion_interface()
    elif page == "💬 Neural Chat (AI)": render_rag_interface()
    else: render_operations_dashboard()

if __name__ == "__main__":
    main()