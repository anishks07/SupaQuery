#!/usr/bin/env python3
"""
Clean up duplicate documents from Memgraph
Keeps only documents that exist in PostgreSQL database
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Set DATABASE_URL to use PostgreSQL explicitly
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql+asyncpg://mac@localhost/supaquery'

from app.database.postgres import db_service
from app.services.memgraph_service import get_memgraph_service

async def cleanup_duplicates():
    """Remove documents from Memgraph that don't exist in PostgreSQL"""
    print("=" * 60)
    print("Cleaning Up Duplicate Documents")
    print("=" * 60)
    
    try:
        # Initialize services
        print("\n🔧 Initializing services...")
        await db_service.init_db()
        graph = get_memgraph_service()
        print("✅ Services initialized")
        
        # Get documents from PostgreSQL
        print("\n📋 Fetching documents from PostgreSQL...")
        pg_docs = await db_service.list_documents(limit=1000)
        pg_doc_ids = {str(doc.id) for doc in pg_docs}
        print(f"   Found {len(pg_doc_ids)} documents in database: {pg_doc_ids}")
        
        # Get documents from Memgraph
        print("\n📊 Fetching documents from Memgraph...")
        graph_docs = graph.list_documents(limit=100)
        print(f"   Found {len(graph_docs)} documents in knowledge graph")
        
        # Find documents to delete (in graph but not in database)
        docs_to_delete = []
        for doc in graph_docs:
            doc_id = str(doc['id'])
            if doc_id not in pg_doc_ids:
                docs_to_delete.append(doc)
                print(f"   ⚠️  Will delete: ID={doc_id}, Name={doc['filename']}")
        
        if not docs_to_delete:
            print("\n✅ No duplicate documents found!")
            return
        
        # Confirm deletion
        print(f"\n⚠️  About to delete {len(docs_to_delete)} document(s) from knowledge graph")
        response = input("Continue? (yes/no): ").lower().strip()
        
        if response != 'yes':
            print("❌ Deletion cancelled")
            return
        
        # Delete documents
        print("\n🗑️  Deleting duplicate documents...")
        deleted_count = 0
        for doc in docs_to_delete:
            try:
                success = graph.delete_document(doc['id'])
                if success:
                    print(f"   ✅ Deleted: {doc['filename']} (ID: {doc['id']})")
                    deleted_count += 1
                else:
                    print(f"   ❌ Failed to delete: {doc['id']}")
            except Exception as e:
                print(f"   ❌ Error deleting {doc['id']}: {e}")
        
        # Show final stats
        print("\n" + "=" * 60)
        print("Cleanup Complete")
        print("=" * 60)
        print(f"✅ Deleted {deleted_count} duplicate document(s)")
        
        stats = graph.get_stats()
        print(f"\n📊 Updated Knowledge Graph Statistics:")
        print(f"   - Documents: {stats['documents']}")
        print(f"   - Chunks: {stats['chunks']}")
        print(f"   - Entities: {stats['entities']}")
        print(f"   - Relationships: {stats['relationships']}")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
