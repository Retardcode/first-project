import os
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing environment variables. Check your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. DATA
data_to_seed = [
    {
        "title": "Lithium-Ion Storage Requirements",
        "content": "Any business storing consumer electronics containing lithium-ion battery modules in quantities exceeding 50 aggregate units must deploy a dedicated thermal runaway mitigation system."
    },
    {
        "title": "Ventilation Standards",
        "content": "Mechanical ventilation arrays must be capable of executing 6 complete air exchanges per hour in all designated battery storage zones."
    },
    {
        "title": "Structural Fire Containment",
        "content": "Physical fire-retardant partitioning must be rated for a minimum of 2 hours of structural containment to prevent the spread of thermal runaway events."
    }
]

# 3. THE HARD RESET
print("Executing Hard Reset on Supabase...")
# Wipe the Math Brain (Structured Data)
supabase.table("compliance_assets").delete().neq("id", 0).execute()
# Wipe the Vector Brain (AI Docs)
supabase.table("regulatory_docs").delete().neq("title", "placeholder").execute()
print("Databases wiped clean.")

# 4. EXECUTION
print("Seeding base vectors...")
for item in data_to_seed:
    response = client.embeddings.create(
        input=item["content"],
        model="text-embedding-3-small"
    )
    
    supabase.table("regulatory_docs").insert({
        "title": item["title"],
        "content": item["content"],
        "embedding": response.data[0].embedding
    }).execute()
    print(f"✔️ Seeded: {item['title']}")

print("Reset complete! Ready for Phase 2 operations.")