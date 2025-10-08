"""
GraphRAG Service with Memgraph and AI Router
Implements Graph-based Retrieval Augmented Generation with intelligent query routing
"""

import os
import re
import asyncio
import requests
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from app.services.memgraph_service import get_memgraph_service
from app.services.entity_extractor import get_entity_extractor
from app.services.faiss_reranker_service import get_faiss_reranker_service

class GraphRAGService:
    def __init__(self):
        print("🔧 Initializing Hybrid GraphRAG (FAISS + Reranker + Memgraph)...")
        self.graph = get_memgraph_service()
        self.faiss = get_faiss_reranker_service()
        self.entity_extractor = get_entity_extractor()
        # Use Ollama directly for better control
        self.ollama_url = "http://localhost:11434"
        Settings.llm = Ollama(
            model="llama3.2", 
            request_timeout=90.0,
            temperature=0.1,
            base_url=self.ollama_url
        )
        print("✅ Hybrid GraphRAG initialized")
        print(f"   - LLM: llama3.2 (direct mode)")
        print(f"   - Vector Search: FAISS ({self.faiss.index.ntotal} vectors)")
        print(f"   - Reranker: Cross-Encoder")
        print(f"   - Graph: Memgraph")
    
    def _call_ollama_direct(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama directly via HTTP for faster, more reliable responses"""
        import requests
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": max_tokens,  # Limit response length
                    }
                },
                timeout=60  # 60 second hard timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Ollama returned status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Direct Ollama call failed: {e}")
            raise
    
    async def add_document(self, file_info: Dict[str, Any]) -> None:
        """
        Add document and extract entities into knowledge graph
        
        Args:
            file_info: Dictionary with document metadata and chunks
        """
        try:
            doc_id = file_info.get("id") or file_info.get("document_db_id")
            if not doc_id:
                raise ValueError("Document ID is required")
            
            print(f"📊 Adding document to hybrid index: {file_info.get('filename', 'Unknown')}")
            
            # Get chunks - they might be in 'chunks', 'chunk_data', or 'chunks_data'
            chunks_data = file_info.get("chunks_data") or file_info.get("chunk_data", [])
            
            # Prepare document info for Memgraph
            doc_info_for_graph = {
                "id": str(doc_id),
                "filename": file_info.get("filename", "Unknown"),
                "type": file_info.get("type", "unknown"),
                "user_id": file_info.get("user_id"),
                "chunks": chunks_data  # This should be the list of chunk strings/dicts
            }
            
            # Add document to Memgraph
            self.graph.add_document(doc_info_for_graph)
            
            # Prepare chunks for FAISS indexing
            faiss_chunks = []
            
            # Extract and add entities from chunks
            if chunks_data:
                for i, chunk_data in enumerate(chunks_data):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    chunk_text = chunk_data if isinstance(chunk_data, str) else chunk_data.get("text", "")
                    
                    # Prepare chunk for FAISS
                    faiss_chunk = {
                        'text': chunk_text,
                        'doc_id': str(doc_id),
                        'chunk_id': chunk_id,
                        'source': file_info.get("filename", "Unknown"),
                        'citation': chunk_data.get("citation", {}) if isinstance(chunk_data, dict) else {}
                    }
                    faiss_chunks.append(faiss_chunk)
                    
                    # Extract entities from chunk (synchronous method)
                    entities = self.entity_extractor.extract_entities(chunk_text)
                    
                    # Add entities to graph
                    for entity in entities:
                        self.graph.add_entity(
                            chunk_id=chunk_id,
                            entity_text=entity['text'],
                            entity_type=entity['type'],  # Changed from 'label' to 'type'
                            context=chunk_text[:200]  # First 200 chars as context
                        )
            
            # Add chunks to FAISS index
            if faiss_chunks:
                self.faiss.add_chunks(faiss_chunks)
            
            print(f"✅ Document indexed in hybrid system (Memgraph + FAISS)")
            
        except Exception as e:
            print(f"❌ Error adding document to graph: {e}")
            raise
    
    async def delete_document(self, doc_id: str, file_path: Optional[str] = None) -> bool:
        """
        Delete document from knowledge graph and optionally delete the physical file
        
        Args:
            doc_id: Document ID to delete
            file_path: Optional path to the physical file to delete
            
        Returns:
            True if successful
        """
        try:
            print(f"🗑️  Deleting document from hybrid system: {doc_id}")
            
            # Delete from Memgraph
            success = self.graph.delete_document(doc_id)
            if success:
                print(f"✅ Document {doc_id} deleted from Memgraph")
            
            # Delete from FAISS
            faiss_success = self.faiss.delete_document(doc_id)
            if faiss_success:
                print(f"✅ Document {doc_id} deleted from FAISS")
            
            # Delete physical file if path provided
            if file_path:
                try:
                    from pathlib import Path
                    file = Path(file_path)
                    if file.exists():
                        file.unlink()
                        print(f"✅ Deleted physical file: {file_path}")
                    else:
                        print(f"⚠️  File not found (may have been already deleted): {file_path}")
                except Exception as e:
                    print(f"❌ Error deleting file {file_path}: {e}")
            
            return success and faiss_success
        except Exception as e:
            print(f"❌ Error deleting document from graph: {e}")
            return False
    
    def _classify_query(self, query: str) -> str:
        """Enhanced query classification with 30+ patterns"""
        query_lower = query.lower().strip()
        
        # Document listing queries (check FIRST - most critical for performance)
        doc_list_patterns = [
            'what documents', 'what files', 'list documents', 'list files',
            'show documents', 'show files', 'which documents', 'which files',
            'names of documents', 'names of files', 'document names', 'file names',
            'what do i have', 'what have i uploaded', 'my documents', 'my files'
        ]
        for pattern in doc_list_patterns:
            if pattern in query_lower:
                return 'document_list'
        
        # Entity queries (check FIRST - most specific)
        entity_patterns = [
            'who is', 'who are', 'who was', 'who were',
            'key people', 'people mentioned', 'main people',
            'authors', 'researchers', 'scientists', 'experts',
            'organizations', 'companies', 'institutions',
            'key players', 'stakeholders', 'contributors',
            'list all people', 'list people', 'names mentioned',
            'participants', 'individuals involved'
        ]
        for pattern in entity_patterns:
            if pattern in query_lower:
                return 'entity'
        
        # Date/event queries
        date_patterns = [
            'key dates', 'key events', 'timeline', 'chronology',
            'when did', 'when was', 'when were', 'what year',
            'what date', 'time period', 'schedule',
            'milestones', 'important dates', 'significant events',
            'historical events', 'event sequence'
        ]
        for pattern in date_patterns:
            if pattern in query_lower:
                return 'date'
        
        # Summary queries
        if any(p in query_lower for p in ['summary', 'summarize', 'overview', 'main points', 'key findings']):
            return 'summary'
        
        # General query
        return 'general'
    
    def _determine_query_strategy(self, query: str, stats: Dict) -> str:
        """AI Router: Decides whether to retrieve, reply directly, or clarify"""
        query_lower = query.lower().strip()
        
        # Direct reply patterns (no retrieval needed)
        # Only match standalone greetings (not "hi what was..." or "hello, can you...")
        greetings = ['hi', 'hello', 'hey', 'greetings']
        first_word = query_lower.split()[0] if query_lower.split() else query_lower
        # Only treat as greeting if it's a single word OR followed by punctuation/comma
        if query_lower in greetings or (first_word in greetings and len(query_lower.split()) == 1):
            return 'direct_reply'
        # Also match "hi!" or "hello!" or "hey there"
        if query_lower in ['hi!', 'hello!', 'hey!', 'hey there', 'hi there', 'hello there']:
            return 'direct_reply'
        
        # Meta questions (about the system itself)
        meta_patterns = ['what can you', 'what do you', 'who are you', 'what are you', 
                        'how do you work', 'what is your purpose', 'help']
        if any(p in query_lower for p in meta_patterns):
            return 'direct_reply'
        
        # Acknowledgments
        if query_lower in ['thanks', 'thank you', 'ok', 'okay', 'got it', 'understood']:
            return 'direct_reply'
        
        # Vague queries (need clarification)
        if len(query.split()) < 3 and stats['documents'] > 1:
            # Short query with multiple documents
            return 'clarify'
        
        # Normal queries - retrieve from knowledge graph
        return 'retrieve'
    
    def _handle_direct_reply(self, query: str, stats: Dict) -> Dict[str, Any]:
        """Handle queries that don't need retrieval"""
        query_lower = query.lower().strip()
        
        # Greetings
        if any(g in query_lower for g in ['hi', 'hello', 'hey', 'greetings']):
            answer = f"Hello! I'm your document analysis assistant. You have {stats['documents']} document(s) uploaded with {stats['entities']} entities extracted. How can I help you today?"
        
        # Meta questions
        elif 'what can you' in query_lower or 'what do you' in query_lower:
            answer = f"""I can help you analyze your {stats['documents']} uploaded document(s). I can:
• Answer questions about document content
• List key people, organizations, and entities
• Identify key dates and events
• Provide summaries and insights
• Find relationships between concepts

Just ask me anything about your documents!"""
        
        elif 'who are you' in query_lower or 'what are you' in query_lower:
            answer = "I'm an AI assistant that helps you understand and analyze your documents using advanced knowledge graph technology."
        
        # Acknowledgments
        elif query_lower in ['thanks', 'thank you', 'ok', 'okay', 'got it']:
            answer = "You're welcome! Feel free to ask me anything else."
        
        else:
            answer = "I'm here to help! Please ask me a question about your documents."
        
        return {
            "answer": answer,
            "citations": [],
            "sources": [],
            "entities": [],
            "query": query,
            "strategy": "direct_reply"
        }
    
    def _handle_clarification(self, query: str, stats: Dict) -> Dict[str, Any]:
        """Ask for clarification on vague queries"""
        answer = f"""Your question is a bit vague. To help you better, could you be more specific?

You have {stats['documents']} document(s) available. You can ask me about:
• Specific people or organizations
• Key dates and events
• Particular topics or concepts
• Document summaries

Example questions:
• "Who are the key people mentioned?"
• "What are the main findings?"
• "When did [specific event] happen?"
"""
        
        return {
            "answer": answer,
            "citations": [],
            "sources": [],
            "entities": [],
            "query": query,
            "strategy": "clarify"
        }
    
    def _handle_document_list(self, query: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Handle document listing queries without LLM (fast response)"""
        try:
            # Get list of documents from graph
            docs = self.graph.list_documents(limit=100)
            
            if not docs:
                answer = "You don't have any documents uploaded yet."
            else:
                # Format document list
                answer = f"You have {len(docs)} document(s) uploaded:\n\n"
                for i, doc in enumerate(docs, 1):
                    filename = doc.get('filename', 'Unknown')
                    chunk_count = doc.get('chunk_count', 0)
                    created = doc.get('created_at', 'Unknown date')
                    answer += f"{i}. **{filename}**\n"
                    answer += f"   - Chunks: {chunk_count}\n"
                    answer += f"   - Uploaded: {created}\n\n"
            
            return {
                "answer": answer,
                "citations": [],
                "sources": [{"filename": doc.get('filename')} for doc in docs],
                "entities": [],
                "query": query,
                "strategy": "document_list"
            }
        except Exception as e:
            print(f"Error listing documents: {e}")
            return {
                "answer": f"I encountered an error while listing documents: {str(e)}",
                "citations": [],
                "sources": [],
                "entities": [],
                "query": query,
                "strategy": "document_list"
            }
    
    async def query(self, query: str, document_ids: Optional[List[str]] = None, top_k: int = 5) -> Dict[str, Any]:
        try:
            print(f"🔍 Processing query: {query[:50]}...")
            stats = self.graph.get_stats()
            
            # If graph stats show 0 documents but we have document_ids, trust the document_ids
            # This handles cases where Memgraph has connection issues but documents exist
            if stats['documents'] == 0 and not document_ids:
                # Try to get document list from graph as final check
                try:
                    docs = self.graph.list_documents(limit=1)
                    if docs and len(docs) > 0:
                        # Documents exist but stats failed - update stats
                        stats['documents'] = len(docs)
                        print(f"⚠️ Stats showed 0 docs, but found {len(docs)} via list_documents")
                    else:
                        return {
                            "answer": "No documents uploaded yet. Please upload a document to get started.",
                            "citations": [],
                            "sources": [],
                            "entities": [],
                            "query": query
                        }
                except Exception as list_err:
                    print(f"⚠️ Could not verify documents: {list_err}")
                    return {
                        "answer": "No documents uploaded yet. Please upload a document to get started.",
                        "citations": [],
                        "sources": [],
                        "entities": [],
                        "query": query
                    }
            
            # Check query type FIRST (before strategy routing)
            query_type = self._classify_query(query)
            print(f"� Query type: {query_type}")
            
            # Handle document listing queries (fast, no LLM needed)
            if query_type == 'document_list':
                return self._handle_document_list(query, document_ids)
            
            # AI Router: Determine strategy
            strategy = self._determine_query_strategy(query, stats)
            print(f"� Query strategy: {strategy}")
            
            if strategy == 'direct_reply':
                return self._handle_direct_reply(query, stats)
            
            if strategy == 'clarify':
                return self._handle_clarification(query, stats)
            
            # Strategy is 'retrieve' - proceed with COMBINED HYBRID RETRIEVAL
            # Architecture: FAISS (semantic) + Memgraph (relational) → Merge → Deduplicate → Rerank → LLM
            
            print(f"🔍 Combined Hybrid Retrieval Pipeline:")
            
            # STAGE 1: FAISS semantic retrieval (top 20 candidates)
            print(f"   � Stage 1: FAISS semantic search...")
            faiss_chunks = []
            try:
                faiss_chunks = self.faiss.search(query, top_k=20, doc_ids=document_ids)
                print(f"   ✓ FAISS retrieved {len(faiss_chunks)} chunks")
            except Exception as e:
                print(f"   ⚠️ FAISS error: {e}")
            
            # STAGE 2: Memgraph relational retrieval (related nodes/chunks)
            print(f"   🕸️ Stage 2: Memgraph graph traversal...")
            memgraph_chunks = []
            try:
                # Get chunks from Memgraph with traversal limits
                memgraph_chunks = self._retrieve_with_graph_traversal(
                    query=query,
                    doc_ids=document_ids,
                    max_depth=2,  # Limit graph traversal depth
                    max_nodes=15  # Limit number of nodes to fetch
                )
                print(f"   ✓ Memgraph retrieved {len(memgraph_chunks)} chunks")
            except Exception as e:
                print(f"   ⚠️ Memgraph error: {e}")
            
            # STAGE 3: Merge and deduplicate
            print(f"   🔀 Stage 3: Merging and deduplicating...")
            merged_chunks = self._merge_and_deduplicate(faiss_chunks, memgraph_chunks)
            print(f"   ✓ Merged to {len(merged_chunks)} unique chunks")
            
            if not merged_chunks:
                return {
                    "answer": "I couldn't find relevant information in the documents. Try rephrasing your question.",
                    "citations": [],
                    "sources": [],
                    "entities": [],
                    "query": query
                }
            
            # STAGE 4: Cross-encoder reranking on merged results
            print(f"   🎯 Stage 4: Cross-encoder reranking...")
            chunks = self.faiss.rerank(query, merged_chunks, top_k=top_k)
            print(f"   ✓ Reranked to top {len(chunks)} chunks")
            
            # STAGE 5: Entity enrichment from selected documents
            print(f"   🏷️ Stage 5: Entity enrichment...")
            
            # Extract entities from documents
            all_entities = []
            doc_ids_in_chunks = list(set([chunk.get('doc_id') or chunk.get('source', '').split('/')[0] for chunk in chunks if chunk.get('doc_id') or chunk.get('source')]))
            
            for doc_id in doc_ids_in_chunks:
                try:
                    entities = self.graph.get_document_entities(doc_id)
                    all_entities.extend(entities)
                except Exception as e:
                    print(f"Warning: Could not get entities for doc {doc_id}: {e}")
            
            # Remove duplicates
            unique_entities = {}
            for entity in all_entities:
                key = (entity['name'], entity['type'])
                if key not in unique_entities:
                    unique_entities[key] = entity
            all_entities = list(unique_entities.values())
            
            # Format context based on query type
            if query_type == 'entity':
                # For entity queries, prioritize entity list
                entity_context = self._format_entity_context(all_entities)
                chunk_context = "\n\n".join([f"[{c['source']}]: {c['text']}" for c in chunks[:3]])
                context = f"{entity_context}\n\n=== DOCUMENT EXCERPTS ===\n{chunk_context}"
            else:
                # For other queries, prioritize document content
                chunk_context = "\n\n".join([f"[{c['source']}]: {c['text']}" for c in chunks])
                entity_context = self._format_entity_context(all_entities) if all_entities else ""
                context = f"{chunk_context}\n\n{entity_context}" if entity_context else chunk_context
            
            # Limit context to prevent LLM timeouts (max ~6000 chars / ~1500 tokens)
            MAX_CONTEXT_LENGTH = 6000
            if len(context) > MAX_CONTEXT_LENGTH:
                print(f"   ⚠️ Context too large ({len(context)} chars), truncating to {MAX_CONTEXT_LENGTH}")
                context = context[:MAX_CONTEXT_LENGTH] + "\n\n[... context truncated for performance ...]"
            
            # Generate response with type-specific instructions
            system_prompt = self._get_system_prompt(query_type)
            user_prompt = self._get_user_prompt(query, context, query_type)
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]
            
            # Use direct Ollama call for faster, more reliable responses
            print(f"   🤖 Generating response using direct mode...")
            
            # Create a concise, focused prompt
            if query_type == 'summary':
                simple_prompt = f"""Based on these document excerpts, provide a concise summary:

{context[:3000]}

Summary:"""
            else:
                simple_prompt = f"""Context:
{context[:3000]}

Question: {query}

Answer:"""
            
            try:
                answer = self._call_ollama_direct(simple_prompt, max_tokens=500)
                print(f"   ✓ Response generated successfully ({len(answer)} chars)")
            except Exception as llm_error:
                print(f"   ❌ LLM generation failed: {llm_error}")
                # Fallback: provide a basic response from the context
                answer = f"Based on the documents, here are the key points:\n\n{context[:500]}..."
            
            return {
                "answer": answer,
                "citations": [{"text": c['text'], "source": c['source']} for c in chunks],
                "sources": [{"filename": src} for src in list(set([c['source'] for c in chunks]))],
                "entities": all_entities,
                "query": query,
                "query_type": query_type,
                "strategy": "retrieve"
            }
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ Error in query: {str(e)}")
            
            # Provide user-friendly error messages
            if 'timed out' in error_msg or 'timeout' in error_msg:
                return {
                    "answer": "⏱️ The query took too long to process. This can happen when the knowledge graph is very large. Try:\n• Being more specific in your question\n• Asking about a particular document\n• Simplifying your query\n\nI'm still learning from your documents in the background!",
                    "citations": [],
                    "sources": [],
                    "entities": [],
                    "query": query
                }
            elif 'connection' in error_msg:
                return {
                    "answer": "🔌 I'm having trouble connecting to the knowledge graph. The system is trying to reconnect. Please try your question again in a moment.",
                    "citations": [],
                    "sources": [],
                    "entities": [],
                    "query": query
                }
            else:
                return {
                    "answer": f"❌ I encountered an error while processing your question. Please try rephrasing or ask something simpler.\n\nError details: {str(e)}",
                    "citations": [],
                    "sources": [],
                    "entities": [],
                    "query": query
                }
    
    def _format_entity_context(self, entities: List[Dict]) -> str:
        """Format entities into structured context"""
        if not entities:
            return ""
        
        # Group by type
        by_type = {}
        for entity in entities:
            etype = entity['type']
            if etype not in by_type:
                by_type[etype] = []
            by_type[etype].append(entity['name'])
        
        lines = ["=== EXTRACTED ENTITIES ==="]
        for etype, names in sorted(by_type.items()):
            unique_names = sorted(set(names))
            lines.append(f"\n{etype}:")
            for name in unique_names:
                lines.append(f"  • {name}")
        
        return "\n".join(lines)
    
    def _get_system_prompt(self, query_type: str) -> str:
        """Get type-specific system prompt"""
        base = "You are a helpful AI assistant that analyzes documents and provides accurate answers based on the given context."
        
        if query_type == 'entity':
            return f"""{base}

IMPORTANT: When asked about people, organizations, or entities:
1. List ALL entities found in the EXTRACTED ENTITIES section
2. Format each entity clearly: **Name** (Type)
3. Do NOT explain or describe unless specifically asked
4. Focus ONLY on listing the entities mentioned"""
        
        elif query_type == 'date':
            return f"""{base}

IMPORTANT: When asked about dates or events:
1. Extract ALL specific dates, years, or time periods from the context
2. Format clearly with date/period followed by event
3. Present in chronological order if possible
4. Include specific quotes if available"""
        
        elif query_type == 'summary':
            return f"""{base}

IMPORTANT: When providing summaries:
1. Focus on main findings and key points
2. Be concise but comprehensive
3. Organize information logically
4. Highlight the most important insights"""
        
        else:
            return base
    
    def _get_user_prompt(self, query: str, context: str, query_type: str) -> str:
        """Get type-specific user prompt"""
        if query_type == 'entity':
            return f"""Context:
{context}

Question: {query}

Instructions: List ALL people and organizations mentioned in the EXTRACTED ENTITIES section above. Use this format:
- **Entity Name** (Entity Type)

Focus only on listing entities, do not provide explanations unless specifically asked."""
        
        elif query_type == 'date':
            return f"""Context:
{context}

Question: {query}

Instructions: Extract and list ALL dates, time periods, or events from the context. Format each as:
- [Date/Period]: Description of event

Be specific and include all temporal information found."""
        
        else:
            return f"""Context:
{context}

Question: {query}

Please provide a clear and accurate answer based on the context above."""
    
    def _retrieve_with_graph_traversal(
        self, 
        query: str, 
        doc_ids: Optional[List[str]] = None,
        max_depth: int = 2,
        max_nodes: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks from Memgraph with graph traversal limits
        
        Args:
            query: Query text
            doc_ids: Optional list of document IDs to filter
            max_depth: Maximum graph traversal depth (default: 2)
            max_nodes: Maximum number of nodes to retrieve (default: 15)
        
        Returns:
            List of chunk dictionaries
        """
        try:
            # Get initial chunks from Memgraph
            chunks = self.graph.query_similar_chunks(
                query_text=query,
                doc_ids=doc_ids,
                limit=max_nodes
            )
            
            # If we got chunks and depth > 1, expand with related chunks
            if chunks and max_depth > 1:
                expanded_chunks = []
                seen_chunk_ids = set()
                
                # Add initial chunks
                for chunk in chunks[:max_nodes]:
                    chunk_id = chunk.get('chunk_id') or chunk.get('id')
                    if chunk_id and chunk_id not in seen_chunk_ids:
                        expanded_chunks.append(chunk)
                        seen_chunk_ids.add(chunk_id)
                
                # For each chunk, get related chunks (depth 2)
                if max_depth >= 2 and len(expanded_chunks) < max_nodes:
                    for chunk in chunks[:5]:  # Only expand from top 5 to limit growth
                        doc_id = chunk.get('doc_id')
                        if doc_id:
                            try:
                                # Get related chunks from same document
                                related = self.graph.query_similar_chunks(
                                    query_text=query,
                                    doc_ids=[doc_id],
                                    limit=3  # Only 3 related per chunk
                                )
                                
                                for rel_chunk in related:
                                    if len(expanded_chunks) >= max_nodes:
                                        break
                                    chunk_id = rel_chunk.get('chunk_id') or rel_chunk.get('id')
                                    if chunk_id and chunk_id not in seen_chunk_ids:
                                        expanded_chunks.append(rel_chunk)
                                        seen_chunk_ids.add(chunk_id)
                            except Exception as e:
                                print(f"   ⚠️ Could not expand chunk {chunk_id}: {e}")
                                continue
                        
                        if len(expanded_chunks) >= max_nodes:
                            break
                
                return expanded_chunks[:max_nodes]
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ Graph traversal error: {e}")
            return []
    
    def _merge_and_deduplicate(
        self, 
        faiss_chunks: List[Dict[str, Any]], 
        memgraph_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge chunks from FAISS and Memgraph, removing duplicates
        
        Deduplication strategy:
        1. Use chunk_id if available
        2. Use content hash (first 100 chars of text)
        3. Keep FAISS version if duplicate (has better relevance scores)
        
        Args:
            faiss_chunks: Chunks from FAISS search
            memgraph_chunks: Chunks from Memgraph traversal
        
        Returns:
            Deduplicated list of chunks
        """
        merged = []
        seen_ids = set()
        seen_hashes = set()
        
        # Helper function to get chunk identifier
        def get_chunk_key(chunk: Dict) -> tuple:
            chunk_id = chunk.get('chunk_id') or chunk.get('id')
            text = chunk.get('text', '')
            text_hash = hash(text[:100]) if text else None
            return (chunk_id, text_hash)
        
        # Add FAISS chunks first (they have relevance scores)
        faiss_added = 0
        faiss_skipped = 0
        obama_count = 0
        pdf_count = 0
        
        for chunk in faiss_chunks:
            chunk_id, text_hash = get_chunk_key(chunk)
            source = chunk.get('source', '')
            
            # Check for duplicates
            is_duplicate = False
            if chunk_id and chunk_id in seen_ids:
                is_duplicate = True
                faiss_skipped += 1
            elif text_hash and text_hash in seen_hashes:
                is_duplicate = True
                faiss_skipped += 1
            
            if not is_duplicate:
                # Mark as from FAISS
                chunk['source_system'] = 'faiss'
                merged.append(chunk)
                faiss_added += 1
                
                # Count by source type
                if 'obama' in source.lower() or '.mp3' in source.lower():
                    obama_count += 1
                elif '.pdf' in source.lower():
                    pdf_count += 1
                
                if chunk_id:
                    seen_ids.add(chunk_id)
                if text_hash:
                    seen_hashes.add(text_hash)
        
        print(f"      FAISS: {faiss_added} added ({obama_count} Obama, {pdf_count} PDF), {faiss_skipped} skipped as duplicates")
        
        # Add Memgraph chunks (skip duplicates)
        memgraph_added = 0
        memgraph_skipped = 0
        for chunk in memgraph_chunks:
            chunk_id, text_hash = get_chunk_key(chunk)
            
            # Check for duplicates
            is_duplicate = False
            if chunk_id and chunk_id in seen_ids:
                is_duplicate = True
            elif text_hash and text_hash in seen_hashes:
                is_duplicate = True
            
            if not is_duplicate:
                # Mark as from Memgraph
                chunk['source_system'] = 'memgraph'
                merged.append(chunk)
                memgraph_added += 1
                
                if chunk_id:
                    seen_ids.add(chunk_id)
                if text_hash:
                    seen_hashes.add(text_hash)
            else:
                memgraph_skipped += 1
        
        print(f"      Memgraph: {memgraph_added} added, {memgraph_skipped} skipped as duplicates")
        print(f"      Final merged count: {len(merged)} ({faiss_added} from FAISS + {memgraph_added} from Memgraph)")
        
        return merged
