#!/bin/bash

# Start Tizzl Server with OpenAI API

echo "============================================"
echo "Starting Tizzl AI Fashion Stylist"
echo "============================================"

# Navigate to parent directory
cd /Users/shagun/Desktop/tizzl_v1

# Activate virtual environment
source tizzl/venv/bin/activate

# Export Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check for API key
if [ -f "tizzl/.env" ]; then
    echo "✅ Found .env file"
    export $(grep -v '^#' tizzl/.env | xargs)
    if [ ! -z "$OPENAI_API_KEY" ]; then
        echo "✅ OpenAI API key configured"
    else
        echo "⚠️  No OpenAI API key found - will use mock responses"
    fi
fi

echo ""
echo "📍 Server will be available at:"
echo "   • Web UI: http://localhost:8000/static/index.html"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"

# Run the server
python -m uvicorn tizzl.api.main:app --host 0.0.0.0 --port 8000 --reload