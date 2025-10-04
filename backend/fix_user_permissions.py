"""
Quick script to ensure user 'Anish' has all necessary permissions
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database.postgres import db_service
from sqlalchemy import select
from app.database.models import User, Role


async def fix_permissions():
    """Ensure Anish has admin or user role with proper permissions"""
    await db_service.init_db()
    
    print("Checking user 'Anish'...")
    
    async with db_service.get_db_session() as session:
        # Get Anish user
        result = await session.execute(select(User).where(User.username == 'Anish'))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User 'Anish' not found!")
            return
        
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        print(f"   Current roles: {[r.name for r in user.roles]}")
        
        # Check if user has any roles
        if not user.roles:
            print("⚠️  User has no roles! Assigning 'admin' role...")
            
            # Get admin role
            admin_result = await session.execute(select(Role).where(Role.name == 'admin'))
            admin_role = admin_result.scalar_one_or_none()
            
            if admin_role:
                user.roles.append(admin_role)
                await session.commit()
                print("✅ Assigned 'admin' role to Anish")
                print(f"   Permissions: {[(p.resource, p.action) for p in admin_role.permissions]}")
            else:
                print("❌ Admin role not found! Run 'python init_db.py' first")
        else:
            print("✅ User has roles:")
            for role in user.roles:
                perms = [(p.resource, p.action) for p in role.permissions]
                print(f"   - {role.name}: {len(perms)} permissions")
                for resource, action in perms:
                    print(f"     • {resource}:{action}")


if __name__ == "__main__":
    asyncio.run(fix_permissions())
