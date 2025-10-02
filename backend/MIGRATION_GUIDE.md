# Migration Guide: SQLite to PostgreSQL with RBAC

This guide walks you through migrating from the SQLite implementation to PostgreSQL with full RBAC support.

## Quick Start

### Option 1: Fresh Start (Recommended)

If you want to start fresh with PostgreSQL:

```bash
# 1. Install and start PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# 2. Create database
createdb supaquery

# 3. Install Python dependencies
cd backend
pip install psycopg2-binary asyncpg sqlalchemy alembic python-jose[cryptography] passlib[bcrypt]

# 4. Configure environment
cp .env.example .env
# Edit .env and add:
#   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/supaquery
#   SECRET_KEY=$(openssl rand -hex 32)

# 5. Initialize database with RBAC
python init_db.py

# 6. Replace main.py with PostgreSQL version
mv main.py main_sqlite.py.bak
mv main_postgres.py main.py

# 7. Start the server
python main.py
```

### Option 2: Migrate Existing Data

If you have existing documents and conversations to migrate:

```bash
# 1-5: Same as Option 1 above

# 6. Export SQLite data
python export_sqlite_data.py  # We'll create this script

# 7. Import to PostgreSQL
python import_to_postgres.py  # We'll create this script

# 8. Replace main.py
mv main.py main_sqlite.py.bak
mv main_postgres.py main.py

# 9. Start server
python main.py
```

## What's Changed

### Database Layer

**Before (SQLite):**
- File: `app/database/schema.py`
- Synchronous operations with `sqlite3`
- Single database file
- No connection pooling
- Manual SQL queries

**After (PostgreSQL):**
- File: `app/database/postgres.py`
- Async operations with `asyncpg` + `SQLAlchemy`
- PostgreSQL server with connection pooling
- ORM-based queries
- Better concurrent access

### New Tables

PostgreSQL adds 5 new tables for authentication and RBAC:

1. **users** - User accounts with authentication
2. **roles** - User roles (admin, user, viewer)
3. **permissions** - Fine-grained permissions
4. **user_roles** - Many-to-many: users ↔ roles
5. **role_permissions** - Many-to-many: roles ↔ permissions

### Modified Tables

Existing tables updated with user ownership:

1. **documents** - Added `user_id`, `is_public`, `shared_with`
2. **chat_sessions** - Added `user_id`
3. **document_shares** - New table for sharing documents

### API Changes

**New Endpoints:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/users/me` - Get current user info
- `POST /api/documents/{id}/share` - Share document
- `GET /api/admin/users` - List all users (admin)
- `POST /api/admin/users/{id}/roles` - Assign role (admin)

**Modified Endpoints:**
All existing endpoints now require authentication:
- Add `Authorization: Bearer <token>` header
- Results filtered by user access
- Documents scoped to user ownership/sharing
- Chat sessions scoped to user

### Authentication Flow

**Before:**
- No authentication
- All users see all documents
- All users see all chat sessions

**After:**
- JWT token required for all operations
- Users only see their own documents + shared + public
- Users only see their own chat sessions
- Role-based permissions enforced

## Testing the New System

### 1. Start the Server

```bash
cd backend
python main.py
```

You should see:
```
🚀 Starting SupaQuery Backend with PostgreSQL + RBAC...
   ✓ Database initialized
   - Documents indexed: 0
   - Authentication: Enabled (JWT)
   - RBAC: Enabled
```

### 2. Register a User

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

Response:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_superuser": false,
  "roles": ["user"],
  "created_at": "2025-01-01T12:00:00",
  "updated_at": "2025-01-01T12:00:00"
}
```

### 3. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { ... }
}
```

Save the `access_token` for subsequent requests!

### 4. Upload a Document

```bash
TOKEN="<your_access_token>"

curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@test.pdf" \
  -F "is_public=false"
```

### 5. List Your Documents

```bash
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Chat with Your Documents

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this document about?",
    "document_ids": [1]
  }'
```

### 7. Share a Document

```bash
# First, create another user or get their user_id
# Then share document 1 with user 2:

curl -X POST http://localhost:8000/api/documents/1/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "user_id": 2
  }'
```

## Troubleshooting

### "Could not validate credentials"
- Your JWT token expired (default: 30 minutes)
- Login again to get a new token

### "Permission denied: documents:create"
- Your user doesn't have the required permission
- Check your role: `GET /api/users/me`
- Admin can assign permissions: `POST /api/admin/users/{id}/roles`

### "Document not found or access denied"
- You don't own the document
- It's not shared with you
- It's not public
- Document was deleted

### "Database connection error"
- PostgreSQL is not running: `brew services list`
- Wrong credentials in DATABASE_URL
- Database doesn't exist: `createdb supaquery`

### Import errors after migration
- Old code still importing `app.database.schema`
- Update imports to `app.database.postgres`
- Or keep both for backward compatibility

## Rollback Plan

If you need to rollback to SQLite:

```bash
# 1. Stop the server
pkill -f "python main.py"

# 2. Restore old main.py
mv main_sqlite.py.bak main.py

# 3. Restart with SQLite
python main.py
```

Your SQLite database at `backend/storage/supaquery.db` is unchanged.

## Frontend Integration

Update your frontend to handle authentication:

### 1. Store JWT Token

```typescript
// After login:
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### 2. Add Authorization Header

```typescript
// For all API calls:
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/documents', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 3. Handle Token Expiration

```typescript
// Check for 401 Unauthorized:
if (response.status === 401) {
  // Token expired, redirect to login
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
}
```

### 4. Create Login Page

Add a login page component:
- Form with username/password fields
- Call `/api/auth/login` endpoint
- Store token in localStorage
- Redirect to app on success

### 5. Add Register Page

Add a registration page component:
- Form with username, email, password fields
- Call `/api/auth/register` endpoint
- Auto-login after successful registration

### 6. Create Protected Route Wrapper

```typescript
// ProtectedRoute.tsx
export function ProtectedRoute({ children }) {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    return <Navigate to="/login" />;
  }
  
  return <>{children}</>;
}

// Usage in App.tsx:
<Route path="/app" element={
  <ProtectedRoute>
    <AppLayout />
  </ProtectedRoute>
} />
```

## Performance Comparison

| Metric | SQLite | PostgreSQL |
|--------|--------|------------|
| Concurrent Users | 1-2 | 100+ |
| Write Performance | Fast (single user) | Faster (concurrent) |
| Read Performance | Fast | Faster (with indexes) |
| Connection Pooling | No | Yes (20 connections) |
| ACID Compliance | Yes | Yes |
| Full-Text Search | Basic | Advanced |
| JSON Support | Limited | Native |
| Backups | File copy | pg_dump / streaming |
| Scalability | Limited | Excellent |

## Security Improvements

### JWT Tokens
- Stateless authentication
- Automatic expiration (30 minutes)
- Secure signing with SECRET_KEY
- Bearer token in Authorization header

### Password Security
- Bcrypt hashing with salt
- Minimum 8 characters enforced
- Never stored in plaintext
- Secure password verification

### Role-Based Access Control
- Fine-grained permissions
- Separation of concerns
- Least privilege principle
- Admin can manage user access

### Data Isolation
- Users only see their own data
- Document sharing requires explicit permission
- Public documents opt-in only
- Superuser bypass for admin operations

## Next Steps

1. **Test all functionality** - Upload, chat, delete with multiple users
2. **Create admin user** - Run `python init_db.py` if not done
3. **Update frontend** - Add login/register pages
4. **Configure production** - Set strong SECRET_KEY, use HTTPS
5. **Set up monitoring** - Track failed logins, permission denials
6. **Regular backups** - Schedule pg_dump cronjobs
7. **Performance tuning** - Adjust connection pool, add indexes
8. **Documentation** - Update API docs with authentication

## Support

If you encounter issues:
- Check `POSTGRES_SETUP.md` for detailed setup
- Review logs in terminal
- Test with `psql -U postgres supaquery`
- Verify DATABASE_URL is correct
- Ensure PostgreSQL is running

## Success Checklist

- [ ] PostgreSQL installed and running
- [ ] Database created: `supaquery`
- [ ] Python dependencies installed
- [ ] `.env` file configured with DATABASE_URL and SECRET_KEY
- [ ] Database initialized: `python init_db.py`
- [ ] Admin user created
- [ ] Default roles and permissions created
- [ ] `main_postgres.py` renamed to `main.py`
- [ ] Server starts without errors
- [ ] Can register new user
- [ ] Can login and get JWT token
- [ ] Can upload document with auth
- [ ] Can list documents (shows only accessible ones)
- [ ] Can share document with another user
- [ ] Can create and retrieve chat sessions
- [ ] Admin can list all users
- [ ] Admin can assign roles
- [ ] Frontend updated with authentication

## Maintenance Commands

```bash
# View database
psql -U postgres supaquery

# List tables
\dt

# View users and roles
SELECT u.username, r.name as role 
FROM users u 
LEFT JOIN user_roles ur ON u.id = ur.user_id 
LEFT JOIN roles r ON ur.role_id = r.id;

# View permissions
SELECT r.name as role, p.resource, p.action 
FROM roles r 
JOIN role_permissions rp ON r.id = rp.role_id 
JOIN permissions p ON rp.permission_id = p.id 
ORDER BY r.name, p.resource, p.action;

# Backup database
pg_dump -U postgres supaquery > backup.sql

# Restore database
psql -U postgres supaquery < backup.sql

# Reset database
dropdb supaquery
createdb supaquery
python init_db.py
```

---

**Congratulations!** 🎉 You now have a production-ready GraphRAG system with PostgreSQL and full role-based access control!
