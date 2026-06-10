import streamlit as st
import os
import random
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from supabase import create_client

# Dictionary of major global hubs to simulate AI entity extraction mapping
GLOBAL_HUBS = {
    "NEW YORK": (40.7128, -74.0060), "LONDON": (51.5074, -0.1278),
    "TOKYO": (35.6762, 139.6503), "SAN FRANCISCO": (37.7749, -122.4194),
    "SINGAPORE": (1.3521, 103.8198), "FRANKFURT": (50.1109, 8.6821),
    "PARIS": (48.8566, 2.3522), "HONG KONG": (22.3193, 114.1694),
    "SYDNEY": (-33.8688, 151.2093), "DUBAI": (25.2048, 55.2708)
}

def get_clients():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return supabase, openai_client

def get_embedding(text):
    _, openai_client = get_clients()
    response = openai_client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def auto_classify_text(text):
    text_upper = text.upper()
    if "CLASSIFICATION: COMPLIANCE" in text_upper: return "compliance_assets"
    elif "CLASSIFICATION: REGULATORY" in text_upper: return "regulatory_docs"
    elif "CLASSIFICATION: INTERNAL" in text_upper: return "internal_documents"
    else: return "general_knowledge"

def extract_geospatial_data(text):
    """Scans document text for global hubs and assigns coordinates with a slight random scatter to prevent overlapping map dots."""
    text_upper = text.upper()
    for city, coords in GLOBAL_HUBS.items():
        if city in text_upper:
            # Slight scatter so multiple documents in the same city are visible
            return coords[0] + random.uniform(-0.02, 0.02), coords[1] + random.uniform(-0.02, 0.02)
    return None, None

def process_and_upload_file(file_path):
    """Extract, classify, geo-tag, chunk, and upload."""
    supabase, _ = get_clients()
    
    loader = PyPDFLoader(file_path) if file_path.endswith(".pdf") else TextLoader(file_path)
    docs = loader.load()
    
    full_text = " ".join([doc.page_content for doc in docs])
    target_table = auto_classify_text(full_text)
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    for chunk in chunks:
        # Extract location data from the chunk
        lat, lon = extract_geospatial_data(chunk.page_content)
        embedding = get_embedding(chunk.page_content)
        
        supabase.table(target_table).insert({
            "content": chunk.page_content,
            "lat": lat,
            "lon": lon,
            "embedding": embedding
        }).execute()
        
    return target_table

def query_rag(question):
    supabase, _ = get_clients()
    question_embedding = get_embedding(question)
    response = supabase.rpc("match_documents", {
        "query_embedding": question_embedding, "match_threshold": 0.3, "match_count": 6
    }).execute()
    return "\n\n".join([doc['content'] for doc in response.data])

def get_document_stats():
    """Scans all 4 tables to aggregate system analytics and geolocation data."""
    tables = ["compliance_assets", "regulatory_docs", "internal_documents", "general_knowledge"]
    stats = []
    try:
        supabase, _ = get_clients()
        for t in tables:
            # Now fetching lat and lon for the interactive map
            res = supabase.table(t).select("id, lat, lon").execute()
            for row in res.data:
                stats.append({
                    "id": row["id"], 
                    "category": t.replace("_", " ").upper(),
                    "lat": row.get("lat"),
                    "lon": row.get("lon")
                })
        return stats
    except Exception as e:
        return []
