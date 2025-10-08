#!/bin/bash

# Docker Health Check Script for SupaQuery
# This script checks the health of all services

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🏥 SupaQuery Health Check"
echo "=========================="
echo ""

# Check if services are running
check_container() {
    local container_name=$1
    local service_name=$2
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${GREEN}✅ ${service_name}: Container running${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service_name}: Container not running${NC}"
        return 1
    fi
}

# Check container health status
check_health() {
    local container_name=$1
    local service_name=$2
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        health=$(docker inspect --format='{{.State.Health.Status}}' $container_name 2>/dev/null)
        if [ "$health" == "healthy" ]; then
            echo -e "${GREEN}   Health: healthy${NC}"
        elif [ "$health" == "unhealthy" ]; then
            echo -e "${RED}   Health: unhealthy${NC}"
        else
            echo -e "${YELLOW}   Health: no health check configured${NC}"
        fi
    fi
}

# Check HTTP endpoint
check_http() {
    local url=$1
    local service_name=$2
    
    if curl -s -f "$url" > /dev/null; then
        echo -e "${GREEN}   HTTP: responding${NC}"
        return 0
    else
        echo -e "${RED}   HTTP: not responding${NC}"
        return 1
    fi
}

# Check PostgreSQL
echo "📊 PostgreSQL Database"
check_container "supaquery-postgres" "PostgreSQL"
if docker exec supaquery-postgres pg_isready -U supaquery 2>/dev/null | grep -q "accepting connections"; then
    echo -e "${GREEN}   Database: accepting connections${NC}"
else
    echo -e "${RED}   Database: not ready${NC}"
fi
echo ""

# Check Memgraph
echo "🕸️  Memgraph Knowledge Graph"
check_container "supaquery-memgraph" "Memgraph"
if docker exec supaquery-memgraph nc -z localhost 7687 2>/dev/null; then
    echo -e "${GREEN}   Bolt protocol: listening on port 7687${NC}"
else
    echo -e "${RED}   Bolt protocol: not responding${NC}"
fi
check_http "http://localhost:3001" "Memgraph Lab UI"
echo ""

# Check Ollama
echo "🤖 Ollama LLM Service"
check_container "supaquery-ollama" "Ollama"
check_health "supaquery-ollama" "Ollama"
if docker exec supaquery-ollama ollama list 2>/dev/null | grep -q "llama3.2"; then
    echo -e "${GREEN}   Model: llama3.2 installed${NC}"
else
    echo -e "${YELLOW}   Model: llama3.2 not found (run: docker exec supaquery-ollama ollama pull llama3.2)${NC}"
fi
check_http "http://localhost:11434" "Ollama API"
echo ""

# Check Backend
echo "🔧 Backend (FastAPI)"
check_container "supaquery-backend" "Backend"
check_health "supaquery-backend" "Backend"
check_http "http://localhost:8000/api/health" "Backend API"
if curl -s http://localhost:8000/api/health 2>/dev/null | grep -q "healthy"; then
    health_data=$(curl -s http://localhost:8000/api/health 2>/dev/null)
    echo -e "${GREEN}   API: ${health_data}${NC}"
fi
check_http "http://localhost:8000/docs" "API Documentation"
echo ""

# Check Frontend
echo "🎨 Frontend (Next.js)"
check_container "supaquery-frontend" "Frontend"
check_health "supaquery-frontend" "Frontend"
check_http "http://localhost:3000" "Frontend Application"
echo ""

# Summary
echo "📋 Summary"
echo "=========="
running=$(docker ps --format '{{.Names}}' | wc -l)
echo "Running containers: $running"
echo ""

# Check if all critical services are running
critical_services=("supaquery-postgres" "supaquery-memgraph" "supaquery-ollama" "supaquery-backend" "supaquery-frontend")
all_running=true

for service in "${critical_services[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        all_running=false
        break
    fi
done

if [ "$all_running" = true ]; then
    echo -e "${GREEN}✅ All critical services are running!${NC}"
    echo ""
    echo "Access the application:"
    echo "  Frontend:      http://localhost:3000"
    echo "  Backend API:   http://localhost:8000"
    echo "  API Docs:      http://localhost:8000/docs"
    echo "  Memgraph Lab:  http://localhost:3001"
else
    echo -e "${RED}❌ Some critical services are not running${NC}"
    echo ""
    echo "To start services, run:"
    echo "  ./docker-setup.sh start"
    echo "  OR"
    echo "  docker-compose up -d"
fi

echo ""
echo "For detailed logs, run:"
echo "  docker-compose logs -f"
