#!/bin/bash

# SupaQuery Docker Setup and Startup Script
# This script helps you set up and run SupaQuery with Docker

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    print_info "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"
}

# Check if Docker Compose is installed
check_docker_compose() {
    print_info "Checking Docker Compose installation..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Check if Docker daemon is running
check_docker_daemon() {
    print_info "Checking if Docker daemon is running..."
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Generate secure secret key
generate_secret_key() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 32
    else
        # Fallback if openssl is not available
        head -c 32 /dev/urandom | base64 | tr -d '\n='
    fi
}

# Create .env file if it doesn't exist
create_env_file() {
    if [ ! -f .env ]; then
        print_info "Creating .env file..."
        SECRET_KEY=$(generate_secret_key)
        cat > .env << EOF
# SupaQuery Environment Configuration

# Docker Compose
COMPOSE_PROJECT_NAME=supaquery

# Backend Configuration
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql+asyncpg://supaquery:supaquery_password@postgres:5432/supaquery
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.2:latest

# Memgraph Configuration
MEMGRAPH_HOST=memgraph
MEMGRAPH_PORT=7687

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Processing Configuration
WHISPER_MODEL=tiny
CHUNK_SIZE=512
CHUNK_OVERLAP=50
MAX_FILE_SIZE=52428800

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
EOF
        print_success ".env file created"
    else
        print_warning ".env file already exists, skipping..."
    fi
}

# Build Docker images
build_images() {
    print_info "Building Docker images..."
    if [ "$1" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml build
    else
        docker-compose build
    fi
    print_success "Docker images built successfully"
}

# Start services
start_services() {
    MODE=${1:-prod}
    print_info "Starting services in $MODE mode..."
    
    if [ "$MODE" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml up -d
    else
        docker-compose up -d
    fi
    
    print_success "Services started!"
    print_info "Waiting for services to be healthy..."
    sleep 10
}

# Pull Ollama model
pull_ollama_model() {
    print_info "Pulling Ollama model (this may take a while)..."
    
    # Wait for Ollama to be ready
    RETRIES=30
    while [ $RETRIES -gt 0 ]; do
        if docker exec supaquery-ollama ollama list &> /dev/null; then
            break
        fi
        print_info "Waiting for Ollama to be ready... ($RETRIES retries left)"
        sleep 5
        RETRIES=$((RETRIES - 1))
    done
    
    if [ $RETRIES -eq 0 ]; then
        print_error "Ollama service did not start in time"
        return 1
    fi
    
    # Pull the model
    if docker exec supaquery-ollama ollama pull llama3.2:latest; then
        print_success "Ollama model pulled successfully"
    else
        print_error "Failed to pull Ollama model"
        return 1
    fi
}

# Initialize database
init_database() {
    print_info "Initializing database..."
    
    # Wait for backend to be ready
    RETRIES=30
    while [ $RETRIES -gt 0 ]; do
        if docker exec supaquery-backend curl -f http://localhost:8000/api/health &> /dev/null; then
            break
        fi
        print_info "Waiting for backend to be ready... ($RETRIES retries left)"
        sleep 5
        RETRIES=$((RETRIES - 1))
    done
    
    if [ $RETRIES -eq 0 ]; then
        print_warning "Backend service did not start in time, but continuing..."
    fi
    
    # Run database initialization
    if docker exec supaquery-backend python init_db.py; then
        print_success "Database initialized successfully"
        print_info "Default admin credentials:"
        echo "  Username: admin"
        echo "  Password: admin123"
        print_warning "Please change the default password after first login!"
    else
        print_error "Failed to initialize database"
        return 1
    fi
}

# Show service URLs
show_urls() {
    echo ""
    print_success "SupaQuery is now running!"
    echo ""
    echo "📱 Access the application:"
    echo "   Frontend:      http://localhost:3000"
    echo "   Backend API:   http://localhost:8000"
    echo "   API Docs:      http://localhost:8000/docs"
    echo "   Memgraph Lab:  http://localhost:3001"
    echo ""
    echo "🔐 Default Admin Credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "📊 View logs:"
    echo "   All services:  docker-compose logs -f"
    echo "   Backend only:  docker-compose logs -f backend"
    echo "   Frontend only: docker-compose logs -f frontend"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker-compose down"
    echo ""
}

# Main menu
show_menu() {
    echo ""
    echo "🚀 SupaQuery Docker Setup"
    echo "=========================="
    echo "1. Quick Start (Production)"
    echo "2. Development Mode"
    echo "3. Stop All Services"
    echo "4. View Logs"
    echo "5. Pull Ollama Model"
    echo "6. Initialize Database"
    echo "7. Clean Everything (removes volumes)"
    echo "8. Health Check"
    echo "9. Exit"
    echo ""
    read -p "Select an option [1-9]: " choice
    
    case $choice in
        1)
            print_info "Starting Quick Setup (Production)..."
            check_docker
            check_docker_compose
            check_docker_daemon
            create_env_file
            build_images prod
            start_services prod
            pull_ollama_model
            init_database
            show_urls
            ;;
        2)
            print_info "Starting Development Mode..."
            check_docker
            check_docker_compose
            check_docker_daemon
            create_env_file
            build_images dev
            start_services dev
            pull_ollama_model
            init_database
            show_urls
            ;;
        3)
            print_info "Stopping all services..."
            docker-compose down
            docker-compose -f docker-compose.dev.yml down
            print_success "All services stopped"
            ;;
        4)
            print_info "Showing logs (press Ctrl+C to exit)..."
            docker-compose logs -f
            ;;
        5)
            pull_ollama_model
            ;;
        6)
            init_database
            ;;
        7)
            read -p "⚠️  This will delete all data. Are you sure? (yes/no): " confirm
            if [ "$confirm" == "yes" ]; then
                print_info "Cleaning everything..."
                docker-compose down -v
                docker-compose -f docker-compose.dev.yml down -v
                docker system prune -af --volumes
                print_success "Cleanup complete"
            else
                print_info "Cleanup cancelled"
            fi
            ;;
        8)
            print_info "Checking service health..."
            echo ""
            echo "Backend Health:"
            curl -s http://localhost:8000/api/health | jq '.' || echo "  ❌ Backend not responding"
            echo ""
            echo "Frontend:"
            if curl -s http://localhost:3000 > /dev/null; then
                echo "  ✅ Frontend OK"
            else
                echo "  ❌ Frontend not responding"
            fi
            echo ""
            echo "PostgreSQL:"
            if docker exec supaquery-postgres pg_isready -U supaquery &> /dev/null; then
                echo "  ✅ PostgreSQL OK"
            else
                echo "  ❌ PostgreSQL not ready"
            fi
            echo ""
            ;;
        9)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            show_menu
            ;;
    esac
}

# If script is run with arguments, execute accordingly
if [ $# -gt 0 ]; then
    case $1 in
        start|up)
            check_docker
            check_docker_compose
            check_docker_daemon
            create_env_file
            build_images prod
            start_services prod
            pull_ollama_model
            init_database
            show_urls
            ;;
        dev)
            check_docker
            check_docker_compose
            check_docker_daemon
            create_env_file
            build_images dev
            start_services dev
            pull_ollama_model
            init_database
            show_urls
            ;;
        stop|down)
            docker-compose down
            docker-compose -f docker-compose.dev.yml down
            ;;
        logs)
            docker-compose logs -f
            ;;
        clean)
            docker-compose down -v
            docker-compose -f docker-compose.dev.yml down -v
            ;;
        *)
            echo "Usage: $0 {start|dev|stop|logs|clean}"
            echo "  start - Start in production mode"
            echo "  dev   - Start in development mode"
            echo "  stop  - Stop all services"
            echo "  logs  - View logs"
            echo "  clean - Clean everything (removes volumes)"
            exit 1
            ;;
    esac
else
    # Show interactive menu
    show_menu
fi
