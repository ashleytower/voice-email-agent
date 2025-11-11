#!/usr/bin/env python3
"""
Fixed document ingestion that properly handles vector embeddings.
Uses direct SQL execution instead of REST API for vector columns.
"""
import os
import psycopg2
from openai import OpenAI

# Sample documents
SAMPLE_DOCUMENTS = [
    {
        "title": "Refund Policy",
        "content": """Our refund policy allows customers to request a full refund within 30 days of purchase. 
        To request a refund, please contact support@company.com with your order number. 
        Refunds are processed within 5-7 business days and will be credited to the original payment method.""",
        "doc_type": "policy",
        "category": "customer_service"
    },
    {
        "title": "Welcome Email Template",
        "content": """Subject: Welcome to [Company Name]!

Hi [First Name],

Thank you for joining us! We're excited to have you as part of our community.

Here's what you can expect:
- Access to all premium features
- 24/7 customer support
- Regular updates and new features

If you have any questions, just reply to this email.

Best regards,
The [Company Name] Team""",
        "doc_type": "email_template",
        "category": "onboarding"
    },
    {
        "title": "Follow-up Email Template",
        "content": """Subject: Following up on our conversation

Hi [First Name],

I wanted to follow up on our recent conversation about [Topic]. 

I've attached some additional information that I think you'll find helpful.

Would you be available for a quick call next week to discuss next steps?

Looking forward to hearing from you.

Best,
[Your Name]""",
        "doc_type": "email_template",
        "category": "sales"
    },
    {
        "title": "Company Overview",
        "content": """We are a technology company specializing in AI-powered email automation solutions. 
        Our mission is to help businesses communicate more efficiently through intelligent automation.
        
        Founded in 2024, we serve clients across multiple industries including tech, healthcare, and finance.
        Our platform integrates with Gmail, Outlook, and other major email providers.""",
        "doc_type": "general",
        "category": "company"
    },
    {
        "title": "Pricing Information",
        "content": """Our pricing is simple and transparent:
        
        - Starter Plan: $29/month - Up to 1,000 emails
        - Professional Plan: $99/month - Up to 10,000 emails  
        - Enterprise Plan: Custom pricing - Unlimited emails
        
        All plans include 24/7 support and a 30-day money-back guarantee.
        Annual billing saves 20%.""",
        "doc_type": "general",
        "category": "sales"
    }
]


def get_db_password():
    """Get database password from user."""
    print("To ingest documents with vector embeddings, we need database access.")
    print()
    print("Get your database password:")
    print("1. Go to: https://supabase.com/dashboard/project/zkqcwgumwszgxjuwovws/settings/database")
    print("2. Under 'Connection string', the password is shown")
    print("3. Or use the 'Reset database password' button to create a new one")
    print()
    password = input("Enter database password (or press Enter to skip): ").strip()
    return password if password else None


def ingest_documents_with_sql(password):
    """Ingest documents using direct SQL connection."""
    project_ref = "zkqcwgumwszgxjuwovws"
    conn_string = f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    print("\n📡 Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Connected\n")
    
    # Initialize OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("📝 Ingesting documents with embeddings...")
    
    for doc in SAMPLE_DOCUMENTS:
        try:
            # Generate embedding
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=doc["content"]
            )
            embedding = response.data[0].embedding
            
            # Insert with SQL
            cursor.execute("""
                INSERT INTO documents (content, embedding, doc_type, category, title)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                doc["content"],
                embedding,
                doc["doc_type"],
                doc["category"],
                doc["title"]
            ))
            
            print(f"✅ Ingested: {doc['title']}")
            
        except Exception as e:
            print(f"❌ Error ingesting {doc['title']}: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Document ingestion complete!")


def ingest_documents_without_embeddings():
    """Fallback: ingest documents without embeddings using REST API."""
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("\n📝 Ingesting documents (without embeddings)...")
    print("⚠️  Note: RAG search won't work without embeddings")
    
    for doc in SAMPLE_DOCUMENTS:
        try:
            supabase.table("documents").insert({
                "content": doc["content"],
                "doc_type": doc["doc_type"],
                "category": doc["category"],
                "title": doc["title"]
            }).execute()
            
            print(f"✅ Ingested: {doc['title']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Documents ingested (without embeddings)")
    print("⚠️  To enable RAG search, you'll need to add embeddings later")


if __name__ == "__main__":
    password = get_db_password()
    
    if password:
        try:
            ingest_documents_with_sql(password)
        except Exception as e:
            print(f"\n❌ SQL ingestion failed: {e}")
            print("\nFalling back to REST API (without embeddings)...")
            ingest_documents_without_embeddings()
    else:
        ingest_documents_without_embeddings()
