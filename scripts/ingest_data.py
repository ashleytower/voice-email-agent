#!/usr/bin/env python3
"""
Data Ingestion Script for RAG Knowledge Base

This script ingests business data (FAQs, templates, policies) into the Supabase
knowledge base using the rag_cli.py tool.

Usage:
    python scripts/ingest_data.py --data-dir /path/to/business/data
"""
import argparse
import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict


def ingest_file(file_path: Path, metadata: Dict = None) -> bool:
    """
    Ingest a single file into the knowledge base.
    
    Args:
        file_path: Path to the file to ingest
        metadata: Optional metadata dictionary
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            print(f"⚠️  Skipping empty file: {file_path}")
            return False
        
        # Prepare metadata
        file_metadata = metadata or {}
        file_metadata.update({
            "filename": file_path.name,
            "file_type": file_path.suffix,
            "source": str(file_path)
        })
        
        metadata_json = json.dumps(file_metadata)
        
        # Call rag_cli.py to add the document
        result = subprocess.run(
            [
                "python", "tools/rag_cli.py", "add",
                "--text", content,
                "--metadata", metadata_json
            ],
            capture_output=True,
            text=True,
            cwd="/home/ubuntu/voice-email-agent"
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                print(f"✅ Ingested: {file_path.name} (ID: {data.get('id')})")
                return True
            else:
                print(f"❌ Failed to ingest {file_path.name}: {data.get('message')}")
                return False
        else:
            print(f"❌ Error ingesting {file_path.name}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception ingesting {file_path.name}: {e}")
        return False


def ingest_directory(data_dir: Path, recursive: bool = True) -> tuple:
    """
    Ingest all files from a directory.
    
    Args:
        data_dir: Path to the directory containing data files
        recursive: Whether to search subdirectories
    
    Returns:
        Tuple of (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0
    
    # Supported file extensions
    supported_extensions = {'.txt', '.md', '.json', '.csv'}
    
    # Get all files
    if recursive:
        files = [f for f in data_dir.rglob('*') if f.is_file() and f.suffix in supported_extensions]
    else:
        files = [f for f in data_dir.glob('*') if f.is_file() and f.suffix in supported_extensions]
    
    print(f"\n📂 Found {len(files)} files to ingest from {data_dir}\n")
    
    for file_path in files:
        # Determine metadata based on directory structure
        metadata = {
            "category": file_path.parent.name if file_path.parent != data_dir else "general"
        }
        
        if ingest_file(file_path, metadata):
            success_count += 1
        else:
            failure_count += 1
    
    return success_count, failure_count


def ingest_sample_data():
    """Ingest sample business data for demonstration."""
    sample_data = [
        {
            "content": "Our refund policy: Customers can request a full refund within 30 days of purchase. After 30 days, we offer store credit for returns. All refunds are processed within 5-7 business days.",
            "metadata": {"type": "policy", "category": "refunds"}
        },
        {
            "content": "Email template for new customer welcome: Subject: Welcome to [Company]! Body: Hi [Name], We're thrilled to have you join us. Here's what you can expect...",
            "metadata": {"type": "template", "category": "onboarding"}
        },
        {
            "content": "Company mission: We strive to deliver exceptional value to our customers through innovative solutions and outstanding service.",
            "metadata": {"type": "about", "category": "company"}
        },
        {
            "content": "Support hours: Our customer support team is available Monday-Friday, 9 AM - 6 PM EST. For urgent issues outside these hours, please email emergency@company.com",
            "metadata": {"type": "faq", "category": "support"}
        },
        {
            "content": "Proposal template: [Client Name] Proposal - Executive Summary: [Brief overview] - Scope of Work: [Detailed scope] - Timeline: [Project timeline] - Investment: [Pricing details]",
            "metadata": {"type": "template", "category": "sales"}
        }
    ]
    
    print("\n📝 Ingesting sample business data...\n")
    
    success_count = 0
    failure_count = 0
    
    for item in sample_data:
        metadata_json = json.dumps(item["metadata"])
        
        result = subprocess.run(
            [
                "python", "tools/rag_cli.py", "add",
                "--text", item["content"],
                "--metadata", metadata_json
            ],
            capture_output=True,
            text=True,
            cwd="/home/ubuntu/voice-email-agent"
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                print(f"✅ Ingested: {item['metadata']['category']} - {item['metadata']['type']}")
                success_count += 1
            else:
                print(f"❌ Failed: {data.get('message')}")
                failure_count += 1
        else:
            print(f"❌ Error: {result.stderr}")
            failure_count += 1
    
    return success_count, failure_count


def main():
    parser = argparse.ArgumentParser(description="Ingest business data into RAG knowledge base")
    parser.add_argument("--data-dir", help="Directory containing business data files")
    parser.add_argument("--sample", action="store_true", help="Ingest sample data for demonstration")
    parser.add_argument("--recursive", action="store_true", default=True, help="Search subdirectories")
    
    args = parser.parse_args()
    
    if args.sample:
        success, failure = ingest_sample_data()
    elif args.data_dir:
        data_dir = Path(args.data_dir)
        if not data_dir.exists():
            print(f"❌ Directory not found: {data_dir}")
            return
        success, failure = ingest_directory(data_dir, args.recursive)
    else:
        print("❌ Please specify --data-dir or --sample")
        parser.print_help()
        return
    
    print(f"\n{'='*50}")
    print(f"✅ Successfully ingested: {success}")
    print(f"❌ Failed: {failure}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
