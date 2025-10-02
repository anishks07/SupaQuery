# PostgreSQL + RBAC Implementation for SupaQuery

## 🎯 Quick Start

### Automated Setup (Recommended)

**macOS/Linux:**
```bash
cd backend
./setup_postgres.sh
```

**Windows:**
```cmd
cd backend
setup_postgres.bat
```

The script will:
1. Install/start PostgreSQL
2. Create `supaquery` database
3. Install Python dependencies
4. Generate SECRET_KEY
5. Initialize database with roles and permissions
6. Create admin user
7. Activate PostgreSQL version

### Manual Setup

If you prefer manual control:

1. **Install PostgreSQL**
   ```bash
   # macOS
   brew install postgresql@14
   brew services start postgresql@14
   
   # Ubuntu/Debian
   sudo apt install postgresql
   sudo systemctl start postgresql
   ```

2. **Create Database**
   ```bash
   createdb supaquery
   ```

3. **Install Dependencies**
   ```bash
   pip install psycopg2-binary asyncpg sqlalchemy alembic python-jose[cryptography] passlib[bcrypt]
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and set:
   #   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/supaquery
   #   SECRET_KEY=$(openssl rand -hex 32)
   ```

5. **Initialize Database**
   ```bash
   python init_db.py
   ```

6. **Activate PostgreSQL Version**
   ```bash
   mv main.py main_sqlite.py.bak
   mv main_postgres.py main.py
   ```

7. **Start Server**
   ```bash
   python main.py
   ```

## 📚 Documentation

### Essential Reading

1. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Start here!
   - What was created (2,500+ lines of code)
   - Security features (JWT, RBAC, data isolation)
   - API changes (authentication required)
   - Database schema (9 tables with relationships)
   - Performance improvements (100+ concurrent users)

2. **[POSTGRES_SETUP.md](POSTGRES_SETUP.md)** - Complete setup guide
   - PostgreSQL installation steps
   - Environment configuration
   - Database initialization
   - API authentication examples
   - Admin operations
   - Security best practices
   - Troubleshooting

3. **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - SQLite to PostgreSQL
   - Two migration paths (fresh vs. data migration)
   - Before/after comparisons
   - Testing with curl examples
   - Frontend integration guide
   - Rollback instructions

## 🏗️ Architecture Overview

### New Components

```
backend/
├── app/
│   ├── auth/                    # NEW: Authentication & RBAC
│   │   ├── __init__.py
│   │   ├── auth.py             # JWT tokens, password hashing
│   │   ├── rbac.py             # Permission checking
│   │   └── schemas.py          # Pydantic models
│   └── database/
│       ├── models.py           # NEW: SQLAlchemy ORM models
│       ├── postgres.py         # NEW: Async database service
│       └── schema.py           # OLD: SQLite (keep for backup)
├── init_db.py                  # NEW: Database initialization
├── main_postgres.py            # NEW: FastAPI with auth
├── main.py                     # OLD: SQLite version (backup)
├── setup_postgres.sh           # NEW: Automated setup (Unix)
├── setup_postgres.bat          # NEW: Automated setup (Windows)
└── .env                        # NEW: PostgreSQL configuration
```

### Database Schema

```
users ──┬─── user_roles ───── roles ──┬─── role_permissions ─── permissions
        │                             │
        └─── documents ────────────────┘
        │    ├── document_chunks
        │    └── document_shares ─── users
        │
        └─── chat_sessions
             └── chat_messages
```

## 🔐 Security Features

### Authentication
- **JWT tokens** with 30-minute expiration
- **Bcrypt password hashing** (automatic salting)
- **Stateless authentication** (no server-side sessions)
- **Bearer token** in Authorization header

### Authorization (RBAC)
- **3 roles**: admin, user, viewer
- **11 permissions**: documents (create/read/update/delete/share), chat (create/read/delete), users (manage/read), roles (manage)
- **Fine-grained control**: resource:action pairs
- **Superuser bypass**: admins have unrestricted access

### Data Isolation
- Users only see their own documents + shared + public
- Chat sessions private to owner
- Document sharing requires explicit permission
- All queries filtered by user context

## 🚀 API Examples

### Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"securepass123"}'

# Response includes access_token
```

### Upload Document (Authenticated)
```bash
TOKEN="your_jwt_token"
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@document.pdf" \
  -F "is_public=false"
```

### List My Documents
```bash
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer $TOKEN"
```

### Share Document
```bash
curl -X POST http://localhost:8000/api/documents/1/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id":1,"user_id":2}'
```

### Chat with Documents
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Summarize this document","document_ids":[1]}'
```

## 🎭 Default Roles & Permissions

| Role | Permissions |
|------|-------------|
| **admin** | All operations + user management + role assignment |
| **user** | Create/read/update/delete own documents, share documents, create/manage own chats |
| **viewer** | Read shared documents, view chat history (read-only) |

## 📊 Performance

| Metric | SQLite | PostgreSQL |
|--------|--------|------------|
| Concurrent Users | 1-2 | 100+ |
| Connection Pool | No | Yes (20+40) |
| Write Concurrency | Serial | Parallel |
| Query Performance | Good | Better (indexes) |
| Scalability | Limited | Excellent |

## 🧪 Testing

### Test Authentication Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123"}'

# 2. Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}' \
  | jq -r '.access_token')

# 3. Upload document
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@test.pdf"

# 4. List documents
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer $TOKEN"

# 5. Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is in the document?"}'
```

## 🔧 Configuration

### Environment Variables

```env
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/supaquery

# JWT Authentication
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama (existing)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Server (existing)
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
```

### Generate Secure SECRET_KEY

```bash
# macOS/Linux
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Online
# Visit: https://randomkeygen.com/
```

## 🐛 Troubleshooting

### "Could not connect to database"
- PostgreSQL not running: `brew services start postgresql@14`
- Wrong credentials in DATABASE_URL
- Database doesn't exist: `createdb supaquery`

### "Could not validate credentials"
- JWT token expired (login again)
- Wrong token format (should be `Bearer <token>`)
- SECRET_KEY changed (invalidates all tokens)

### "Permission denied: documents:create"
- User doesn't have required permission
- Check role: `GET /api/users/me`
- Admin can assign role: `POST /api/admin/users/{id}/roles`

### "Document not found or access denied"
- Document doesn't exist
- User doesn't own it
- Not shared with user
- Not public

## 🔄 Rollback to SQLite

If you need to rollback:

```bash
# Stop server
pkill -f "python main.py"

# Restore old main.py
mv main_sqlite.py.bak main.py

# Restart with SQLite
python main.py
```

Your SQLite database at `storage/supaquery.db` is unchanged.

## 📖 Frontend Integration

### Add to your frontend:

1. **Login Page** - Form with username/password
2. **Register Page** - Form with email, username, password
3. **Token Storage** - Save JWT in localStorage
4. **Auth Header** - Add `Authorization: Bearer <token>` to all API calls
5. **Token Refresh** - Handle 401 errors by redirecting to login
6. **Protected Routes** - Wrap routes requiring authentication

Example React:
```typescript
// Store token after login
localStorage.setItem('token', data.access_token);

// Add to all API calls
const token = localStorage.getItem('token');
fetch('http://localhost:8000/api/documents', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Handle expiration
if (response.status === 401) {
  localStorage.removeItem('token');
  navigate('/login');
}
```

## ✅ Success Checklist

Before deploying:

- [ ] PostgreSQL installed and running
- [ ] Database `supaquery` created
- [ ] Python dependencies installed
- [ ] `.env` file configured with DATABASE_URL
- [ ] SECRET_KEY generated and set (32+ characters)
- [ ] Database initialized: `python init_db.py` completed
- [ ] Admin user created
- [ ] Default roles and permissions created
- [ ] Server starts without errors: `python main.py`
- [ ] Can register new user
- [ ] Can login and receive JWT token
- [ ] Can upload document with authentication
- [ ] Can list documents (shows only accessible)
- [ ] Can share document with another user
- [ ] Can create and view chat sessions
- [ ] Admin can list all users
- [ ] Admin can assign roles to users
- [ ] Frontend updated with login/register pages
- [ ] Token stored and sent with API calls

## 📞 Support

### Check Logs
```bash
# Server logs
python main.py  # Watch terminal output

# PostgreSQL logs (macOS)
tail -f /usr/local/var/log/postgresql@14/server.log

# PostgreSQL logs (Ubuntu)
tail -f /var/log/postgresql/postgresql-14-main.log
```

### Database Access
```bash
# Connect to database
psql -U postgres supaquery

# List tables
\dt

# View users
SELECT id, username, email, is_active FROM users;

# View roles
SELECT u.username, r.name 
FROM users u 
JOIN user_roles ur ON u.id = ur.user_id 
JOIN roles r ON ur.role_id = r.id;
```

### Common Commands
```bash
# Restart PostgreSQL
brew services restart postgresql@14  # macOS
sudo systemctl restart postgresql    # Ubuntu

# Backup database
pg_dump -U postgres supaquery > backup.sql

# Restore database
psql -U postgres supaquery < backup.sql

# Reset database
dropdb supaquery
createdb supaquery
python init_db.py
```

## 🎉 You're All Set!

Your SupaQuery instance now has:
- ✅ Production-ready PostgreSQL database
- ✅ Secure JWT authentication
- ✅ Role-based access control
- ✅ Multi-user support
- ✅ Document sharing
- ✅ Data isolation
- ✅ Scalable architecture

**Start building!** 🚀

---

For detailed information, see:
- **IMPLEMENTATION_SUMMARY.md** - What was built
- **POSTGRES_SETUP.md** - How to set it up
- **MIGRATION_GUIDE.md** - How to migrate from SQLite
