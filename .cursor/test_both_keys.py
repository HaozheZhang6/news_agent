#!/usr/bin/env python3
"""Test both anon key and service key."""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env
env_file = Path(__file__).parent.parent / "env_files" / "supabase.env"
load_dotenv(env_file)

url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_KEY")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

user_id = "03f6b167-0c4d-4983-a380-54b8eb42f830"

print("=" * 80)
print("🔐 TESTING ANON KEY")
print("=" * 80)
try:
    client_anon = create_client(url, anon_key)
    result = client_anon.table("users").select("preferred_topics, watchlist_stocks").eq("id", user_id).execute()
    print(f"✅ Result: {result.data}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("🔐 TESTING SERVICE KEY")
print("=" * 80)
try:
    client_service = create_client(url, service_key)
    result = client_service.table("users").select("preferred_topics, watchlist_stocks").eq("id", user_id).execute()
    print(f"✅ Result: {result.data}")
except Exception as e:
    print(f"❌ Error: {e}")

