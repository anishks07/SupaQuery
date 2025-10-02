#!/bin/bash
# Quick Start Script for PostgreSQL + RBAC Setup

set -e  # Exit on error

echo "=================================================="
echo "SupaQuery PostgreSQL + RBAC Quick Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}✗ Homebrew not found${NC}"
        echo "Please install Homebrew first: https://brew.sh"
        exit 1
    fi
    echo -e "${GREEN}✓ Homebrew found${NC}"
    
    # Check if PostgreSQL is installed
    if ! brew list postgresql@14 &> /dev/null; then
        echo "Installing PostgreSQL..."
        brew install postgresql@14
    else
        echo -e "${GREEN}✓ PostgreSQL already installed${NC}"
    fi
    
    # Start PostgreSQL
    echo "Starting PostgreSQL..."
    brew services start postgresql@14
    sleep 2
    echo -e "${GREEN}✓ PostgreSQL started${NC}"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    
    # Check if PostgreSQL is installed
    if ! command -v psql &> /dev/null; then
        echo "Installing PostgreSQL..."
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
    else
        echo -e "${GREEN}✓ PostgreSQL already installed${NC}"
    fi
    
    # Start PostgreSQL
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    echo -e "${GREEN}✓ PostgreSQL started${NC}"
else
    echo -e "${YELLOW}⚠ Unsupported OS: $OSTYPE${NC}"
    echo "Please install PostgreSQL manually"
    exit 1
fi

# Determine PostgreSQL user (Homebrew uses current user, not 'postgres')
if [[ "$OSTYPE" == "darwin"* ]]; then
    PG_USER=$(whoami)
else
    PG_USER="postgres"
fi
echo "Using PostgreSQL user: $PG_USER"

# Create database
echo ""
echo "Creating database..."
if psql -U $PG_USER -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw supaquery; then
    echo -e "${YELLOW}⚠ Database 'supaquery' already exists${NC}"
    read -p "Drop and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        dropdb -U $PG_USER supaquery 2>/dev/null || true
        createdb -U $PG_USER supaquery
        echo -e "${GREEN}✓ Database recreated${NC}"
    fi
else
    createdb -U $PG_USER supaquery
    echo -e "${GREEN}✓ Database created${NC}"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install psycopg2-binary asyncpg sqlalchemy alembic python-jose[cryptography] passlib[bcrypt]
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Configure environment
echo ""
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
    fi
else
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
fi

# Generate SECRET_KEY and update DATABASE_URL
echo ""
echo "Generating SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|your-secret-key-change-this-in-production-use-openssl-rand-hex-32|$SECRET_KEY|g" .env
    # Update DATABASE_URL with correct user (Homebrew uses current user)
    sed -i '' "s|postgresql+asyncpg://postgres:postgres@|postgresql+asyncpg://$PG_USER@|g" .env
else
    sed -i "s|your-secret-key-change-this-in-production-use-openssl-rand-hex-32|$SECRET_KEY|g" .env
fi
echo -e "${GREEN}✓ SECRET_KEY generated and saved to .env${NC}"
echo -e "${GREEN}✓ DATABASE_URL updated for user: $PG_USER${NC}"

# Initialize database
echo ""
echo "=================================================="
echo "Database Initialization"
echo "=================================================="
echo "This will create tables, roles, and admin user"
echo ""
read -p "Initialize database now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    python init_db.py
fi

# Backup old main.py if exists
echo ""
if [ -f "main.py" ]; then
    echo "Backing up existing main.py..."
    cp main.py main_sqlite.py.bak
    echo -e "${GREEN}✓ Backed up to main_sqlite.py.bak${NC}"
fi

# Replace main.py
if [ -f "main_postgres.py" ]; then
    echo "Activating PostgreSQL version..."
    cp main_postgres.py main.py
    echo -e "${GREEN}✓ main.py updated with PostgreSQL version${NC}"
fi

echo ""
echo "=================================================="
echo "Setup Complete! 🎉"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Start the server: python main.py"
echo "2. Test registration: curl -X POST http://localhost:8000/api/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"username\":\"test\",\"email\":\"test@example.com\",\"password\":\"password123\"}'"
echo ""
echo "3. Read the documentation:"
echo "   - POSTGRES_SETUP.md - Setup guide"
echo "   - MIGRATION_GUIDE.md - Migration instructions"
echo "   - IMPLEMENTATION_SUMMARY.md - Features overview"
echo ""
echo "To rollback to SQLite: mv main_sqlite.py.bak main.py"
echo ""
