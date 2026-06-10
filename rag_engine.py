import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from supabase import create_client

def get_clients():
    """Initialize secure connections using Streamlit Secrets."""
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return supabase, openai_client

def get_embedding(text):
    """Generate vector embeddings for text chunks."""
    _, openai_client = get_clients()
    response = openai_client.embeddings.create(
        input=text, model="text-embedding-3-small"
    )
    return response.data[0].embedding

def auto_classify_text(text):
    """Scans text for classification triggers and auto-routes the document."""
    text_upper = text.upper()
    if "CLASSIFICATION: COMPLIANCE" in text_upper:
        return "compliance assets"
    elif "CLASSIFICATION: REGULATORY" in text_upper:
        return "regulatory docs"
    elif "CLASSIFICATION: INTERNAL" in text_upper:
        return "internal documents"
    elif "CLASSIFICATION: GENERAL" in text_upper:
        return "general knowledge"
    else:
        return "uncategorized"

def process_and_upload_file(file_path):
    """Extract, auto-classify, chunk, embed, and upload document data."""
    supabase, _ = get_clients()
    
    # 1. Detect file type and load
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)
    
    docs = loader.load()
    
    # 2. Extract full text to determine category
    full_text = " ".join([doc.page_content for doc in docs])
    category_name = auto_classify_text(full_text)
    
    # 3. Chunk the Text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    # 4. Vectorize and Store with the Auto-Detected Category
    for chunk in chunks:
        embedding = get_embedding(chunk.page_content)
        supabase.table("documents").insert({
            "content": chunk.page_content,
            "embedding": embedding,
            "category": category_name 
        }).execute()
        
    return category_name # Return category to the UI to show the user where it went

def query_rag(question):
    """Search the vector database with a low threshold for deep context."""
    supabase, _ = get_clients()
    question_embedding = get_embedding(question)
    
    # Lowered threshold to 0.3 and increased count to 6 for broader, deeper AI understanding
    response = supabase.rpc("match_documents", {
        "query_embedding": question_embedding,
        "match_threshold": 0.3,
        "match_count": 6
    }).execute()
    
    return "\n\n".join([doc['content'] for doc in response.data])

def get_document_stats():
    """Fetch live analytics from Supabase to power the Dashboard."""
    try:
        supabase, _ = get_clients()
        response = supabase.table("documents").select("id, category").execute()
        return response.data
    except Exception as e:
        return []
