-- Supabase Database Schema for Voice News Agent
-- PostgreSQL with Row Level Security (RLS)

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'premium', 'enterprise')),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences and settings
CREATE TABLE public.user_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    preferred_topics TEXT[] DEFAULT '{}',
    watchlist_stocks TEXT[] DEFAULT '{}',
    voice_settings JSONB DEFAULT '{
        "speech_rate": 1.0,
        "voice_type": "default",
        "interruption_sensitivity": 0.5,
        "auto_play": true
    }',
    notification_settings JSONB DEFAULT '{
        "breaking_news": true,
        "stock_alerts": true,
        "daily_briefing": true,
        "email_notifications": false
    }',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- News sources and categories
CREATE TABLE public.news_sources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT,
    category TEXT NOT NULL CHECK (category IN (
        'technology', 'finance', 'politics', 'crypto', 'energy', 
        'healthcare', 'automotive', 'real_estate', 'retail', 'general'
    )),
    reliability_score DECIMAL(3,2) DEFAULT 0.5 CHECK (reliability_score >= 0 AND reliability_score <= 1),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- News articles
CREATE TABLE public.news_articles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_id UUID REFERENCES public.news_sources(id),
    external_id TEXT, -- AlphaVantage or other source ID
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    url TEXT,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    relevance_score DECIMAL(3,2) DEFAULT 0.5 CHECK (relevance_score >= 0 AND relevance_score <= 1),
    topics TEXT[] DEFAULT '{}',
    keywords TEXT[] DEFAULT '{}',
    is_breaking BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stock data
CREATE TABLE public.stock_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol TEXT NOT NULL,
    company_name TEXT,
    current_price DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    volume BIGINT,
    market_cap BIGINT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, last_updated)
);

-- Conversation sessions
CREATE TABLE public.conversation_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    total_interactions INTEGER DEFAULT 0,
    voice_interruptions INTEGER DEFAULT 0,
    topics_discussed TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true
);

-- Individual conversation messages
CREATE TABLE public.conversation_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES public.conversation_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    message_type TEXT NOT NULL CHECK (message_type IN ('user_input', 'agent_response', 'system_event')),
    content TEXT NOT NULL,
    audio_url TEXT, -- URL to stored audio file
    processing_time_ms INTEGER,
    confidence_score DECIMAL(3,2),
    referenced_news_ids UUID[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User interaction analytics
CREATE TABLE public.user_interactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    interaction_type TEXT NOT NULL CHECK (interaction_type IN (
        'news_request', 'stock_query', 'voice_command', 'interruption', 
        'deep_dive', 'skip', 'preference_update'
    )),
    target_content TEXT, -- What they interacted with
    success BOOLEAN DEFAULT true,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cached AI responses for performance
CREATE TABLE public.ai_response_cache (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    cache_key TEXT UNIQUE NOT NULL,
    prompt_hash TEXT NOT NULL,
    response_content TEXT NOT NULL,
    response_type TEXT NOT NULL CHECK (response_type IN ('news_summary', 'stock_analysis', 'deep_dive', 'general')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_news_articles_published ON public.news_articles(published_at DESC);
CREATE INDEX idx_news_articles_topics ON public.news_articles USING GIN(topics);
CREATE INDEX idx_news_articles_sentiment ON public.news_articles(sentiment_score);
CREATE INDEX idx_conversation_messages_session ON public.conversation_messages(session_id);
CREATE INDEX idx_conversation_messages_user ON public.conversation_messages(user_id);
CREATE INDEX idx_user_interactions_user ON public.user_interactions(user_id);
CREATE INDEX idx_stock_data_symbol ON public.stock_data(symbol);
CREATE INDEX idx_stock_data_updated ON public.stock_data(last_updated DESC);
CREATE INDEX idx_ai_cache_key ON public.ai_response_cache(cache_key);
CREATE INDEX idx_ai_cache_expires ON public.ai_response_cache(expires_at);

-- Full-text search indexes
CREATE INDEX idx_news_articles_search ON public.news_articles USING GIN(to_tsvector('english', title || ' ' || COALESCE(summary, '')));

-- Row Level Security (RLS) policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_interactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own data" ON public.users FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users can manage own preferences" ON public.user_preferences FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own conversations" ON public.conversation_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own messages" ON public.conversation_messages FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own interactions" ON public.user_interactions FOR ALL USING (auth.uid() = user_id);

-- Public read access for news and stock data
CREATE POLICY "Public read access for news" ON public.news_articles FOR SELECT USING (true);
CREATE POLICY "Public read access for stocks" ON public.stock_data FOR SELECT USING (true);
CREATE POLICY "Public read access for sources" ON public.news_sources FOR SELECT USING (true);

-- Functions for common operations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_news_articles_updated_at BEFORE UPDATE ON public.news_articles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to get user's recent news preferences
CREATE OR REPLACE FUNCTION get_user_news_preferences(user_uuid UUID)
RETURNS TABLE(
    preferred_topics TEXT[],
    watchlist_stocks TEXT[],
    voice_settings JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        up.preferred_topics,
        up.watchlist_stocks,
        up.voice_settings
    FROM public.user_preferences up
    WHERE up.user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean up expired cache
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.ai_response_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Insert default news sources
INSERT INTO public.news_sources (name, category, reliability_score) VALUES
('AlphaVantage News', 'general', 0.8),
('Financial Times', 'finance', 0.9),
('TechCrunch', 'technology', 0.85),
('Reuters', 'general', 0.95),
('Bloomberg', 'finance', 0.9),
('CoinDesk', 'crypto', 0.8),
('Energy News', 'energy', 0.75);

-- Create a view for active news with source info
CREATE VIEW public.active_news AS
SELECT 
    na.*,
    ns.name as source_name,
    ns.category as source_category,
    ns.reliability_score as source_reliability
FROM public.news_articles na
JOIN public.news_sources ns ON na.source_id = ns.id
WHERE ns.is_active = true
ORDER BY na.published_at DESC;
