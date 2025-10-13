#!/usr/bin/env python3
"""Get all tables and their columns from Supabase."""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import json

# Load env
env_file = Path(__file__).parent.parent / "env_files" / "supabase.env"
load_dotenv(env_file)

url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

client = create_client(url, service_key)

# List of known tables
tables = [
    "users",
    "conversation_sessions", 
    "conversation_messages",
    "news_articles"
]

print("=" * 100)
print("📊 SUPABASE DATABASE SCHEMA")
print("=" * 100)

for table_name in tables:
    print(f"\n{'='*100}")
    print(f"📋 TABLE: {table_name}")
    print(f"{'='*100}")
    
    try:
        # Get one row to see structure
        result = client.table(table_name).select("*").limit(1).execute()
        
        # Get count
        count_result = client.table(table_name).select("*", count="exact").limit(0).execute()
        print(f"📊 Total rows: {count_result.count}")
        
        if result.data:
            row = result.data[0]
            print(f"\n📝 Columns ({len(row)}):")
            print("-" * 100)
            print(f"{'Column Name':<30} {'Type':<15} {'Sample Value':<55}")
            print("-" * 100)
            
            for key, value in row.items():
                value_type = type(value).__name__
                if value_type == 'list':
                    sample = f"{value} (length: {len(value)})"
                elif value_type == 'dict':
                    sample = f"{{...}} (keys: {', '.join(list(value.keys())[:3])})"
                elif value_type == 'str' and len(value) > 50:
                    sample = value[:47] + "..."
                else:
                    sample = str(value)
                
                print(f"{key:<30} {value_type:<15} {sample:<55}")
        else:
            # Empty table - try to get structure differently
            print(f"\n⚠️  Table is empty, attempting to fetch structure...")
            # Make a query that will fail to get column info
            try:
                result = client.table(table_name).select("*").limit(0).execute()
                print(f"   Table exists but is empty")
            except Exception as e:
                print(f"   Error: {e}")
    
    except Exception as e:
        print(f"❌ Error accessing table: {e}")

print("\n" + "=" * 100)
print("✅ Schema inspection complete!")
print("=" * 100)

