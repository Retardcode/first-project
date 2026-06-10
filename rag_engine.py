import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
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

def process_and_upload_file(file_path, category_name="general"):
    """Extract, chunk, embed, and upload document data with category tags."""
    supabase, _ = get_clients()
    
    # 1. Load and Extract Text
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # 2. Chunk the Text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    # 3. Vectorize and Store
    for chunk in chunks:
        embedding = get_embedding(chunk.page_content)
        
        # Insert into unified table with the category tag
        supabase.table("documents").insert({
            "content": chunk.page_content,
            "embedding": embedding,
            "category": category_name 
        }).execute()

def query_rag(question):
    """Search the vector database for relevant context."""
    supabase, _ = get_clients()
    question_embedding = get_embedding(question)
    
    # Perform vector similarity search across all documents
    response = supabase.rpc("match_documents", {
        "query_embedding": question_embedding,
        "match_threshold": 0.5,
        "match_count": 4
    }).execute()
    
    # Combine the matched chunks into a single context string
    return "\n\n".join([doc['content'] for doc in response.data])
