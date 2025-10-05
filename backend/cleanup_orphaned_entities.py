#!/usr/bin/env python3
"""
Clean up orphaned entities from Memgraph
Removes entities that are no longer referenced by any chunks
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.memgraph_service import get_memgraph_service

def cleanup_orphaned_entities():
    """Remove entities that have no chunk references"""
    print("=" * 60)
    print("Cleaning Up Orphaned Entities")
    print("=" * 60)
    
    try:
        graph = get_memgraph_service()
        print("✅ Connected to Memgraph")
        
        # Get current stats
        stats_before = graph.get_stats()
        print(f"\n📊 Current Statistics:")
        print(f"   - Documents: {stats_before['documents']}")
        print(f"   - Chunks: {stats_before['chunks']}")
        print(f"   - Entities: {stats_before['entities']}")
        print(f"   - Relationships: {stats_before['relationships']}")
        
        # Find orphaned entities (entities with no chunk references)
        print(f"\n🔍 Finding orphaned entities...")
        result = graph.db.execute_and_fetch("""
            MATCH (e:Entity)
            WHERE NOT EXISTS((e)<-[:MENTIONS]-(:Chunk))
            RETURN e.name as name, e.type as type
        """)
        
        orphaned = list(result)
        
        if not orphaned:
            print("✅ No orphaned entities found!")
            return
        
        print(f"⚠️  Found {len(orphaned)} orphaned entities:")
        for entity in orphaned[:10]:  # Show first 10
            print(f"   - {entity['name']} ({entity['type']})")
        if len(orphaned) > 10:
            print(f"   ... and {len(orphaned) - 10} more")
        
        # Confirm deletion
        response = input(f"\nDelete {len(orphaned)} orphaned entities? (yes/no): ").lower().strip()
        
        if response != 'yes':
            print("❌ Cleanup cancelled")
            return
        
        # Delete orphaned entities
        print(f"\n🗑️  Deleting orphaned entities...")
        graph.db.execute("""
            MATCH (e:Entity)
            WHERE NOT EXISTS((e)<-[:MENTIONS]-(:Chunk))
            DETACH DELETE e
        """)
        
        # Get updated stats
        stats_after = graph.get_stats()
        deleted_count = stats_before['entities'] - stats_after['entities']
        
        print(f"\n✅ Deleted {deleted_count} orphaned entities")
        
        print(f"\n📊 Updated Statistics:")
        print(f"   - Documents: {stats_after['documents']}")
        print(f"   - Chunks: {stats_after['chunks']}")
        print(f"   - Entities: {stats_after['entities']} (was {stats_before['entities']})")
        print(f"   - Relationships: {stats_after['relationships']}")
        
        print("\n" + "=" * 60)
        print("Cleanup Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_orphaned_entities()
