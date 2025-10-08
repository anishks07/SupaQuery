# SupaQuery Makefile
# Convenient commands for Docker operations

.PHONY: help build up down restart logs clean pull-model init-db dev prod

# Default target
help:
	@echo "SupaQuery Docker Commands"
	@echo "========================="
	@echo "make build       - Build all Docker images"
	@echo "make up          - Start all services in production mode"
	@echo "make down        - Stop all services"
	@echo "make restart     - Restart all services"
	@echo "make logs        - View logs from all services"
	@echo "make logs-f      - Follow logs from all services"
	@echo "make clean       - Remove all containers, volumes, and images"
	@echo "make pull-model  - Pull Ollama model in container"
	@echo "make init-db     - Initialize database with tables and admin user"
	@echo ""
	@echo "Development:"
	@echo "make dev         - Start services in development mode with hot-reload"
	@echo "make dev-logs    - View development logs"
	@echo ""
	@echo "Production:"
	@echo "make prod        - Start services in production mode"
	@echo ""
	@echo "Individual services:"
	@echo "make backend     - View backend logs"
	@echo "make frontend    - View frontend logs"
	@echo "make ollama      - View Ollama logs"
	@echo "make postgres    - View PostgreSQL logs"
	@echo "make memgraph    - View Memgraph logs"

# Build all images
build:
	docker-compose build

# Start all services (production)
up:
	docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Memgraph Lab: http://localhost:3001"

# Start in development mode
dev:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000 (hot-reload enabled)"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Memgraph Lab: http://localhost:3001"

# Start in production mode
prod:
	docker-compose up -d --build
	@echo "Production services started!"

# Stop all services
down:
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

# Restart all services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs

# Follow logs
logs-f:
	docker-compose logs -f

# Development logs
dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Individual service logs
backend:
	docker-compose logs -f backend

frontend:
	docker-compose logs -f frontend

ollama:
	docker-compose logs -f ollama

postgres:
	docker-compose logs -f postgres

memgraph:
	docker-compose logs -f memgraph

# Pull Ollama model
pull-model:
	docker exec supaquery-ollama ollama pull llama3.2:latest
	@echo "Model pulled successfully!"

# Initialize database
init-db:
	docker exec supaquery-backend python init_db.py
	@echo "Database initialized!"

# Clean everything
clean:
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -af --volumes
	@echo "Cleaned all Docker resources!"

# Health check
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/api/health | jq '.' || echo "Backend not responding"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend: OK" || echo "Frontend: NOT OK"
	@docker exec supaquery-postgres pg_isready -U supaquery && echo "PostgreSQL: OK" || echo "PostgreSQL: NOT OK"

# Backup database
backup-db:
	docker exec supaquery-postgres pg_dump -U supaquery supaquery > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backup created!"

# Restore database
restore-db:
	@read -p "Enter backup file path: " backup_file; \
	cat $$backup_file | docker exec -i supaquery-postgres psql -U supaquery supaquery
	@echo "Database restored!"

# Shell access
shell-backend:
	docker exec -it supaquery-backend /bin/sh

shell-frontend:
	docker exec -it supaquery-frontend /bin/sh

shell-postgres:
	docker exec -it supaquery-postgres psql -U supaquery -d supaquery

# Update all images
update:
	docker-compose pull
	docker-compose up -d --build
	@echo "All services updated!"
