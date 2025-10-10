# Voice Agent Frontend

A comprehensive voice agent frontend application with authentication, profile management, and conversation history.

## 🗄️ Database Architecture

**✅ SINGLE TABLE - ZERO CUSTOM TABLES**

This application uses **ONLY Supabase's built-in auth.users table**:

| Table | Field | Purpose |
|-------|-------|---------|
| `auth.users` | Standard fields | Email, password, authentication |
| `auth.users` | `user_metadata` (JSONB) | Profile, watchlist, conversations |

**No custom tables, no migrations, no DDL** - pure Supabase!

## Features

### 🔐 Authentication
- Email/password login and registration
- Supabase Auth integration
- Social login support (Google, GitHub) - requires additional setup
- Secure session management

### 👤 Profile Management
- **Interests**: Select from 10+ categories (Technology, Finance, Business, Health, etc.)
- **Stock Watchlist**: Add and track stocks with real-time price updates
- **Voice Settings**: Customize speech rate, interruption sensitivity, and voice type
- **Notifications**: Configure alerts for market updates, news, and daily briefings

### 🎙️ Voice Agent Interface
- **Single Talk Button**: Simple one-button interaction
- **Visual States**:
  - Blue (Idle): Ready to start
  - Red (Listening): Recording your voice
  - Green (Speaking): Agent is responding
- **Quick Commands**: Pre-configured buttons for common requests
- **Status Indicators**: Real-time connection and activity status

### 📚 Conversation History
- Timeline view with user/agent message bubbles
- News articles associated with conversations
- Search and filter functionality
- Statistics dashboard with usage metrics

## Getting Started

### 1. Seed Test Users

When you first load the application:

1. Click the **Settings icon** (⚙️) in the top-right corner of the login page
2. Click **"Seed Test Users"** to create test accounts in Supabase
3. Wait for confirmation that users were created successfully

### 2. Log In with Test Accounts

Use any of these test accounts to explore the application:

| Email | Password | Name |
|-------|----------|------|
| demo@voiceagent.com | demo123 | Demo User |
| alice@example.com | password123 | Alice Johnson |
| bob@example.com | password123 | Bob Smith |
| carol@example.com | password123 | Carol Davis |
| david@example.com | password123 | David Wilson |

Each test user has:
- Pre-configured interests
- Sample stock watchlist
- Sample conversation history
- Default notification settings

### 3. Explore the Application

After logging in, you can:

- **Dashboard**: Start voice conversations, view quick commands, and see activity summary
- **Profile** (User icon): Customize interests, manage watchlist, adjust voice settings
- **History** (History icon): View past conversations, search transcripts, analyze usage stats
- **Logout** (Logout icon): Sign out of your account

## Technical Architecture

### Frontend
- **React** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** components
- **Context API** for state management
- **Supabase Client** for auth and API calls

### Backend
- **Supabase Auth**: User authentication (stored in auth.users table)
- **Supabase Edge Functions**: Hono-based API server
- **KV Store**: Profile and conversation data storage

### Data Storage

**IMPORTANT: This application uses ONLY the auth.users table. No custom tables created.**

#### Supabase Auth (`auth.users`) - Built-in Table
- User credentials (email, password hash)
- Email addresses
- **user_metadata (JSONB field)** - ALL application data:
  - Name
  - Profile (interests, watchlist, settings, notifications)
  - Conversations (full message history with news items)

**No custom tables, no migrations, no DDL** - everything in `user_metadata`!

## API Endpoints

All endpoints are prefixed with `/make-server-19e78e3b/`

### Authentication
- `POST /signup` - Create new user with initial metadata
- `POST /seed-users` - Seed test users with full data

### Profile (stored in user_metadata.profile)
- `GET /profile` - Fetch from user_metadata
- `PUT /profile` - Update user_metadata

### Conversations (stored in user_metadata.conversations)
- `GET /conversations` - Fetch from user_metadata
- `POST /conversations` - Append to user_metadata
- `GET /stats` - Calculate from user_metadata

## Social Login Setup

To enable Google or GitHub login:

1. **Google**: Follow instructions at https://supabase.com/docs/guides/auth/social-login/auth-google
2. **GitHub**: Follow instructions at https://supabase.com/docs/guides/auth/social-login/auth-github

Without completing these steps, clicking the social login buttons will show a setup reminder.

## Customization

### Adding New Interests

Edit `/pages/ProfilePage.tsx` and add to the `interestCategories` array:

```typescript
{
  id: "your-category",
  icon: YourIcon,
  title: "Your Category",
  description: "Category description"
}
```

### Modifying Voice States

Edit `/components/VoiceButton.tsx` to customize the visual appearance and behavior of the voice button states.

### Changing Theme Colors

The application uses Tailwind v4 with CSS variables defined in `/styles/globals.css`. Modify the `:root` variables to change the color scheme.

## Environment

This application uses Supabase's built-in environment variables:
- `SUPABASE_URL` - Auto-configured
- `SUPABASE_SERVICE_ROLE_KEY` - Auto-configured (server-side only)
- `SUPABASE_ANON_KEY` - Auto-configured (client-side)

## Security Notes

⚠️ **Important**: This is a prototype application. For production use:
- Implement proper password policies
- Add email verification
- Set up rate limiting
- Configure CORS properly
- Add input validation
- Implement comprehensive error handling
- Add audit logging

## Support

For questions or issues:
1. Check the console for error messages
2. Verify Supabase connection status
3. Ensure test users are seeded properly
4. Review the admin panel for user creation status
