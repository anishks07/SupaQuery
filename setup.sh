#!/bin/bash

# SupaQuery Setup Script
# This script will install Ollama and download required models

set -e

echo "🚀 Setting up SupaQuery..."
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama is already installed"
fi

# Start Ollama service (if not running)
echo "🔄 Starting Ollama service..."
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
sleep 5

# Pull required models
echo "📦 Downloading LLaMA 3.2 model (this may take a while)..."
ollama pull llama3.2:latest

echo "📦 Downloading Mistral model (alternative)..."
ollama pull mistral:latest

echo ""
echo "✅ Setup complete!"
echo ""
echo "Models downloaded:"
ollama list

# Kill the background Ollama process
kill $OLLAMA_PID 2>/dev/null || true

echo ""
echo "Next steps:"
echo "1. Start Ollama: ollama serve"
echo "2. Install Python dependencies: cd backend && pip install -r requirements.txt"
echo "3. Install frontend dependencies: cd frontend && npm install"
echo "4. Start the backend: cd backend && python main.py"
echo "5. Start the frontend: cd frontend && npm run dev"
echo ""
echo "Or use Docker:"
echo "docker-compose up --build"
