"""
FAISS Vector Store with Cross-Encoder Reranking
Provides fast semantic search with high-precision reranking
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import re


class FAISSRerankerService:
    """
    Hybrid retrieval service combining:
    1. FAISS for fast semantic search (bi-encoder)
    2. Cross-Encoder for accurate reranking
    """
    
    def __init__(self, storage_path: str = "./storage"):
        """Initialize FAISS index and reranker models"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self.index_path = self.storage_path / "faiss_index.bin"
        self.metadata_path = self.storage_path / "faiss_metadata.pkl"
        
        # Initialize embedding model (bi-encoder for fast retrieval)
        print("🔧 Initializing FAISS + BM25 Reranker service (fully offline)...")
        # Use the correct model name that's already cached
        try:
            self.embedding_model = SentenceTransformer(
                'all-MiniLM-L6-v2', 
                device='cpu'
            )
            print(f"   ✓ Loaded embedding model from cache (offline mode)")
        except Exception as e:
            print(f"   ❌ Error loading model: {e}")
            print(f"   💡 Run: python download_models.py to cache models")
            raise e
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        
        # BM25 reranker - fully offline, no external API calls
        print(f"   ✓ Using BM25 reranker (fully offline, no external dependencies)")
        
        # FAISS index and metadata
        self.index = None
        self.chunk_metadata = []  # List of {text, doc_id, chunk_id, citation, source}
        
        # Try to load existing index
        self._load_index()
        
        if self.index is None:
            # Create new index
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            print(f"   ✓ Created new FAISS index (dim={self.embedding_dim})")
        
        print(f"✅ FAISS + BM25 Reranker initialized (fully offline)")
        print(f"   - Embedding model: all-MiniLM-L6-v2 (local)")
        print(f"   - Reranker: BM25Okapi (fully offline)")
        print(f"   - Index size: {self.index.ntotal} vectors")
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add chunks to FAISS index
        
        Args:
            chunks: List of chunk dicts with 'text', 'doc_id', 'chunk_id', 'source', 'citation'
        """
        if not chunks:
            return
        
        try:
            # Extract text for embedding
            texts = [chunk.get('text', '') for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Normalize for cosine similarity (optional but recommended)
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings)
            
            # Store metadata
            for chunk in chunks:
                self.chunk_metadata.append({
                    'text': chunk.get('text', ''),
                    'doc_id': chunk.get('doc_id', ''),
                    'chunk_id': chunk.get('chunk_id', ''),
                    'source': chunk.get('source', ''),
                    'citation': chunk.get('citation', {})
                })
            
            print(f"   ✓ Added {len(chunks)} chunks to FAISS index (total: {self.index.ntotal})")
            
            # Auto-save after adding
            self._save_index()
            
        except Exception as e:
            print(f"   ❌ Error adding chunks to FAISS: {e}")
    
    def search(self, query: str, top_k: int = 20, doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Stage 1: Fast semantic search using FAISS
        
        Args:
            query: Search query
            top_k: Number of candidates to retrieve (will be reranked)
            doc_ids: Optional list of doc IDs to filter by
            
        Returns:
            List of candidate chunks with scores
        """
        if self.index.ntotal == 0:
            print("   ⚠️ FAISS index is empty")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], show_progress_bar=False)
            query_embedding = np.array(query_embedding).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search FAISS index
            # Get more candidates than needed for filtering and reranking
            search_k = top_k * 2 if doc_ids else top_k
            distances, indices = self.index.search(query_embedding, min(search_k, self.index.ntotal))
            
            # Collect results
            candidates = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.chunk_metadata):
                    chunk = self.chunk_metadata[idx].copy()
                    chunk['faiss_score'] = float(1 / (1 + distance))  # Convert distance to similarity score
                    
                    # Filter by doc_ids if specified
                    if doc_ids is None or chunk['doc_id'] in doc_ids:
                        candidates.append(chunk)
            
            # Limit to top_k after filtering
            candidates = candidates[:top_k]
            
            # Count by source type for debugging
            obama_cnt = sum(1 for c in candidates if 'obama' in c.get('source', '').lower() or '.mp3' in c.get('source', '').lower())
            pdf_cnt = sum(1 for c in candidates if '.pdf' in c.get('source', '').lower())
            
            print(f"   ✓ FAISS retrieved {len(candidates)} candidates ({obama_cnt} Obama, {pdf_cnt} PDF)")
            
            # Show top 3 for debugging
            if candidates:
                print(f"      Top 3 FAISS results:")
                for i, c in enumerate(candidates[:3], 1):
                    source_type = "Obama" if 'obama' in c.get('source', '').lower() else "PDF"
                    print(f"         {i}. [{source_type}] Score: {c['faiss_score']:.4f} - {c.get('text', '')[:60]}...")
            return candidates
            
        except Exception as e:
            print(f"   ❌ Error searching FAISS: {e}")
            return []
    
    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Stage 2: Rerank candidates using BM25 (fully offline)
        
        BM25 is a probabilistic retrieval function that ranks documents based on
        query term frequency and document length normalization. It's very effective
        for reranking and requires no external models or API calls.
        
        Args:
            query: Original query
            candidates: Candidate chunks from FAISS
            top_k: Number of final results after reranking
            
        Returns:
            Reranked and filtered chunks
        """
        if not candidates:
            return []
        
        try:
            # Tokenize query and candidate texts
            def tokenize(text: str) -> List[str]:
                """Simple tokenization: lowercase and split on non-alphanumeric"""
                return re.findall(r'\w+', text.lower())
            
            query_tokens = tokenize(query)
            candidate_texts = [chunk['text'] for chunk in candidates]
            tokenized_corpus = [tokenize(text) for text in candidate_texts]
            
            # Create BM25 index
            bm25 = BM25Okapi(tokenized_corpus)
            
            # Get BM25 scores for all candidates
            bm25_scores = bm25.get_scores(query_tokens)
            
            # Combine BM25 scores with FAISS scores (weighted average)
            # BM25 is better at exact matches, FAISS is better at semantic similarity
            for i, chunk in enumerate(candidates):
                faiss_score = chunk.get('faiss_score', 0.5)
                bm25_score = float(bm25_scores[i])
                
                # Normalize BM25 score to 0-1 range
                bm25_normalized = bm25_score / (bm25_score + 1.0) if bm25_score > 0 else 0
                
                # Weighted combination: 60% FAISS (semantic) + 40% BM25 (lexical)
                combined_score = 0.6 * faiss_score + 0.4 * bm25_normalized
                
                chunk['rerank_score'] = combined_score
                chunk['bm25_score'] = bm25_normalized
            
            # Sort by combined score (descending)
            reranked = sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)
            
            # Return top_k
            final_results = reranked[:top_k]
            
            print(f"   ✓ BM25 reranked to top {len(final_results)} chunks (fully offline)")
            return final_results
            
        except Exception as e:
            print(f"   ❌ Error reranking: {e}")
            # Fallback to FAISS scores only
            return sorted(candidates, key=lambda x: x.get('faiss_score', 0), reverse=True)[:top_k]
    
    def search_and_rerank(self, query: str, top_k: int = 5, doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Combined search: FAISS retrieval + Cross-encoder reranking
        
        Args:
            query: Search query
            top_k: Number of final results
            doc_ids: Optional list of doc IDs to filter by
            
        Returns:
            Top-k reranked chunks
        """
        # Stage 1: Fast retrieval (get 4x for better reranking)
        candidates = self.search(query, top_k=top_k * 4, doc_ids=doc_ids)
        
        if not candidates:
            return []
        
        # Stage 2: Precision reranking
        reranked = self.rerank(query, candidates, top_k=top_k)
        
        return reranked
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document
        Note: FAISS doesn't support deletion, so we rebuild the index
        
        Args:
            doc_id: Document ID to remove
            
        Returns:
            True if successful
        """
        try:
            # Filter out chunks from this document
            remaining_chunks = [c for c in self.chunk_metadata if c['doc_id'] != doc_id]
            
            if len(remaining_chunks) == len(self.chunk_metadata):
                print(f"   ⚠️ No chunks found for doc_id: {doc_id}")
                return False
            
            # Rebuild index with remaining chunks
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.chunk_metadata = []
            
            if remaining_chunks:
                self.add_chunks(remaining_chunks)
            
            # ⚠️ CRITICAL: Save the updated index to disk
            self._save_index()
            
            print(f"   ✓ Removed document {doc_id} from FAISS index and saved changes")
            return True
            
        except Exception as e:
            print(f"   ❌ Error deleting document from FAISS: {e}")
            return False
    
    def clear_index(self) -> None:
        """Clear the entire index"""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.chunk_metadata = []
        self._save_index()
        print("   ✓ FAISS index cleared")
    
    def _save_index(self) -> None:
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.chunk_metadata, f)
            
        except Exception as e:
            print(f"   ⚠️ Error saving FAISS index: {e}")
    
    def _load_index(self) -> None:
        """Load FAISS index and metadata from disk"""
        try:
            if self.index_path.exists() and self.metadata_path.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(self.index_path))
                
                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    self.chunk_metadata = pickle.load(f)
                
                print(f"   ✓ Loaded existing FAISS index ({self.index.ntotal} vectors)")
            
        except Exception as e:
            print(f"   ⚠️ Could not load FAISS index: {e}")
            self.index = None
            self.chunk_metadata = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.embedding_dim,
            'total_chunks': len(self.chunk_metadata),
            'unique_documents': len(set(c['doc_id'] for c in self.chunk_metadata))
        }


# Global instance
_faiss_service = None

def get_faiss_reranker_service() -> FAISSRerankerService:
    """Get or create FAISSRerankerService instance"""
    global _faiss_service
    if _faiss_service is None:
        _faiss_service = FAISSRerankerService()
    return _faiss_service
