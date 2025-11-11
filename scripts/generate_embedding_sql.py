#!/usr/bin/env python3
"""
Generate SQL UPDATE statements to add embeddings to documents.
Run this, then copy the output SQL into Supabase SQL Editor.
"""
import os
from openai import OpenAI
from supabase import create_client

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Get all documents without embeddings
print("📡 Fetching documents from Supabase...")
response = supabase.table("documents").select("id, content, title").is_("embedding", "null").execute()
documents = response.data

if not documents:
    print("✅ All documents already have embeddings!")
    exit(0)

print(f"Found {len(documents)} documents without embeddings\n")
print("Generating embeddings and SQL...\n")
print("=" * 80)
print("-- Copy everything below this line and paste into Supabase SQL Editor")
print("=" * 80)
print()

for doc in documents:
    try:
        # Generate embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=doc["content"]
        )
        embedding = embedding_response.data[0].embedding
        
        # Format as PostgreSQL array
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Generate SQL
        print(f"-- Update: {doc['title']}")
        print(f"UPDATE documents")
        print(f"SET embedding = '{embedding_str}'::vector")
        print(f"WHERE id = '{doc['id']}';")
        print()
        
    except Exception as e:
        print(f"-- ERROR for {doc['title']}: {e}")
        print()

print("=" * 80)
print("-- End of SQL")
print("=" * 80)
print()
print("✅ SQL generated! Copy the SQL above and run it in Supabase SQL Editor.")
