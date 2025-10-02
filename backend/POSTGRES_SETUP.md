# PostgreSQL with RBAC Setup Guide

This guide walks you through setting up PostgreSQL with Role-Based Access Control (RBAC) for SupaQuery.

## Prerequisites

- Python 3.13+
- PostgreSQL 14+ installed
- pip package manager

## Installation Steps

### 1. Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

### 2. Create Database

```bash
# Create database user (optional, or use default postgres user)
createuser -U postgres supaquery_user -P

# Create database
createdb -U postgres supaquery

# Or using psql:
psql -U postgres
CREATE DATABASE supaquery;
CREATE USER supaquery_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE supaquery TO supaquery_user;
\q
```

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `psycopg2-binary` - PostgreSQL adapter for Python
- `asyncpg` - Async PostgreSQL driver
- `sqlalchemy` - ORM for database operations
- `alembic` - Database migration tool
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing

### 4. Configure Environment Variables

Create a `.env` file in the `backend` directory (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and update:

```env
# PostgreSQL connection string
# Format: postgresql+asyncpg://username:password@host:port/database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/supaquery

# Generate a secure secret key
SECRET_KEY=your-secret-key-here

# Token expiration time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate a secure SECRET_KEY:**
```bash
openssl rand -hex 32
```

### 5. Initialize Database

Run the initialization script to create tables, roles, permissions, and admin user:

```bash
cd backend
python init_db.py
```

This will:
1. Create all database tables (users, roles, permissions, documents, etc.)
2. Create default roles: `admin`, `user`, `viewer`
3. Create permissions for documents, chat, and user management
4. Assign permissions to roles
5. Prompt you to create an admin user

**Example initialization:**
```
Enter admin username (default: admin): admin
Enter admin email: admin@example.com
Enter full name (optional): System Administrator
Enter admin password (min 8 characters): ********
Confirm password: ********

✓ Admin user 'admin' created successfully!
```

### 6. Start the Application

```bash
cd backend
python main.py
```

The backend will start on `http://localhost:8000`

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `hashed_password` - Bcrypt hashed password
- `full_name` - User's full name
- `is_active` - Account status
- `is_superuser` - Superuser flag (bypasses all permission checks)
- `created_at`, `updated_at` - Timestamps

### Roles Table
- `id` - Primary key
- `name` - Role name (admin, user, viewer)
- `description` - Role description
- `created_at` - Timestamp

### Permissions Table
- `id` - Primary key
- `resource` - Resource type (documents, chat, users)
- `action` - Action type (create, read, update, delete)
- `description` - Permission description

### Documents Table
- `id` - Primary key
- `user_id` - Owner (foreign key to users)
- `filename`, `original_filename` - File names
- `file_type`, `file_size`, `file_path` - File metadata
- `status` - Processing status
- `total_chunks` - Number of chunks
- `is_public` - Public access flag
- `created_at`, `updated_at` - Timestamps

### Chat Sessions Table
- `id` - Session ID (string)
- `user_id` - Owner (foreign key to users)
- `title` - Session title
- `message_count` - Number of messages
- `created_at`, `updated_at` - Timestamps

### Document Chunks Table
- Links documents to their text chunks

### Chat Messages Table
- Links chat sessions to messages with full conversation history

## Default Roles and Permissions

### Admin Role
Full system access:
- All document operations (create, read, update, delete, share)
- All chat operations
- User management
- Role management

### User Role
Standard user access:
- Create, read, update, delete own documents
- Share documents with others
- Create and manage own chat sessions
- Cannot manage users or roles

### Viewer Role
Read-only access:
- Read shared documents
- View chat history
- Cannot create, update, or delete

## API Authentication

### Register New User
```bash
POST http://localhost:8000/api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

### Login
```bash
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "username": "newuser",
  "password": "securepassword123"
}

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    ...
  }
}
```

### Access Protected Endpoints
Include the JWT token in the `Authorization` header:

```bash
GET http://localhost:8000/api/documents
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Get Current User
```bash
GET http://localhost:8000/api/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Admin Operations

### List All Users (Admin Only)
```bash
GET http://localhost:8000/api/admin/users
Authorization: Bearer <admin_token>
```

### Assign Role to User (Admin Only)
```bash
POST http://localhost:8000/api/admin/users/{user_id}/roles
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role_name": "user"
}
```

## Document Access Control

### Public Documents
Set `is_public=true` when uploading:
```bash
POST http://localhost:8000/api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file_data>
is_public: true
```

### Share Document with User
```bash
POST http://localhost:8000/api/documents/{doc_id}/share
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 2
}
```

### List Accessible Documents
```bash
# Returns: owned + shared + public documents
GET http://localhost:8000/api/documents
Authorization: Bearer <token>
```

## Chat Session Access

Chat sessions are private by default - only the owner can access them. Use the JWT token to ensure users only see their own conversations.

```bash
# Get my chat sessions
GET http://localhost:8000/api/chat/sessions
Authorization: Bearer <token>

# Get specific session (only if I own it)
GET http://localhost:8000/api/chat/sessions/{session_id}
Authorization: Bearer <token>
```

## Database Backup

### Backup Database
```bash
pg_dump -U postgres supaquery > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
psql -U postgres supaquery < backup_20250101.sql
```

## Troubleshooting

### Connection Refused
Check PostgreSQL is running:
```bash
# macOS
brew services list

# Ubuntu/Debian
sudo systemctl status postgresql
```

### Authentication Failed
Check connection string in `.env`:
- Username and password are correct
- Database exists
- User has access to database

### Permission Denied Errors
Check user roles and permissions:
```bash
psql -U postgres supaquery
SELECT u.username, r.name as role 
FROM users u 
JOIN user_roles ur ON u.id = ur.user_id 
JOIN roles r ON ur.role_id = r.id;
```

### Reset Admin Password
```bash
psql -U postgres supaquery
UPDATE users SET hashed_password = '<new_bcrypt_hash>' WHERE username = 'admin';
```

Or run `init_db.py` again to create a new admin user.

## Migration from SQLite

If migrating from the old SQLite database:

1. Export SQLite data
2. Transform to PostgreSQL format
3. Import using `psql` or `COPY` commands
4. Run `init_db.py` to set up RBAC tables
5. Manually assign user_id to existing documents and sessions

## Security Best Practices

1. **Change SECRET_KEY**: Never use the default in production
2. **Use Strong Passwords**: Minimum 8 characters, mixed case, numbers, symbols
3. **HTTPS Only**: Use TLS/SSL in production
4. **Token Expiration**: Keep ACCESS_TOKEN_EXPIRE_MINUTES reasonable (15-30 minutes)
5. **Database Access**: Use separate PostgreSQL user with limited privileges
6. **Regular Backups**: Automate daily database backups
7. **Update Dependencies**: Keep all packages up to date for security patches

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost/supaquery` |
| `SECRET_KEY` | JWT signing secret | (required, no default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token lifetime | `30` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Default LLM model | `llama3.2:latest` |
| `BACKEND_PORT` | Server port | `8000` |
| `BACKEND_HOST` | Server host | `0.0.0.0` |

## Next Steps

1. Test authentication with Postman or curl
2. Create additional users with different roles
3. Test document upload and sharing
4. Test chat with role-based access
5. Configure frontend to use JWT authentication
6. Set up production environment with proper secrets

## Support

For issues or questions:
- Check PostgreSQL logs: `tail -f /var/log/postgresql/postgresql-14-main.log`
- Check application logs in terminal
- Verify environment variables are loaded
- Test database connection: `psql -U postgres supaquery`
