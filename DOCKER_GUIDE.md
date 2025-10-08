# 🐳 Docker Deployment Guide for SupaQuery

Complete guide for running SupaQuery with Docker and Docker Compose.

---

## 📋 Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **System Requirements**:
  - 8GB RAM minimum (16GB recommended)
  - 20GB free disk space
  - (Optional) NVIDIA GPU for faster LLM inference

### Install Docker

**macOS:**
```bash
brew install docker docker-compose
# Or download Docker Desktop from https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

**Windows:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop

---

## 🚀 Quick Start

### Option 1: Using Make (Recommended)

```bash
# Build and start all services
make build
make up

# Pull the Ollama model (required on first run)
make pull-model

# Initialize the database
make init-db

# View logs
make logs-f
```

### Option 2: Using Docker Compose Directly

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Pull Ollama model
docker exec supaquery-ollama ollama pull llama3.2:latest

# Initialize database
docker exec supaquery-backend python init_db.py

# View logs
docker-compose logs -f
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Memgraph Lab**: http://localhost:3001
- **PostgreSQL**: localhost:5432

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`

> ⚠️ **Change the default password immediately!**

---

## 🛠️ Development Mode

For development with hot-reload:

```bash
# Start in development mode
make dev

# Or using docker-compose
docker-compose -f docker-compose.dev.yml up

# View logs
make dev-logs
```

**Development features:**
- Hot-reload for backend (code changes auto-restart)
- Hot-reload for frontend (instant updates)
- Longer JWT token expiration (24 hours)
- Debug logging enabled
- Source code mounted as volumes

---

## 📦 Services Overview

### 1. PostgreSQL Database
- **Port**: 5432
- **Database**: supaquery
- **User**: supaquery
- **Purpose**: User authentication, document metadata, RBAC

**Connect to database:**
```bash
docker exec -it supaquery-postgres psql -U supaquery -d supaquery
```

### 2. Memgraph Knowledge Graph
- **Port**: 7687 (Bolt protocol)
- **Lab UI**: http://localhost:3001
- **Purpose**: Entity relationships, knowledge graph

**Access Memgraph Lab:**
```bash
open http://localhost:3001
```

**Example Cypher query:**
```cypher
MATCH (d:Document)-[:CONTAINS]->(c:Chunk)-[:MENTIONS]->(e:Entity)
RETURN d, c, e LIMIT 50;
```

### 3. Ollama LLM Service
- **Port**: 11434
- **Model**: llama3.2:latest
- **Purpose**: Local LLM inference

**Available models:**
```bash
# List installed models
docker exec supaquery-ollama ollama list

# Pull additional models
docker exec supaquery-ollama ollama pull mistral
docker exec supaquery-ollama ollama pull phi
```

### 4. Backend (FastAPI)
- **Port**: 8000
- **Workers**: 4 (production), 1 (development)
- **Features**: GraphRAG, document processing, API endpoints

**Shell access:**
```bash
docker exec -it supaquery-backend /bin/sh
```

### 5. Frontend (Next.js)
- **Port**: 3000
- **Framework**: Next.js 15 with React 19

**Shell access:**
```bash
docker exec -it supaquery-frontend /bin/sh
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Docker Compose Environment
COMPOSE_PROJECT_NAME=supaquery

# Backend
SECRET_KEY=your-secret-key-here-use-32-chars-minimum
DATABASE_URL=postgresql+asyncpg://supaquery:supaquery_password@postgres:5432/supaquery

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Ollama
OLLAMA_MODEL=llama3.2:latest
```

### GPU Support (Optional)

If you have an NVIDIA GPU, uncomment the GPU section in `docker-compose.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

Then install NVIDIA Container Toolkit:

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

---

## 📊 Monitoring

### View Service Status

```bash
# All services
docker-compose ps

# Specific service health
docker inspect --format='{{.State.Health.Status}}' supaquery-backend
```

### View Logs

```bash
# All services
make logs-f

# Individual services
make backend      # Backend logs
make frontend     # Frontend logs
make postgres     # Database logs
make memgraph     # Knowledge graph logs
make ollama       # LLM logs
```

### Health Check

```bash
# Check all services
make health

# Manual checks
curl http://localhost:8000/api/health
curl http://localhost:3000
```

---

## 🔄 Common Operations

### Restart Services

```bash
# Restart all
make restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Update Services

```bash
# Pull latest images and rebuild
make update

# Or manually
docker-compose pull
docker-compose up -d --build
```

### Scale Backend

```bash
# Run 3 backend instances
docker-compose up -d --scale backend=3
```

### Database Operations

**Backup:**
```bash
make backup-db
# Or manually
docker exec supaquery-postgres pg_dump -U supaquery supaquery > backup.sql
```

**Restore:**
```bash
make restore-db
# Or manually
cat backup.sql | docker exec -i supaquery-postgres psql -U supaquery supaquery
```

**Reset database:**
```bash
docker-compose down -v postgres
docker-compose up -d postgres
make init-db
```

---

## 🐛 Troubleshooting

### Services Not Starting

**Check logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Common issues:**
- Port conflicts: Change ports in `docker-compose.yml`
- Memory issues: Increase Docker memory limit (Docker Desktop → Settings → Resources)
- Disk space: Run `docker system prune -a` to free space

### Ollama Model Not Loading

```bash
# Pull model manually
docker exec supaquery-ollama ollama pull llama3.2:latest

# Check if model exists
docker exec supaquery-ollama ollama list

# Test model
docker exec supaquery-ollama ollama run llama3.2 "Hello"
```

### Database Connection Error

```bash
# Check PostgreSQL status
docker exec supaquery-postgres pg_isready -U supaquery

# View database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Memgraph Not Responding

```bash
# Check container status
docker ps | grep memgraph

# Restart Memgraph
docker-compose restart memgraph

# View logs
docker-compose logs memgraph
```

### Frontend Build Fails

```bash
# Clear build cache
docker-compose build --no-cache frontend

# Check Node.js version
docker exec supaquery-frontend node --version

# View build logs
docker-compose logs frontend
```

### Backend Health Check Failing

```bash
# Check backend status
curl http://localhost:8000/api/health

# View detailed logs
docker-compose logs -f backend

# Test database connection
docker exec supaquery-backend python -c "from app.models.database import engine; print(engine)"
```

---

## 🧹 Cleanup

### Stop Services

```bash
# Stop all services
make down

# Or
docker-compose down
```

### Remove Volumes (Deletes Data!)

```bash
# Remove all volumes
docker-compose down -v

# Remove specific volume
docker volume rm supaquery_postgres_data
```

### Complete Cleanup

```bash
# Remove everything (containers, volumes, images)
make clean

# Or manually
docker-compose down -v
docker system prune -af --volumes
```

---

## 🚢 Production Deployment

### Production Checklist

- [ ] Change default passwords in `.env`
- [ ] Generate secure SECRET_KEY (32+ characters)
- [ ] Set `NODE_ENV=production`
- [ ] Configure SSL/TLS certificates
- [ ] Set up reverse proxy (Nginx/Traefik)
- [ ] Enable firewall rules
- [ ] Configure log rotation
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure backups
- [ ] Test disaster recovery

### Production Configuration

**docker-compose.prod.yml:**
```yaml
services:
  backend:
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    restart: always
    
  frontend:
    restart: always
    
  postgres:
    restart: always
    volumes:
      - /path/to/production/data:/var/lib/postgresql/data
      
  memgraph:
    restart: always
    volumes:
      - /path/to/production/memgraph:/var/lib/memgraph
```

**Start production services:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Using Nginx Reverse Proxy

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📈 Performance Tuning

### Backend Workers

Adjust workers based on CPU cores:

```yaml
backend:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 8
```

**Formula:** `workers = (2 * CPU_cores) + 1`

### Database Connection Pool

In `backend/.env`:
```bash
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

### Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## 🔐 Security Best Practices

1. **Use secrets management:**
   ```bash
   docker secret create db_password ./db_password.txt
   ```

2. **Scan images for vulnerabilities:**
   ```bash
   docker scan supaquery-backend
   docker scan supaquery-frontend
   ```

3. **Update base images regularly:**
   ```bash
   docker-compose pull
   docker-compose up -d --build
   ```

4. **Use non-root users** (already configured in Dockerfiles)

5. **Enable Docker Content Trust:**
   ```bash
   export DOCKER_CONTENT_TRUST=1
   ```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Ollama Docker Documentation](https://hub.docker.com/r/ollama/ollama)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Memgraph Documentation](https://memgraph.com/docs)

---

## 🆘 Getting Help

**Check logs first:**
```bash
docker-compose logs -f
```

**Verify configuration:**
```bash
docker-compose config
```

**Report issues:**
- GitHub Issues: https://github.com/anishks07/SupaQuery/issues
- Include: Docker version, compose file, error logs

---

**Happy Deploying! 🚀**
