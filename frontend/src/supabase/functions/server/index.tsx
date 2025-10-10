import { Hono } from 'npm:hono';
import { cors } from 'npm:hono/cors';
import { logger } from 'npm:hono/logger';
import { createClient } from 'npm:@supabase/supabase-js@2';

/**
 * Voice Agent API Server
 * 
 * DATA STORAGE:
 * - Users: Supabase Auth (auth.users table) - built-in, no custom tables needed
 * - All Data: Stored in auth.users.user_metadata JSONB field
 * 
 * NO CUSTOM TABLES - Uses only Supabase's built-in auth.users table
 */

const app = new Hono();

// Middleware
app.use('*', cors());
app.use('*', logger(console.log));

// Create Supabase client
const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
);

// Helper function to verify user from auth.users table
async function verifyUser(authHeader: string | null) {
  if (!authHeader) return null;
  const token = authHeader.split(' ')[1];
  const { data: { user }, error } = await supabase.auth.getUser(token);
  if (error || !user) return null;
  return user;
}

// Helper function to update user metadata
async function updateUserMetadata(userId: string, metadata: any) {
  const { data, error } = await supabase.auth.admin.updateUserById(userId, {
    user_metadata: metadata
  });
  if (error) throw error;
  return data;
}

// Health check endpoint - shows which tables are being used
app.get('/make-server-19e78e3b/health', async (c) => {
  return c.json({
    status: 'ok',
    database: {
      users: 'auth.users (Supabase built-in)',
      storage: 'auth.users.user_metadata (JSONB field)',
      note: 'No custom tables created - using only Supabase built-in auth.users table'
    },
    endpoints: [
      'POST /signup - Create user in auth.users',
      'POST /seed-users - Seed test users',
      'GET /profile - Fetch from user_metadata',
      'PUT /profile - Update in user_metadata',
      'GET /conversations - Fetch from user_metadata',
      'POST /conversations - Save to user_metadata',
      'GET /stats - Calculate from user_metadata'
    ]
  });
});

// Seed test users endpoint - creates users in auth.users table with full metadata
app.post('/make-server-19e78e3b/seed-users', async (c) => {
  try {
    const testUsers = [
      {
        email: 'demo@voiceagent.com',
        password: 'demo123',
        name: 'Demo User',
        interests: {
          technology: true,
          finance: true,
          business: true,
          health: false,
          entertainment: false,
          sports: false,
          science: true,
          politics: false,
          music: false,
          books: false,
        },
        watchlist: [
          { symbol: 'AAPL', name: 'Apple Inc.', price: 178.45, change: 2.34, changePercent: 1.33 },
          { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 142.67, change: -1.23, changePercent: -0.85 },
          { symbol: 'MSFT', name: 'Microsoft Corp.', price: 412.89, change: 5.67, changePercent: 1.39 },
        ],
        conversations: [
          {
            id: '1',
            messages: [
              { type: 'user', content: 'What\'s happening in the market today?', timestamp: '2:30 PM' },
              { 
                type: 'agent', 
                content: 'The market is showing mixed signals today. The S&P 500 is up 0.3%, while the Nasdaq is down 0.5%. Tech stocks are seeing some profit-taking after yesterday\'s rally.', 
                timestamp: '2:30 PM',
                newsItems: [
                  { title: 'Tech Stocks Face Headwinds as Fed Signals Rate Stability', source: 'Bloomberg', url: '#' },
                  { title: 'Market Analysis: What\'s Driving Today\'s Trading', source: 'CNBC', url: '#' }
                ]
              }
            ],
            date: 'Today, 2:30 PM',
            timestamp: Date.now()
          }
        ]
      },
      {
        email: 'alice@example.com',
        password: 'password123',
        name: 'Alice Johnson',
        interests: {
          technology: true,
          finance: false,
          business: false,
          health: true,
          entertainment: true,
          sports: false,
          science: false,
          politics: false,
          music: true,
          books: true,
        },
        watchlist: [
          { symbol: 'TSLA', name: 'Tesla Inc.', price: 245.32, change: -3.21, changePercent: -1.29 },
          { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 489.12, change: 12.45, changePercent: 2.61 },
        ],
        conversations: [
          {
            id: '1',
            messages: [
              { type: 'user', content: 'Tell me about my watchlist', timestamp: '9:15 AM' },
              { 
                type: 'agent', 
                content: 'Tesla is down 1.29% at $245.32, while NVIDIA is up 2.61% at $489.12. Overall, your tech stocks are mixed today.', 
                timestamp: '9:15 AM'
              }
            ],
            date: 'Today, 9:15 AM',
            timestamp: Date.now() - 100000
          }
        ]
      },
      {
        email: 'bob@example.com',
        password: 'password123',
        name: 'Bob Smith',
        interests: {
          technology: false,
          finance: true,
          business: true,
          health: false,
          entertainment: false,
          sports: true,
          science: false,
          politics: true,
          music: false,
          books: false,
        },
        watchlist: [
          { symbol: 'JPM', name: 'JPMorgan Chase', price: 156.78, change: 0.89, changePercent: 0.57 },
          { symbol: 'BAC', name: 'Bank of America', price: 34.56, change: -0.23, changePercent: -0.66 },
          { symbol: 'GS', name: 'Goldman Sachs', price: 389.45, change: 4.32, changePercent: 1.12 },
        ],
        conversations: []
      },
      {
        email: 'carol@example.com',
        password: 'password123',
        name: 'Carol Davis',
        interests: {
          technology: true,
          finance: false,
          business: false,
          health: true,
          entertainment: false,
          sports: false,
          science: true,
          politics: false,
          music: false,
          books: true,
        },
        watchlist: [
          { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 178.92, change: 3.45, changePercent: 1.97 },
        ],
        conversations: []
      },
      {
        email: 'david@example.com',
        password: 'password123',
        name: 'David Wilson',
        interests: {
          technology: false,
          finance: true,
          business: true,
          health: false,
          entertainment: true,
          sports: true,
          science: false,
          politics: false,
          music: true,
          books: false,
        },
        watchlist: [
          { symbol: 'META', name: 'Meta Platforms', price: 498.23, change: 8.76, changePercent: 1.79 },
          { symbol: 'NFLX', name: 'Netflix Inc.', price: 612.34, change: -2.11, changePercent: -0.34 },
          { symbol: 'DIS', name: 'Walt Disney Co.', price: 89.45, change: 1.23, changePercent: 1.39 },
        ],
        conversations: [
          {
            id: '1',
            messages: [
              { type: 'user', content: 'Give me the latest entertainment news', timestamp: '5:45 PM' },
              { 
                type: 'agent', 
                content: 'Meta reports strong quarterly earnings, Netflix announces new content slate, and Disney+ subscriber growth exceeds expectations.', 
                timestamp: '5:45 PM',
                newsItems: [
                  { title: 'Meta Beats Earnings Expectations on Strong Ad Revenue', source: 'Reuters', url: '#' }
                ]
              }
            ],
            date: 'Yesterday, 5:45 PM',
            timestamp: Date.now() - 200000
          }
        ]
      }
    ];

    const createdUsers = [];

    for (const testUser of testUsers) {
      // Check if user exists in auth.users table
      const { data: existingUsers } = await supabase.auth.admin.listUsers();
      const userExists = existingUsers?.users?.some(u => u.email === testUser.email);

      if (userExists) {
        console.log(`User ${testUser.email} already exists in auth.users, skipping...`);
        continue;
      }

      // Create user in Supabase auth.users table with ALL data in user_metadata
      const { data, error } = await supabase.auth.admin.createUser({
        email: testUser.email,
        password: testUser.password,
        user_metadata: {
          name: testUser.name,
          profile: {
            interests: testUser.interests,
            watchlist: testUser.watchlist,
            settings: {
              speechRate: 1.0,
              interruptionSensitivity: 50,
              voiceType: 'professional'
            },
            notifications: {
              marketAlerts: true,
              newsDigest: true,
              watchlistUpdates: true,
              dailyBrief: false
            }
          },
          conversations: testUser.conversations
        },
        email_confirm: true
      });

      if (error) {
        console.log(`Error creating user ${testUser.email}: ${error.message}`);
        continue;
      }

      createdUsers.push({
        email: testUser.email,
        name: testUser.name,
        id: data.user.id
      });
    }

    return c.json({ 
      message: `Created ${createdUsers.length} test users`,
      users: createdUsers 
    });
  } catch (error) {
    console.log(`Error seeding users: ${error}`);
    return c.json({ error: 'Failed to seed users' }, 500);
  }
});

// Auth routes - uses auth.users table (Supabase built-in)
app.post('/make-server-19e78e3b/signup', async (c) => {
  try {
    const { email, password, name } = await c.req.json();
    
    // Create user in auth.users table with initial profile in user_metadata
    const { data, error } = await supabase.auth.admin.createUser({
      email,
      password,
      user_metadata: {
        name,
        profile: {
          interests: {},
          watchlist: [],
          settings: {
            speechRate: 1.0,
            interruptionSensitivity: 50,
            voiceType: 'professional'
          },
          notifications: {
            marketAlerts: true,
            newsDigest: true,
            watchlistUpdates: true,
            dailyBrief: false
          }
        },
        conversations: []
      },
      email_confirm: true
    });

    if (error) {
      console.log(`Error creating user in auth.users: ${error.message}`);
      return c.json({ error: error.message }, 400);
    }

    return c.json({ user: data.user });
  } catch (error) {
    console.log(`Error in signup: ${error}`);
    return c.json({ error: 'Signup failed' }, 500);
  }
});

// Profile routes - stores data in auth.users.user_metadata
app.get('/make-server-19e78e3b/profile', async (c) => {
  const user = await verifyUser(c.req.header('Authorization'));
  if (!user) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  try {
    // Profile is stored in user_metadata.profile
    const profile = user.user_metadata?.profile || {
      interests: {},
      watchlist: [],
      settings: {
        speechRate: 1.0,
        interruptionSensitivity: 50,
        voiceType: 'professional'
      },
      notifications: {
        marketAlerts: true,
        newsDigest: true,
        watchlistUpdates: true,
        dailyBrief: false
      }
    };
    
    return c.json({ profile });
  } catch (error) {
    console.log(`Error fetching profile from user_metadata: ${error}`);
    return c.json({ error: 'Failed to fetch profile' }, 500);
  }
});

app.put('/make-server-19e78e3b/profile', async (c) => {
  const user = await verifyUser(c.req.header('Authorization'));
  if (!user) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  try {
    const updates = await c.req.json();
    const currentMetadata = user.user_metadata || {};
    const currentProfile = currentMetadata.profile || {};
    
    // Merge updates with existing profile
    const updatedProfile = { ...currentProfile, ...updates };
    
    // Update user_metadata in auth.users table
    await updateUserMetadata(user.id, {
      ...currentMetadata,
      profile: updatedProfile
    });
    
    return c.json({ profile: updatedProfile });
  } catch (error) {
    console.log(`Error updating profile in user_metadata: ${error}`);
    return c.json({ error: 'Failed to update profile' }, 500);
  }
});

// Conversation history routes - stores data in auth.users.user_metadata
app.get('/make-server-19e78e3b/conversations', async (c) => {
  const user = await verifyUser(c.req.header('Authorization'));
  if (!user) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  try {
    // Conversations are stored in user_metadata.conversations array
    const conversations = user.user_metadata?.conversations || [];
    return c.json({ 
      conversations: conversations.sort((a: any, b: any) => b.timestamp - a.timestamp) 
    });
  } catch (error) {
    console.log(`Error fetching conversations from user_metadata: ${error}`);
    return c.json({ error: 'Failed to fetch conversations' }, 500);
  }
});

app.post('/make-server-19e78e3b/conversations', async (c) => {
  const user = await verifyUser(c.req.header('Authorization'));
  if (!user) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  try {
    const conversation = await c.req.json();
    const timestamp = Date.now();
    const conversationId = `${timestamp}`;
    
    const currentMetadata = user.user_metadata || {};
    const currentConversations = currentMetadata.conversations || [];
    
    // Add new conversation to array
    const newConversation = {
      id: conversationId,
      ...conversation,
      timestamp
    };
    
    // Update user_metadata with new conversation
    await updateUserMetadata(user.id, {
      ...currentMetadata,
      conversations: [...currentConversations, newConversation]
    });

    return c.json({ id: conversationId, timestamp });
  } catch (error) {
    console.log(`Error saving conversation to user_metadata: ${error}`);
    return c.json({ error: 'Failed to save conversation' }, 500);
  }
});

// Statistics route - calculates from auth.users.user_metadata
app.get('/make-server-19e78e3b/stats', async (c) => {
  const user = await verifyUser(c.req.header('Authorization'));
  if (!user) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  try {
    // Get conversations from user_metadata
    const conversations = user.user_metadata?.conversations || [];
    
    const stats = {
      totalConversations: conversations.length,
      totalDuration: conversations.reduce((sum: number, conv: any) => sum + (conv.duration || 0), 0),
      newsBriefings: conversations.filter((conv: any) => 
        conv.messages?.some((msg: any) => msg.newsItems && msg.newsItems.length > 0)
      ).length,
      avgPerDay: Math.round(conversations.length / 7)
    };

    return c.json({ stats });
  } catch (error) {
    console.log(`Error calculating stats from user_metadata: ${error}`);
    return c.json({ error: 'Failed to fetch stats' }, 500);
  }
});

Deno.serve(app.fetch);
