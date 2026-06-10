import streamlit as st
from rag_engine import process_and_upload_file, query_rag
from openai import OpenAI

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(page_title="Nexus RAG Engine", page_icon="🌌", layout="wide")

# 2. Advanced Custom CSS Injection (Geometry, Colors, Glassmorphism)
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0d1117;
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,0.2) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,0.2) 0, transparent 50%);
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Glowing Gradient Text */
    .gradient-text {
        font-weight: 800;
        font-size: 3rem;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    /* Subtitle */
    .sub-text {
        color: #8b949e;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Glassmorphism Containers (Sidebar & Main elements) */
    [data-testid="stSidebar"] {
        background: rgba(22, 27, 34, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Chat Message Bubbles */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* File Uploader Customization */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(0, 242, 254, 0.05);
        border: 2px dashed rgba(0, 242, 254, 0.4);
        border-radius: 15px;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: rgba(0, 242, 254, 0.1);
        border: 2px dashed rgba(0, 242, 254, 0.8);
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
    }
    
    /* Hide top header bar */
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. Session State Initialization (Memory for Chat)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Sidebar: Document Management & Categorization
with st.sidebar:
    st.markdown("### 🗄️ Neural Database")
    st.markdown("Upload and classify documents into the vector space.")
    
    # Category Tagging Dropdown
    target_category = st.selectbox(
        "Select Classification:",
        ["compliance assets", "documents", "regulatory documents", "general"]
    )
    
    uploaded_file = st.file_uploader("Drop PDF here", type=["pdf"], label_visibility="collapsed")
    
    if uploaded_file:
        with st.status(f"Integrating into '{target_category}'...", expanded=True) as status:
            st.write("Extracting data blocks...")
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.write("Vectorizing context...")
            process_and_upload_file("temp.pdf", category_name=target_category)
            
            status.update(label="Upload Complete!", state="complete", expanded=False)
            st.success("Knowledge successfully integrated into Supabase.")

# 5. Main Interface: The Chat
st.markdown('<p class="gradient-text">Nexus Terminal</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Advanced Retrieval-Augmented Generation Interface</p>', unsafe_allow_html=True)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Query the knowledge base..."):
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("Quantum searching Supabase vectors..."):
            context = query_rag(prompt)
            
        if not context:
            full_response = "I couldn't find relevant information in the uploaded documents to answer this."
            message_placeholder.markdown(full_response)
        else:
            # Call OpenAI with the context
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"You are a highly advanced AI. Answer the user strictly using this context:\n\n{context}"},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            
            # Stream the response beautifully
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            # Remove the cursor block when finished
            message_placeholder.markdown(full_response)
            
        # Save assistant response to state
        st.session_state.messages.append({"role": "assistant", "content": full_response})
