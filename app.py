import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import time
from datetime import datetime
from openai import OpenAI
from rag_engine import process_and_upload_file, query_rag, get_document_stats, get_clients

# ==========================================
# 1. PAGE CONFIGURATION & MAXIMALIST CSS
# ==========================================
st.set_page_config(page_title="REGUSHIELD | MATRIX", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 50% -20%, rgb(12, 17, 30) 0%, rgb(2, 4, 10) 100%);
        color: #e2e8f0;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    @keyframes scanline {
        0% { background-position: 0 0; }
        100% { background-position: 0 100%; }
    }
    .scanlines::before {
        content: " "; display: block; position: fixed; top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 999; background-size: 100% 2px, 3px 100%; pointer-events: none; opacity: 0.15;
    }
    .title-glow {
        background: linear-gradient(90deg, #00f2fe, #4facfe, #00f2fe);
        background-size: 200% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 4.5rem; font-weight: 900; letter-spacing: 8px;
        animation: neon-pulse 3s infinite linear; margin-bottom: 0px;
    }
    @keyframes neon-pulse { to { background-position: 200% center; } }
    .subtitle-glow {
        color: #89cff0; font-size: 1.1rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 12px; border-bottom: 2px solid #00f2fe; padding-bottom: 15px; margin-bottom: 30px;
    }
    [data-testid="metric-container"] {
        background: rgba(12, 17, 30, 0.8); backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 242, 254, 0.2); border-left: 6px solid #00f2fe;
        border-radius: 4px; padding: 20px; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.5);
        transition: all 0.3s;
    }
    [data-testid="metric-container"]:hover { border-left: 6px solid #ff007f; transform: translateY(-5px); box-shadow: 0 10px 40px 0 rgba(0,242,254,0.3); }
    [data-testid="stSidebar"] { background: #030408 !important; border-right: 1px solid #00f2fe; }
    .stButton>button {
        background: transparent; color: #00f2fe; border: 1px solid #00f2fe;
        border-radius: 2px; font-weight: bold; letter-spacing: 2px; width: 100%; transition: all 0.2s;
    }
    .stButton>button:hover { background: rgba(0, 242, 254, 0.1); box-shadow: 0 0 15px rgba(0, 242, 254, 0.4); border: 1px solid #fff; color: #fff; }
    .terminal-box { background: #000; border: 1px solid #333; border-left: 3px solid #00f2fe; padding: 15px; font-size: 0.85rem; color: #0f0; height: 250px; overflow-y: auto; }
    .stChatMessage { background: rgba(10, 12, 20, 0.9) !important; border: 1px solid rgba(0, 242, 254, 0.4) !important; border-radius: 4px !important; }
    
    /* Interactive Node Diagnostics Card */
    .node-card {
        background: linear-gradient(145deg, rgba(20,25,45,0.9), rgba(10,12,25,0.95));
        border: 2px solid #ff007f; border-radius: 8px; padding: 25px;
        box-shadow: 0 0 30px rgba(255, 0, 127, 0.3);
        margin-top: 20px;
    }
    .node-title { color: #fff; font-size: 1.5rem; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 10px;}
    .node-metric { color: #00f2fe; font-size: 1.1rem; margin-bottom: 8px;}
    .node-risk { color: #ff007f; font-weight: bold; font-size: 1.3rem;}
</style>
<div class="scanlines"></div>
""", unsafe_allow_html=True)

# ==========================================
# 2. SESSION & STATE INITIALIZATION
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "logs" not in st.session_state: st.session_state.logs = ["[SYSTEM] ReguShield Core v4.0 Initialized.", f"[TIME] {datetime.now().strftime('%H:%M:%S UTC')}"]
if "current_page" not in st.session_state: st.session_state.current_page = "MAIN HUB"
if "llm_temp" not in st.session_state: st.session_state.llm_temp = 0.3
if "queued_prompt" not in st.session_state: st.session_state.queued_prompt = None

def add_log(msg):
    st.session_state.logs.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

raw_data = get_document_stats()
df_stats = pd.DataFrame(raw_data) if raw_data else pd.DataFrame(columns=["id", "file_name", "category", "location_hub", "lat", "lon", "individual_risk", "export_domain"])

# Advanced Risk Math (100 = BAD, 0 = GOOD)
total_docs = len(df_stats)
if df_stats.empty:
    calculated_risk = 100.0
else:
    avg_file_risk = df_stats["individual_risk"].mean()
    geo_spread = len(df_stats["location_hub"].unique())
    table_spread = len(df_stats["category"].unique())
    deduction = (geo_spread * 2) + (table_spread * 10)
    calculated_risk = max(5.0, min(100.0, avg_file_risk - deduction + 30))

if calculated_risk >= 75: threat_status, color = "CRITICAL VULNERABILITY", "#ff007f"
elif calculated_risk >= 40: threat_status, color = "ELEVATED EXPOSURE", "#f59e0b"
else: threat_status, color = "SECURE MATRIX", "#00f2fe"

# ==========================================
# 3. ADVANCED SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103322.png", width=60)
    st.markdown("### **REGUSHIELD CORE**")
    
    st.session_state.current_page = st.radio(
        "OPERATIONAL MODULES",
        ["MAIN HUB", "RISK & OPERATIONS", "DATA ASSIMILATION", "NEURAL TERMINAL"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 🎛️ SYSTEM TELEMETRY")
    st.progress(max(1, min(100, int(100 - calculated_risk))), text=f"Shield Integrity: {100-calculated_risk:.1f}%")
    st.progress(min(100, int(total_docs * 2.5)), text=f"Vector Capacity: {total_docs}/MAX")
    
    col_a, col_b = st.columns(2)
    col_a.metric("CPU LOAD", f"{np.random.randint(12, 35)}%", "Nominal")
    col_b.metric("LATENCY", f"{np.random.randint(18, 45)}ms", "Optimized")
    
    st.markdown("---")
    st.markdown("### 🧠 LLM PARAMETERS")
    st.session_state.llm_temp = st.slider("Neural Temperature", 0.0, 1.0, st.session_state.llm_temp, 0.1)

# ==========================================
# PAGE 1: MAIN HUB (COMMAND CENTER)
# ==========================================
if st.session_state.current_page == "MAIN HUB":
    st.markdown('<p class="title-glow">REGUSHIELD COMMAND</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Global Intelligence & Defense Matrix</p>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NETWORK VECTORS", f"{total_docs} Nodes", "+ Active Datasets")
    c2.metric("THREAT INDEX", f"{calculated_risk:.1f}%", f"{threat_status}", delta_color="inverse")
    c3.metric("GEO-HUBS SECURED", f"{len(df_stats['location_hub'].unique()) if not df_stats.empty else 0}", "Global Nodes")
    c4.metric("ENCRYPTION KEY", "AES-256-Q", "Rotating", delta_color="normal")
    
    st.markdown("---")
    col_globe, col_logs = st.columns([2, 1])
    
    with col_globe:
        st.markdown("### 🌍 3D Global Data Distribution (Interactive)")
        st.info("💡 **Click any glowing node on the map** to instantly extract and display its structural risk profile below.")
        
        df_geo = df_stats.dropna(subset=['lat', 'lon']).reset_index(drop=True)
        if df_geo.empty:
            st.error("NO GEOSPATIAL DATA. Upload ReguShield payloads to render the globe.")
        else:
            fig_globe = go.Figure(go.Scattergeo(
                lon=df_geo['lon'], lat=df_geo['lat'],
                # Pass data we want to retrieve upon clicking via customdata
                customdata=df_geo[['file_name', 'category', 'individual_risk', 'export_domain', 'location_hub']],
                hovertemplate="<b>%{customdata[4]} Node</b><br>Click to Analyze<extra></extra>",
                mode='markers', marker=dict(size=14, color='#00f2fe', opacity=0.8, line=dict(width=2, color='white'))
            ))
            fig_globe.update_geos(
                projection_type="orthographic", showocean=True, oceancolor="rgba(8,12,25,1)",
                showland=True, landcolor="rgba(25,30,50,1)", showcountries=True, countrycolor="#00f2fe",
                bgcolor="rgba(0,0,0,0)"
            )
            fig_globe.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', height=450)
            
            # This captures the click event from the map
            chart_event = st.plotly_chart(fig_globe, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # Interactive Diagnostic Display Panel
            selected_points = chart_event.selection.get("points", []) if chart_event else []
            if selected_points:
                point_data = selected_points[0].get("customdata", [])
                if point_data:
                    file_name, cat, risk, domain, loc = point_data
                    st.markdown(f"""
                    <div class="node-card">
                        <div class="node-title">🛡️ NODE DIAGNOSTICS: {loc.upper()}</div>
                        <div class="node-metric">📄 <b>File Asset:</b> {file_name}</div>
                        <div class="node-metric">🗄️ <b>SQL Table:</b> {cat}</div>
                        <div class="node-metric">🌐 <b>Export Domain:</b> {domain}</div>
                        <div class="node-risk">⚠️ <b>Isolated Risk Score:</b> {risk}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    add_log(f"Analyzed node {loc} ({file_name}).")
            
    with col_logs:
        st.markdown("### 🖥️ Live Terminal Output")
        log_text = "<br>".join(st.session_state.logs[:15])
        st.markdown(f'<div class="terminal-box">{log_text}</div>', unsafe_allow_html=True)

# ==========================================
# PAGE 2: RISK & OPERATIONS OVERVIEW
# ==========================================
elif st.session_state.current_page == "RISK & OPERATIONS":
    st.markdown('<p class="title-glow">RISK ANALYTICS</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Multi-Dimensional Vulnerability Mapping</p>', unsafe_allow_html=True)
    
    if df_stats.empty:
        st.warning("SYSTEM EMPTY. INJECT PAYLOADS VIA ASSIMILATION TAB.")
    else:
        t1, t2 = st.tabs(["📊 Executive Dash", "🔍 Deep Matrix Analysis"])
        
        with t1:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("### 🕸️ Relational Table Saturation")
                # Using 'Plasma' color scale to fix the previous bug
                fig_sun = px.sunburst(df_stats, path=['category', 'export_domain', 'location_hub'], 
                                      color='individual_risk', color_continuous_scale='Plasma')
                fig_sun.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_sun, use_container_width=True)
            with c2:
                st.markdown("### 📉 Threat Exposure Vector")
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number", value=calculated_risk,
                    gauge={'axis': {'range': [None, 100]}, 'bar': {'color': color},
                           'steps': [{'range': [0, 40], 'color': 'rgba(0,242,254,0.1)'}, {'range': [75, 100], 'color': 'rgba(255,0,127,0.2)'}]}
                ))
                fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=400)
                st.plotly_chart(fig_gauge, use_container_width=True)

        with t2:
            st.markdown("### 🗺️ Vulnerability Heatmap (Geo vs Export Domain)")
            pivot_df = pd.pivot_table(df_stats, values='individual_risk', index='location_hub', columns='export_domain', aggfunc=np.mean).fillna(0)
            fig_heat = px.imshow(pivot_df, text_auto=True, color_continuous_scale='Plasma', aspect="auto")
            fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig_heat, use_container_width=True)
            
            st.markdown("### 📋 Complete Node Ledger")
            st.dataframe(df_stats.style.background_gradient(subset=['individual_risk'], cmap='coolwarm'), use_container_width=True)

# ==========================================
# PAGE 3: DATA ASSIMILATION (UPLOAD)
# ==========================================
elif st.session_state.current_page == "DATA ASSIMILATION":
    st.markdown('<p class="title-glow">DATA ASSIMILATION</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Batch Processing & Autonomous SQL Routing</p>', unsafe_allow_html=True)
    
    with st.expander("📥 GENERATE REGUSHIELD ENTERPRISE PAYLOADS (12 FILES)"):
        st.write("Click to download the full suite of ReguShield operational test data. Drag and drop them all below to watch the system classify, tag, and route them.")
        
        payloads = {
            "01_COMPLIANCE_London.txt": "CLASSIFICATION: COMPLIANCE\nLOCATION: LONDON\nRISK_SCORE: 85%\nEXPORT_AREA: EMEA_FINANCIALS\nTITLE: AML Framework\nAll transactions >$10k routed via ReguShield London require 24h escrow verification. Bypassing triggers Level 4 lockout.",
            "02_COMPLIANCE_Singapore.txt": "CLASSIFICATION: COMPLIANCE\nLOCATION: SINGAPORE\nRISK_SCORE: 65%\nEXPORT_AREA: APAC_CLOUD_CORE\nTITLE: Sovereign Data Protocol\nReguShield telemetry older than 36 months in SG node must be cryptographically shredded via Quantum-Hash.",
            "03_COMPLIANCE_Geneva.txt": "CLASSIFICATION: COMPLIANCE\nLOCATION: GENEVA\nRISK_SCORE: 90%\nEXPORT_AREA: SWISS_BANKING\nTITLE: Offshore Wealth Audit\nAll ReguShield Swiss-node cross-border transfers require manual signatory verification by VP of Risk.",
            "04_REGULATORY_Tokyo.txt": "CLASSIFICATION: REGULATORY\nLOCATION: TOKYO\nRISK_SCORE: 95%\nEXPORT_AREA: EAST_ASIA_INFRASTRUCTURE\nTITLE: Quantum Encryption Directive\nReguShield Tokyo arrays must use AES-256-Q immediately. Outdated configs face total connection termination.",
            "05_REGULATORY_Frankfurt.txt": "CLASSIFICATION: REGULATORY\nLOCATION: FRANKFURT\nRISK_SCORE: 45%\nEXPORT_AREA: WEST_EUROPE_OPS\nTITLE: ISO 27001 Validation\nServer rooms mandate biometric multi-factor access. Legacy ID cards disabled.",
            "06_REGULATORY_Sydney.txt": "CLASSIFICATION: REGULATORY\nLOCATION: SYDNEY\nRISK_SCORE: 70%\nEXPORT_AREA: OCEANIA_DATA\nTITLE: Data Sovereignty Act\nAustralian citizen data must not leave the ReguShield Sydney physical servers. External backups strictly forbidden.",
            "07_INTERNAL_NewYork.txt": "CLASSIFICATION: INTERNAL\nLOCATION: NEW YORK\nRISK_SCORE: 75%\nEXPORT_AREA: AMER_ENGINEERING\nTITLE: Core Migration Sprint\nNY databases migrating this weekend. 4-hour downtime expected at 0200 UTC.",
            "08_INTERNAL_SanFrancisco.txt": "CLASSIFICATION: INTERNAL\nLOCATION: SAN FRANCISCO\nRISK_SCORE: 20%\nEXPORT_AREA: GLOBAL_STRATEGY\nTITLE: Q2 Financial Review\nOverhead down 14% thanks to ReguShield AI integration. Engineering headcount expands by 50.",
            "09_INTERNAL_Toronto.txt": "CLASSIFICATION: INTERNAL\nLOCATION: TORONTO\nRISK_SCORE: 40%\nEXPORT_AREA: NA_ARCHITECTURE\nTITLE: Microservices Architecture Review\nTransitioning from monolithic to containerized deployments for all ReguShield Toronto compute tasks.",
            "10_GENERAL_Dubai.txt": "CLASSIFICATION: GENERAL\nLOCATION: DUBAI\nRISK_SCORE: 30%\nEXPORT_AREA: ME_TRANSIT\nTITLE: Regional Holidays\nDubai offices closed Friday. Standby engineers receive 3x compensation.",
            "11_GENERAL_Paris.txt": "CLASSIFICATION: GENERAL\nLOCATION: PARIS\nRISK_SCORE: 10%\nEXPORT_AREA: EU_FACILITIES\nTITLE: Safety Protocols\nReguShield Paris HQ evacuation routes updated. Gather at Rally Point Alpha (North Lot) during alarms.",
            "12_GENERAL_HongKong.txt": "CLASSIFICATION: GENERAL\nLOCATION: HONG KONG\nRISK_SCORE: 15%\nEXPORT_AREA: APAC_LOGISTICS\nTITLE: Approved Vendor List 2026\nNew hardware providers authorized for HK hub. Procurement limits raised to $50k per PO."
        }
        
        cols = st.columns(4)
        for i, (fname, content) in enumerate(payloads.items()):
            cols[i % 4].download_button(fname.split("_")[1] + " " + fname.split("_")[2].split(".")[0], content, file_name=fname)

    st.markdown("### 📤 NEURAL BATCH UPLOAD GATEWAY")
    uploaded_files = st.file_uploader("Drop Enterprise Payloads (.txt, .pdf)", accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("INITIATE BATCH ASSIMILATION"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, u_file in enumerate(uploaded_files):
                status_text.text(f"Scanning & Routing: {u_file.name}...")
                temp_name = "temp_" + u_file.name
                with open(temp_name, "wb") as f: f.write(u_file.getbuffer())
                
                time.sleep(0.5) # Simulating complex security checks
                
                target_table, chunks, tokens = process_and_upload_file(temp_name, u_file.name)
                add_log(f"Routed {u_file.name} to {target_table} ({chunks} vectors)")
                os.remove(temp_name)
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            st.success("BATCH ASSIMILATION COMPLETE. ALL DATABASES SECURED.")
            time.sleep(1)
            st.rerun()

# ==========================================
# PAGE 4: NEURAL TERMINAL (CHAT)
# ==========================================
elif st.session_state.current_page == "NEURAL TERMINAL":
    st.markdown('<p class="title-glow">NEURAL TERMINAL</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-glow">Cross-Table Relational Database Interface</p>', unsafe_allow_html=True)
    
    col_chat, col_diag = st.columns([3, 1])
    
    with col_diag:
        st.markdown("### ⚡ AUTO-INJECT PROMPTS")
        st.info("Click a button below to automatically load and execute a system query in the terminal.")
        # When clicked, these buttons save the prompt to session state and rerun the app
        if st.button("Highest physical security risk?"):
            st.session_state.queued_prompt = "What is our highest physical security risk across all ReguShield hubs?"
            st.rerun()
        if st.button("Summarize Tokyo Directives"):
            st.session_state.queued_prompt = "Summarize the Tokyo Directives and their encryption requirements."
            st.rerun()
        if st.button("Where are server migrations?"):
            st.session_state.queued_prompt = "Where are our server migrations happening and what is the expected downtime?"
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 📡 QUERY DIAGNOSTICS")
        if "last_matches" in st.session_state and st.session_state.last_matches:
            st.success("✅ RAG Retrieval Successful")
            st.markdown("**Vectors Hit:**")
            for match in st.session_state.last_matches:
                st.markdown(f"- `{match['file_name']}` (Sim: {match['similarity']:.2f})")
        else:
            st.info("Awaiting Query Execution.")
            
    with col_chat:
        chat_container = st.container(height=600)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
        # This logic checks if a button was clicked. If so, it uses that text instead of waiting for input.
        user_command = st.chat_input("Query the ReguShield system...")
        
        if st.session_state.queued_prompt:
            user_command = st.session_state.queued_prompt
            st.session_state.queued_prompt = None # Reset it so it only fires once
            
        if user_command:
            st.session_state.messages.append({"role": "user", "content": user_command})
            chat_container.chat_message("user").markdown(user_command)
            add_log(f"User Query Executed: {user_command[:20]}...")
            
            with chat_container.chat_message("assistant"):
                response_container = st.empty()
                with st.spinner("Executing UNION ALL search across 4 ReguShield Tables..."):
                    extracted_context, raw_matches = query_rag(user_command)
                    st.session_state.last_matches = raw_matches # Save for diagnostics
                    
                if not extracted_context:
                    response_container.markdown("ACCESS DENIED / DATA NOT FOUND.")
                else:
                    _, open_client = get_clients()
                    completion_stream = open_client.chat.completions.create(
                        model="gpt-4o",
                        temperature=st.session_state.llm_temp,
                        messages=[
                            {"role": "system", "content": f"You are REGUSHIELD CORE, an elite security AI. Use this database context to protect and inform:\n\n{extracted_context}"},
                            {"role": "user", "content": user_command}
                        ],
                        stream=True
                    )
                    
                    computed_text = ""
                    for packet in completion_stream:
                        if packet.choices[0].delta.content is not None:
                            computed_text += packet.choices[0].delta.content
                            response_container.markdown(computed_text + "█")
                    response_container.markdown(computed_text)
                    st.session_state.messages.append({"role": "assistant", "content": computed_text})
                    st.rerun() # Refresh the UI so the diagnostics panel updates instantly
