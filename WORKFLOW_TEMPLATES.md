# SupaQuery - Workflow Templates & Automation

This file contains ready-to-use workflow configurations for CI/CD, deployment, and automation.

---

## 📋 Table of Contents

1. [GitHub Actions Workflows](#github-actions-workflows)
2. [Docker Compose Setup](#docker-compose-setup)
3. [Deployment Scripts](#deployment-scripts)
4. [Development Scripts](#development-scripts)
5. [Monitoring & Logging](#monitoring--logging)

---

## 1. GitHub Actions Workflows

### 1.1 CI/CD Pipeline - Backend Tests

**File**: `.github/workflows/backend-ci.yml`

```yaml
name: Backend CI/CD

on:
  push:
    branches: [ main, master, develop ]
    paths:
      - 'backend/**'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: supaquery_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      memgraph:
        image: memgraph/memgraph:latest
        ports:
          - 7687:7687
        options: >-
          --health-cmd "echo 'RETURN 1;' | mgconsole"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.13
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
        cache: 'pip'
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr
    
    - name: Install Python dependencies
      working-directory: ./backend
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        python -m spacy download en_core_web_sm
    
    - name: Run linting
      working-directory: ./backend
      run: |
        pip install flake8 black
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
    
    - name: Run tests
      working-directory: ./backend
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/supaquery_test
        MEMGRAPH_HOST: localhost
        MEMGRAPH_PORT: 7687
        SECRET_KEY: test-secret-key-for-ci
        OLLAMA_HOST: http://localhost:11434
      run: |
        pytest tests/ -v --cov=app --cov-report=xml --cov-report=html
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        name: backend-coverage

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Backend
      uses: docker/build-push-action@v4
      with:
        context: ./backend
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/supaquery-backend:latest
          ${{ secrets.DOCKER_USERNAME }}/supaquery-backend:${{ github.sha }}
        cache-from: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/supaquery-backend:buildcache
        cache-to: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/supaquery-backend:buildcache,mode=max
```

---

### 1.2 CI/CD Pipeline - Frontend Tests

**File**: `.github/workflows/frontend-ci.yml`

```yaml
name: Frontend CI/CD

on:
  push:
    branches: [ main, master, develop ]
    paths:
      - 'frontend/**'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'frontend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: ./frontend/package-lock.json
    
    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci
    
    - name: Run linting
      working-directory: ./frontend
      run: npm run lint
    
    - name: Run type checking
      working-directory: ./frontend
      run: npm run type-check || npx tsc --noEmit
    
    - name: Run tests
      working-directory: ./frontend
      run: npm test -- --coverage --watchAll=false
    
    - name: Build application
      working-directory: ./frontend
      env:
        NEXT_PUBLIC_API_URL: http://localhost:8000
      run: npm run build
    
    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: frontend-build
        path: ./frontend/.next

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Frontend
      uses: docker/build-push-action@v4
      with:
        context: ./frontend
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/supaquery-frontend:latest
          ${{ secrets.DOCKER_USERNAME }}/supaquery-frontend:${{ github.sha }}
        build-args: |
          NEXT_PUBLIC_API_URL=${{ secrets.API_URL }}
```

---

### 1.3 Dependency Update Workflow

**File**: `.github/workflows/dependency-update.yml`

```yaml
name: Dependency Updates

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  update-python-dependencies:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Update Python dependencies
      working-directory: ./backend
      run: |
        pip install --upgrade pip pip-tools
        pip-compile --upgrade requirements.in -o requirements.txt
    
    - name: Create Pull Request
      uses: peter-evans/create-pull-request@v5
      with:
        commit-message: 'chore: update Python dependencies'
        title: 'chore: Weekly Python dependency updates'
        body: 'Automated Python dependency updates'
        branch: deps/python-updates

  update-npm-dependencies:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '20'
    
    - name: Update npm dependencies
      working-directory: ./frontend
      run: |
        npx npm-check-updates -u
        npm install
    
    - name: Create Pull Request
      uses: peter-evans/create-pull-request@v5
      with:
        commit-message: 'chore: update npm dependencies'
        title: 'chore: Weekly npm dependency updates'
        body: 'Automated npm dependency updates'
        branch: deps/npm-updates
```

---

### 1.4 Security Scanning

**File**: `.github/workflows/security-scan.yml`

```yaml
name: Security Scanning

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  security-scan-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: './backend'
        format: 'sarif'
        output: 'trivy-backend-results.sarif'
    
    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-backend-results.sarif'
    
    - name: Run Bandit security linter
      run: |
        pip install bandit
        bandit -r backend/ -f json -o bandit-report.json
    
    - name: Upload Bandit results
      uses: actions/upload-artifact@v3
      with:
        name: bandit-report
        path: bandit-report.json

  security-scan-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run npm audit
      working-directory: ./frontend
      run: |
        npm audit --production --audit-level=moderate || true
        npm audit --production --json > npm-audit.json
    
    - name: Upload npm audit results
      uses: actions/upload-artifact@v3
      with:
        name: npm-audit-report
        path: ./frontend/npm-audit.json
```

---

## 2. Docker Compose Setup

### 2.1 Development Environment

**File**: `docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: supaquery-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: supaquery
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init_scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - supaquery-network

  # Memgraph Graph Database
  memgraph:
    image: memgraph/memgraph-platform:latest
    container_name: supaquery-memgraph
    ports:
      - "7687:7687"  # Bolt protocol
      - "7444:7444"  # WebSocket
      - "3001:3000"  # Lab UI
    volumes:
      - memgraph_data:/var/lib/memgraph
      - memgraph_log:/var/log/memgraph
      - memgraph_etc:/etc/memgraph
    environment:
      - MEMGRAPH_LOG_LEVEL=WARNING
    healthcheck:
      test: ["CMD-SHELL", "echo 'RETURN 1;' | mgconsole"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - supaquery-network

  # Ollama LLM Service
  ollama:
    image: ollama/ollama:latest
    container_name: supaquery-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - supaquery-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    # Comment out above deploy section if no GPU available

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: supaquery-backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /app/venv  # Prevent overwriting venv
      - backend_uploads:/app/uploads
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/supaquery
      - MEMGRAPH_HOST=memgraph
      - MEMGRAPH_PORT=7687
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_MODEL=llama3.2:latest
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key-change-in-production}
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - PYTHONUNBUFFERED=1
    depends_on:
      postgres:
        condition: service_healthy
      memgraph:
        condition: service_healthy
      ollama:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - supaquery-network

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: supaquery-frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NODE_ENV=development
    depends_on:
      - backend
    command: npm run dev
    networks:
      - supaquery-network

  # Redis for caching (optional)
  redis:
    image: redis:7-alpine
    container_name: supaquery-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - supaquery-network

volumes:
  postgres_data:
  memgraph_data:
  memgraph_log:
  memgraph_etc:
  ollama_data:
  backend_uploads:
  redis_data:

networks:
  supaquery-network:
    driver: bridge
```

---

### 2.2 Production Environment

**File**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: supaquery-postgres-prod
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - supaquery-prod-network

  memgraph:
    image: memgraph/memgraph-platform:latest
    container_name: supaquery-memgraph-prod
    ports:
      - "7687:7687"
      - "3001:3000"
    volumes:
      - memgraph_data_prod:/var/lib/memgraph
      - memgraph_log_prod:/var/log/memgraph
    restart: unless-stopped
    networks:
      - supaquery-prod-network

  ollama:
    image: ollama/ollama:latest
    container_name: supaquery-ollama-prod
    volumes:
      - ollama_data_prod:/root/.ollama
    restart: unless-stopped
    networks:
      - supaquery-prod-network
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  backend:
    image: ${DOCKER_USERNAME}/supaquery-backend:latest
    container_name: supaquery-backend-prod
    ports:
      - "8000:8000"
    volumes:
      - backend_uploads_prod:/app/uploads
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - MEMGRAPH_HOST=memgraph
      - MEMGRAPH_PORT=7687
      - OLLAMA_HOST=http://ollama:11434
      - SECRET_KEY=${SECRET_KEY}
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
    depends_on:
      - postgres
      - memgraph
      - ollama
    restart: unless-stopped
    networks:
      - supaquery-prod-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
      replicas: 2

  frontend:
    image: ${DOCKER_USERNAME}/supaquery-frontend:latest
    container_name: supaquery-frontend-prod
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - supaquery-prod-network

  nginx:
    image: nginx:alpine
    container_name: supaquery-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_cache:/var/cache/nginx
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
    networks:
      - supaquery-prod-network

  redis:
    image: redis:7-alpine
    container_name: supaquery-redis-prod
    volumes:
      - redis_data_prod:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    networks:
      - supaquery-prod-network

volumes:
  postgres_data_prod:
  memgraph_data_prod:
  memgraph_log_prod:
  ollama_data_prod:
  backend_uploads_prod:
  redis_data_prod:
  nginx_cache:

networks:
  supaquery-prod-network:
    driver: bridge
```

---

## 3. Deployment Scripts

### 3.1 One-Click Deployment Script

**File**: `deploy.sh`

```bash
#!/bin/bash

# SupaQuery Deployment Script
# Usage: ./deploy.sh [dev|prod|staging]

set -e  # Exit on error

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting SupaQuery deployment for environment: $ENVIRONMENT"

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    echo "📝 Loading environment variables from .env.$ENVIRONMENT"
    export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)
else
    echo "⚠️  No .env.$ENVIRONMENT file found, using defaults"
fi

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to check if required services are available
check_services() {
    echo "🔍 Checking required services..."
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo "⚠️  PostgreSQL client not found (optional for local dev)"
    fi
    
    # Check if ports are available
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port 8000 is in use. Backend might already be running."
    fi
    
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port 3000 is in use. Frontend might already be running."
    fi
}

# Function to initialize Ollama models
init_ollama() {
    echo "🤖 Initializing Ollama..."
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        # Wait for Ollama to be ready
        echo "⏳ Waiting for Ollama service to be ready..."
        sleep 10
        
        # Pull the model
        docker exec supaquery-ollama ollama pull llama3.2 || echo "⚠️  Failed to pull model, continuing..."
    fi
}

# Function to initialize databases
init_databases() {
    echo "🗄️  Initializing databases..."
    
    # Wait for services to be healthy
    echo "⏳ Waiting for services to be healthy..."
    sleep 15
    
    # Run database initialization
    if [ "$ENVIRONMENT" = "dev" ]; then
        docker exec supaquery-backend python init_db.py || echo "⚠️  Database already initialized"
    fi
}

# Function to setup backend
setup_backend() {
    echo "🔧 Setting up backend..."
    
    cd "$SCRIPT_DIR/backend"
    
    # Download spaCy model if needed
    if [ "$ENVIRONMENT" = "dev" ]; then
        docker exec supaquery-backend python -m spacy download en_core_web_sm || echo "⚠️  spaCy model already installed"
    fi
    
    cd "$SCRIPT_DIR"
}

# Function to deploy using Docker Compose
deploy_docker_compose() {
    echo "🐳 Deploying with Docker Compose..."
    
    COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "❌ Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Build and start services
    docker-compose -f "$COMPOSE_FILE" build
    docker-compose -f "$COMPOSE_FILE" up -d
    
    echo "✅ Services started"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Function to show deployment info
show_info() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          SupaQuery Deployment Complete! 🎉              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "📍 Service URLs:"
    echo "   Frontend:      http://localhost:3000"
    echo "   Backend API:   http://localhost:8000"
    echo "   API Docs:      http://localhost:8000/docs"
    echo "   Memgraph Lab:  http://localhost:3001"
    echo ""
    echo "📊 Monitoring:"
    echo "   View logs:     docker-compose -f docker-compose.$ENVIRONMENT.yml logs -f"
    echo "   Stop services: docker-compose -f docker-compose.$ENVIRONMENT.yml down"
    echo "   Restart:       docker-compose -f docker-compose.$ENVIRONMENT.yml restart"
    echo ""
    echo "🔐 Default credentials (if using init_db.py):"
    echo "   Username: Anish"
    echo "   Password: Admin123!"
    echo ""
}

# Main deployment flow
main() {
    check_docker
    check_services
    deploy_docker_compose
    init_ollama
    init_databases
    setup_backend
    show_info
}

# Run main function
main
```

---

### 3.2 Backup Script

**File**: `backup.sh`

```bash
#!/bin/bash

# SupaQuery Backup Script
# Usage: ./backup.sh

set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Starting SupaQuery backup..."

# Backup PostgreSQL
echo "💾 Backing up PostgreSQL..."
docker exec supaquery-postgres pg_dumpall -U postgres > "$BACKUP_DIR/postgres_dump.sql"

# Backup Memgraph
echo "💾 Backing up Memgraph..."
docker exec supaquery-memgraph mgconsole --execute "DUMP DATABASE;" > "$BACKUP_DIR/memgraph_dump.cypherl"

# Backup uploaded files
echo "💾 Backing up uploaded files..."
docker cp supaquery-backend:/app/uploads "$BACKUP_DIR/uploads"

# Backup environment files
echo "💾 Backing up configuration..."
cp .env.* "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  No .env files found"

# Create archive
echo "📦 Creating backup archive..."
tar -czf "backup_$(date +%Y%m%d_%H%M%S).tar.gz" "$BACKUP_DIR"

echo "✅ Backup completed: $BACKUP_DIR"
```

---

### 3.3 Restore Script

**File**: `restore.sh`

```bash
#!/bin/bash

# SupaQuery Restore Script
# Usage: ./restore.sh <backup_directory>

set -e

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Usage: ./restore.sh <backup_directory>"
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "♻️  Starting SupaQuery restore from: $BACKUP_DIR"

# Restore PostgreSQL
if [ -f "$BACKUP_DIR/postgres_dump.sql" ]; then
    echo "💾 Restoring PostgreSQL..."
    docker exec -i supaquery-postgres psql -U postgres < "$BACKUP_DIR/postgres_dump.sql"
else
    echo "⚠️  PostgreSQL backup not found"
fi

# Restore Memgraph
if [ -f "$BACKUP_DIR/memgraph_dump.cypherl" ]; then
    echo "💾 Restoring Memgraph..."
    docker exec -i supaquery-memgraph mgconsole < "$BACKUP_DIR/memgraph_dump.cypherl"
else
    echo "⚠️  Memgraph backup not found"
fi

# Restore uploaded files
if [ -d "$BACKUP_DIR/uploads" ]; then
    echo "💾 Restoring uploaded files..."
    docker cp "$BACKUP_DIR/uploads" supaquery-backend:/app/
else
    echo "⚠️  Uploads backup not found"
fi

echo "✅ Restore completed"
```

---

## 4. Development Scripts

### 4.1 Setup Script

**File**: `setup.sh`

```bash
#!/bin/bash

# SupaQuery Development Setup Script

set -e

echo "🔧 Setting up SupaQuery development environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "✅ All prerequisites met"

# Setup backend
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Create .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo "⚠️  No .env.example found"
fi

cd ..

# Setup frontend
echo "🔧 Setting up frontend..."
cd frontend

npm install

# Create .env.local if not exists
if [ ! -f ".env.local" ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
fi

cd ..

# Start services with Docker Compose
echo "🐳 Starting services..."
docker-compose -f docker-compose.dev.yml up -d postgres memgraph ollama redis

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 20

# Initialize database
echo "🗄️  Initializing database..."
cd backend
source venv/bin/activate
python init_db.py
cd ..

# Pull Ollama model
echo "🤖 Pulling Ollama model..."
docker exec supaquery-ollama ollama pull llama3.2

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          SupaQuery Setup Complete! 🎉                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 To start development:"
echo "   Terminal 1: cd backend && source venv/bin/activate && python main.py"
echo "   Terminal 2: cd frontend && npm run dev"
echo ""
echo "📍 Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo ""
```

---

### 4.2 Test Runner Script

**File**: `test.sh`

```bash
#!/bin/bash

# SupaQuery Test Runner
# Usage: ./test.sh [backend|frontend|all]

set -e

TEST_TARGET=${1:-all}

run_backend_tests() {
    echo "🧪 Running backend tests..."
    cd backend
    source venv/bin/activate
    
    # Run linting
    echo "🔍 Running linting..."
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
    
    # Run type checking
    echo "🔍 Running type checking..."
    mypy app/ --ignore-missing-imports || true
    
    # Run tests
    echo "🧪 Running unit tests..."
    pytest tests/ -v --cov=app --cov-report=html --cov-report=term
    
    cd ..
}

run_frontend_tests() {
    echo "🧪 Running frontend tests..."
    cd frontend
    
    # Run linting
    echo "🔍 Running linting..."
    npm run lint
    
    # Run type checking
    echo "🔍 Running type checking..."
    npx tsc --noEmit || true
    
    # Run tests
    echo "🧪 Running unit tests..."
    npm test -- --coverage --watchAll=false
    
    cd ..
}

case $TEST_TARGET in
    backend)
        run_backend_tests
        ;;
    frontend)
        run_frontend_tests
        ;;
    all)
        run_backend_tests
        run_frontend_tests
        ;;
    *)
        echo "❌ Unknown target: $TEST_TARGET"
        echo "Usage: ./test.sh [backend|frontend|all]"
        exit 1
        ;;
esac

echo "✅ All tests completed"
```

---

## 5. Monitoring & Logging

### 5.1 Log Aggregation Script

**File**: `logs.sh`

```bash
#!/bin/bash

# SupaQuery Log Viewer
# Usage: ./logs.sh [service_name]

SERVICE=${1:-all}

if [ "$SERVICE" = "all" ]; then
    docker-compose -f docker-compose.dev.yml logs -f
else
    docker-compose -f docker-compose.dev.yml logs -f "$SERVICE"
fi
```

---

### 5.2 Health Check Script

**File**: `health-check.sh`

```bash
#!/bin/bash

# SupaQuery Health Check Script

echo "🏥 Checking SupaQuery services health..."

check_service() {
    local name=$1
    local url=$2
    
    if curl -f -s -o /dev/null "$url"; then
        echo "✅ $name is healthy"
        return 0
    else
        echo "❌ $name is unhealthy"
        return 1
    fi
}

FAILED=0

# Check Frontend
check_service "Frontend" "http://localhost:3000" || FAILED=1

# Check Backend
check_service "Backend API" "http://localhost:8000" || FAILED=1
check_service "Backend Health" "http://localhost:8000/api/health" || FAILED=1

# Check Memgraph
if docker exec supaquery-memgraph mgconsole --execute "RETURN 1;" &>/dev/null; then
    echo "✅ Memgraph is healthy"
else
    echo "❌ Memgraph is unhealthy"
    FAILED=1
fi

# Check PostgreSQL
if docker exec supaquery-postgres pg_isready -U postgres &>/dev/null; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL is unhealthy"
    FAILED=1
fi

# Check Ollama
check_service "Ollama" "http://localhost:11434/api/tags" || FAILED=1

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "✅ All services are healthy!"
    exit 0
else
    echo ""
    echo "❌ Some services are unhealthy"
    exit 1
fi
```

---

## 📝 Usage Instructions

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd SupaQuery
   chmod +x *.sh
   ./setup.sh
   ```

2. **Deploy Development Environment**
   ```bash
   ./deploy.sh dev
   ```

3. **Run Tests**
   ```bash
   ./test.sh all
   ```

4. **Check Health**
   ```bash
   ./health-check.sh
   ```

5. **View Logs**
   ```bash
   ./logs.sh backend  # Or frontend, or all
   ```

### Production Deployment

1. **Setup environment variables**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with production values
   ```

2. **Deploy**
   ```bash
   ./deploy.sh prod
   ```

3. **Setup backups (cron job)**
   ```bash
   crontab -e
   # Add: 0 2 * * * /path/to/SupaQuery/backup.sh
   ```

---

## 🔐 Environment Variables

Create `.env.dev`, `.env.staging`, `.env.prod` files:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=supaquery

# Backend
SECRET_KEY=your_secret_key_min_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Docker
DOCKER_USERNAME=your_dockerhub_username

# API
API_URL=https://api.yourdomain.com

# Redis
REDIS_PASSWORD=your_redis_password
```

---

**All scripts are ready to copy and use!** 🚀
