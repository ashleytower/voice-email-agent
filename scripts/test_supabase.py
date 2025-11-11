#!/usr/bin/env python3
"""Test Supabase connection and verify tables."""
import os
from supabase import create_client

# Get credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"URL: {supabase_url}")
print(f"Key: {supabase_key[:20]}...")

# Create client
supabase = create_client(supabase_url, supabase_key)

# Test each table
tables = ["documents", "contacts", "proposals", "faqs", "faq_categories"]

for table in tables:
    try:
        response = supabase.table(table).select("count", count="exact").execute()
        print(f"✅ {table}: {response.count} rows")
    except Exception as e:
        print(f"❌ {table}: {e}")

# Try to insert a simple document
print("\nTrying to insert a test document...")
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Generate embedding
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input="test"
    )
    embedding = response.data[0].embedding
    
    # Insert
    result = supabase.table("documents").insert({
        "content": "Test document",
        "embedding": embedding,
        "doc_type": "test",
        "title": "Test"
    }).execute()
    
    print(f"✅ Insert successful: {result.data}")
except Exception as e:
    print(f"❌ Insert failed: {e}")
