#!/usr/bin/env python3
"""
Supabase Database Inspection Tool
Reads credentials from env_files/supabase.env and inspects database schema
"""
import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv


def load_supabase_credentials():
    """Load Supabase credentials from env file."""
    env_file = Path(__file__).parent.parent / "env_files" / "supabase.env"
    if not env_file.exists():
        print(f"❌ Env file not found: {env_file}")
        sys.exit(1)
    
    load_dotenv(env_file)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for full access
    
    if not url or not key:
        print("❌ SUPABASE_URL or SUPABASE_SERVICE_KEY not found in env file")
        sys.exit(1)
    
    return url, key


def get_supabase_client() -> Client:
    """Create Supabase client."""
    url, key = load_supabase_credentials()
    return create_client(url, key)


def list_tables(client: Client):
    """List all tables in the database."""
    print("\n" + "="*80)
    print("📊 SUPABASE TABLES")
    print("="*80)
    
    # Try each known table to see which ones exist
    known_tables = [
        "users", 
        "conversation_sessions", 
        "conversation_messages", 
        "user_preferences", 
        "news_articles", 
        "stock_data",
        "watchlist_stocks"
    ]
    
    print("\n📋 Checking tables:")
    for table in known_tables:
        try:
            result = client.table(table).select("*", count="exact").limit(0).execute()
            print(f"  ✅ {table:30s} ({result.count} rows)")
        except Exception as e:
            print(f"  ❌ {table:30s} (not found)")


def inspect_users_table(client: Client):
    """Inspect the users table structure."""
    print("\n" + "="*80)
    print("👤 USERS TABLE")
    print("="*80)
    
    try:
        # Get first user to see structure
        result = client.table("users").select("*").limit(1).execute()
        
        if result.data:
            user = result.data[0]
            print("\n📋 Columns:")
            for key, value in user.items():
                value_type = type(value).__name__
                value_preview = str(value)[:50] if value else "NULL"
                print(f"  - {key:20s} ({value_type:10s}): {value_preview}")
            
            # Check if preferences column exists
            if 'preferences' in user:
                print("\n📦 Preferences Column Content:")
                print(f"  Type: {type(user['preferences'])}")
                print(f"  Value: {user['preferences']}")
            
            # Check for watchlist_stocks
            if 'watchlist_stocks' in user:
                print("\n📈 Watchlist Stocks Column:")
                print(f"  Value: {user['watchlist_stocks']}")
        else:
            print("⚠️  No users found in table")
            
        # Get total count
        count_result = client.table("users").select("*", count="exact").execute()
        print(f"\n📊 Total users: {count_result.count}")
        
    except Exception as e:
        print(f"❌ Error inspecting users table: {e}")
        import traceback
        traceback.print_exc()


def get_user_by_id(client: Client, user_id: str):
    """Get a specific user by ID."""
    print("\n" + "="*80)
    print(f"🔍 USER: {user_id}")
    print("="*80)
    
    try:
        result = client.table("users").select("*").eq("id", user_id).execute()
        
        if result.data:
            user = result.data[0]
            print("\n📋 User Data:")
            for key, value in user.items():
                print(f"  {key:20s}: {value}")
            
            # Check watchlist specifically
            if 'preferences' in user and user['preferences']:
                prefs = user['preferences']
                if isinstance(prefs, dict) and 'watchlist_stocks' in prefs:
                    print(f"\n📈 Watchlist Stocks: {prefs['watchlist_stocks']}")
                else:
                    print(f"\n⚠️  No watchlist_stocks in preferences")
            
            return user
        else:
            print(f"❌ User not found: {user_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_watchlist_query(client: Client, user_id: str):
    """Test how to properly query watchlist."""
    print("\n" + "="*80)
    print(f"🧪 WATCHLIST QUERY TEST")
    print("="*80)
    
    try:
        # Method 1: Query preferred_topics and watchlist_stocks
        print("\n📋 Method 1: Select preferred_topics, watchlist_stocks")
        result = client.table("users").select("preferred_topics, watchlist_stocks").eq("id", user_id).execute()
        print(f"  Result: {result}")
        print(f"  Result.data: {result.data}")
        if result.data:
            row = result.data[0]
            print(f"  Row: {row}")
            print(f"  Watchlist: {row.get('watchlist_stocks', [])}")
        
        # Method 2: Select all columns
        print("\n📋 Method 2: Select * (all columns)")
        result = client.table("users").select("*").eq("id", user_id).execute()
        print(f"  Result.data: {result.data}")
        if result.data:
            row = result.data[0]
            print(f"  Watchlist from *: {row.get('watchlist_stocks', [])}")
        
    except Exception as e:
        print(f"❌ Error testing watchlist query: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    print("🔧 Supabase Database Inspection Tool")
    
    # Get client
    client = get_supabase_client()
    print("✅ Connected to Supabase")
    
    # List tables
    list_tables(client)
    
    # Inspect users table
    inspect_users_table(client)
    
    # If user ID provided, get that user
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        user = get_user_by_id(client, user_id)
        if user:
            test_watchlist_query(client, user_id)
    else:
        print("\n💡 Tip: Run with user_id to inspect specific user:")
        print(f"   python {Path(__file__).name} <user_id>")


if __name__ == "__main__":
    main()

