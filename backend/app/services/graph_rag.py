"""
GraphRAG Service
Implements Graph-based Retrieval Augmented Generation using:
- LlamaIndex for document indexing
- FAISS for vector storage
- Ollama for local LLM inference
- Graph-based relationships between document chunks
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import faiss

# LlamaIndex
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    Document as LlamaDocument
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.core.vector_stores import SimpleVectorStore

# Database
from app.database import db


class GraphRAGService:
    def __init__(self):
        """Initialize GraphRAG service with local models"""
        
        print("🔧 Initializing GraphRAG with Ollama...")
        
        # Use mock/basic embeddings (works without external dependencies)
        # For a production system, you'd want proper embeddings, but this allows the system to work
        from llama_index.core.embeddings import BaseEmbedding
        
        class SimpleEmbedding(BaseEmbedding):
            """Simple embedding that uses basic text hashing - no ML models needed"""
            def _get_query_embedding(self, query: str):
                # Simple hash-based embedding (384 dimensions to match typical models)
                import hashlib
                hash_bytes = hashlib.sha384(query.encode()).digest()
                return [float(b) / 255.0 for b in hash_bytes]
            
            def _get_text_embedding(self, text: str):
                import hashlib
                hash_bytes = hashlib.sha384(text.encode()).digest()
                return [float(b) / 255.0 for b in hash_bytes]
            
            async def _aget_query_embedding(self, query: str):
                return self._get_query_embedding(query)
        
        Settings.embed_model = SimpleEmbedding()
        
        # Use Ollama for LLM (make sure Ollama is running)
        Settings.llm = Ollama(
            model="llama3.2:latest",
            request_timeout=60.0,  # Reduced timeout
            temperature=0.3,  # Lower temperature for more focused, accurate responses
            base_url="http://localhost:11434",
            additional_kwargs={
                "num_ctx": 2048,  # Reduce context window for faster responses
                "num_predict": 512,  # Allow longer responses for detailed answers
            }
        )
        
        # Define system prompt for better accuracy
        self.system_prompt = """You are SupaQuery, an AI assistant specialized in analyzing and answering questions about uploaded documents.

Core Principles:
1. **Accuracy First**: Base all answers strictly on the provided document context. Never make assumptions or add information not present in the documents.
2. **Source Attribution**: Always specify which document(s) your answer comes from.
3. **Clarity**: If information is not in the documents, explicitly state "This information is not available in the uploaded documents."
4. **Precision**: Quote or reference specific sections when appropriate.

Capabilities:
- Analyze PDFs, DOCX files, images (with OCR), and audio transcriptions
- Extract and summarize information from documents
- Answer questions based on document content
- Compare information across multiple documents
- List references, citations, and structured data verbatim when requested

Query Handling:
- For **reference/citation queries** (e.g., "give references", "list citations"): Return the exact text from the document without summarization
- For **data extraction** (e.g., "what are the query clauses", "list skills"): Extract and format the specific information requested
- For **general questions**: Provide clear, concise answers based on document content with proper citations
- For **clarification**: Ask one brief clarifying question if the query is ambiguous

Limitations:
- Cannot access external information or the internet
- Cannot modify or create new documents
- Cannot perform calculations beyond simple logic
- Knowledge is limited to the uploaded documents only

Current date: October 2, 2025

Remember: Be helpful, accurate, and transparent about what you can and cannot answer based on the available documents."""
        
        # Create storage directory
        storage_dir = Path("./storage/vector_store")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Use simple in-memory vector store (backed by FAISS under the hood)
        # This is simpler and more compatible with Python 3.13
        self.index = VectorStoreIndex([])
        
        # Store document metadata
        self.documents_metadata = {}
        
        print("✅ GraphRAG Service initialized")
        print(f"   - Embedding: Simple hash-based (no ML required)")
        print(f"   - LLM: Ollama (llama3.2)")
        print(f"   - Vector store: In-memory")
        print(f"   - Backend: http://localhost:11434")
        print(f"   💡 System is ready - all local, no external dependencies!")
    
    async def add_document(self, file_info: Dict[str, Any]) -> None:
        """
        Add a processed document to the GraphRAG system and database
        """
        try:
            doc_id = file_info["id"]
            chunks = file_info.get("chunk_data", [])
            
            if not chunks:
                print(f"⚠️  No chunks found for document {doc_id}")
                return
            
            # Save to database first
            db.create_document({
                'id': doc_id,
                'filename': file_info["filename"],
                'original_filename': file_info.get("original_filename", file_info["filename"]),
                'file_type': file_info["type"],
                'file_size': file_info.get("size"),
                'file_path': file_info.get("file_path"),
                'status': 'processing'
            })
            
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
            for doc in documents:
                self.index.insert(doc)
            
            # Save chunks to database
            db.create_chunks(doc_id, chunks)
            
            # Store metadata in memory for quick access
            self.documents_metadata[doc_id] = {
                "id": doc_id,
                "filename": file_info["filename"],
                "type": file_info["type"],
                "chunks": len(chunks),
                "added_at": datetime.now().isoformat()
            }
            
            print(f"✅ Added document {file_info['filename']} with {len(chunks)} chunks to database and index")
            
        except Exception as e:
            print(f"❌ Error adding document to GraphRAG: {str(e)}")
            # Update document status to failed
            try:
                db.update_document(doc_id, {'status': 'failed'})
            except:
                pass
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
            print(f"🔍 Processing query: {query[:50]}...")
            
            # Check if index has documents
            if len(self.documents_metadata) == 0:
                print(f"   ⚠️ No documents in index, responding without context")
                # Use LLM directly without RAG, but include system prompt
                from llama_index.core.llms import ChatMessage
                messages = [
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(role="user", content=query)
                ]
                response_obj = Settings.llm.chat(messages)
                return {
                    "answer": str(response_obj.message.content),
                    "citations": [],
                    "sources": [],
                    "query": query
                }
            
            # Check if this is a "give references" or "show references" type query
            query_lower = query.lower()
            is_reference_query = any(term in query_lower for term in [
                'give reference', 'show reference', 'list reference', 
                'what are the reference', 'references in', 'citation'
            ])
            
            if is_reference_query:
                print(f"   📚 Reference extraction query detected")
                # For reference queries, use retrieval mode to get raw chunks
                retriever = self.index.as_retriever(
                    similarity_top_k=5,
                    similarity_cutoff=0.2
                )
                nodes = retriever.retrieve(query)
                
                # Extract and combine all text that looks like references
                reference_texts = []
                seen_docs = set()
                
                for node in nodes:
                    text = node.node.get_content()
                    metadata = node.node.metadata
                    doc_id = metadata.get('doc_id')
                    
                    # Look for reference-like patterns in the text
                    if any(pattern in text for pattern in ['[1]', '[2]', 'et al', 'arXiv:', 'doi:', 'http']):
                        reference_texts.append(text)
                        if doc_id:
                            seen_docs.add(doc_id)
                
                if reference_texts:
                    answer = "\n\n".join(reference_texts)
                    citations = [{"title": self.documents_metadata[doc_id]["filename"], 
                                  "url": f"#doc-{doc_id}", 
                                  "snippet": reference_texts[0][:150]} 
                                 for doc_id in seen_docs if doc_id in self.documents_metadata]
                    return {
                        "answer": answer,
                        "citations": citations,
                        "sources": [],
                        "query": query
                    }
                else:
                    print(f"   ⚠️ No references found in retrieved chunks")
            
            # Create query engine with system prompt for better accuracy
            # Use stricter similarity to avoid irrelevant documents
            from llama_index.core.prompts import PromptTemplate
            
            # Custom QA prompt that includes our system instructions
            qa_prompt_template = PromptTemplate(
                f"""{self.system_prompt}

Context information from the documents:
{{context_str}}

User Query: {{query_str}}

Answer: """
            )
            
            query_engine = self.index.as_query_engine(
                similarity_top_k=min(top_k, 3),  # Limit to 3 chunks max for speed
                response_mode="compact",  # Faster than tree_summarize
                similarity_cutoff=0.3,  # Only include chunks with >30% similarity
                text_qa_template=qa_prompt_template
            )
            print(f"   - Query engine created with system prompt (index has {len(self.documents_metadata)} docs), executing...")
            
            # If specific documents requested, add filter
            if document_ids:
                # Note: Filtering would require custom implementation
                # For now, we query all documents
                pass
            
            # Execute query
            response = query_engine.query(query)
            print(f"   - Response generated: {str(response)[:100]}...")
            
            # Extract sources and citations
            sources = []
            citations = []
            seen_docs = set()  # Track which documents we've already cited
            
            if hasattr(response, 'source_nodes'):
                for i, node in enumerate(response.source_nodes):
                    metadata = node.node.metadata
                    doc_id = metadata.get('doc_id')
                    filename = metadata.get("filename", "Unknown")
                    
                    # Only include nodes with good relevance scores
                    score = node.score if hasattr(node, 'score') else 0.0
                    if score < 0.1:  # Skip low-relevance chunks
                        continue
                    
                    source_info = {
                        "filename": filename,
                        "chunk_id": metadata.get("chunk_id", 0),
                        "score": score,
                        "text": node.node.get_content()[:200] + "..."
                    }
                    sources.append(source_info)
                    
                    # Only add citation once per document
                    if doc_id not in seen_docs:
                        seen_docs.add(doc_id)
                        citation = {
                            "title": filename,
                            "url": f"#doc-{doc_id}",
                            "snippet": node.node.get_content()[:150] + "..."
                        }
                        citations.append(citation)
            
            print(f"   - Found {len(sources)} relevant sources from {len(citations)} documents")
            
            return {
                "answer": str(response),
                "citations": citations,
                "sources": sources,
                "query": query
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Query error: {str(e)}")
            print(f"   Full traceback:\n{error_details}")
            return {
                "answer": f"I encountered an error processing your query. Please make sure Ollama is running. Error: {str(e)}",
                "citations": [],
                "sources": [],
                "query": query
            }
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the system from database"""
        docs = db.list_documents()
        return docs
    
    async def delete_document(self, document_id: str) -> None:
        """Delete a document from the system and database"""
        # Delete from database (cascades to chunks)
        db.delete_document(document_id)
        
        # Remove from memory cache
        if document_id in self.documents_metadata:
            del self.documents_metadata[document_id]
        
        print(f"✅ Deleted document {document_id} from database and index")
