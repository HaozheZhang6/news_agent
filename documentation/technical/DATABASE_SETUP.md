# Database Setup Guide

Your backend is showing "database unhealthy" because the Supabase database tables haven't been created yet. Here's how to fix it:

## What This Means

The health check in `backend/app/database.py:43` tries to query the `users` table:
```python
result = self.client.table('users').select('id').limit(1).execute()
```

But the table doesn't exist yet, causing the health check to fail.

## Solution 1: Using Supabase Dashboard (Recommended)

1. **Go to your Supabase project**:
   - URL: https://zaipmdlbcraufolrizpn.supabase.co
   - Or visit: https://supabase.com/dashboard/projects

2. **Open the SQL Editor**:
   - Click on the SQL Editor icon in the left sidebar
   - Or go to: https://supabase.com/dashboard/project/zaipmdlbcraufolrizpn/sql/new

3. **Run the schema**:
   - Copy the entire contents of `database/schema.sql`
   - Paste it into the SQL editor
   - Click "Run" or press `Cmd/Ctrl + Enter`

4. **Verify tables were created**:
   - Go to "Table Editor" in the sidebar
   - You should see all these tables:
     - users
     - user_preferences
     - news_sources
     - news_articles
     - stock_data
     - conversation_sessions
     - conversation_messages
     - user_interactions
     - ai_response_cache

## Solution 2: Using Command Line (Alternative)

If you have `psql` installed and want to use the Makefile:

1. **Get your database connection string**:
   - Go to Supabase Dashboard → Project Settings → Database
   - Copy the "Connection string" (URI format)
   - It should look like: `postgresql://postgres:[PASSWORD]@db.zaipmdlbcraufolrizpn.supabase.co:5432/postgres`

2. **Set the DATABASE_URL environment variable**:
   ```bash
   export DATABASE_URL="your_connection_string_here"
   ```

3. **Apply the schema**:
   ```bash
   make db-apply
   ```

## Verification

After applying the schema, restart your backend server:

```bash
make run-server
```

Then check the health endpoint:

```bash
curl http://localhost:8000/health
```

You should now see:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",  // ✅ Changed from "unhealthy"
    "cache": "healthy",
    "websocket": "healthy"
  },
  "active_connections": 0,
  "timestamp": "..."
}
```

## What the Schema Creates

The schema creates a complete database structure for your Voice News Agent:

- **User Management**: Users, preferences, authentication
- **News System**: Articles, sources, categories with full-text search
- **Stock Data**: Real-time stock information tracking
- **Conversations**: Session tracking, message history, voice interactions
- **Analytics**: User interaction tracking, performance metrics
- **Caching**: AI response caching for performance
- **Security**: Row Level Security (RLS) policies for data protection

## Troubleshooting

If you still see "unhealthy" after applying the schema:

1. **Check Supabase credentials** in `env_files/supabase.env`:
   - SUPABASE_URL should match your project URL
   - SUPABASE_KEY should be valid (anon or service role key)

2. **Test connection directly**:
   ```bash
   curl -X GET "https://zaipmdlbcraufolrizpn.supabase.co/rest/v1/users?select=id&limit=1" \
     -H "apikey: YOUR_SUPABASE_KEY" \
     -H "Authorization: Bearer YOUR_SUPABASE_KEY"
   ```

3. **Check the backend logs** when starting the server:
   ```bash
   make run-server
   ```
   Look for any error messages about database connection.

## Next Steps

Once the database is healthy:

1. ✅ All backend API endpoints will work
2. ✅ Conversation history will be stored
3. ✅ User preferences will persist
4. ✅ News and stock data can be cached
5. ✅ Ready for production deployment
