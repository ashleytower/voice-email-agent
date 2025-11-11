#!/usr/bin/env python3
"""
Comprehensive Business Data Ingestion Script

This script ingests ALL types of business data into Supabase:
- FAQs
- Proposal templates
- Contacts
- Email templates
- Policies and procedures
- General business knowledge

Usage:
    # Ingest from structured JSON file
    python ingest_business_data.py --json /path/to/business_data.json
    
    # Ingest sample data for testing
    python ingest_business_data.py --sample
    
    # Ingest from directory (auto-categorize by folder structure)
    python ingest_business_data.py --dir /path/to/business/data
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from supabase import create_client, Client
from openai import OpenAI


def get_clients():
    """Initialize Supabase and OpenAI clients."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not all([supabase_url, supabase_key, openai_key]):
        raise ValueError("Required environment variables not set")
    
    supabase = create_client(supabase_url, supabase_key)
    openai_client = OpenAI(api_key=openai_key)
    
    return supabase, openai_client


def generate_embedding(text: str, openai_client: OpenAI) -> List[float]:
    """Generate embedding for text."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def ingest_document(supabase: Client, openai_client: OpenAI, doc: Dict[str, Any]) -> bool:
    """
    Ingest a single document into the knowledge base.
    
    Args:
        doc: Dictionary with keys: content, doc_type, category, title (optional)
    """
    try:
        content = doc.get("content", "")
        if not content.strip():
            print(f"⚠️  Skipping empty document: {doc.get('title', 'Untitled')}")
            return False
        
        embedding = generate_embedding(content, openai_client)
        
        data = {
            "content": content,
            "embedding": embedding,
            "doc_type": doc.get("doc_type", "general"),
            "category": doc.get("category", "general"),
            "title": doc.get("title"),
            "source": doc.get("source"),
            "metadata": doc.get("metadata", {})
        }
        
        response = supabase.table("documents").insert(data).execute()
        
        print(f"✅ Ingested: {doc.get('title', 'Untitled')} ({doc.get('doc_type')})")
        return True
        
    except Exception as e:
        print(f"❌ Error ingesting document: {e}")
        return False


def ingest_contact(supabase: Client, contact: Dict[str, Any]) -> bool:
    """Ingest a contact into the database."""
    try:
        required_fields = ["email"]
        if not all(field in contact for field in required_fields):
            print(f"⚠️  Skipping contact: missing required fields")
            return False
        
        data = {
            "email": contact["email"],
            "name": contact.get("name"),
            "company": contact.get("company"),
            "role": contact.get("role"),
            "phone": contact.get("phone"),
            "relationship_type": contact.get("relationship_type", "client"),
            "notes": contact.get("notes"),
            "metadata": contact.get("metadata", {})
        }
        
        # Upsert (insert or update if exists)
        response = supabase.table("contacts").upsert(data, on_conflict="email").execute()
        
        print(f"✅ Ingested contact: {contact.get('name', contact['email'])}")
        return True
        
    except Exception as e:
        print(f"❌ Error ingesting contact: {e}")
        return False


def ingest_proposal_template(supabase: Client, proposal: Dict[str, Any]) -> bool:
    """Ingest a proposal template."""
    try:
        required_fields = ["title", "content"]
        if not all(field in proposal for field in required_fields):
            print(f"⚠️  Skipping proposal: missing required fields")
            return False
        
        data = {
            "title": proposal["title"],
            "content": proposal["content"],
            "is_template": True,
            "template_name": proposal.get("template_name", proposal["title"]),
            "metadata": proposal.get("metadata", {})
        }
        
        response = supabase.table("proposals").insert(data).execute()
        
        print(f"✅ Ingested proposal template: {proposal['title']}")
        return True
        
    except Exception as e:
        print(f"❌ Error ingesting proposal: {e}")
        return False


def ingest_faq(supabase: Client, faq: Dict[str, Any]) -> bool:
    """Ingest an FAQ."""
    try:
        required_fields = ["question", "answer"]
        if not all(field in faq for field in required_fields):
            print(f"⚠️  Skipping FAQ: missing required fields")
            return False
        
        # Get or create category
        category_name = faq.get("category", "General")
        category_response = supabase.table("faq_categories").select("id").eq("name", category_name).execute()
        
        if not category_response.data:
            # Create category
            cat_response = supabase.table("faq_categories").insert({"name": category_name}).execute()
            category_id = cat_response.data[0]["id"]
        else:
            category_id = category_response.data[0]["id"]
        
        data = {
            "category_id": category_id,
            "question": faq["question"],
            "answer": faq["answer"],
            "keywords": faq.get("keywords", [])
        }
        
        response = supabase.table("faqs").insert(data).execute()
        
        print(f"✅ Ingested FAQ: {faq['question'][:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error ingesting FAQ: {e}")
        return False


def ingest_from_json(file_path: Path) -> tuple:
    """
    Ingest data from a structured JSON file.
    
    Expected format:
    {
        "documents": [...],
        "contacts": [...],
        "proposals": [...],
        "faqs": [...]
    }
    """
    supabase, openai_client = get_clients()
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    stats = {"documents": 0, "contacts": 0, "proposals": 0, "faqs": 0, "errors": 0}
    
    # Ingest documents
    for doc in data.get("documents", []):
        if ingest_document(supabase, openai_client, doc):
            stats["documents"] += 1
        else:
            stats["errors"] += 1
    
    # Ingest contacts
    for contact in data.get("contacts", []):
        if ingest_contact(supabase, contact):
            stats["contacts"] += 1
        else:
            stats["errors"] += 1
    
    # Ingest proposals
    for proposal in data.get("proposals", []):
        if ingest_proposal_template(supabase, proposal):
            stats["proposals"] += 1
        else:
            stats["errors"] += 1
    
    # Ingest FAQs
    for faq in data.get("faqs", []):
        if ingest_faq(supabase, faq):
            stats["faqs"] += 1
        else:
            stats["errors"] += 1
    
    return stats


def ingest_sample_data() -> tuple:
    """Ingest comprehensive sample business data."""
    supabase, openai_client = get_clients()
    
    stats = {"documents": 0, "contacts": 0, "proposals": 0, "faqs": 0, "errors": 0}
    
    print("\n📝 Ingesting sample business data...\n")
    
    # Sample documents (knowledge base)
    documents = [
        {
            "title": "Refund Policy",
            "content": "Our refund policy allows customers to request a full refund within 30 days of purchase for any reason. After 30 days, we offer store credit for returns. All refunds are processed within 5-7 business days to the original payment method. For defective products, we offer immediate replacement or full refund regardless of the purchase date.",
            "doc_type": "policy",
            "category": "customer_service"
        },
        {
            "title": "Onboarding Email Template",
            "content": "Subject: Welcome to [Company Name]!\n\nHi [First Name],\n\nWe're thrilled to have you join us! Here's what you can expect in your first week:\n\n1. Access to your dashboard (link below)\n2. A welcome call from your account manager\n3. Getting started guide and resources\n\nYour dashboard: [LINK]\n\nIf you have any questions, reply to this email or call us at [PHONE].\n\nBest regards,\n[Your Name]",
            "doc_type": "email_template",
            "category": "onboarding"
        },
        {
            "title": "Company Mission Statement",
            "content": "Our mission is to empower businesses with innovative AI solutions that streamline operations and enhance productivity. We believe in building technology that is accessible, reliable, and transformative. Our core values are: Innovation, Integrity, Customer Success, and Continuous Learning.",
            "doc_type": "general",
            "category": "company"
        },
        {
            "title": "Support Hours and Contact",
            "content": "Our customer support team is available Monday through Friday, 9 AM to 6 PM EST. For urgent issues outside these hours, please email emergency@company.com. We also offer 24/7 chat support for enterprise customers. Phone: 1-800-555-0123. Email: support@company.com",
            "doc_type": "policy",
            "category": "support"
        },
        {
            "title": "Standard Proposal Template",
            "content": "[CLIENT NAME] - Project Proposal\n\nExecutive Summary:\n[Brief overview of the project and value proposition]\n\nScope of Work:\n1. [Deliverable 1]\n2. [Deliverable 2]\n3. [Deliverable 3]\n\nTimeline:\n- Phase 1: [Duration]\n- Phase 2: [Duration]\n- Phase 3: [Duration]\n\nInvestment:\nTotal Project Cost: $[AMOUNT]\nPayment Terms: [TERMS]\n\nNext Steps:\n[Call to action]",
            "doc_type": "proposal_template",
            "category": "sales"
        }
    ]
    
    for doc in documents:
        if ingest_document(supabase, openai_client, doc):
            stats["documents"] += 1
        else:
            stats["errors"] += 1
    
    # Sample contacts
    contacts = [
        {
            "name": "John Smith",
            "email": "john.smith@acmecorp.com",
            "company": "Acme Corporation",
            "role": "CEO",
            "relationship_type": "client",
            "notes": "Key decision maker. Prefers email communication."
        },
        {
            "name": "Sarah Johnson",
            "email": "sarah.j@techstartup.io",
            "company": "Tech Startup Inc",
            "role": "CTO",
            "relationship_type": "prospect",
            "notes": "Interested in enterprise plan. Follow up in Q1."
        },
        {
            "name": "Michael Chen",
            "email": "m.chen@consulting.com",
            "company": "Chen Consulting",
            "role": "Partner",
            "relationship_type": "partner",
            "notes": "Referral partner. Monthly check-ins."
        }
    ]
    
    for contact in contacts:
        if ingest_contact(supabase, contact):
            stats["contacts"] += 1
        else:
            stats["errors"] += 1
    
    # Sample proposal templates
    proposals = [
        {
            "title": "Consulting Services Proposal",
            "template_name": "consulting_standard",
            "content": "# Consulting Services Proposal\n\n## Overview\nWe propose a comprehensive consulting engagement to help [CLIENT] achieve [GOALS].\n\n## Services Included\n- Strategic planning and roadmap development\n- Process optimization\n- Technology assessment\n- Implementation support\n\n## Timeline\n8-12 weeks\n\n## Investment\n$25,000 - $50,000 depending on scope"
        },
        {
            "title": "Software Development Proposal",
            "template_name": "software_dev_standard",
            "content": "# Software Development Proposal\n\n## Project Scope\nDevelopment of [APPLICATION] with the following features:\n- Feature 1\n- Feature 2\n- Feature 3\n\n## Technology Stack\n[STACK]\n\n## Deliverables\n- Fully functional application\n- Source code\n- Documentation\n- 3 months support\n\n## Timeline\n12-16 weeks\n\n## Investment\n$75,000 - $150,000"
        }
    ]
    
    for proposal in proposals:
        if ingest_proposal_template(supabase, proposal):
            stats["proposals"] += 1
        else:
            stats["errors"] += 1
    
    # Sample FAQs
    faqs = [
        {
            "category": "Billing",
            "question": "How do I update my payment method?",
            "answer": "You can update your payment method by logging into your account, navigating to Settings > Billing, and clicking 'Update Payment Method'. We accept all major credit cards and ACH transfers.",
            "keywords": ["payment", "billing", "credit card", "update"]
        },
        {
            "category": "Technical",
            "question": "What are the system requirements?",
            "answer": "Our platform works on any modern web browser (Chrome, Firefox, Safari, Edge). For mobile, we support iOS 13+ and Android 10+. No installation required.",
            "keywords": ["requirements", "browser", "mobile", "compatibility"]
        },
        {
            "category": "Account",
            "question": "How do I reset my password?",
            "answer": "Click 'Forgot Password' on the login page, enter your email, and we'll send you a reset link. The link expires in 24 hours. If you don't receive it, check your spam folder.",
            "keywords": ["password", "reset", "login", "account"]
        }
    ]
    
    for faq in faqs:
        if ingest_faq(supabase, faq):
            stats["faqs"] += 1
        else:
            stats["errors"] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Ingest business data into Supabase")
    parser.add_argument("--json", help="Path to JSON file with structured data")
    parser.add_argument("--sample", action="store_true", help="Ingest sample data")
    parser.add_argument("--dir", help="Directory containing business data files")
    
    args = parser.parse_args()
    
    if args.sample:
        stats = ingest_sample_data()
    elif args.json:
        stats = ingest_from_json(Path(args.json))
    else:
        print("❌ Please specify --sample or --json")
        parser.print_help()
        return
    
    print(f"\n{'='*60}")
    print(f"📊 Ingestion Complete!")
    print(f"{'='*60}")
    print(f"✅ Documents: {stats['documents']}")
    print(f"✅ Contacts: {stats['contacts']}")
    print(f"✅ Proposals: {stats['proposals']}")
    print(f"✅ FAQs: {stats['faqs']}")
    print(f"❌ Errors: {stats['errors']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
