# 🐳 Docker Quick Reference

Quick commands for SupaQuery Docker operations.

---

## 🚀 Quick Start

```bash
# Interactive setup
./docker-setup.sh

# Or direct commands
./docker-setup.sh start    # Production mode
./docker-setup.sh dev      # Development mode
./docker-setup.sh stop     # Stop services
./docker-setup.sh logs     # View logs
./docker-setup.sh clean    # Clean everything
```

---

## 📦 Using Makefile

```bash
make help          # Show all available commands
make build         # Build images
make up            # Start services (production)
make dev           # Start in development mode
make down          # Stop services
make logs-f        # Follow logs
make pull-model    # Pull Ollama model
make init-db       # Initialize database
make clean         # Remove everything
```

---

## 🔧 Docker Compose Commands

### Start Services

```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up -d

# With rebuild
docker-compose up -d --build

# View output (no detach)
docker-compose up
```

### Stop Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f memgraph
docker-compose logs -f ollama

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Service Management

```bash
# Restart service
docker-compose restart backend

# Rebuild service
docker-compose up -d --build backend

# Scale service
docker-compose up -d --scale backend=3

# Check status
docker-compose ps
```

---

## 🛠️ Container Operations

### Shell Access

```bash
# Backend
docker exec -it supaquery-backend /bin/sh

# Frontend
docker exec -it supaquery-frontend /bin/sh

# PostgreSQL
docker exec -it supaquery-postgres psql -U supaquery -d supaquery

# Run command in container
docker exec supaquery-backend python init_db.py
```

### File Operations

```bash
# Copy file to container
docker cp file.txt supaquery-backend:/app/

# Copy file from container
docker cp supaquery-backend:/app/file.txt ./

# View file
docker exec supaquery-backend cat /app/main.py
```

### Container Info

```bash
# List containers
docker ps
docker ps -a  # Include stopped

# Inspect container
docker inspect supaquery-backend

# View resource usage
docker stats supaquery-backend

# Check health
docker inspect --format='{{.State.Health.Status}}' supaquery-backend
```

---

## 🗄️ Database Operations

### PostgreSQL

```bash
# Connect to database
docker exec -it supaquery-postgres psql -U supaquery -d supaquery

# Backup database
docker exec supaquery-postgres pg_dump -U supaquery supaquery > backup.sql

# Restore database
cat backup.sql | docker exec -i supaquery-postgres psql -U supaquery supaquery

# Run SQL file
docker exec -i supaquery-postgres psql -U supaquery -d supaquery < init.sql

# List databases
docker exec supaquery-postgres psql -U supaquery -c "\l"

# List tables
docker exec supaquery-postgres psql -U supaquery -d supaquery -c "\dt"
```

### Memgraph

```bash
# Access Memgraph Lab UI
open http://localhost:3001

# Run Cypher query
docker exec -it supaquery-memgraph mgconsole

# In mgconsole:
MATCH (n) RETURN n LIMIT 10;
MATCH (d:Document) RETURN d;
```

---

## 🤖 Ollama Operations

```bash
# List models
docker exec supaquery-ollama ollama list

# Pull model
docker exec supaquery-ollama ollama pull llama3.2:latest
docker exec supaquery-ollama ollama pull mistral
docker exec supaquery-ollama ollama pull phi

# Test model
docker exec supaquery-ollama ollama run llama3.2 "Hello, world!"

# Remove model
docker exec supaquery-ollama ollama rm llama3.2
```

---

## 🔍 Debugging

### View Service Health

```bash
# Backend
curl http://localhost:8000/api/health

# Frontend
curl http://localhost:3000

# PostgreSQL
docker exec supaquery-postgres pg_isready -U supaquery

# Memgraph
docker exec supaquery-memgraph nc -z localhost 7687 && echo "OK" || echo "FAIL"
```

### View Environment Variables

```bash
# Backend
docker exec supaquery-backend env | grep -E 'DATABASE|OLLAMA|MEMGRAPH'

# Frontend
docker exec supaquery-frontend env | grep NEXT_PUBLIC
```

### Check Ports

```bash
# List ports
docker-compose ps

# Check if port is in use
lsof -i :8000
lsof -i :3000
lsof -i :5432
```

### Resource Usage

```bash
# All containers
docker stats

# Specific container
docker stats supaquery-backend

# Disk usage
docker system df
docker system df -v
```

---

## 🧹 Cleanup

### Remove Containers

```bash
# Stop and remove all
docker-compose down

# Remove with volumes
docker-compose down -v

# Remove specific container
docker rm -f supaquery-backend
```

### Clean Images

```bash
# Remove unused images
docker image prune

# Remove all unused images
docker image prune -a

# Remove specific image
docker rmi supaquery-backend
```

### Clean Volumes

```bash
# List volumes
docker volume ls

# Remove specific volume
docker volume rm supaquery_postgres_data

# Remove unused volumes
docker volume prune
```

### Complete Cleanup

```bash
# Remove everything (careful!)
docker system prune -af --volumes

# Or use make
make clean
```

---

## 🔄 Update & Rebuild

### Update Images

```bash
# Pull latest base images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build
```

### Update Single Service

```bash
# Rebuild backend
docker-compose build backend
docker-compose up -d backend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

---

## 📊 Monitoring

### Real-time Logs

```bash
# All services with timestamps
docker-compose logs -f --timestamps

# Filter by service
docker-compose logs -f backend | grep ERROR

# Last N lines
docker-compose logs --tail=50 backend
```

### Service Status

```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose ps backend

# Detailed info
docker inspect supaquery-backend | jq '.[0].State'
```

---

## 🔐 Security

### Scan Images

```bash
# Scan for vulnerabilities
docker scan supaquery-backend
docker scan supaquery-frontend
```

### Update Secrets

```bash
# Regenerate SECRET_KEY
openssl rand -hex 32

# Update .env file
# Then restart services
docker-compose up -d --force-recreate backend
```

---

## 🚀 Production Tips

### Run in Production Mode

```bash
# Set environment
export NODE_ENV=production

# Start with production settings
docker-compose -f docker-compose.yml up -d

# Check logs
docker-compose logs -f
```

### Enable Auto-restart

```bash
# Already configured in docker-compose.yml
restart: unless-stopped
```

### Resource Limits

Add to docker-compose.yml:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

---

## 📱 URLs

```
Frontend:      http://localhost:3000
Backend API:   http://localhost:8000
API Docs:      http://localhost:8000/docs
Memgraph Lab:  http://localhost:3001
PostgreSQL:    localhost:5432
```

---

## 🆘 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check if port is in use
lsof -i :8000

# Force recreate
docker-compose up -d --force-recreate backend
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec supaquery-postgres pg_isready -U supaquery

# Restart database
docker-compose restart postgres

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
```

### Out of Disk Space

```bash
# Check usage
docker system df

# Clean up
docker system prune -af --volumes

# Clean specific items
docker volume prune
docker image prune -a
```

---

**Need more help? Check:**
- Full guide: `DOCKER_GUIDE.md`
- Interactive setup: `./docker-setup.sh`
- Make commands: `make help`
