"""
GraphRAG Service with Memgraph
Implements Graph-based Retrieval Augmented Generation using:
- Memgraph for knowledge graph storage
- Entity extraction with spaCy
- Ollama for local LLM inference
- Graph-based relationships             # Query similar chunks from graph
            print(f"   � Retrieving relevant chunks from grap            # Classi            # Query entities related to the query
            print(f"   🏷️  Searching for relevant entities...")
            relevant_entities = self.graph.query_entities(query, limit=5)
            
            # Adjust retrieval strategy based on query type
            retrieval_limit = top_k
            if query_type in ['summary', 'overview']:
                retrieval_limit = min(10, top_k * 2)  # More context for summaries
            elif query_type in ['fact', 'entity']:
                retrieval_limit = max(3, top_k // 2)  # Precise results for facts
            
            # Query similar chunks from graph
            print(f"   � Retrieving relevant chunks from graph (limit: {retrieval_limit})...")
            chunks = self.graph.query_similar_chunks(query, doc_ids=document_ids, limit=retrieval_limit)y type for better handling
            query_type = self._classify_query(query)
            print(f"   🎯 Query type: {query_type}")
            
            # Query entities related to the query
            print(f"   🏷️  Searching for relevant entities...")
            relevant_entities = self.graph.query_entities(query, limit=5)
            
            # Adjust retrieval based on query type
            retrieval_limit = top_k
            if query_type in ['summary', 'overview']:
                retrieval_limit = min(10, top_k * 2)  # Get more context for summaries
            elif query_type in ['fact', 'entity']:
                retrieval_limit = max(3, top_k // 2)  # Fewer, more precise results for facts
            
            # Query similar chunks from graph
            print(f"   � Retrieving relevant chunks from graph...")
            chunks = self.graph.query_similar_chunks(query, doc_ids=document_ids, limit=retrieval_limit)            chunks = self.graph.query_similar_chunks(query, doc_ids=document_ids, limit=top_k)
            
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
        
        # Define advanced system prompt for robust AI behavior
        self.system_prompt = """You are SupaQuery, an advanced AI assistant specialized in document analysis using knowledge graphs and entity extraction.

# CORE IDENTITY
You are intelligent, professional, and context-aware. You understand natural language queries and respond appropriately based on the question type and available information.

# FUNDAMENTAL PRINCIPLES

## 1. ACCURACY & TRUTHFULNESS
- Base ALL answers strictly on provided document context
- NEVER fabricate, assume, or use external knowledge
- If information isn't in documents, explicitly say: "I don't have information about that in the uploaded documents"
- When uncertain, express uncertainty clearly

## 2. INTELLIGENT QUERY UNDERSTANDING
Detect and handle different query types appropriately:

**Factual Questions** ("What is...", "Who are...", "When did...")
→ Extract precise facts from documents, cite sources

**Analytical Questions** ("Why...", "How...", "What caused...")  
→ Synthesize information, explain relationships, show reasoning

**Comparative Questions** ("Compare X and Y", "Difference between...")
→ Analyze multiple sources, highlight contrasts and similarities

**Summarization** ("Summarize", "Give me an overview", "What's this about")
→ Provide structured, hierarchical summaries with key points

**List Queries** ("List all...", "What are the key...")
→ Return structured lists with bullet points

**Follow-up Questions** (Context-dependent, short questions)
→ Use conversation context, understand references like "it", "them", "that"

**Exploratory** ("Tell me more about...", "Explain...")
→ Provide comprehensive explanations with examples from documents

## 3. RESPONSE QUALITY STANDARDS

### Structure
- Start with direct answer to the question
- Support with evidence from documents
- Cite sources naturally in the text
- End with additional relevant context if helpful

### Clarity
- Use clear, professional language
- Break complex information into digestible points
- Use formatting (bold, lists, sections) for readability
- Avoid jargon unless it's in the source documents

### Completeness
- Answer the full question, not just part of it
- Include relevant context that enriches understanding
- Connect related concepts when appropriate
- Acknowledge limitations of available information

## 4. CITATION & ATTRIBUTION
- Always cite which document information comes from
- Use natural citations: "According to [document name]..."
- Be specific: mention sections, pages, or contexts when relevant
- Never claim knowledge not present in documents

## 5. ENTITY AWARENESS
Leverage extracted entities (people, organizations, locations, dates, etc.):
- Identify key entities in the question
- Find relationships between entities
- Use entity context to provide richer answers
- Track entity mentions across documents

## 6. MULTI-DOCUMENT REASONING
When multiple documents are available:
- Compare and contrast information
- Identify agreements and contradictions
- Synthesize insights across sources
- Note when documents complement each other

## 7. HANDLING EDGE CASES

**Vague Questions** → Ask for clarification or provide general overview
**Out-of-scope Questions** → Politely state it's not in the documents
**Ambiguous Terms** → Clarify which meaning based on context
**Contradictory Info** → Present both views, note the contradiction
**Incomplete Info** → State what's known and what's missing

## 8. CONVERSATIONAL INTELLIGENCE
- Understand pronouns and references ("it", "they", "that", "the previous")
- Maintain context across conversation
- Be helpful and guide users to ask better questions
- Suggest related questions users might find useful

# RESPONSE PATTERNS

## For Factual Queries:
"According to [document], [direct fact]. This is mentioned in the context of [relevant context]."

## For Analysis:
"Based on the documents, [analysis]. This is supported by [evidence 1] and [evidence 2]. The key insight is [conclusion]."

## For Summaries:
"Here's a summary of [topic]:

**Main Points:**
- [Point 1]
- [Point 2]
- [Point 3]

**Key Details:**
[Elaboration with sources]"

## For No Information:
"I don't have information about [topic] in the uploaded documents. The documents focus on [what they do cover]. Would you like to know more about those areas?"

# QUALITY CHECKS
Before responding, verify:
✓ Answer is grounded in document content
✓ Sources are cited appropriately  
✓ Response format matches query type
✓ Language is clear and professional
✓ All parts of question are addressed

Current date: October 4, 2025

Remember: You're not just a search engine - you're an intelligent assistant that understands context, reasons about information, and helps users gain insights from their documents."""
        
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
            
            # Basic greetings
            greeting_patterns = [
                'hi', 'hello', 'hey', 'good morning', 'good afternoon', 
                'good evening', 'greetings', 'howdy', 'sup', 'yo'
            ]
            
            # Acknowledgments and simple responses
            acknowledgment_patterns = [
                'thanks', 'thank you', 'ok', 'okay', 'alright', 'cool',
                'got it', 'i see', 'understood', 'nice', 'great',
                'bye', 'goodbye', 'see you', 'later'
            ]
            
            # Identity/introduction statements
            identity_patterns = [
                'i am', "i'm", 'my name is', 'this is', 'im ', 'call me'
            ]
            
            # Check if it's a simple introduction or identity statement (short statements only)
            is_identity = any(pattern in query_lower for pattern in identity_patterns) and len(query.split()) <= 6
            
            # Check if it's a simple acknowledgment
            is_acknowledgment = (
                query_lower in acknowledgment_patterns or
                (len(query.split()) <= 3 and any(pattern in query_lower for pattern in acknowledgment_patterns))
            )
            
            # Check if query is just a greeting (exact match or very short)
            is_greeting = (
                query_lower in greeting_patterns or 
                len(query.split()) <= 2 and any(pattern in query_lower for pattern in greeting_patterns) or
                is_identity or
                is_acknowledgment
            )
            
            if is_greeting:
                print(f"   💬 Detected greeting/simple message, responding conversationally")
                stats = self.graph.get_stats()
                
                # Handle acknowledgments differently
                if is_acknowledgment:
                    # Simple acknowledgments get simple responses
                    acknowledgment_responses = [
                        "You're welcome! Let me know if you have any questions about your documents. 😊",
                        "Happy to help! Feel free to ask anything about your uploaded documents.",
                        "Anytime! What would you like to know about your documents?",
                        "Glad I could help! Any other questions?"
                    ]
                    import random
                    return {
                        "answer": random.choice(acknowledgment_responses),
                        "citations": [],
                        "sources": [],
                        "entities": [],
                        "query": query
                    }
                
                # Extract name if it's an introduction
                user_name = None
                if is_identity:
                    # Try to extract name from "I am [name]" or "My name is [name]"
                    for pattern in ['i am ', "i'm ", 'my name is ', 'this is ', 'im ']:
                        if pattern in query_lower:
                            potential_name = query_lower.split(pattern)[-1].strip().split()[0]
                            if potential_name and len(potential_name) > 1:
                                user_name = potential_name.capitalize()
                                break
                
                if stats['documents'] > 0:
                    doc_text = f"{stats['documents']} document{'s' if stats['documents'] > 1 else ''}"
                    
                    # Get list of uploaded documents
                    try:
                        doc_list = self.graph.list_documents()
                        
                        doc_list_text = ""
                        if doc_list and len(doc_list) > 0:
                            # Remove duplicates by filename and get unique docs
                            seen_filenames = set()
                            unique_docs = []
                            for doc in doc_list:
                                filename = doc.get('filename', '')
                                if filename and filename not in seen_filenames:
                                    seen_filenames.add(filename)
                                    unique_docs.append(doc)
                            
                            if unique_docs:
                                doc_list_text = "\n\n**Your uploaded documents:**\n"
                                for i, doc in enumerate(unique_docs[:5], 1):  # Show max 5 unique docs
                                    doc_name = doc.get('filename', f'Document {i}')
                                    # Truncate long filenames
                                    if len(doc_name) > 50:
                                        doc_name = doc_name[:47] + "..."
                                    doc_list_text += f"{i}. 📄 {doc_name}\n"
                                
                                remaining = len(unique_docs) - 5
                                if remaining > 0:
                                    doc_list_text += f"   ...and {remaining} more\n"
                                
                                doc_list_text += "\n*Ask me anything about these documents!*"
                    except Exception as e:
                        doc_list_text = ""
                        print(f"   ⚠️ Could not fetch document list: {e}")
                    
                    # Personalized greeting if name detected
                    if user_name:
                        greeting_start = f"Nice to meet you, {user_name}! 👋 I'm SupaQuery, your AI assistant."
                    else:
                        greeting_start = "Hello! 👋 I'm SupaQuery, your AI assistant for document analysis."
                    
                    greeting_response = f"""{greeting_start}

I can see you have {doc_text} uploaded with {stats['entities']} entities extracted. I'm ready to help you analyze them!{doc_list_text}

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
                    # Personalized greeting if name detected
                    if user_name:
                        greeting_start = f"Nice to meet you, {user_name}! 👋 I'm SupaQuery, your AI assistant."
                    else:
                        greeting_start = "Hello! 👋 I'm SupaQuery, your AI assistant for document analysis."
                    
                    greeting_response = f"""{greeting_start}

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
            
            # Classify query type for intelligent handling
            query_type = self._classify_query(query)
            print(f"   🎯 Query type detected: {query_type}")
            
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
            
            # Generate answer with LLM using query-type-aware prompting
            print(f"   🤖 Generating answer with Ollama...")
            from llama_index.core.llms import ChatMessage
            
            # Customize instruction based on query type
            query_instructions = {
                'summary': "Provide a comprehensive summary with main points in bullet format.",
                'fact': "Provide a precise, factual answer. Be concise and cite the source.",
                'entity': "List all relevant entities with their roles/descriptions. Use bullet points.",
                'analysis': "Provide a detailed analytical answer explaining the reasoning and relationships.",
                'comparison': "Compare and contrast the items clearly, highlighting key differences and similarities.",
                'list': "Provide a structured list with clear bullet points or numbering.",
                'overview': "Provide a clear, well-structured answer with relevant details."
            }
            
            instruction = query_instructions.get(query_type, query_instructions['overview'])
            
            messages = [
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=f"""Context from knowledge graph:
{context}

User Question: {query}

Instructions: {instruction}

Please provide your answer based strictly on the context above.""")
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
    
    def _classify_query(self, query: str) -> str:
        """
        Classify query type to optimize retrieval and response generation
        Returns: 'fact', 'summary', 'analysis', 'comparison', 'list', 'entity', 'overview'
        """
        query_lower = query.lower()
        
        # Summary/Overview queries
        if any(word in query_lower for word in ['summarize', 'summary', 'overview', 'about this', 'main topic', 'what is this']):
            return 'summary'
        
        # Factual queries
        if any(query_lower.startswith(word) for word in ['what is', 'what are', 'when', 'where', 'which', 'how many', 'how much']):
            return 'fact'
        
        # Entity queries
        if any(word in query_lower for word in ['who is', 'who are', 'who mentioned', 'list people', 'list organizations']):
            return 'entity'
        
        # Analytical queries
        if any(query_lower.startswith(word) for word in ['why', 'how does', 'how do', 'explain', 'analyze']):
            return 'analysis'
        
        # Comparison queries
        if any(word in query_lower for word in ['compare', 'difference between', 'vs', 'versus', 'contrast']):
            return 'comparison'
        
        # List queries
        if any(word in query_lower for word in ['list all', 'list the', 'what are all', 'enumerate']):
            return 'list'
        
        # Default to overview for longer queries or general questions
        return 'overview'
    
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
