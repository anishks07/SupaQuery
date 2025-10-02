# Manual Setup Guide - PostgreSQL + RBAC

## Step-by-Step Manual Setup

### 1. Activate Virtual Environment

```bash
cd /Users/mac/Desktop/SupaQuery/backend
source venv/bin/activate  # or whatever your venv path is
```

### 2. Database Already Created ✓

The database `supaquery` has been created successfully with user `mac`.

### 3. Install Python Dependencies

```bash
pip install psycopg2-binary asyncpg sqlalchemy alembic
pip install 'python-jose[cryptography]'
pip install 'passlib[bcrypt]'
```

Or all at once:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and update these lines:
# DATABASE_URL=postgresql+asyncpg://mac@localhost/supaquery
# SECRET_KEY=<generate below>
```

Generate SECRET_KEY:
```bash
openssl rand -hex 32
```

Copy the output and paste it in `.env` as `SECRET_KEY=<paste here>`

### 5. Initialize Database

```bash
python3 init_db.py
```

This will:
- Create all tables (users, roles, permissions, documents, chat_sessions, etc.)
- Create 3 default roles (admin, user, viewer)
- Create 11 permissions
- Assign permissions to roles
- Prompt you to create an admin user

**Example admin user:**
- Username: admin
- Email: admin@example.com
- Password: (choose a secure password)

### 6. Backup Old main.py and Activate PostgreSQL Version

```bash
# Backup SQLite version
mv main.py main_sqlite.py.bak

# Activate PostgreSQL version
cp main_postgres.py main.py
```

### 7. Start the Server

```bash
python3 main.py
```

You should see:
```
🚀 Starting SupaQuery Backend with PostgreSQL + RBAC...
   ✓ Database initialized
   - Documents indexed: 0
   - Authentication: Enabled (JWT)
   - RBAC: Enabled
```

### 8. Test Authentication

**Register a test user:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

**Login and get token:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

Save the `access_token` from the response!

**Test with token:**
```bash
TOKEN="your_access_token_here"

# List documents
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer $TOKEN"

# Get current user info
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN"
```

## Quick Reference

### Your PostgreSQL Settings

- **Database**: `supaquery`
- **User**: `mac` (your macOS username)
- **Host**: `localhost`
- **Port**: `5432` (default)
- **Connection String**: `postgresql+asyncpg://mac@localhost/supaquery`

### Environment Variables (.env)

```env
# PostgreSQL (use your user 'mac')
DATABASE_URL=postgresql+asyncpg://mac@localhost/supaquery

# JWT Authentication (generate with: openssl rand -hex 32)
SECRET_KEY=your-generated-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama (existing)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Server
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
```

### Common Commands

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if needed
brew services start postgresql@14

# Connect to database
psql supaquery

# List tables (inside psql)
\dt

# Exit psql
\q

# View server logs
# Just watch the terminal where you ran: python3 main.py
```

### Rollback to SQLite

If you need to go back to SQLite:

```bash
# Stop server (Ctrl+C)

# Restore SQLite version
mv main_sqlite.py.bak main.py

# Restart
python3 main.py
```

## Troubleshooting

### "Module not found" errors
- Make sure venv is activated: `source venv/bin/activate`
- Check which Python: `which python` (should show venv path)
- Reinstall dependencies: `pip install -r requirements.txt`

### "Connection refused" database errors
- Check PostgreSQL is running: `brew services list`
- Verify DATABASE_URL in .env uses `mac` (not `postgres`)

### Import errors in Python files
- These are linting errors, ignore them
- The code will work at runtime when dependencies are installed

## Next Steps

1. ✅ Database created
2. Activate venv ← **YOU ARE HERE**
3. Install dependencies
4. Configure .env
5. Run init_db.py
6. Activate PostgreSQL version
7. Start server
8. Test with curl

## Full Documentation

- **POSTGRES_README.md** - Quick start overview
- **POSTGRES_SETUP.md** - Detailed setup guide
- **MIGRATION_GUIDE.md** - Migration from SQLite
- **IMPLEMENTATION_SUMMARY.md** - Technical details

Good luck! 🚀
