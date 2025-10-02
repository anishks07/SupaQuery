"""
Cleanup script to remove duplicate permissions and reset the database
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.postgres import db_service


async def cleanup_duplicates():
    """Remove duplicate permissions, keeping only the first one"""
    print("Cleaning up duplicate permissions...")
    
    async with db_service.engine.begin() as conn:
        # First, clear the role_permissions junction table
        await conn.execute(text("DELETE FROM role_permissions"))
        print("✓ Cleared role-permission assignments")
        
        # Get all permissions with their IDs
        result = await conn.execute(text("""
            SELECT id, resource, action, 
                   ROW_NUMBER() OVER (PARTITION BY resource, action ORDER BY id) as rn
            FROM permissions
        """))
        
        rows = result.fetchall()
        ids_to_delete = [row[0] for row in rows if row[3] > 1]
        
        if ids_to_delete:
            # Delete duplicate permissions
            placeholders = ','.join([f'${i+1}' for i in range(len(ids_to_delete))])
            await conn.execute(
                text(f"DELETE FROM permissions WHERE id = ANY(ARRAY[{','.join(map(str, ids_to_delete))}])")
            )
            print(f"✓ Deleted {len(ids_to_delete)} duplicate permissions")
        else:
            print("✓ No duplicate permissions found")
    
    print("\nDatabase cleanup complete!")


async def main():
    print("="*50)
    print("DATABASE CLEANUP")
    print("="*50)
    print()
    
    await db_service.initialize()
    await cleanup_duplicates()
    await db_service.close()


if __name__ == '__main__':
    asyncio.run(main())
