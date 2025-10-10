# Database Information

## ✅ Single Table Architecture

This application uses **ONLY the Supabase built-in auth.users table**. No custom tables created.

## Table Used

### `auth.users` (Supabase Built-in)

**Type:** Supabase managed table (automatically available)  
**Purpose:** User authentication and account management

**Fields Used:**
- `id` - User UUID (primary key)
- `email` - User email address
- `encrypted_password` - Password hash
- `user_metadata` - JSON field storing: `{ name: string }`
- `email_confirmed_at` - Email confirmation timestamp
- `created_at` - Account creation timestamp

**Management:** Handled entirely by Supabase Auth API
- Create users: `supabase.auth.admin.createUser()`
- Sign in: `supabase.auth.signInWithPassword()`
- Get user: `supabase.auth.getUser(token)`
- Sign out: `supabase.auth.signOut()`

**Application Data Storage:** All stored in `user_metadata` JSONB field

#### user_metadata Structure
**Field:** `user_metadata` (JSONB)  
**Structure:**
```json
{
  "name": string,
  "profile": {
    "interests": {
      "technology": boolean,
      "finance": boolean,
      "business": boolean,
      "health": boolean,
      "entertainment": boolean,
      "sports": boolean,
      "science": boolean,
      "politics": boolean,
      "music": boolean,
      "books": boolean
    },
    "watchlist": [
      {
        "symbol": string,
        "name": string,
        "price": number,
        "change": number,
        "changePercent": number
      }
    ],
    "settings": {
      "speechRate": number,
      "interruptionSensitivity": number,
      "voiceType": string
    },
    "notifications": {
      "marketAlerts": boolean,
      "newsDigest": boolean,
      "watchlistUpdates": boolean,
      "dailyBrief": boolean
    }
  },
  "conversations": [
    {
      "id": string,
      "messages": [
        {
          "type": "user" | "agent",
          "content": string,
          "timestamp": string,
          "newsItems": [
            {
              "title": string,
              "source": string,
              "url": string
            }
          ]
        }
      ],
      "date": string,
      "timestamp": number
    }
  ]
}
```

## Data Flow

### User Registration
1. Create user in `auth.users` via Supabase Auth API
2. Initialize profile and empty conversations in `user_metadata`
3. Return user session

### User Login
1. Authenticate against `auth.users` via Supabase Auth API
2. Profile and conversations automatically available in `user_metadata`

### Profile Updates
1. Verify user session (check `auth.users`)
2. Update `user_metadata.profile` via `supabase.auth.admin.updateUserById()`

### Save Conversation
1. Verify user session (check `auth.users`)
2. Append to `user_metadata.conversations` array

## Why This Approach?

### ✅ Advantages
- **Single Table:** Only uses `auth.users` - no custom tables
- **Zero Setup:** No schema migrations or DDL required
- **JSONB Flexibility:** Easy to modify data structure
- **Supabase Native:** Leverages built-in auth system
- **Instant Deployment:** Works out of the box

### ⚠️ Considerations
- `user_metadata` size limit (~1MB recommended)
- Not optimized for complex cross-user queries
- For production with large datasets, consider separate tables

## API Endpoints & Data Access

| Endpoint | Auth Table | user_metadata | Operation |
|----------|-----------|---------------|-----------|
| `POST /signup` | ✅ Create | ✅ Initialize | Create user + profile |
| `POST /seed-users` | ✅ Create | ✅ Full data | Bulk user creation |
| `GET /profile` | ✅ Verify | ✅ Read | Fetch `user_metadata.profile` |
| `PUT /profile` | ✅ Verify | ✅ Update | Update `user_metadata.profile` |
| `GET /conversations` | ✅ Verify | ✅ Read | Fetch `user_metadata.conversations` |
| `POST /conversations` | ✅ Verify | ✅ Append | Add to `user_metadata.conversations` |
| `GET /stats` | ✅ Verify | ✅ Calculate | Process `user_metadata.conversations` |

## Data Access Examples

### Fetch User Profile
```typescript
const { data: { user } } = await supabase.auth.getUser(token);
const profile = user.user_metadata?.profile;
```

### Fetch All Conversations
```typescript
const { data: { user } } = await supabase.auth.getUser(token);
const conversations = user.user_metadata?.conversations || [];
```

### Update User Profile
```typescript
await supabase.auth.admin.updateUserById(userId, {
  user_metadata: {
    ...currentMetadata,
    profile: updatedProfile
  }
});
```

### Save Conversation
```typescript
await supabase.auth.admin.updateUserById(userId, {
  user_metadata: {
    ...currentMetadata,
    conversations: [...currentConversations, newConversation]
  }
});
```

## Security Notes

### Authentication & Authorization
- `auth.users`: Protected by Supabase Auth
- `user_metadata`: Only accessible with valid JWT token

### Authentication Flow
1. User signs in → Receives JWT token
2. Token includes user ID and metadata
3. Server validates token via `supabase.auth.getUser()`
4. User can only access their own `user_metadata`

### Data Isolation
- Each user's data is in their own `user_metadata` field
- No cross-user data access possible
- Supabase ensures users can only access their own data

## Monitoring & Maintenance

### Health Check
Access `GET /health` to verify setup:
```json
{
  "status": "ok",
  "database": {
    "users": "auth.users (Supabase built-in)",
    "storage": "auth.users.user_metadata (JSONB field)",
    "note": "No custom tables created"
  }
}
```

### Data Cleanup
To remove user data:
1. Delete user from `auth.users` via Supabase dashboard
2. All data (profile + conversations) automatically deleted with user

## Future Considerations

If you need to scale beyond KV storage, consider:

1. **Structured Tables:** Migrate to dedicated tables for profiles and conversations
2. **Indexes:** Add indexes for common queries
3. **Relationships:** Use foreign keys to link users and data
4. **Analytics:** Create materialized views for reporting

But for prototyping and MVP: **The current approach is perfect!** ✨
