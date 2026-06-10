import streamlit as st
import os
import random
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from supabase import create_client

# Definitive Global Coordinates Registry for Physical Node Mapping
GLOBAL_HUBS = {
    "LONDON": (51.5074, -0.1278),
    "SINGAPORE": (1.3521, 103.8198),
    "TOKYO": (35.6762, 139.6503),
    "FRANKFURT": (50.1109, 8.6821),
    "NEW YORK": (40.7128, -74.0060),
    "SAN FRANCISCO": (37.7749, -122.4194),
    "DUBAI": (25.2048, 55.2708),
    "PARIS": (48.8566, 2.3522)
}

def get_clients():
    """Initializes and provides authenticated cloud client architecture connections."""
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return supabase, openai_client

def get_embedding(text):
    """Generates highly dense 1536-dimensional vector representations using OpenAIs semantic model."""
    _, openai_client = get_clients()
    response = openai_client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def parse_metadata_tags(text):
    """
    Strips raw string files down to isolate exact system parameter keys.
    Processes custom tag payloads smoothly with programmatic validation checks.
    """
    lines = text.split("\n")
    meta = {
        "classification": "general_knowledge",
        "location": "UNKNOWN HUB",
        "risk": 15,
        "export_area": "GLOBAL METRICS"
    }
    
    for line in lines:
        line_upper = line.upper().strip()
        if line_upper.startswith("CLASSIFICATION:"):
            val = line_upper.split(":", 1)[1].strip()
            if "COMPLIANCE" in val: meta["classification"] = "compliance_assets"
            elif "REGULATORY" in val: meta["classification"] = "regulatory_docs"
            elif "INTERNAL" in val: meta["classification"] = "internal_documents"
            else: meta["classification"] = "general_knowledge"
            
        elif line_upper.startswith("LOCATION:"):
            meta["location"] = line.split(":", 1)[1].strip()
            
        elif line_upper.startswith("RISK_SCORE:"):
            try:
                meta["risk"] = int(line_upper.split(":", 1)[1].replace("%", "").strip())
            except ValueError:
                meta["risk"] = 25
                
        elif line_upper.startswith("EXPORT_AREA:"):
            meta["export_area"] = line.split(":", 1)[1].strip()
            
    return meta

def process_and_upload_file(file_path, display_name):
    """
    Parses structural documents, slices content into logical semantic chunks,
    extracts geospatial data, coordinates, and routes vectors straight into target relational tables.
    """
    supabase, _ = get_clients()
    
    loader = PyPDFLoader(file_path) if file_path.endswith(".pdf") else TextLoader(file_path)
    docs = loader.load()
    full_text = "\n".join([doc.page_content for doc in docs])
    
    # Extract explicit document parameters
    meta = parse_metadata_tags(full_text)
    
    # Geolocation resolution matching
    lat, lon = None, None
    lookup_key = meta["location"].upper()
    if lookup_key in GLOBAL_HUBS:
        base_lat, base_lon = GLOBAL_HUBS[lookup_key]
        lat = base_lat + random.uniform(-0.015, 0.015)
        lon = base_lon + random.uniform(-0.015, 0.015)
        
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    
    for chunk in chunks:
        embedding = get_embedding(chunk.page_content)
        supabase.table(meta["classification"]).insert({
            "file_name": display_name,
            "content": chunk.page_content,
            "location_hub": meta["location"],
            "lat": lat,
            "lon": lon,
            "individual_risk": meta["risk"],
            "export_domain": meta["export_area"],
            "embedding": embedding
        }).execute()
        
    return meta["classification"].upper()

def query_rag(question):
    """Executes a unified relational scan to provide real-time document context updates."""
    supabase, _ = get_clients()
    question_embedding = get_embedding(question)
    response = supabase.rpc("match_documents", {
        "query_embedding": question_embedding, 
        "match_threshold": 0.25, 
        "match_count": 7
    }).execute()
    return "\n\n".join([f"[Source: {doc['file_name']} | Risk: {doc['individual_risk']}%]: {doc['content']}" for doc in response.data])

def get_document_stats():
    """Aggregates all real-time structured telemetry data from the database layer."""
    tables = ["compliance_assets", "regulatory_docs", "internal_documents", "general_knowledge"]
    stats = []
    try:
        supabase, _ = get_clients()
        for t in tables:
            res = supabase.table(t).select("id, file_name, location_hub, lat, lon, individual_risk, export_domain").execute()
            for row in res.data:
                stats.append({
                    "id": row["id"],
                    "file_name": row["file_name"],
                    "category": t.replace("_", " ").upper(),
                    "location_hub": row.get("location_hub", "UNKNOWN"),
                    "lat": row.get("lat"),
                    "lon": row.get("lon"),
                    "individual_risk": row.get("individual_risk", 0),
                    "export_domain": row.get("export_domain", "GLOBAL METRICS")
                })
        return stats
    except Exception as e:
        return []
