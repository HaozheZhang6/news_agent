# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │   Login    │  │  Dashboard  │  │     Profile      │     │
│  │   Page     │  │    Page     │  │      Page        │     │
│  └────────────┘  └─────────────┘  └──────────────────┘     │
│         │               │                    │               │
│         └───────────────┴────────────────────┘               │
│                         │                                    │
│                  Auth Context                                │
│                  Profile Context                             │
│                  Conversation Context                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ HTTPS / REST API
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Supabase Edge Function (Hono)                   │
│                                                               │
│  Routes:                                                      │
│  • POST   /signup                                            │
│  • POST   /seed-users                                        │
│  • GET    /profile                                           │
│  • PUT    /profile                                           │
│  • GET    /conversations                                     │
│  • POST   /conversations                                     │
│  • GET    /stats                                             │
│  • GET    /health                                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                ┌─────────┴────────┐
                │                  │
                ▼                  ▼
┌───────────────────────┐  ┌──────────────────────┐
│   auth.users          │  │  kv_store_19e78e3b   │
│   (Supabase Built-in) │  │  (Existing KV Table) │
│                       │  │                      │
│  • id                 │  │  Keys:               │
│  • email              │  │  • profile:{userId}  │
│  • encrypted_password │  │  • conversation:...  │
│  • user_metadata      │ 
└───────────────────────┘
```

## Data Storage Strategy

### ✅ ZERO Custom Tables Created

This application demonstrates how to build a full-featured app using **ONLY** Supabase's existing infrastructure:

1. **Authentication:** `auth.users` (built-in Supabase table)
2. **Application Data:** `kv_store_19e78e3b` (existing key-value table)

### Why This Approach?

**For Prototyping & MVPs:**

- ✅ No database migrations needed
- ✅ No schema design required
- ✅ Instant deployment
- ✅ Flexible data structure
- ✅ Rapid iteration

**Trade-offs:**

- ⚠️ No complex SQL queries
- ⚠️ Manual data relationships
- ⚠️ Limited indexing

## Component Hierarchy

```
App
├── AuthProvider
│   └── AppContent
│       ├── LoginPage (unauthenticated)
│       ├── RegisterPage (unauthenticated)
│       ├── AdminPage (unauthenticated)
│       └── ProfileProvider (authenticated)
│           └── ConversationProvider
│               ├── DashboardPage
│               ├── ProfilePage
│               └── HistoryPage
```

## State Management

### Context Providers

1. **AuthContext** (`/lib/auth-context.tsx`)
   - Manages user session
   - Stores access token
   - Provides login/logout functions
   - Syncs with Supabase Auth

2. **ProfileContext** (`/lib/profile-context.tsx`)
   - Loads profile from `kv_store_19e78e3b`
   - Manages interests, watchlist, settings
   - Syncs updates to backend

3. **ConversationContext** (`/lib/conversation-context.tsx`)
   - Loads conversation history from `kv_store_19e78e3b`
   - Manages message list
   - Saves new conversations

## API Routes

### Authentication Routes

```typescript
POST /make-server-19e78e3b/signup
  ↓
  Creates user in auth.users
  ↓
  Initializes profile in kv_store_19e78e3b
```

### Profile Routes

```typescript
GET /make-server-19e78e3b/profile
  ↓
  Verifies user from auth.users
  ↓
  Fetches profile from kv_store_19e78e3b (key: profile:{userId})

PUT /make-server-19e78e3b/profile
  ↓
  Verifies user from auth.users
  ↓
  Updates profile in kv_store_19e78e3b (key: profile:{userId})
```

### Conversation Routes

```typescript
GET /make-server-19e78e3b/conversations
  ↓
  Verifies user from auth.users
  ↓
  Fetches all with prefix: conversation:{userId}:

POST /make-server-19e78e3b/conversations
  ↓
  Verifies user from auth.users
  ↓
  Saves to kv_store_19e78e3b (key: conversation:{userId}:{timestamp})
```

## Security Model

### Authentication Layer

```
User Request
    ↓
Check JWT Token (from auth.users)
    ↓
Extract User ID
    ↓
Scope all operations to this User ID
```

### Data Isolation

- All KV keys include user ID
- No cross-user data access
- Server validates token before any operation

## Key Design Decisions

### 1. Using Supabase Auth Table

**Why:** Built-in, secure, maintained by Supabase

- Email/password hashing handled automatically
- Session management included
- Social login support available
- No custom auth logic needed

### 2. Using KV Store for Application Data

**Why:** Flexible, no schema changes, perfect for prototyping

- JSON storage allows schema evolution
- Simple key-based access
- No migrations required
- Easy to understand and debug

### 3. Namespace Pattern

**Why:** Data isolation and clarity

```
profile:{userId}              → One profile per user
conversation:{userId}:{time}  → Many conversations per user
```

## Scaling Path

When you outgrow the KV approach:

### Phase 1: Current (KV Store)

```
auth.users + kv_store_19e78e3b
Perfect for: MVP, prototypes, demos
```

### Phase 2: Structured Tables (Future)

```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  interests JSONB,
  settings JSONB,
  created_at TIMESTAMP
);

CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  messages JSONB,
  created_at TIMESTAMP
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
```

### Phase 3: Normalized Schema (Production)

```sql
CREATE TABLE user_interests (
  user_id UUID REFERENCES auth.users(id),
  category VARCHAR,
  enabled BOOLEAN
);

CREATE TABLE stocks (
  id UUID PRIMARY KEY,
  symbol VARCHAR UNIQUE,
  name VARCHAR
);

CREATE TABLE user_watchlist (
  user_id UUID REFERENCES auth.users(id),
  stock_id UUID REFERENCES stocks(id)
);
```

But for now: **Keep it simple with existing tables!** 🚀

## File Structure

```
/
├── App.tsx                        # Main entry point
├── lib/
│   ├── auth-context.tsx          # Auth state (uses auth.users)
│   ├── profile-context.tsx       # Profile state (uses kv_store)
│   └── conversation-context.tsx  # Conv state (uses kv_store)
├── pages/
│   ├── LoginPage.tsx             # Auth UI
│   ├── RegisterPage.tsx          # Auth UI
│   ├── AdminPage.tsx             # Seeding UI
│   ├── DashboardPage.tsx         # Main app
│   ├── ProfilePage.tsx           # Settings
│   └── HistoryPage.tsx           # Conversations
├── supabase/functions/server/
│   ├── index.tsx                 # API routes
│   └── kv_store.tsx              # KV utilities
└── utils/supabase/
    ├── client.ts                 # Supabase client
    └── info.tsx                  # Project config
```

## Environment Variables

```bash
SUPABASE_URL              # Auto-configured
SUPABASE_SERVICE_ROLE_KEY # Auto-configured (server-side)
SUPABASE_ANON_KEY         # Auto-configured (client-side)
```

No additional setup required! ✨

## Testing the Setup

1. **Verify Tables:**

   ```
   Visit /admin → See health check showing:
   - auth.users (Supabase built-in)
   - kv_store_19e78e3b (existing KV table)
   ```

2. **Seed Users:**

   ```
   Click "Seed Test Users" → Creates 5 users in auth.users
   ```

3. **Login:**

   ```
   Use test credentials → Authenticates against auth.users
   ```

4. **Use App:**
   ```
   Update profile → Writes to kv_store_19e78e3b
   View history → Reads from kv_store_19e78e3b
   ```

## Summary

This architecture demonstrates how to build a full-featured application using **ONLY existing Supabase infrastructure**:

- ✅ No custom tables
- ✅ No migrations
- ✅ No DDL statements
- ✅ Just code and existing tables

Perfect for rapid prototyping and MVPs! 🎉