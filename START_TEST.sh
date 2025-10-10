#!/bin/bash
# Quick start script for local testing

echo "🚀 Starting Voice News Agent - Local Test"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No backend/.env file found!"
    echo "Creating a minimal .env for testing..."
    
    cat > backend/.env << EOF
# Minimal config for local testing
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Add your API keys here:
# ZHIPUAI_API_KEY=your_key_here
# ALPHAVANTAGE_API_KEY=your_key_here
# SUPABASE_URL=your_url_here
# SUPABASE_KEY=your_key_here
# UPSTASH_REDIS_REST_URL=your_url_here
# UPSTASH_REDIS_REST_TOKEN=your_token_here
EOF
    
    echo "✅ Created backend/.env"
    echo "⚠️  Please edit backend/.env and add your API keys!"
    echo ""
fi

echo "📦 Starting backend server..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

