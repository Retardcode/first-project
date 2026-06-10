import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from supabase import create_client

def get_clients():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return supabase, openai_client

def get_embedding(text):
    _, openai_client = get_clients()
    response = openai_client.embeddings.create(
        input=text, model="text-embedding-3-small"
    )
    return response.data[0].embedding

def process_and_upload_file(file_path):
    supabase, _ = get_clients()
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    for chunk in chunks:
        embedding = get_embedding(chunk.page_content)
        supabase.table("documents").insert({
            "content": chunk.page_content,
            "embedding": embedding
        }).execute()

def query_rag(question):
    supabase, _ = get_clients()
    question_embedding = get_embedding(question)
    
    response = supabase.rpc("match_documents", {
        "query_embedding": question_embedding,
        "match_threshold": 0.5,
        "match_count": 3
    }).execute()
    
    return "\n".join([doc['content'] for doc in response.data])
