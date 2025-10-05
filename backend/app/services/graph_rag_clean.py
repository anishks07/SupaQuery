"""
GraphRAG Service with Memgraph
Implements Graph-based Retrieval Augmented Generation using:
- Memgraph for knowledge graph storage
- Entity extraction with spaCy
- Ollama for local LLM inference
- Graph-based relationships             # Query similar chunks from graph
            print(f"   � Retrieving relevant chunks from graph...")
            chunks = self.graph.query_similar_chunks(query, doc_ids=document_ids, limit=top_k)
            
            if not chunks:
                stats = self.graph.get_stats()
                return {
                    "answer": f"I couldn't find any relevant information in your uploaded documents for that query.\n\nYour knowledge graph contains:\n- {stats['documents']} document(s)\n- {stats['chunks']} text chunks\n- {stats['entities']} entities\n\nTry:\n- Being more specific in your question\n- Asking about topics covered in your documents\n- Checking what documents are uploaded\n- Using keywords from your documents",
                    "citations": [],
                    "sources": [],
                    "entities": relevant_entities,
                    "query": query
                }ment chunks and entities
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# LlamaIndex
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

# Memgraph and Entity Extraction
from app.services.memgraph_service import get_memgraph_service
from app.services.entity_extractor import get_entity_extractor


class GraphRAGService:
    def __init__(self):
        """Initialize GraphRAG service with Memgraph and Ollama"""
        
        print("🔧 Initializing GraphRAG with Memgraph + Ollama...")
        
        # Initialize Memgraph service
        self.graph = get_memgraph_service()
        
        # Initialize entity extractor
        self.entity_extractor = get_entity_extractor()
        
        # Use Ollama for LLM (make sure Ollama is running)
        Settings.llm = Ollama(
            model="llama3.2:latest",
            request_timeout=60.0,
            temperature=0.3,  # Lower temperature for more focused responses
            base_url="http://localhost:11434",
            additional_kwargs={
                "num_ctx": 2048,
                "num_predict": 512,
            }
        )
        
        # Define system prompt for better accuracy
        self.system_prompt = """You are SupaQuery, an AI assistant specialized in analyzing and answering questions about uploaded documents using a knowledge graph.

Core Principles:
1. **Accuracy First**: Base all answers strictly on the provided document context and extracted entities. Never make assumptions.
2. **Source Attribution**: Always specify which document(s) your answer comes from.
3. **Entity-Aware**: Leverage extracted entities (people, organizations, locations, etc.) to provide richer context.
4. **Clarity**: If information is not in the documents, explicitly state this.
5. **Precision**: Quote or reference specific sections when appropriate.

Capabilities:
- Analyze documents using a knowledge graph of entities and relationships
- Extract and track entities (people, organizations, locations, concepts)
- Answer questions based on document content and entity relationships
- Compare information across multiple documents
- List references, citations, and structured data

Query Handling:
- For **reference/citation queries**: Return the exact text from documents
- For **entity queries** (e.g., "who is mentioned"): Use extracted entities
- For **relationship queries**: Leverage graph relationships between entities
- For **general questions**: Provide clear answers with proper citations

Current date: October 3, 2025

Remember: Be helpful, accurate, and transparent. Use the knowledge graph to provide richer, entity-aware answers."""
        
        print("✅ GraphRAG Service initialized with Memgraph")
        print(f"   - Knowledge Graph: Memgraph")
        print(f"   - Entity Extraction: spaCy")
        print(f"   - LLM: Ollama (llama3.2)")
        print(f"   - Backend: http://localhost:11434")
        print(f"   - Graph UI: http://localhost:3001")
        
        # Print current graph stats
        stats = self.graph.get_stats()
        print(f"   � Graph Stats: {stats['documents']} docs, {stats['chunks']} chunks, {stats['entities']} entities")
    
    async def add_document(self, file_info: Dict[str, Any]) -> None:
        """
        Add a processed document to Memgraph knowledge graph with entity extraction
        """
        try:
            doc_id = file_info["id"]
            chunks = file_info.get("chunk_data", [])
            
            if not chunks:
                print(f"⚠️  No chunks found for document {doc_id}")
                return
            
            # Prepare chunks for Memgraph
            chunk_list = []
            for i, chunk_data in enumerate(chunks):
                chunk_text = chunk_data if isinstance(chunk_data, str) else chunk_data.get("text", "")
                chunk_list.append(chunk_text)
            
            # Add document to Memgraph graph
            self.graph.add_document({
                "id": doc_id,
                "filename": file_info["filename"],
                "type": file_info.get("type", "unknown"),
                "user_id": file_info.get("user_id"),
                "chunks": chunk_list
            })
            
            # Extract and add entities from chunks
            print(f"   🔍 Extracting entities from {len(chunk_list)} chunks...")
            entity_count = 0
            
            for i, chunk_text in enumerate(chunk_list):
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # Extract entities from this chunk
                entities = self.entity_extractor.extract_entities(chunk_text)
                
                for entity in entities:
                    # Add entity to graph
                    self.graph.add_entity(
                        chunk_id=chunk_id,
                        entity_text=entity["text"],
                        entity_type=entity["type"],
                        context=chunk_text[max(0, entity["start"]-50):min(len(chunk_text), entity["end"]+50)]
                    )
                    entity_count += 1
            
            print(f"✅ Added document '{file_info['filename']}' to graph")
            print(f"   - {len(chunks)} chunks processed")
            print(f"   - {entity_count} entities extracted")
            
        except Exception as e:
            print(f"❌ Error adding document to GraphRAG: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    async def query(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query the Memgraph knowledge graph using entity-aware retrieval
        Returns answer with citations and sources from the graph
        """
        try:
            print(f"🔍 Processing query with Memgraph: {query[:50]}...")
            
            # Detect greetings and simple messages that don't need RAG
            query_lower = query.lower().strip()
            greeting_patterns = [
                'hi', 'hello', 'hey', 'good morning', 'good afternoon', 
                'good evening', 'greetings', 'howdy', 'sup', 'yo',
                'thanks', 'thank you', 'ok', 'okay', 'bye', 'goodbye'
            ]
            
            # Check if query is just a greeting (exact match or very short)
            is_greeting = (
                query_lower in greeting_patterns or 
                len(query.split()) <= 2 and any(pattern in query_lower for pattern in greeting_patterns)
            )
            
            if is_greeting:
                print(f"   💬 Detected greeting/simple message, responding conversationally")
                stats = self.graph.get_stats()
                
                if stats['documents'] > 0:
                    doc_text = f"{stats['documents']} document{'s' if stats['documents'] > 1 else ''}"
                    greeting_response = f"""Hello! 👋 I'm SupaQuery, your AI assistant for document analysis.

I can see you have {doc_text} uploaded with {stats['entities']} entities extracted. I'm ready to help you analyze them!

**What I can do:**
- Answer questions about your documents
- Find specific information and entities
- Compare content across documents
- Provide summaries and insights

**Try asking:**
- "What is this document about?"
- "Who are the key people mentioned?"
- "Summarize the main findings"
- "What are the key dates and events?"

How can I help you today?"""
                else:
                    greeting_response = """Hello! 👋 I'm SupaQuery, your AI assistant for document analysis.

I don't see any documents uploaded yet. Upload some documents using the upload button above, and I'll help you:
- Extract and analyze content
- Find entities (people, organizations, locations, etc.)
- Answer questions about your documents
- Build a knowledge graph of relationships

Ready to get started? Upload a document to begin! 📄"""
                
                return {
                    "answer": greeting_response,
                    "citations": [],
                    "sources": [],
                    "entities": [],
                    "query": query
                }
            
            # Check if graph has documents
            stats = self.graph.get_stats()
            if stats['documents'] == 0:
                print(f"   ⚠️ No documents in graph, responding without context")
                return {
                    "answer": "I don't have any documents uploaded yet. Please upload documents first so I can analyze them and answer your questions. You can upload PDFs, Word documents, images, or audio files using the upload button above.",
                    "citations": [],
                    "sources": [],
                    "entities": [],
                    "query": query
                }
            
            # Query entities related to the query
            print(f"   🏷️  Searching for relevant entities...")
            relevant_entities = self.graph.query_entities(query, limit=5)
            
            # Query similar chunks from graph
            print(f"   � Retrieving relevant chunks from graph...")
            chunks = self.graph.query_similar_chunks(query, doc_ids=document_ids, limit=top_k)
            
            if not chunks:
                return {
                    "answer": "I couldn't find any relevant information in the uploaded documents.",
                    "citations": [],
                    "sources": [],
                    "entities": relevant_entities,
                    "query": query
                }
            
            # Build context from chunks
            context_parts = []
            sources = []
            citations = []
            seen_docs = set()
            
            for chunk in chunks:
                context_parts.append(f"[From {chunk['source']}]: {chunk['text']}")
                
                sources.append({
                    "filename": chunk['source'],
                    "chunk_id": chunk['chunk_id'],
                    "text": chunk['text'][:200] + "..."
                })
                
                # Add citation (one per document)
                if chunk['doc_id'] not in seen_docs:
                    seen_docs.add(chunk['doc_id'])
                    citations.append({
                        "title": chunk['source'],
                        "url": f"#doc-{chunk['doc_id']}",
                        "snippet": chunk['text'][:150] + "..."
                    })
            
            context = "\n\n".join(context_parts)
            
            # Add entity context if we found relevant entities
            if relevant_entities:
                entity_context = "Relevant entities mentioned: " + ", ".join([
                    f"{e['name']} ({e['type']})" for e in relevant_entities[:5]
                ])
                context = entity_context + "\n\n" + context
            
            print(f"   - Retrieved {len(chunks)} chunks, {len(relevant_entities)} entities")
            
            # Generate answer with LLM
            print(f"   🤖 Generating answer with Ollama...")
            from llama_index.core.llms import ChatMessage
            
            messages = [
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=f"""Context from knowledge graph:
{context}

User Question: {query}

Please provide a clear, accurate answer based on the context above.""")
            ]
            
            response_obj = Settings.llm.chat(messages)
            answer = str(response_obj.message.content)
            
            print(f"   ✅ Answer generated: {answer[:100]}...")
            
            return {
                "answer": answer,
                "citations": citations,
                "sources": sources,
                "entities": relevant_entities,
                "query": query
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Query error: {str(e)}")
            print(f"   Full traceback:\n{error_details}")
            return {
                "answer": f"I encountered an error processing your query. Error: {str(e)}",
                "citations": [],
                "sources": [],
                "entities": [],
                "query": query
            }
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the knowledge graph"""
        stats = self.graph.get_stats()
        return [{
            "total_documents": stats['documents'],
            "total_chunks": stats['chunks'],
            "total_entities": stats['entities']
        }]
    
    async def delete_document(self, document_id: str) -> None:
        """Delete a document from the knowledge graph"""
        success = self.graph.delete_document(document_id)
        
        if success:
            print(f"✅ Deleted document {document_id} from knowledge graph")
        else:
            print(f"⚠️  Failed to delete document {document_id}")
