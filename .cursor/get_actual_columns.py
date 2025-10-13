#!/usr/bin/env python3
"""Get ACTUAL column structure by trying to insert into empty tables."""
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
print("🔍 GETTING ACTUAL COLUMNS FROM EMPTY TABLES")
print("=" * 80)

# For empty tables, we need to try inserting with minimal data to see error
# Or better: query the information_schema directly

tables = ["conversation_messages", "news_articles"]

for table_name in tables:
    print(f"\n{'='*80}")
    print(f"TABLE: {table_name}")
    print(f"{'='*80}")
    
    try:
        # Try to select with a deliberate error to see column names
        # Better: use a raw SQL query through RPC or similar
        # For now, let's try to insert with empty dict and see error
        
        # Actually, better approach: try selecting specific columns
        # If column doesn't exist, we'll get an error
        
        # Test common columns
        test_columns = {
            'conversation_messages': [
                'id', 'session_id', 'user_id', 'message_type', 'content',
                'audio_url', 'processing_time_ms', 'confidence_score',
                'referenced_news_ids', 'metadata', 'created_at',
                # Alternative names that might exist
                'type', 'text', 'message', 'timestamp', 'role'
            ],
            'news_articles': [
                'id', 'source_id', 'external_id', 'title', 'summary',
                'content', 'url', 'published_at', 'sentiment_score',
                'relevance_score', 'topics', 'keywords', 'is_breaking',
                'created_at', 'updated_at',
                # Alternative names
                'headline', 'description', 'link', 'published'
            ]
        }
        
        existing_columns = []
        missing_columns = []
        
        for col in test_columns.get(table_name, []):
            try:
                # Try to select just this column
                result = client.table(table_name).select(col).limit(0).execute()
                existing_columns.append(col)
                print(f"  ✅ {col}")
            except Exception as e:
                if "does not exist" in str(e):
                    missing_columns.append(col)
                    # Don't print missing columns to keep output clean
                else:
                    print(f"  ⚠️  {col}: {e}")
        
        print(f"\n📊 Summary:")
        print(f"  ✅ Found {len(existing_columns)} columns")
        if missing_columns:
            print(f"  ❌ {len(missing_columns)} columns don't exist")
        
        if existing_columns:
            print(f"\n✅ Existing columns in {table_name}:")
            for col in existing_columns:
                print(f"  • {col}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ Column discovery complete!")
print("=" * 80)





