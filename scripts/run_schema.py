#!/usr/bin/env python3
"""
Run the complete database schema on Supabase.

This script executes the SQL schema file directly using psycopg2.
"""
import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2...")
    os.system("sudo pip3 install psycopg2-binary --quiet")
    import psycopg2


def run_schema():
    """Execute the complete SQL schema."""
    # Read the schema file
    schema_path = Path(__file__).parent / "setup_supabase_complete.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Build connection string
    # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    project_ref = "zkqcwgumwszgxjuwovws"
    
    # Extract password from service_role key (it's the database password)
    # For Supabase, we need to get the actual database password
    # Let's use the direct Supabase connection
    
    print("⚠️  To run the schema, we need the database password.")
    print("   This is different from the API keys.")
    print()
    print("To get it:")
    print("1. Go to: https://supabase.com/dashboard/project/zkqcwgumwszgxjuwovws/settings/database")
    print("2. Under 'Connection string', click 'URI'")
    print("3. Copy the password from the connection string")
    print()
    password = input("Enter your database password: ").strip()
    
    if not password:
        print("❌ No password provided")
        return False
    
    # Connection string
    conn_string = f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    print("\n📡 Connecting to Supabase database...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected successfully\n")
        print("🔧 Executing schema (this may take 30 seconds)...")
        
        # Execute the schema
        cursor.execute(schema_sql)
        
        print("✅ Schema executed successfully!\n")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = run_schema()
    sys.exit(0 if success else 1)
