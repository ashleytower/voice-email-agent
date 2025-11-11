#!/usr/bin/env python3
"""
RAG System Demonstration Test

This test demonstrates the complete RAG workflow:
1. Ingest sample business data (refund policy, email templates, etc.)
2. Query the system with a business question
3. Retrieve relevant documents using vector similarity search
4. Generate an answer using the retrieved context

Run this test to verify your Supabase setup is working correctly.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from openai import OpenAI


def test_rag_system_end_to_end():
    """
    Demonstrates the RAG system successfully retrieving business knowledge
    to answer an email-related question.
    """
    print("\n" + "="*70)
    print("RAG SYSTEM DEMONSTRATION")
    print("="*70 + "\n")
    
    # Step 1: Initialize clients
    print("📡 Step 1: Connecting to Supabase and OpenAI...")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not all([supabase_url, supabase_key, openai_key]):
        print("❌ ERROR: Missing environment variables")
        print("   Please set: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    openai_client = OpenAI(api_key=openai_key)
    print("✅ Connected successfully\n")
    
    # Step 2: Check if we have data
    print("📊 Step 2: Checking for existing business data...")
    response = supabase.table("documents").select("count", count="exact").execute()
    doc_count = response.count
    print(f"   Found {doc_count} documents in the knowledge base")
    
    if doc_count == 0:
        print("⚠️  No data found. Run: python scripts/ingest_business_data.py --sample")
        return False
    print("✅ Data is available\n")
    
    # Step 3: User asks a question
    user_question = "What is our refund policy?"
    print(f"❓ Step 3: User Question")
    print(f"   \"{user_question}\"\n")
    
    # Step 4: Generate embedding for the question
    print("🔢 Step 4: Generating embedding for the question...")
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=user_question
    )
    query_embedding = embedding_response.data[0].embedding
    print(f"✅ Generated {len(query_embedding)}-dimensional embedding\n")
    
    # Step 5: Search the knowledge base
    print("🔍 Step 5: Searching knowledge base with vector similarity...")
    search_response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": 3
        }
    ).execute()
    
    results = search_response.data
    print(f"✅ Found {len(results)} relevant documents\n")
    
    if not results:
        print("❌ No relevant documents found")
        return False
    
    # Step 6: Display retrieved documents
    print("📄 Step 6: Retrieved Documents")
    print("-" * 70)
    for i, doc in enumerate(results, 1):
        print(f"\n   Document {i}:")
        print(f"   Title: {doc.get('title', 'Untitled')}")
        print(f"   Type: {doc.get('doc_type')}")
        print(f"   Similarity: {doc.get('similarity', 0):.2%}")
        print(f"   Content Preview: {doc['content'][:150]}...")
    print("\n" + "-" * 70 + "\n")
    
    # Step 7: Generate answer using retrieved context
    print("🤖 Step 7: Generating answer with LLM...")
    
    # Build context from retrieved documents
    context = "\n\n".join([
        f"Document: {doc.get('title', 'Untitled')}\n{doc['content']}"
        for doc in results
    ])
    
    # Generate answer
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful business assistant. Answer the user's question based on the provided context. Be concise and accurate."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {user_question}\n\nAnswer:"
            }
        ],
        temperature=0.3
    )
    
    answer = completion.choices[0].message.content
    print("✅ Answer generated\n")
    
    # Step 8: Display final answer
    print("💬 Step 8: Final Answer")
    print("=" * 70)
    print(f"\n{answer}\n")
    print("=" * 70 + "\n")
    
    # Step 9: Verify answer quality
    print("✅ Step 9: Verification")
    
    # Check if the answer mentions key refund policy terms
    refund_keywords = ["refund", "30 days", "return", "credit"]
    found_keywords = [kw for kw in refund_keywords if kw.lower() in answer.lower()]
    
    if found_keywords:
        print(f"   ✅ Answer contains expected keywords: {', '.join(found_keywords)}")
        print("   ✅ RAG system is working correctly!")
        success = True
    else:
        print("   ⚠️  Answer may not be accurate")
        success = False
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")
    
    return success


def test_contact_retrieval():
    """Test retrieving contact information."""
    print("\n" + "="*70)
    print("CONTACT RETRIEVAL TEST")
    print("="*70 + "\n")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([supabase_url, supabase_key]):
        print("❌ ERROR: Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("📇 Retrieving contacts...")
    response = supabase.table("contacts").select("*").limit(5).execute()
    
    if response.data:
        print(f"✅ Found {len(response.data)} contacts\n")
        for contact in response.data:
            print(f"   • {contact.get('name')} ({contact.get('email')})")
            print(f"     Company: {contact.get('company')}")
            print(f"     Type: {contact.get('relationship_type')}\n")
        return True
    else:
        print("⚠️  No contacts found. Run: python scripts/ingest_business_data.py --sample")
        return False


def test_proposal_templates():
    """Test retrieving proposal templates."""
    print("\n" + "="*70)
    print("PROPOSAL TEMPLATE TEST")
    print("="*70 + "\n")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([supabase_url, supabase_key]):
        print("❌ ERROR: Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("📄 Retrieving proposal templates...")
    response = supabase.table("proposals").select("*").eq("is_template", True).execute()
    
    if response.data:
        print(f"✅ Found {len(response.data)} proposal templates\n")
        for proposal in response.data:
            print(f"   • {proposal.get('title')}")
            print(f"     Template Name: {proposal.get('template_name')}")
            print(f"     Preview: {proposal.get('content')[:100]}...\n")
        return True
    else:
        print("⚠️  No proposal templates found. Run: python scripts/ingest_business_data.py --sample")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting RAG System Tests...\n")
    
    # Run all tests
    test1 = test_rag_system_end_to_end()
    test2 = test_contact_retrieval()
    test3 = test_proposal_templates()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"RAG System Test: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Contact Retrieval: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Proposal Templates: {'✅ PASS' if test3 else '❌ FAIL'}")
    print("="*70 + "\n")
    
    if all([test1, test2, test3]):
        print("🎉 All tests passed! Your Supabase RAG system is ready to use.\n")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check your Supabase setup.\n")
        sys.exit(1)
