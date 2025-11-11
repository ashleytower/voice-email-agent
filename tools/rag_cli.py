#!/usr/bin/env python3
"""
RAG CLI Tool - MCP-Optimized Knowledge Base Operations

This tool provides CLI commands for RAG operations using Supabase pgvector,
following the Code Execution with MCP pattern for maximum token efficiency.

Usage:
    python rag_cli.py search --query "What is our refund policy?" --limit 5
    python rag_cli.py add --text "Our refund policy is..." --metadata '{"type":"policy"}'
    python rag_cli.py delete --id "abc123"
"""
import argparse
import json
import sys
import os
from typing import Dict, Any, List
from supabase import create_client, Client
from openai import OpenAI


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)


def get_openai_client() -> OpenAI:
    """Initialize and return OpenAI client for embeddings."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set")
    return OpenAI(api_key=api_key)


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    client = get_openai_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def search_knowledge(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search the knowledge base using vector similarity."""
    try:
        supabase = get_supabase_client()
        query_embedding = generate_embedding(query)
        
        # Use Supabase RPC function for vector similarity search
        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.7,
                "match_count": limit
            }
        ).execute()
        
        results = []
        for doc in response.data:
            results.append({
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "similarity": doc["similarity"]
            })
        
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def add_knowledge(text: str, metadata: str = "{}") -> Dict[str, Any]:
    """Add a new document to the knowledge base."""
    try:
        supabase = get_supabase_client()
        metadata_dict = json.loads(metadata)
        embedding = generate_embedding(text)
        
        response = supabase.table("documents").insert({
            "content": text,
            "metadata": metadata_dict,
            "embedding": embedding
        }).execute()
        
        doc_id = response.data[0]["id"] if response.data else None
        return {"status": "success", "id": doc_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_knowledge(doc_id: str) -> Dict[str, Any]:
    """Delete a document from the knowledge base."""
    try:
        supabase = get_supabase_client()
        supabase.table("documents").delete().eq("id", doc_id).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_knowledge(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """List documents in the knowledge base."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("documents").select("id, content, metadata").range(offset, offset + limit - 1).execute()
        
        documents = []
        for doc in response.data:
            documents.append({
                "id": doc["id"],
                "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "metadata": doc["metadata"]
            })
        
        return {"status": "success", "documents": documents}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="RAG CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search knowledge base")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add document to knowledge base")
    add_parser.add_argument("--text", required=True, help="Document text content")
    add_parser.add_argument("--metadata", default="{}", help="Metadata as JSON string")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete document from knowledge base")
    delete_parser.add_argument("--id", required=True, help="Document ID")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List documents in knowledge base")
    list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    list_parser.add_argument("--offset", type=int, default=0, help="Offset for pagination")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    result = {}
    if args.command == "search":
        result = search_knowledge(args.query, args.limit)
    elif args.command == "add":
        result = add_knowledge(args.text, args.metadata)
    elif args.command == "delete":
        result = delete_knowledge(args.id)
    elif args.command == "list":
        result = list_knowledge(args.limit, args.offset)
    
    # Output result as JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
