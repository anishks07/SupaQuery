#!/bin/bash
# Startup script for SupaQuery backend with GraphRAG v2

echo "🚀 Starting SupaQuery Backend..."
echo ""

cd /Users/mac/Desktop/SupaQuery/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment and start
echo "✓ Activating virtual environment..."
source venv/bin/activate

echo "✓ Starting server..."
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python3 main.py
