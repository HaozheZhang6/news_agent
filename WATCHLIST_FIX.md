# ✅ Watchlist Bug Fix - COMPLETE

## Problem

The `/api/user/watchlist` endpoint was returning an empty array `[]` even though the Supabase database had `watchlist_stocks: ['TSLA']` for the test user.

## Root Cause

**Permissions Issue**: The backend was using the **ANON key** instead of the **SERVICE_ROLE key** to connect to Supabase.

- **ANON key**: Limited permissions, cannot read user data (returns empty results)
- **SERVICE_ROLE key**: Full permissions, can read/write all data (returns correct results)

## Investigation Steps

1. **Created Supabase inspection tool** (`.cursor/supabase_tool.py`)
   - Verified data exists in Supabase: `watchlist_stocks: ['TSLA']` ✅
   
2. **Tested both keys** (`.cursor/test_both_keys.py`)
   - ANON key: Returns `[]` ❌
   - SERVICE_ROLE key: Returns `[{'watchlist_stocks': ['TSLA']}]` ✅
   
3. **Found the issue**: Multiple `.env` files with conflicting `SUPABASE_KEY` values
   - `backend/.env` - Initially had ANON key
   - `env_files/supabase.env` - Also had ANON key, loaded AFTER backend/.env
   - Pydantic loads env files in order, later files override earlier ones

## Solution

Updated `SUPABASE_KEY` in **both** `.env` files to use the SERVICE_ROLE key:

### Files Changed:
1. `/Users/haozhezhang/Documents/Agents/News_agent/backend/.env`
   ```
   SUPABASE_KEY=<service_role_key>
   ```

2. `/Users/haozhezhang/Documents/Agents/News_agent/env_files/supabase.env`
   ```
   SUPABASE_KEY=<service_role_key>
   ```

3. `/Users/haozhezhang/Documents/Agents/News_agent/backend/app/config.py`
   - Updated field definition to explicitly use `SUPABASE_SERVICE_KEY`
   - Added comment explaining the change

4. `/Users/haozhezhang/Documents/Agents/News_agent/backend/app/database.py`
   - Added `asyncio.to_thread()` wrapper for Supabase queries (proper async handling)
   - Added debug logging to trace query results

## Test Results

### Before Fix:
```bash
$ curl "http://localhost:8000/api/user/watchlist?user_id=03f6b167-0c4d-4983-a380-54b8eb42f830"
{"watchlist_stocks":[]}
```

### After Fix:
```bash
$ curl "http://localhost:8000/api/user/watchlist?user_id=03f6b167-0c4d-4983-a380-54b8eb42f830"
{"watchlist_stocks":["TSLA"]}
```

✅ **SUCCESS!**

## Tools Created

1. **`.cursor/supabase_tool.py`** - Database inspection utility
   - Lists all tables and row counts
   - Inspects table schemas
   - Tests queries with different keys
   - Usage: `uv run python .cursor/supabase_tool.py [user_id]`

2. **`.cursor/test_watchlist.py`** - Direct database test
   - Tests `get_user_preferences()` function
   - Bypasses API layer for debugging

3. **`.cursor/test_both_keys.py`** - Key comparison test
   - Tests ANON vs SERVICE_ROLE key permissions
   - Identifies which key has required access

## Key Learnings

1. **Backend services should use SERVICE_ROLE key**, not ANON key
2. **Supabase-py client is synchronous**, wrap calls in `asyncio.to_thread()` for async code
3. **Pydantic env file loading order matters** - later files override earlier ones
4. **Row-Level Security (RLS)** in Supabase restricts ANON key access to user data

## Next Steps

1. ✅ Watchlist endpoint now returns correct data
2. Consider removing debug logging once confirmed stable
3. Document which key to use for different scenarios:
   - **ANON key**: Frontend/client-side requests (RLS protected)
   - **SERVICE_ROLE key**: Backend server operations (full access)

---

**Status**: FIXED ✅  
**Date**: 2025-10-12  
**Test User**: `03f6b167-0c4d-4983-a380-54b8eb42f830`  
**Expected Result**: `["TSLA"]`  
**Actual Result**: `["TSLA"]` ✅

