#!/usr/bin/env python3
"""Get column structure for existing tables."""
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

tables = ["users", "conversation_sessions", "conversation_messages", "news_articles"]

print("=" * 80)
print("📊 GETTING COLUMN STRUCTURE FOR ALL TABLES")
print("=" * 80)

for table_name in tables:
    print(f"\n{'='*80}")
    print(f"TABLE: {table_name}")
    print(f"{'='*80}")
    
    try:
        # Try to get one row to see structure
        result = client.table(table_name).select("*").limit(1).execute()
        
        if result.data and len(result.data) > 0:
            # Has data - we can see real structure
            row = result.data[0]
            print(f"\n✅ Has data - showing actual columns:")
            print("\nCOLUMN COMMENTS:")
            print("-" * 80)
            for key, value in row.items():
                value_type = type(value).__name__
                print(f"\nCOMMENT ON COLUMN public.{table_name}.{key} IS")
                print(f"'TODO: Add description for {key} ({value_type})';")
        else:
            # Empty table - try to infer structure from error or schema
            print(f"\n⚠️  Table is empty - attempting to infer structure...")
            
            # Try to insert and rollback to see error message with column names
            # Or just note that we need to check schema.sql
            print(f"Cannot determine columns without data.")
            print(f"Check database/schema.sql for {table_name} structure.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ Column inspection complete!")
print("=" * 80)





