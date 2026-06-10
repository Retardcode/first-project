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
    """Scans text and routes it to the correct Supabase table. Defaults to General."""
    text_upper = text.upper()
    if "CLASSIFICATION: COMPLIANCE" in text_upper:
        return "compliance_assets"
    elif "CLASSIFICATION: REGULATORY" in text_upper:
        return "regulatory_docs"
    elif "CLASSIFICATION: INTERNAL" in text_upper:
        return "internal_documents"
    else:
        # Fallback for unclassified files
        return "general_knowledge" 

def process_and_upload_file(file_path):
    """Extract, classify, chunk, embed, and upload directly to the target table."""
    supabase, _ = get_clients()
    
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)
    
    docs = loader.load()
    full_text = " ".join([doc.page_content for doc in docs])
    
    # AI decides which table ("folder") to use
    target_table = auto_classify_text(full_text)
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    for chunk in chunks:
        embedding = get_embedding(chunk.page_content)
        # Dynamically injects into the correct table
        supabase.table(target_table).insert({
            "content": chunk.page_content,
            "embedding": embedding
        }).execute()
        
    return target_table

def query_rag(question):
    """Uses the Master SQL function to search across all 4 tables simultaneously."""
    supabase, _ = get_clients()
    question_embedding = get_embedding(question)
    
    response = supabase.rpc("match_documents", {
        "query_embedding": question_embedding,
        "match_threshold": 0.3, # Deep search threshold
        "match_count": 6
    }).execute()
    
    return "\n\n".join([doc['content'] for doc in response.data])

def get_document_stats():
    """Scans all 4 tables to aggregate system analytics."""
    tables = ["compliance_assets", "regulatory_docs", "internal_documents", "general_knowledge"]
    stats = []
    try:
        supabase, _ = get_clients()
        for t in tables:
            res = supabase.table(t).select("id").execute()
            for row in res.data:
                # Format the table name to look pretty on the UI
                stats.append({"id": row["id"], "category": t.replace("_", " ").upper()})
        return stats
    except Exception as e:
        return []
