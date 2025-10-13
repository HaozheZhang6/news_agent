#!/usr/bin/env python3
"""List ALL tables that actually exist in Supabase."""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env
env_file = Path(__file__).parent.parent / "env_files" / "supabase.env"
load_dotenv(env_file)

url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

client = create_client(url, service_key)

print("=" * 80)
print("🔍 DISCOVERING ALL TABLES IN SUPABASE")
print("=" * 80)

# Try to list tables by attempting to query them
# Since Supabase doesn't expose information_schema easily, we'll try known tables
# and also attempt some discovery

potential_tables = [
    # From schema.sql
    "users",
    "user_preferences",
    "news_sources",
    "news_articles",
    "stock_data",
    "conversation_sessions",
    "conversation_messages",
    "user_interactions",
    "ai_response_cache",
    # Other potential tables
    "profiles",
    "settings",
    "watchlist",
    "watchlist_stocks",
]

existing_tables = []
missing_tables = []

print("\n📋 Checking tables...")
print("-" * 80)

for table in potential_tables:
    try:
        result = client.table(table).select("*", count="exact").limit(0).execute()
        existing_tables.append((table, result.count))
        status = "✅ EXISTS"
        print(f"{status:15} {table:30} ({result.count} rows)")
    except Exception as e:
        missing_tables.append(table)
        status = "❌ NOT FOUND"
        print(f"{status:15} {table:30}")

print("\n" + "=" * 80)
print(f"📊 SUMMARY")
print("=" * 80)
print(f"✅ Existing tables: {len(existing_tables)}")
print(f"❌ Missing tables:  {len(missing_tables)}")

if existing_tables:
    print("\n✅ Tables that exist:")
    for table, count in existing_tables:
        print(f"  - {table:30} ({count} rows)")

if missing_tables:
    print("\n❌ Tables that don't exist:")
    for table in missing_tables:
        print(f"  - {table}")

print("\n" + "=" * 80)
print("💡 RECOMMENDATION")
print("=" * 80)
print("""
To add comments, only use tables that exist (✅).
Update add_table_descriptions.sql to comment out sections for missing tables.
""")



