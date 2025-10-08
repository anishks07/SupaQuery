#!/usr/bin/env python3
"""
Cleanup Orphaned Knowledge Graph Data

This script removes orphaned documents, chunks, and entities from Memgraph
that no longer have corresponding entries in the PostgreSQL database.

Use this after files have been deleted from the database but not properly
cleaned up from the knowledge graph.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.postgres import DatabaseService
from app.services.memgraph_service import get_memgraph_service


async def cleanup_orphaned_graph_data():
    """Remove all orphaned data from Memgraph knowledge graph"""
    
    print("=" * 80)
    print("🧹 KNOWLEDGE GRAPH CLEANUP - Removing Orphaned Data")
    print("=" * 80)
    
    # Initialize services
    db_service = DatabaseService()
    graph_service = get_memgraph_service()
    
    print("\n📊 Getting current state...")
    
    # Get all document IDs from PostgreSQL database
    print("   - Fetching documents from PostgreSQL...")
    try:
        valid_doc_ids = set()
        documents = await db_service.list_documents(limit=10000)
        for doc in documents:
            valid_doc_ids.add(str(doc.id))
        print(f"   ✅ Found {len(valid_doc_ids)} valid documents in database")
    except Exception as e:
        print(f"   ❌ Error fetching from database: {e}")
        return
    
    # Get all document IDs from Memgraph
    print("   - Fetching documents from Memgraph...")
    try:
        query = """
        MATCH (d:Document)
        RETURN d.id as doc_id
        """
        results = list(graph_service.db.execute_and_fetch(query))
        graph_doc_ids = set([r['doc_id'] for r in results if r.get('doc_id')])
        print(f"   ✅ Found {len(graph_doc_ids)} documents in knowledge graph")
    except Exception as e:
        print(f"   ❌ Error fetching from graph: {e}")
        return
    
    # Find orphaned documents
    orphaned_doc_ids = graph_doc_ids - valid_doc_ids
    
    print(f"\n📋 Analysis:")
    print(f"   - Valid documents: {len(valid_doc_ids)}")
    print(f"   - Graph documents: {len(graph_doc_ids)}")
    print(f"   - Orphaned documents: {len(orphaned_doc_ids)}")
    
    if not orphaned_doc_ids:
        print("\n✅ No orphaned data found! Knowledge graph is clean.")
        return
    
    print(f"\n🗑️  Found {len(orphaned_doc_ids)} orphaned documents to remove:")
    for doc_id in list(orphaned_doc_ids)[:10]:  # Show first 10
        print(f"   - Document ID: {doc_id}")
    if len(orphaned_doc_ids) > 10:
        print(f"   ... and {len(orphaned_doc_ids) - 10} more")
    
    # Confirm deletion
    print(f"\n⚠️  This will DELETE:")
    print(f"   - {len(orphaned_doc_ids)} orphaned Document nodes")
    print(f"   - All associated Chunk nodes")
    print(f"   - All associated Entity nodes")
    print(f"   - All relationships")
    
    response = input("\n❓ Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Cleanup cancelled.")
        return
    
    print("\n🔄 Starting cleanup...")
    
    # Delete orphaned documents and their related data
    deleted_count = 0
    failed_count = 0
    
    for doc_id in orphaned_doc_ids:
        try:
            print(f"   🗑️  Deleting document {doc_id}...")
            success = graph_service.delete_document(doc_id)
            if success:
                deleted_count += 1
                print(f"      ✅ Deleted")
            else:
                failed_count += 1
                print(f"      ⚠️  Delete returned False")
        except Exception as e:
            failed_count += 1
            print(f"      ❌ Error: {e}")
    
    # Get final stats
    print("\n📊 Getting final statistics...")
    final_stats = graph_service.get_stats()
    
    print("\n" + "=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)
    print(f"\n📈 Results:")
    print(f"   - Successfully deleted: {deleted_count} documents")
    print(f"   - Failed: {failed_count} documents")
    print(f"\n📊 Final Knowledge Graph Stats:")
    print(f"   - Documents: {final_stats['documents']}")
    print(f"   - Chunks: {final_stats['chunks']}")
    print(f"   - Entities: {final_stats['entities']}")
    print(f"   - Relationships: {final_stats['relationships']}")
    print("\n✨ Knowledge graph is now synchronized with the database!")


async def cleanup_all_graph_data():
    """Nuclear option: Delete ALL data from knowledge graph"""
    
    print("=" * 80)
    print("⚠️  NUCLEAR CLEANUP - DELETE ALL KNOWLEDGE GRAPH DATA")
    print("=" * 80)
    
    graph_service = get_memgraph_service()
    
    # Get current stats
    stats = graph_service.get_stats()
    
    print(f"\n📊 Current Knowledge Graph:")
    print(f"   - Documents: {stats['documents']}")
    print(f"   - Chunks: {stats['chunks']}")
    print(f"   - Entities: {stats['entities']}")
    print(f"   - Relationships: {stats['relationships']}")
    
    print(f"\n⚠️  THIS WILL DELETE EVERYTHING FROM THE KNOWLEDGE GRAPH!")
    print(f"   The database will remain intact, but you'll need to re-index all documents.")
    
    response = input("\n❓ Are you ABSOLUTELY SURE? Type 'DELETE ALL' to confirm: ").strip()
    
    if response != 'DELETE ALL':
        print("\n❌ Cleanup cancelled.")
        return
    
    print("\n🔥 Deleting all data from knowledge graph...")
    
    try:
        # Delete all nodes and relationships
        graph_service.db.execute("MATCH (n) DETACH DELETE n")
        print("   ✅ All nodes and relationships deleted")
        
        # Recreate indexes
        graph_service._create_indexes()
        print("   ✅ Indexes recreated")
        
        # Get final stats
        final_stats = graph_service.get_stats()
        
        print("\n" + "=" * 80)
        print("✅ NUCLEAR CLEANUP COMPLETE")
        print("=" * 80)
        print(f"\n📊 Final Knowledge Graph Stats:")
        print(f"   - Documents: {final_stats['documents']}")
        print(f"   - Chunks: {final_stats['chunks']}")
        print(f"   - Entities: {final_stats['entities']}")
        print(f"   - Relationships: {final_stats['relationships']}")
        
        print("\n💡 Next steps:")
        print("   1. Use the frontend to view your documents")
        print("   2. They should still appear (they're in PostgreSQL)")
        print("   3. To re-index them, use: python reindex_documents.py")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")


def print_menu():
    """Print cleanup menu"""
    print("\n" + "=" * 80)
    print("🧹 KNOWLEDGE GRAPH CLEANUP TOOL")
    print("=" * 80)
    print("\nOptions:")
    print("  1. Smart Cleanup - Remove only orphaned data (Recommended)")
    print("  2. Nuclear Cleanup - Delete ALL graph data (Re-index required)")
    print("  3. View Stats Only")
    print("  4. Exit")
    print()


async def view_stats():
    """View current stats without making changes"""
    print("\n📊 Knowledge Graph Statistics")
    print("=" * 80)
    
    db_service = DatabaseService()
    graph_service = get_memgraph_service()
    
    # Database stats
    print("\n📚 PostgreSQL Database:")
    try:
        documents = await db_service.list_documents(limit=10000)
        print(f"   - Documents: {len(documents)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Graph stats
    print("\n🕸️  Memgraph Knowledge Graph:")
    stats = graph_service.get_stats()
    print(f"   - Documents: {stats['documents']}")
    print(f"   - Chunks: {stats['chunks']}")
    print(f"   - Entities: {stats['entities']}")
    print(f"   - Relationships: {stats['relationships']}")


async def main():
    """Main menu"""
    while True:
        print_menu()
        choice = input("Select option (1-4): ").strip()
        
        if choice == '1':
            await cleanup_orphaned_graph_data()
        elif choice == '2':
            await cleanup_all_graph_data()
        elif choice == '3':
            await view_stats()
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid option. Please choose 1-4.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Cleanup cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
