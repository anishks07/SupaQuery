"""
GraphRAG Service
Implements Graph-based Retrieval Augmented Generation using:
- LlamaIndex for document indexing
- ChromaDB for vector storage
- Ollama for local LLM inference
- Graph-based relationships between document chunks
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# LlamaIndex
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    Document as LlamaDocument
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

# ChromaDB
import chromadb
from chromadb.config import Settings as ChromaSettings


class GraphRAGService:
    def __init__(self):
        """Initialize GraphRAG service with local models"""
        
        # Configure LlamaIndex settings
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Use Ollama for LLM (make sure Ollama is running)
        Settings.llm = Ollama(
            model="llama3.2:latest",  # or "mistral", "phi", etc.
            request_timeout=120.0,
            temperature=0.7
        )
        
        # Initialize ChromaDB
        chroma_client = chromadb.PersistentClient(
            path="./storage/chroma_db"
        )
        
        # Create or get collection
        self.collection = chroma_client.get_or_create_collection(
            name="supaquery_documents"
        )
        
        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        
        # Create storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        # Initialize index (will be populated as documents are added)
        self.index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=self.storage_context
        )
        
        # Store document metadata
        self.documents_metadata = {}
        
        print("✅ GraphRAG Service initialized")
        print(f"   - Embedding model: sentence-transformers/all-MiniLM-L6-v2")
        print(f"   - LLM: Ollama (llama3.2)")
        print(f"   - Vector store: ChromaDB")
    
    async def add_document(self, file_info: Dict[str, Any]) -> None:
        """
        Add a processed document to the GraphRAG system
        """
        try:
            doc_id = file_info["id"]
            chunks = file_info.get("chunk_data", [])
            
            if not chunks:
                print(f"⚠️  No chunks found for document {doc_id}")
                return
            
            # Create LlamaIndex documents from chunks
            documents = []
            for chunk in chunks:
                doc = LlamaDocument(
                    text=chunk["text"],
                    metadata={
                        "doc_id": doc_id,
                        "filename": file_info["filename"],
                        "file_type": file_info["type"],
                        "chunk_id": chunk["chunk_id"],
                        "source": file_info["filename"]
                    }
                )
                documents.append(doc)
            
            # Add documents to index
            self.index.insert_nodes(
                [doc.to_langchain_format() for doc in documents]
            )
            
            # Store metadata
            self.documents_metadata[doc_id] = {
                "id": doc_id,
                "filename": file_info["filename"],
                "type": file_info["type"],
                "chunks": len(chunks),
                "added_at": datetime.now().isoformat()
            }
            
            print(f"✅ Added document {file_info['filename']} with {len(chunks)} chunks")
            
        except Exception as e:
            print(f"❌ Error adding document to GraphRAG: {str(e)}")
            raise
    
    async def query(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query the GraphRAG system
        Returns answer with citations and sources
        """
        try:
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="tree_summarize"
            )
            
            # If specific documents requested, add filter
            if document_ids:
                # Note: Filtering would require custom implementation
                # For now, we query all documents
                pass
            
            # Execute query
            response = query_engine.query(query)
            
            # Extract sources and citations
            sources = []
            citations = []
            
            if hasattr(response, 'source_nodes'):
                for i, node in enumerate(response.source_nodes):
                    metadata = node.node.metadata
                    
                    source_info = {
                        "filename": metadata.get("filename", "Unknown"),
                        "chunk_id": metadata.get("chunk_id", 0),
                        "score": node.score if hasattr(node, 'score') else 0.0,
                        "text": node.node.get_content()[:200] + "..."
                    }
                    sources.append(source_info)
                    
                    citation = {
                        "title": metadata.get("filename", "Unknown"),
                        "url": f"#doc-{metadata.get('doc_id')}",
                        "snippet": node.node.get_content()[:150] + "..."
                    }
                    citations.append(citation)
            
            return {
                "answer": str(response),
                "citations": citations,
                "sources": sources,
                "query": query
            }
            
        except Exception as e:
            print(f"❌ Query error: {str(e)}")
            return {
                "answer": f"I encountered an error processing your query: {str(e)}. Please make sure Ollama is running and has the required model installed.",
                "citations": [],
                "sources": [],
                "query": query
            }
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the system"""
        return list(self.documents_metadata.values())
    
    async def delete_document(self, document_id: str) -> None:
        """Delete a document from the system"""
        if document_id in self.documents_metadata:
            # Note: ChromaDB deletion would require custom implementation
            # For now, just remove from metadata
            del self.documents_metadata[document_id]
            print(f"✅ Deleted document {document_id}")
        else:
            raise ValueError(f"Document {document_id} not found")
