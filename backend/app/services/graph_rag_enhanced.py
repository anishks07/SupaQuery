"""
Enhanced GraphRAG Service with Multi-Query, Routing, and Evaluation
Implements: Query -> Multi-Query Generator -> Routing Agent -> Retrieval -> Evaluation Agent (with feedback loop)
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
from app.services.multi_query_generator import get_multi_query_generator
from app.services.evaluation_agent import get_evaluation_agent


class EnhancedGraphRAGService:
    """
    Enhanced GraphRAG with intelligent query processing pipeline:
    1. Multi-Query Generation - Generate query variations
    2. Routing Agent - Route to appropriate retrieval strategy
    3. Retrieval - Get relevant information
    4. Evaluation Agent - Assess quality and provide feedback
    5. Feedback Loop - Re-route if answer is insufficient
    """
    
    def __init__(self):
        print("🔧 Initializing Enhanced GraphRAG with Multi-Query and Evaluation...")
        self.graph = get_memgraph_service()
        self.entity_extractor = get_entity_extractor()
        self.multi_query_generator = get_multi_query_generator()
        self.evaluation_agent = get_evaluation_agent()
        
        # Use Ollama directly for better control
        self.ollama_url = "http://localhost:11434"
        Settings.llm = Ollama(
            model="llama3.2", 
            request_timeout=90.0,
            temperature=0.1,
            base_url=self.ollama_url
        )
        
        # Configuration
        self.max_retries = 2  # Maximum feedback loop iterations
        self.enable_multi_query = True  # Toggle multi-query generation
        self.enable_evaluation = True  # Toggle evaluation feedback
        
        print("✅ Enhanced GraphRAG initialized")
        print(f"   - Multi-Query Generation: {'Enabled' if self.enable_multi_query else 'Disabled'}")
        print(f"   - Evaluation Feedback: {'Enabled' if self.enable_evaluation else 'Disabled'}")
        print(f"   - Max Retries: {self.max_retries}")
    
    async def query(
        self, 
        query: str, 
        document_ids: Optional[List[str]] = None, 
        top_k: int = 5,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Main query processing pipeline with evaluation feedback loop.
        
        Args:
            query: User's question
            document_ids: Optional list of specific documents to search
            top_k: Number of chunks to retrieve
            conversation_history: Previous messages for context
            
        Returns:
            Dictionary with answer, citations, sources, and metadata
        """
        
        print(f"\n{'='*80}")
        print(f"🔍 NEW QUERY: {query[:80]}...")
        print(f"{'='*80}")
        
        # Get knowledge base stats
        stats = self.graph.get_stats()
        
        # Check if we have documents
        if stats['documents'] == 0 and not document_ids:
            return {
                "answer": "No documents uploaded yet. Please upload a document to get started.",
                "citations": [],
                "sources": [],
                "entities": [],
                "query": query,
                "strategy": "no_documents"
            }
        
        # STEP 1: Classify query type
        query_type = self._classify_query(query)
        print(f"📋 Query Type: {query_type}")
        
        # STEP 2: Determine routing strategy
        strategy = self._determine_query_strategy(query, stats)
        print(f"🎯 Routing Strategy: {strategy}")
        
        # Handle non-retrieval strategies
        if strategy == 'direct_reply':
            return self._handle_direct_reply(query, stats)
        
        if strategy == 'clarify':
            return self._handle_clarification(query, stats)
        
        # STEP 3: Multi-Query Generation (for retrieval strategy)
        if self.enable_multi_query:
            queries = self.multi_query_generator.generate_with_context(
                original_query=query,
                conversation_history=conversation_history,
                num_queries=2  # Generate 2 variations + original = 3 total
            )
        else:
            queries = [query]
        
        # STEP 4: Retrieval with Evaluation Feedback Loop
        retry_count = 0
        best_answer = None
        best_evaluation = None
        
        while retry_count <= self.max_retries:
            print(f"\n🔄 Attempt {retry_count + 1}/{self.max_retries + 1}")
            
            # Retrieve information
            retrieval_result = await self._retrieve_with_multi_query(
                queries=queries,
                document_ids=document_ids,
                top_k=top_k,
                query_type=query_type
            )
            
            # STEP 5: Evaluate answer quality
            if self.enable_evaluation:
                evaluation = self.evaluation_agent.evaluate_answer(
                    query=query,
                    answer=retrieval_result["answer"],
                    retrieved_chunks=retrieval_result.get("retrieved_chunks", []),
                    sources=retrieval_result.get("sources", [])
                )
                
                # Store best answer
                if best_answer is None or evaluation["overall_score"] > best_evaluation["overall_score"]:
                    best_answer = retrieval_result
                    best_evaluation = evaluation
                
                # Check if answer is sufficient
                if evaluation["is_sufficient"]:
                    print(f"✅ Answer meets quality threshold")
                    break
                else:
                    print(f"⚠️  Answer quality insufficient, preparing retry...")
                    
                    # Get retry strategy
                    retry_strategy = self.evaluation_agent.get_retry_strategy(evaluation)
                    print(f"   Retry Strategy: {retry_strategy}")
                    
                    # Apply retry strategy for next iteration
                    if retry_strategy["expand_search"]:
                        top_k = retry_strategy["increase_top_k"]
                        print(f"   📈 Expanding search to top_{top_k}")
                    
                    if retry_strategy["refine_query"]:
                        # Generate more query variations
                        queries = self.multi_query_generator.generate_queries(query, num_queries=3)
                        print(f"   🔄 Refined queries: {len(queries)}")
            else:
                # No evaluation, just return result
                best_answer = retrieval_result
                break
            
            retry_count += 1
        
        # Add evaluation metadata to response
        if self.enable_evaluation and best_evaluation:
            best_answer["evaluation"] = {
                "overall_score": best_evaluation["overall_score"],
                "quality_score": best_evaluation["quality_score"],
                "completeness_score": best_evaluation["completeness_score"],
                "relevance_score": best_evaluation["relevance_score"],
                "attempts": retry_count + 1
            }
        
        return best_answer
    
    async def _retrieve_with_multi_query(
        self,
        queries: List[str],
        document_ids: Optional[List[str]],
        top_k: int,
        query_type: str
    ) -> Dict[str, Any]:
        """
        Retrieve information using multiple query variations and merge results.
        """
        
        print(f"🔎 Retrieving with {len(queries)} queries...")
        
        all_chunks = []
        seen_chunk_ids = set()
        
        # Retrieve chunks for each query variation
        for i, q in enumerate(queries):
            print(f"   Query {i+1}: {q[:60]}...")
            
            chunks = self.graph.query_similar_chunks(q, doc_ids=document_ids, limit=top_k)
            
            # Deduplicate chunks
            for chunk in chunks:
                chunk_id = chunk.get('id', chunk.get('text', '')[:50])
                if chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk_id)
                    all_chunks.append(chunk)
        
        print(f"   Retrieved {len(all_chunks)} unique chunks")
        
        if not all_chunks:
            return {
                "answer": "I couldn't find relevant information in the documents. Try rephrasing your question.",
                "citations": [],
                "sources": [],
                "entities": [],
                "retrieved_chunks": [],
                "query": queries[0],
                "strategy": "retrieve"
            }
        
        # Limit chunks to prevent context overflow
        all_chunks = all_chunks[:top_k * 2]  # Keep top 2*top_k chunks
        
        # Extract entities
        all_entities = self._extract_entities_from_chunks(all_chunks)
        
        # Build context
        context = self._build_context(all_chunks, all_entities, query_type)
        
        # Generate answer
        answer = await self._generate_answer(queries[0], context, query_type)
        
        # Format response with citations
        return {
            "answer": answer,
            "citations": self._format_citations(all_chunks),
            "sources": self._format_sources(all_chunks),
            "entities": all_entities,
            "retrieved_chunks": all_chunks,  # Include for evaluation
            "query": queries[0],
            "query_type": query_type,
            "strategy": "retrieve",
            "num_queries_used": len(queries)
        }
    
    def _extract_entities_from_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Extract entities from retrieved chunks"""
        all_entities = []
        doc_ids_in_chunks = list(set([
            chunk.get('doc_id') or chunk.get('source', '').split('/')[0] 
            for chunk in chunks 
            if chunk.get('doc_id') or chunk.get('source')
        ]))
        
        for doc_id in doc_ids_in_chunks:
            try:
                entities = self.graph.get_document_entities(doc_id)
                all_entities.extend(entities)
            except Exception as e:
                print(f"   Warning: Could not get entities for doc {doc_id}: {e}")
        
        # Deduplicate entities
        unique_entities = {}
        for entity in all_entities:
            key = (entity['name'], entity['type'])
            if key not in unique_entities:
                unique_entities[key] = entity
        
        return list(unique_entities.values())
    
    def _build_context(
        self, 
        chunks: List[Dict], 
        entities: List[Dict], 
        query_type: str
    ) -> str:
        """Build context string from chunks and entities"""
        
        # Format chunks
        chunk_context = "\n\n".join([
            f"[{c.get('source', 'Unknown')}]: {c.get('text', '')}" 
            for c in chunks
        ])
        
        # Format entities
        entity_context = self._format_entity_context(entities) if entities else ""
        
        # Combine based on query type
        if query_type == 'entity' and entity_context:
            context = f"{entity_context}\n\n=== DOCUMENT EXCERPTS ===\n{chunk_context}"
        else:
            context = f"{chunk_context}\n\n{entity_context}" if entity_context else chunk_context
        
        # Limit context length
        MAX_CONTEXT_LENGTH = 6000
        if len(context) > MAX_CONTEXT_LENGTH:
            print(f"   ⚠️ Context truncated from {len(context)} to {MAX_CONTEXT_LENGTH} chars")
            context = context[:MAX_CONTEXT_LENGTH] + "\n\n[... truncated ...]"
        
        return context
    
    async def _generate_answer(self, query: str, context: str, query_type: str) -> str:
        """Generate answer using LLM"""
        
        print(f"   🤖 Generating answer...")
        
        # Create focused prompt
        if query_type == 'summary':
            prompt = f"""Based on these document excerpts, provide a concise summary:

{context[:3000]}

Summary:"""
        else:
            prompt = f"""Context from documents:
{context[:3000]}

Question: {query}

Provide a clear, accurate answer based on the context:"""
        
        try:
            answer = self._call_ollama_direct(prompt, max_tokens=600)
            print(f"   ✓ Generated {len(answer)} chars")
            return answer
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            return f"Based on the documents:\n\n{context[:500]}..."
    
    def _format_citations(self, chunks: List[Dict]) -> List[Dict]:
        """Format chunks into citations"""
        return [
            {
                "text": c.get('text', ''),
                "source": c.get('source', 'Unknown'),
                "doc_id": c.get('doc_id', ''),
                "chunk_id": c.get('id', '')
            }
            for c in chunks
        ]
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format unique sources from chunks"""
        sources = list(set([c.get('source', 'Unknown') for c in chunks]))
        return [{"filename": src} for src in sources]
    
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
        
        # Format
        lines = ["=== EXTRACTED ENTITIES ==="]
        for etype, names in sorted(by_type.items()):
            unique_names = list(set(names))[:10]  # Max 10 per type
            lines.append(f"{etype}: {', '.join(unique_names)}")
        
        return "\n".join(lines)
    
    def _classify_query(self, query: str) -> str:
        """Classify query type"""
        q_lower = query.lower().strip()
        
        # Check patterns
        if any(word in q_lower for word in ['list', 'show', 'what documents', 'which files', 'how many']):
            return 'document_list'
        
        if any(word in q_lower for word in ['summarize', 'summary', 'overview', 'key points']):
            return 'summary'
        
        if any(word in q_lower for word in ['who', 'what is', 'define', 'explain']):
            return 'factual'
        
        if any(word in q_lower for word in ['entities', 'people', 'organizations', 'dates', 'locations']):
            return 'entity'
        
        return 'general'
    
    def _determine_query_strategy(self, query: str, stats: Dict) -> str:
        """Determine routing strategy"""
        q_lower = query.lower().strip()
        
        # Direct reply patterns
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon']
        if any(q_lower.startswith(g) for g in greetings):
            return 'direct_reply'
        
        acknowledgments = ['thanks', 'thank you', 'ok', 'okay', 'bye', 'goodbye']
        if q_lower in acknowledgments:
            return 'direct_reply'
        
        meta_questions = ['what can you do', 'how do you work', 'help', 'what are you']
        if any(m in q_lower for m in meta_questions):
            return 'direct_reply'
        
        # Clarification needed
        vague_terms = ['it', 'that', 'this', 'them', 'more']
        if q_lower in vague_terms or len(q_lower) < 5:
            return 'clarify'
        
        # Default to retrieve
        return 'retrieve'
    
    def _handle_direct_reply(self, query: str, stats: Dict) -> Dict[str, Any]:
        """Handle queries that don't need retrieval"""
        q_lower = query.lower()
        
        if any(g in q_lower for g in ['hi', 'hello', 'hey']):
            answer = f"Hello! 👋 I'm SupaQuery, your AI document assistant.\n\nI can help you analyze and query {stats['documents']} documents in your knowledge base. What would you like to know?"
        elif 'what can you do' in q_lower or 'help' in q_lower:
            answer = f"""I'm SupaQuery, specialized in document analysis. Here's what I can do:

📚 Knowledge Base: {stats['documents']} documents, {stats['chunks']} chunks, {stats['entities']} entities

✨ Capabilities:
1. Answer questions about your documents
2. Summarize content
3. Extract key entities and facts
4. Find specific information
5. Compare and analyze documents

Just ask me anything about your documents!"""
        else:
            answer = "You're welcome! Feel free to ask if you need anything else. 😊"
        
        return {
            "answer": answer,
            "citations": [],
            "sources": [],
            "entities": [],
            "query": query,
            "strategy": "direct_reply"
        }
    
    def _handle_clarification(self, query: str, stats: Dict) -> Dict[str, Any]:
        """Handle vague queries"""
        answer = f"""I need a bit more information to help you effectively.

Your knowledge base contains:
- {stats['documents']} documents
- {stats['chunks']} text chunks
- {stats['entities']} extracted entities

Try asking:
- "Summarize the main findings"
- "What are the key entities mentioned?"
- "Explain [specific topic]"
- "List the documents"

What would you like to know?"""
        
        return {
            "answer": answer,
            "citations": [],
            "sources": [],
            "entities": [],
            "query": query,
            "strategy": "clarify"
        }
    
    def _call_ollama_direct(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama API directly"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": max_tokens,
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Ollama returned status {response.status_code}")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {e}")
    
    async def add_document(self, file_info: Dict[str, Any]) -> None:
        """Add document to knowledge graph (delegates to graph service)"""
        doc_id = file_info.get("id") or file_info.get("document_db_id")
        if not doc_id:
            raise ValueError("Document ID is required")
        
        print(f"📊 Adding document to knowledge graph: {file_info.get('filename', 'Unknown')}")
        
        chunks_data = file_info.get("chunks_data") or file_info.get("chunk_data", [])
        
        doc_info_for_graph = {
            "id": str(doc_id),
            "filename": file_info.get("filename", "Unknown"),
            "type": file_info.get("type", "unknown"),
            "user_id": file_info.get("user_id"),
            "chunks": chunks_data
        }
        
        self.graph.add_document(doc_info_for_graph)
        
        # Extract entities
        if chunks_data:
            for i, chunk_data in enumerate(chunks_data):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_text = chunk_data if isinstance(chunk_data, str) else chunk_data.get("text", "")
                
                entities = self.entity_extractor.extract_entities(chunk_text)
                
                for entity in entities:
                    self.graph.add_entity({
                        "name": entity["name"],
                        "type": entity["type"],
                        "doc_id": str(doc_id),
                        "chunk_id": chunk_id
                    })


# Singleton instance
_enhanced_graph_rag_service = None

def get_enhanced_graph_rag_service() -> EnhancedGraphRAGService:
    """Get the singleton EnhancedGraphRAGService instance"""
    global _enhanced_graph_rag_service
    if _enhanced_graph_rag_service is None:
        _enhanced_graph_rag_service = EnhancedGraphRAGService()
    return _enhanced_graph_rag_service
