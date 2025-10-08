#!/bin/bash
# Run Knowledge Graph Cleanup
# This script ensures the virtual environment is activated before running cleanup

echo "🧹 Knowledge Graph Cleanup Tool"
echo "================================"
echo ""

# Check if we're in the backend directory
if [ ! -f "cleanup_knowledge_graph.py" ]; then
    echo "❌ Error: Must run from backend directory"
    echo "   Run: cd /Users/mac/Desktop/SupaQuery/backend"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Create it with: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
python -c "import sqlalchemy, gqlalchemy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies not installed"
    echo "   Installing requirements..."
    pip install -r requirements.txt
fi

# Check if services are running (best effort)
echo "🔍 Checking services..."
echo "   Note: The cleanup script will verify connections when it runs"
echo "   If there are connection issues, they will be reported during cleanup"

# Run the cleanup script
echo ""
echo "✅ All checks passed! Starting cleanup..."
echo ""
python cleanup_knowledge_graph.py

# Deactivate virtual environment
deactivate
