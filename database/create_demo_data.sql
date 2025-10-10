-- Create demo data for testing Voice News Agent
-- Run this in Supabase SQL Editor to populate the database

-- Insert demo users (using Supabase auth.users UUID format)
-- Note: You'll need to create actual auth users through Supabase Auth first
-- For testing without auth, we'll create public records

-- Insert demo user (anonymous testing user)
INSERT INTO public.users (id, email, subscription_tier, preferences)
VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'demo@voicenews.test',
    'free',
    '{"theme": "dark", "language": "en"}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- Insert user preferences for demo user
INSERT INTO public.user_preferences (user_id, preferred_topics, watchlist_stocks, voice_settings, notification_settings)
VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    ARRAY['technology', 'finance', 'crypto'],
    ARRAY['AAPL', 'GOOGL', 'TSLA', 'BTC'],
    '{
        "speech_rate": 1.0,
        "voice_type": "default",
        "interruption_sensitivity": 0.5,
        "auto_play": true
    }'::jsonb,
    '{
        "breaking_news": true,
        "stock_alerts": true,
        "daily_briefing": true,
        "email_notifications": false
    }'::jsonb
)
ON CONFLICT (user_id) DO NOTHING;

-- Insert demo stock data
INSERT INTO public.stock_data (symbol, company_name, current_price, change_percent, volume, market_cap, last_updated)
VALUES
    ('AAPL', 'Apple Inc.', 178.50, 1.25, 50000000, 2800000000000, NOW()),
    ('GOOGL', 'Alphabet Inc.', 142.30, 0.85, 25000000, 1800000000000, NOW()),
    ('TSLA', 'Tesla Inc.', 242.80, -0.50, 100000000, 770000000000, NOW()),
    ('MSFT', 'Microsoft Corporation', 378.90, 1.10, 30000000, 2820000000000, NOW()),
    ('NVDA', 'NVIDIA Corporation', 495.20, 2.30, 45000000, 1220000000000, NOW())
ON CONFLICT (symbol, last_updated) DO NOTHING;

-- Insert demo news articles
INSERT INTO public.news_articles (
    source_id,
    title,
    summary,
    url,
    published_at,
    sentiment_score,
    relevance_score,
    topics,
    keywords,
    is_breaking
)
SELECT
    ns.id,
    'Apple Announces Revolutionary AI Features',
    'Apple unveiled groundbreaking AI capabilities in its latest operating system, focusing on privacy and on-device processing.',
    'https://example.com/apple-ai-announcement',
    NOW() - INTERVAL '2 hours',
    0.75,
    0.90,
    ARRAY['technology', 'ai', 'privacy'],
    ARRAY['Apple', 'AI', 'iOS', 'privacy'],
    true
FROM public.news_sources ns WHERE ns.name = 'TechCrunch' LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO public.news_articles (
    source_id,
    title,
    summary,
    url,
    published_at,
    sentiment_score,
    relevance_score,
    topics,
    keywords,
    is_breaking
)
SELECT
    ns.id,
    'Tesla Stock Surges on Strong Q4 Earnings',
    'Tesla reports record profits and delivery numbers, beating analyst expectations by wide margin.',
    'https://example.com/tesla-earnings',
    NOW() - INTERVAL '5 hours',
    0.85,
    0.95,
    ARRAY['finance', 'automotive', 'stocks'],
    ARRAY['Tesla', 'TSLA', 'earnings', 'EV'],
    false
FROM public.news_sources ns WHERE ns.name = 'Bloomberg' LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO public.news_articles (
    source_id,
    title,
    summary,
    url,
    published_at,
    sentiment_score,
    relevance_score,
    topics,
    keywords,
    is_breaking
)
SELECT
    ns.id,
    'Bitcoin Reaches New All-Time High',
    'Bitcoin surpasses $100,000 mark amid institutional adoption and favorable regulatory developments.',
    'https://example.com/bitcoin-ath',
    NOW() - INTERVAL '1 hour',
    0.90,
    0.88,
    ARRAY['crypto', 'finance'],
    ARRAY['Bitcoin', 'BTC', 'cryptocurrency', 'ATH'],
    true
FROM public.news_sources ns WHERE ns.name = 'CoinDesk' LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO public.news_articles (
    source_id,
    title,
    summary,
    url,
    published_at,
    sentiment_score,
    relevance_score,
    topics,
    keywords,
    is_breaking
)
SELECT
    ns.id,
    'NVIDIA Unveils Next-Generation AI Chips',
    'NVIDIA announces breakthrough GPU architecture designed for advanced AI workloads and machine learning.',
    'https://example.com/nvidia-gpu',
    NOW() - INTERVAL '3 hours',
    0.80,
    0.92,
    ARRAY['technology', 'ai', 'hardware'],
    ARRAY['NVIDIA', 'GPU', 'AI', 'chip'],
    false
FROM public.news_sources ns WHERE ns.name = 'TechCrunch' LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO public.news_articles (
    source_id,
    title,
    summary,
    url,
    published_at,
    sentiment_score,
    relevance_score,
    topics,
    keywords,
    is_breaking
)
SELECT
    ns.id,
    'Global Markets Rally on Positive Economic Data',
    'Stock markets worldwide surge as employment and GDP figures exceed expectations, boosting investor confidence.',
    'https://example.com/markets-rally',
    NOW() - INTERVAL '4 hours',
    0.70,
    0.85,
    ARRAY['finance', 'markets', 'economy'],
    ARRAY['stocks', 'markets', 'economy', 'GDP'],
    false
FROM public.news_sources ns WHERE ns.name = 'Financial Times' LIMIT 1
ON CONFLICT DO NOTHING;

-- Create a demo conversation session
INSERT INTO public.conversation_sessions (id, user_id, session_start, total_interactions, is_active)
VALUES (
    'b0000000-0000-0000-0000-000000000001'::uuid,
    'a0000000-0000-0000-0000-000000000001'::uuid,
    NOW() - INTERVAL '10 minutes',
    3,
    true
)
ON CONFLICT DO NOTHING;

-- Add demo conversation messages
INSERT INTO public.conversation_messages (session_id, user_id, message_type, content, processing_time_ms, confidence_score)
VALUES
    (
        'b0000000-0000-0000-0000-000000000001'::uuid,
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'user_input',
        'What are the latest tech news?',
        50,
        0.95
    ),
    (
        'b0000000-0000-0000-0000-000000000001'::uuid,
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'agent_response',
        'Here are the top technology stories: Apple has announced revolutionary AI features focusing on privacy...',
        1200,
        NULL
    ),
    (
        'b0000000-0000-0000-0000-000000000001'::uuid,
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'user_input',
        'Tell me more about Apple AI',
        45,
        0.97
    )
ON CONFLICT DO NOTHING;

-- Track some demo interactions
INSERT INTO public.user_interactions (user_id, interaction_type, target_content, success, response_time_ms)
VALUES
    (
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'news_request',
        'technology',
        true,
        1200
    ),
    (
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'deep_dive',
        'Apple AI announcement',
        true,
        1500
    ),
    (
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'stock_query',
        'AAPL',
        true,
        800
    )
ON CONFLICT DO NOTHING;

-- Verify data was inserted
SELECT 'Users:', COUNT(*) FROM public.users;
SELECT 'User Preferences:', COUNT(*) FROM public.user_preferences;
SELECT 'News Sources:', COUNT(*) FROM public.news_sources;
SELECT 'News Articles:', COUNT(*) FROM public.news_articles;
SELECT 'Stock Data:', COUNT(*) FROM public.stock_data;
SELECT 'Conversation Sessions:', COUNT(*) FROM public.conversation_sessions;
SELECT 'Conversation Messages:', COUNT(*) FROM public.conversation_messages;
SELECT 'User Interactions:', COUNT(*) FROM public.user_interactions;

-- Display sample data
SELECT 'Latest News Articles:' as info;
SELECT title, published_at, topics FROM public.news_articles ORDER BY published_at DESC LIMIT 3;

SELECT 'Stock Prices:' as info;
SELECT symbol, company_name, current_price, change_percent FROM public.stock_data ORDER BY symbol;

SELECT 'Demo User:' as info;
SELECT email, subscription_tier FROM public.users WHERE id = 'a0000000-0000-0000-0000-000000000001'::uuid;
