"""
Debug script to inspect FAISS index and test queries
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.services.faiss_reranker_service import FAISSRerankerService

def debug_faiss_index():
    """Inspect FAISS index contents and test Obama query"""
    print("🔍 Debugging FAISS Index")
    print("=" * 80)
    
    # Initialize FAISS service
    faiss = FAISSRerankerService()
    
    print(f"\n📊 Index Statistics:")
    print(f"   Total vectors: {faiss.index.ntotal}")
    print(f"   Embedding dimension: {faiss.embedding_dim}")
    print(f"   Metadata entries: {len(faiss.chunk_metadata)}")
    
    print(f"\n📄 Index Contents:")
    for i, chunk in enumerate(faiss.chunk_metadata):
        print(f"\n[{i+1}] Doc ID: {chunk.get('doc_id', 'Unknown')}")
        print(f"    Source: {chunk.get('source', 'Unknown')}")
        print(f"    Text preview: {chunk.get('text', '')[:100]}...")
    
    # Check for Obama-specific content FIRST (before slow search)
    print(f"\n" + "=" * 80)
    print(f"🔎 Searching for Obama-related chunks in index:")
    print("=" * 80)
    obama_chunks = [c for c in faiss.chunk_metadata if 'obama' in c.get('text', '').lower() or 'obama' in c.get('source', '').lower()]
    print(f"Found {len(obama_chunks)} chunks containing 'obama'")
    for i, chunk in enumerate(obama_chunks, 1):
        print(f"\n[{i}] Source: {chunk.get('source', 'Unknown')}")
        print(f"    Text: {chunk.get('text', '')[:200]}...")

if __name__ == "__main__":
    debug_faiss_index()
