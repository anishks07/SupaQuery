"""
Database initialization script for PostgreSQL with RBAC
This script creates the database schema, default roles, permissions, and admin user
"""
import asyncio
import os
import sys
from getpass import getpass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.postgres import db_service
from app.auth.auth import get_password_hash


async def init_roles_and_permissions():
    """Initialize default roles and permissions"""
    print("Creating default roles...")
    
    # Create roles
    roles = [
        {
            'name': 'admin',
            'description': 'Full system access with user management'
        },
        {
            'name': 'user',
            'description': 'Standard user with document and chat access'
        },
        {
            'name': 'viewer',
            'description': 'Read-only access to shared documents'
        }
    ]
    
    for role_data in roles:
        try:
            role = await db_service.create_role(**role_data)
            print(f"✓ Created role: {role.name}")
        except Exception as e:
            if "duplicate key" in str(e) or "already exists" in str(e):
                print(f"⊙ Role '{role_data['name']}' already exists, skipping...")
            else:
                print(f"✗ Failed to create role {role_data['name']}: {e}")
    
    print("\nCreating permissions...")
    
    # Define permissions
    permissions = [
        # Document permissions
        {'resource': 'documents', 'action': 'create', 'description': 'Create new documents'},
        {'resource': 'documents', 'action': 'read', 'description': 'Read documents'},
        {'resource': 'documents', 'action': 'update', 'description': 'Update documents'},
        {'resource': 'documents', 'action': 'delete', 'description': 'Delete documents'},
        {'resource': 'documents', 'action': 'share', 'description': 'Share documents with others'},
        
        # Chat permissions
        {'resource': 'chat', 'action': 'create', 'description': 'Create chat sessions'},
        {'resource': 'chat', 'action': 'read', 'description': 'Read chat sessions'},
        {'resource': 'chat', 'action': 'delete', 'description': 'Delete chat sessions'},
        
        # User management permissions
        {'resource': 'users', 'action': 'manage', 'description': 'Manage users (create, update, delete)'},
        {'resource': 'users', 'action': 'read', 'description': 'View user information'},
        
        # Role management permissions
        {'resource': 'roles', 'action': 'manage', 'description': 'Manage roles and permissions'},
    ]
    
    for perm_data in permissions:
        try:
            perm = await db_service.create_permission(**perm_data)
            print(f"✓ Created permission: {perm.resource}:{perm.action}")
        except Exception as e:
            if "duplicate key" in str(e) or "already exists" in str(e):
                print(f"⊙ Permission '{perm_data['resource']}:{perm_data['action']}' already exists, skipping...")
            else:
                print(f"✗ Failed to create permission {perm_data['resource']}:{perm_data['action']}: {e}")
    
    print("\nAssigning permissions to roles...")
    
    # Admin role gets all permissions
    admin_permissions = [
        ('documents', 'create'),
        ('documents', 'read'),
        ('documents', 'update'),
        ('documents', 'delete'),
        ('documents', 'share'),
        ('chat', 'create'),
        ('chat', 'read'),
        ('chat', 'delete'),
        ('users', 'manage'),
        ('users', 'read'),
        ('roles', 'manage'),
    ]
    
    for resource, action in admin_permissions:
        try:
            await db_service.assign_permission_to_role('admin', resource, action)
            print(f"✓ Assigned {resource}:{action} to admin")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print(f"⊙ Permission {resource}:{action} already assigned to admin, skipping...")
            else:
                print(f"✗ Failed to assign {resource}:{action} to admin: {e}")
    
    # User role gets standard permissions
    user_permissions = [
        ('documents', 'create'),
        ('documents', 'read'),
        ('documents', 'update'),
        ('documents', 'delete'),
        ('documents', 'share'),
        ('chat', 'create'),
        ('chat', 'read'),
        ('chat', 'delete'),
    ]
    
    for resource, action in user_permissions:
        try:
            await db_service.assign_permission_to_role('user', resource, action)
            print(f"✓ Assigned {resource}:{action} to user")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print(f"⊙ Permission {resource}:{action} already assigned to user, skipping...")
            else:
                print(f"✗ Failed to assign {resource}:{action} to user: {e}")
    
    # Viewer role gets read-only permissions
    viewer_permissions = [
        ('documents', 'read'),
        ('chat', 'read'),
    ]
    
    for resource, action in viewer_permissions:
        try:
            await db_service.assign_permission_to_role('viewer', resource, action)
            print(f"✓ Assigned {resource}:{action} to viewer")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print(f"⊙ Permission {resource}:{action} already assigned to viewer, skipping...")
            else:
                print(f"✗ Failed to assign {resource}:{action} to viewer: {e}")


async def create_admin_user():
    """Create the initial admin user"""
    print("\n" + "="*50)
    print("CREATE ADMIN USER")
    print("="*50)
    
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email: ").strip()
    
    while not email:
        print("Email is required!")
        email = input("Enter admin email: ").strip()
    
    full_name = input("Enter full name (optional): ").strip() or None
    
    password = getpass("Enter admin password (min 8 characters, max 72 characters): ")
    confirm_password = getpass("Confirm password: ")
    
    while password != confirm_password:
        print("Passwords don't match!")
        password = getpass("Enter admin password (min 8 characters, max 72 characters): ")
        confirm_password = getpass("Confirm password: ")
    
    while len(password) < 8 or len(password) > 72:
        if len(password) < 8:
            print("Password must be at least 8 characters!")
        else:
            print("Password cannot be longer than 72 characters (bcrypt limitation)!")
        password = getpass("Enter admin password (min 8 characters, max 72 characters): ")
        confirm_password = getpass("Confirm password: ")
        while password != confirm_password:
            print("Passwords don't match!")
            password = getpass("Enter admin password (min 8 characters, max 72 characters): ")
            confirm_password = getpass("Confirm password: ")
    
    try:
        # Hash password in a thread pool (bcrypt is blocking)
        hashed_password = await asyncio.to_thread(get_password_hash, password)
        
        # Create admin user
        user = await db_service.create_user(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_superuser=True
        )
        
        # Assign admin role
        await db_service.assign_role_to_user(user.id, 'admin')
        
        print(f"\n✓ Admin user '{username}' created successfully!")
        print(f"  Email: {email}")
        print(f"  User ID: {user.id}")
        
    except Exception as e:
        print(f"\n✗ Failed to create admin user: {e}")


async def main():
    """Main initialization function"""
    print("="*50)
    print("SUPAQUERY DATABASE INITIALIZATION")
    print("="*50)
    print()
    
    # Check database URL
    db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost/supaquery')
    print(f"Database URL: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print()
    
    try:
        # Initialize database schema
        print("Initializing database schema...")
        await db_service.init_db()
        print("✓ Database schema created successfully!")
        print()
        
        # Initialize roles and permissions
        await init_roles_and_permissions()
        print()
        
        # Create admin user
        create_admin = input("\nCreate admin user? (y/n): ").strip().lower()
        if create_admin == 'y':
            await create_admin_user()
        
        print("\n" + "="*50)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*50)
        print("\nYou can now start the application with: python main.py")
        print()
        
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(main())
