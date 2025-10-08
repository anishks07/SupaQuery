"""
Re-index all documents from Memgraph into FAISS
Run this after implementing the hybrid system to populate FAISS with existing documents
"""

import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.memgraph_service import MemgraphService
from app.services.faiss_reranker_service import FAISSRerankerService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def reindex_all_documents():
    """Re-index all documents from Memgraph into FAISS"""
    print("🔄 Starting FAISS re-indexing...")
    print("-" * 80)
    
    # Initialize services
    memgraph = MemgraphService()
    faiss = FAISSRerankerService()
    
    # Get all documents from Memgraph
    try:
        documents = memgraph.list_documents(limit=1000)
        print(f"📚 Found {len(documents)} documents in Memgraph")
        
        if not documents:
            print("⚠️ No documents found. Upload documents first.")
            return
        
        total_chunks = 0
        
        # For each document, get chunks and add to FAISS
        for i, doc in enumerate(documents, 1):
            doc_id = doc.get('id') or doc.get('doc_id')
            filename = doc.get('filename', 'Unknown')
            
            print(f"\n[{i}/{len(documents)}] Processing: {filename}")
            print(f"   Doc ID: {doc_id}")
            
            try:
                # Get all chunks for this document from Memgraph
                chunks = memgraph.query_similar_chunks(
                    query_text="",  # Empty query to get all chunks
                    doc_ids=[doc_id],
                    limit=1000
                )
                
                if not chunks:
                    print(f"   ⚠️ No chunks found for {filename}")
                    continue
                
                print(f"   📄 Found {len(chunks)} chunks")
                
                # Prepare chunks for FAISS
                chunk_data = []
                for chunk in chunks:
                    chunk_data.append({
                        'text': chunk.get('text', ''),
                        'doc_id': doc_id,
                        'chunk_id': chunk.get('chunk_id') or chunk.get('id'),
                        'source': chunk.get('source', filename)
                    })
                
                # Add to FAISS
                faiss.add_chunks(chunk_data)
                total_chunks += len(chunk_data)
                print(f"   ✅ Added {len(chunk_data)} chunks to FAISS")
                
            except Exception as e:
                print(f"   ❌ Error processing {filename}: {e}")
                continue
        
        print("\n" + "=" * 80)
        print(f"✅ Re-indexing complete!")
        print(f"   Documents processed: {len(documents)}")
        print(f"   Total chunks indexed: {total_chunks}")
        print(f"   FAISS index size: {faiss.index.ntotal}")
        
    except Exception as e:
        print(f"❌ Error during re-indexing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    reindex_all_documents()
