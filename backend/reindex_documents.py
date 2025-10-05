#!/usr/bin/env python3
"""
Re-index existing documents from PostgreSQL into Memgraph knowledge graph
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set DATABASE_URL to use PostgreSQL explicitly
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql+asyncpg://mac@localhost/supaquery'

from app.database.postgres import db_service
from app.services.graph_rag_v2 import GraphRAGService
from app.services.document_processor import DocumentProcessor

async def reindex_documents():
    """Re-index all documents from PostgreSQL into Memgraph"""
    print("=" * 60)
    print("Re-indexing Documents into Knowledge Graph")
    print("=" * 60)
    
    try:
        # Initialize services
        print("\n🔧 Initializing services...")
        await db_service.init_db()
        graph_rag = GraphRAGService()
        doc_processor = DocumentProcessor()
        print("✅ Services initialized")
        
        # Get all documents from database
        print("\n📋 Fetching documents from database...")
        documents = await db_service.list_documents(limit=1000)
        print(f"   Found {len(documents)} documents")
        
        if not documents:
            print("\n⚠️  No documents found in database")
            return
        
        # Process each document
        success_count = 0
        error_count = 0
        
        for i, doc in enumerate(documents, 1):
            try:
                print(f"\n[{i}/{len(documents)}] Processing: {doc.original_filename}")
                print(f"   - ID: {doc.id}")
                print(f"   - File path: {doc.file_path}")
                
                # Check if file exists
                file_path = Path(doc.file_path)
                if not file_path.exists():
                    print(f"   ⚠️  File not found, skipping")
                    error_count += 1
                    continue
                
                # Re-process the file
                file_info = await doc_processor.process_file(
                    file_path=str(file_path),
                    original_filename=doc.original_filename,
                    file_id=str(doc.id)
                )
                
                # Add metadata
                file_info['user_id'] = doc.user_id
                file_info['document_db_id'] = doc.id
                
                # Add to knowledge graph
                await graph_rag.add_document(file_info)
                
                print(f"   ✅ Successfully indexed with {file_info.get('chunks', 0)} chunks")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                error_count += 1
                continue
        
        # Summary
        print("\n" + "=" * 60)
        print("Re-indexing Complete")
        print("=" * 60)
        print(f"✅ Successfully indexed: {success_count} documents")
        if error_count > 0:
            print(f"❌ Failed: {error_count} documents")
        
        # Show graph stats
        stats = graph_rag.graph.get_stats()
        print(f"\n📊 Knowledge Graph Statistics:")
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
    asyncio.run(reindex_documents())
