#!/usr/bin/env python3
"""Check RLS policies on the users table."""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env
env_file = Path(__file__).parent.parent / "env_files" / "supabase.env"
load_dotenv(env_file)

url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

print("=" * 80)
print("🔐 CHECKING RLS POLICIES ON USERS TABLE")
print("=" * 80)

# Use service key to query RLS policies
client = create_client(url, service_key)

# Query to get RLS policies
query = """
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'users'
ORDER BY policyname;
"""

try:
    # Check if RLS is enabled
    rls_query = """
    SELECT relname, relrowsecurity 
    FROM pg_class 
    WHERE relname = 'users' AND relnamespace = 'public'::regnamespace;
    """
    
    print("\n📋 RLS Status:")
    result = client.rpc('exec_sql', {'query': rls_query}).execute()
    print(f"  Result: {result}")
    
    # Try a different approach - query information_schema
    print("\n📋 Checking table privileges:")
    priv_query = """
    SELECT grantee, privilege_type 
    FROM information_schema.role_table_grants 
    WHERE table_name='users' 
    AND table_schema='public';
    """
    
    result = client.rpc('exec_sql', {'query': priv_query}).execute()
    print(f"  Result: {result}")
    
except Exception as e:
    print(f"❌ Error querying RLS policies: {e}")
    print("\nNote: Supabase may not expose exec_sql RPC by default.")
    print("Let's try a direct approach...")

# Try to access with anon key
print("\n" + "=" * 80)
print("🧪 TESTING ANON KEY ACCESS")
print("=" * 80)

anon_key = os.getenv("SUPABASE_KEY")
anon_client = create_client(url, anon_key)

user_id = "03f6b167-0c4d-4983-a380-54b8eb42f830"

print(f"\n1. Testing SELECT with anon key (user_id={user_id[:8]}...):")
try:
    result = anon_client.table("users").select("*").eq("id", user_id).execute()
    print(f"   ✅ Success! Data: {result.data}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print(f"\n2. Testing SELECT specific columns:")
try:
    result = anon_client.table("users").select("preferred_topics, watchlist_stocks").eq("id", user_id).execute()
    print(f"   ✅ Success! Data: {result.data}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print(f"\n3. Testing SELECT without filter:")
try:
    result = anon_client.table("users").select("id, email").limit(1).execute()
    print(f"   ✅ Success! Data: {result.data}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("💡 RECOMMENDATION")
print("=" * 80)
print("""
If anon key cannot access the users table, you need to:

1. Enable RLS on the users table (if not already enabled)
2. Add a policy to allow authenticated users to read their own data:

   CREATE POLICY "Users can view own data"
   ON users FOR SELECT
   USING (true);  -- Or: USING (auth.uid() = id) for authenticated users

3. Or temporarily disable RLS for development:
   
   ALTER TABLE users DISABLE ROW LEVEL SECURITY;
   
   (NOT recommended for production!)

Go to Supabase Dashboard → Authentication → Policies to configure RLS.
""")

