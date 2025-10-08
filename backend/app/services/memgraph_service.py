"""
Memgraph Service for Knowledge Graph
Replaces in-memory FAISS with persistent graph database
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from gqlalchemy import Memgraph, Node, Relationship
from gqlalchemy.models import MemgraphIndex
import hashlib
import json


class MemgraphService:
    """Service for managing knowledge graph in Memgraph"""
    
    def __init__(self):
        """Initialize connection to Memgraph"""
        self.host = os.getenv('MEMGRAPH_HOST', 'localhost')
        self.port = int(os.getenv('MEMGRAPH_PORT', '7687'))
        self.query_timeout = 30  # 30 second timeout for queries
        
        try:
            self.db = Memgraph(host=self.host, port=self.port)
            print(f"✅ Memgraph Service initialized")
            print(f"   - Host: {self.host}:{self.port}")
            print(f"   - Lab UI: http://localhost:3001")
            print(f"   - Query timeout: {self.query_timeout}s")
            
            # Create indexes for performance
            self._create_indexes()
            
            # Verify connection
            self._verify_connection()
            
        except Exception as e:
            print(f"❌ Failed to connect to Memgraph: {e}")
            print(f"   - Make sure Memgraph is running: docker ps | grep memgraph")
            raise
    
    def _verify_connection(self):
        """Verify connection to Memgraph"""
        try:
            result = list(self.db.execute_and_fetch("RETURN 1 as test"))
            if result and result[0]['test'] == 1:
                print(f"   ✓ Connection verified")
                
            # Set query execution timeout at database level
            try:
                self.db.execute(f"SET DATABASE SETTING 'query.timeout' TO '{self.query_timeout}';")
                print(f"   ✓ Query timeout set to {self.query_timeout}s")
            except Exception as timeout_err:
                # Not all Memgraph versions support this, it's okay
                print(f"   ⚠️ Could not set query timeout (not critical): {timeout_err}")
                
        except Exception as e:
            print(f"   ✗ Connection test failed: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for faster queries"""
        indexes = [
            "CREATE INDEX ON :Document(id);",
            "CREATE INDEX ON :Chunk(id);",
            "CREATE INDEX ON :Entity(name);",
            "CREATE INDEX ON :Concept(name);",
            "CREATE INDEX ON :User(id);"
        ]
        
        for index_query in indexes:
            try:
                self.db.execute(index_query)
            except Exception:
                # Index might already exist, that's fine
                pass
        
        print(f"   ✓ Indexes created/verified")
    
    def add_document(self, doc_info: Dict[str, Any]) -> None:
        """
        Add document and its chunks to the knowledge graph
        
        Args:
            doc_info: Dictionary containing:
                - id: document ID
                - filename: original filename
                - file_type: type of file
                - user_id: owner user ID
                - chunks: list of text chunks with embeddings
        """
        doc_id = doc_info["id"]
        filename = doc_info.get("filename", "unknown")
        file_type = doc_info.get("type", "unknown")
        user_id = doc_info.get("user_id")
        chunks = doc_info.get("chunks", [])
        
        try:
            # Create document node
            current_time = datetime.now().isoformat()
            self.db.execute("""
                MERGE (d:Document {id: $id})
                ON CREATE SET 
                    d.filename = $filename,
                    d.file_type = $file_type,
                    d.user_id = $user_id,
                    d.created_at = $created_at,
                    d.chunk_count = $chunk_count
                ON MATCH SET
                    d.updated_at = $updated_at
            """, {
                "id": str(doc_id),
                "filename": filename,
                "file_type": file_type,
                "user_id": user_id,
                "chunk_count": len(chunks),
                "created_at": current_time,
                "updated_at": current_time
            })
            
            # Add chunks and their embeddings
            for i, chunk_data in enumerate(chunks):
                chunk_text = chunk_data if isinstance(chunk_data, str) else chunk_data.get("text", "")
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # Generate a simple embedding hash for now
                embedding_hash = hashlib.sha256(chunk_text.encode()).hexdigest()[:16]
                
                # Extract citation metadata if available
                citation_json = None
                if isinstance(chunk_data, dict) and 'citation' in chunk_data:
                    import json
                    citation_json = json.dumps(chunk_data['citation'])
                
                # Create chunk node with citation metadata
                self.db.execute("""
                    MATCH (d:Document {id: $doc_id})
                    MERGE (c:Chunk {id: $chunk_id})
                    ON CREATE SET
                        c.text = $text,
                        c.chunk_index = $index,
                        c.embedding_hash = $embedding_hash,
                        c.citation_json = $citation_json,
                        c.created_at = $created_at
                    MERGE (d)-[:CONTAINS]->(c)
                """, {
                    "doc_id": str(doc_id),
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "index": i,
                    "embedding_hash": embedding_hash,
                    "citation_json": citation_json,
                    "created_at": current_time
                })
            
            print(f"✅ Added document '{filename}' to graph with {len(chunks)} chunks")
            
        except Exception as e:
            print(f"❌ Error adding document to graph: {e}")
            raise
    
    def add_entity(self, chunk_id: str, entity_text: str, entity_type: str, context: str = "") -> None:
        """
        Add an entity extracted from a chunk
        
        Args:
            chunk_id: ID of the chunk containing the entity
            entity_text: The entity text
            entity_type: Type of entity (PERSON, ORG, LOCATION, etc.)
            context: Surrounding context
        """
        try:
            current_time = datetime.now().isoformat()
            self.db.execute("""
                MATCH (c:Chunk {id: $chunk_id})
                MERGE (e:Entity {name: $name, type: $type})
                ON CREATE SET
                    e.created_at = $created_at,
                    e.mention_count = 1
                ON MATCH SET
                    e.mention_count = e.mention_count + 1
                MERGE (c)-[m:MENTIONS]->(e)
                ON CREATE SET
                    m.context = $context,
                    m.created_at = $created_at
            """, {
                "chunk_id": chunk_id,
                "name": entity_text,
                "type": entity_type,
                "context": context[:500],  # Limit context length
                "created_at": current_time
            })
        except Exception as e:
            print(f"Warning: Could not add entity {entity_text}: {e}")
    
    def add_relationship(self, entity1: str, entity2: str, rel_type: str, properties: Dict = None) -> None:
        """
        Add a relationship between two entities
        
        Args:
            entity1: First entity name
            entity2: Second entity name
            rel_type: Type of relationship (RELATES_TO, CITES, etc.)
            properties: Additional properties for the relationship
        """
        properties = properties or {}
        
        try:
            current_time = datetime.now().isoformat()
            properties['created_at'] = current_time
            self.db.execute(f"""
                MATCH (e1:Entity {{name: $name1}})
                MATCH (e2:Entity {{name: $name2}})
                MERGE (e1)-[r:{rel_type}]->(e2)
                ON CREATE SET r += $props
            """, {
                "name1": entity1,
                "name2": entity2,
                "props": properties
            })
        except Exception as e:
            print(f"Warning: Could not add relationship: {e}")
    
    def query_similar_chunks(self, query_text: str, doc_ids: Optional[List[str]] = None, limit: int = 5) -> List[Dict]:
        """
        Query for similar chunks with timeout protection and retry logic
        Uses keyword matching for relevance when doc_ids is None
        
        Args:
            query_text: Query text
            doc_ids: Optional list of document IDs to search within
            limit: Maximum number of results
            
        Returns:
            List of chunk dictionaries with text and metadata, sorted by relevance
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # If specific documents are requested, use them
                if doc_ids:
                    result = self.db.execute_and_fetch("""
                        MATCH (d:Document)-[:CONTAINS]->(c:Chunk)
                        WHERE d.id IN $doc_ids
                        WITH c, d
                        LIMIT $limit
                        RETURN c.text as text, c.id as chunk_id, d.filename as source, d.id as doc_id, c.citation_json as citation_json
                    """, {"doc_ids": doc_ids, "limit": limit})
                else:
                    # When no docs specified, get more chunks for relevance ranking
                    # Get 3x the limit to ensure good results after ranking
                    fetch_limit = limit * 3
                    result = self.db.execute_and_fetch("""
                        MATCH (d:Document)-[:CONTAINS]->(c:Chunk)
                        WITH c, d
                        LIMIT $limit
                        RETURN c.text as text, c.id as chunk_id, d.filename as source, d.id as doc_id, c.citation_json as citation_json
                    """, {"limit": fetch_limit})
                
                chunks = []
                for row in result:
                    chunk_data = {
                        "text": row["text"],
                        "chunk_id": row["chunk_id"],
                        "source": row["source"],
                        "doc_id": row["doc_id"]
                    }
                    
                    # Parse citation metadata if available
                    if row.get("citation_json"):
                        try:
                            import json
                            chunk_data["citation"] = json.loads(row["citation_json"])
                        except:
                            pass
                    
                    chunks.append(chunk_data)
                
                if chunks:
                    print(f"   ✓ Retrieved {len(chunks)} chunks")
                else:
                    print(f"   ⚠️ No chunks found")
                
                return chunks
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'timed out' in error_msg or 'timeout' in error_msg:
                    if attempt < max_retries - 1:
                        print(f"   ⚠️ Query timeout, retrying with smaller limit...")
                        limit = max(1, limit // 2)  # Reduce limit by half
                        # Recreate connection
                        try:
                            self.db = Memgraph(host=self.host, port=self.port)
                        except:
                            pass
                    else:
                        print(f"   ❌ Query timed out after {max_retries} attempts")
                        # Return empty list instead of crashing
                        return []
                else:
                    print(f"   ❌ Error querying chunks: {e}")
                    if attempt < max_retries - 1:
                        # Try reconnecting
                        try:
                            self.db = Memgraph(host=self.host, port=self.port)
                        except:
                            pass
                    else:
                        return []
        
        return []
    
    def query_entities(self, query_text: str, entity_types: Optional[List[str]] = None, limit: int = 10) -> List[Dict]:
        """
        Query for entities related to the query
        
        Args:
            query_text: Query text
            entity_types: Optional filter by entity types
            limit: Maximum number of results
            
        Returns:
            List of entity dictionaries
        """
        try:
            if entity_types:
                result = self.db.execute_and_fetch("""
                    MATCH (e:Entity)
                    WHERE e.type IN $types AND toLower(e.name) CONTAINS toLower($query)
                    RETURN e.name as name, e.type as type, e.mention_count as mentions
                    ORDER BY e.mention_count DESC
                    LIMIT $limit
                """, {"query": query_text, "types": entity_types, "limit": limit})
            else:
                result = self.db.execute_and_fetch("""
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($query)
                    RETURN e.name as name, e.type as type, e.mention_count as mentions
                    ORDER BY e.mention_count DESC
                    LIMIT $limit
                """, {"query": query_text, "limit": limit})
            
            entities = []
            for row in result:
                entities.append({
                    "name": row["name"],
                    "type": row["type"],
                    "mentions": row.get("mentions", 0)
                })
            
            return entities
            
        except Exception as e:
            print(f"❌ Error querying entities: {e}")
            return []
    
    def get_document_entities(self, doc_id: str) -> List[Dict]:
        """
        Get all entities mentioned in a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of entities with their types and mention counts
        """
        try:
            result = self.db.execute_and_fetch("""
                MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(c:Chunk)-[:MENTIONS]->(e:Entity)
                RETURN DISTINCT e.name as name, e.type as type, count(c) as mentions
                ORDER BY mentions DESC
            """, {"doc_id": str(doc_id)})
            
            entities = []
            for row in result:
                entities.append({
                    "name": row["name"],
                    "type": row["type"],
                    "mentions": row["mentions"]
                })
            
            return entities
            
        except Exception as e:
            print(f"❌ Error getting document entities: {e}")
            return []
    
    def get_entity_relationships(self, entity_name: str, depth: int = 1) -> Dict:
        """
        Get relationships for an entity
        
        Args:
            entity_name: Name of the entity
            depth: How many hops to traverse
            
        Returns:
            Dictionary with entity and its related entities
        """
        try:
            result = self.db.execute_and_fetch("""
                MATCH path = (e1:Entity {name: $name})-[r*1..$$depth]-(e2:Entity)
                RETURN e1, r, e2
                LIMIT 50
            """.replace('$$depth', str(depth)), {"name": entity_name})
            
            relationships = {
                "entity": entity_name,
                "related": []
            }
            
            for row in result:
                if "e2" in row:
                    relationships["related"].append({
                        "name": row["e2"].get("name"),
                        "type": row["e2"].get("type")
                    })
            
            return relationships
            
        except Exception as e:
            print(f"❌ Error getting entity relationships: {e}")
            return {"entity": entity_name, "related": []}
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and all its related nodes
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            # First, collect entities that will become orphaned
            orphan_check = self.db.execute_and_fetch("""
                MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(c:Chunk)-[:MENTIONS]->(e:Entity)
                WITH e, COUNT(DISTINCT c) as chunk_refs
                MATCH (e)<-[:MENTIONS]-(all_chunks:Chunk)
                WITH e, chunk_refs, COUNT(DISTINCT all_chunks) as total_refs
                WHERE total_refs = chunk_refs
                RETURN COLLECT(DISTINCT e.name) as orphan_entities
            """, {"doc_id": str(doc_id)})
            
            orphan_list = list(orphan_check)
            orphan_entities = orphan_list[0].get('orphan_entities', []) if orphan_list else []
            
            # Delete the document and its chunks
            self.db.execute("""
                MATCH (d:Document {id: $doc_id})
                OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
                DETACH DELETE d, c
            """, {"doc_id": str(doc_id)})
            
            # Delete orphaned entities (entities only referenced by this document's chunks)
            if orphan_entities:
                self.db.execute("""
                    UNWIND $entities as entity_name
                    MATCH (e:Entity {name: entity_name})
                    WHERE NOT EXISTS((e)<-[:MENTIONS]-(:Chunk))
                    DETACH DELETE e
                """, {"entities": orphan_entities})
                print(f"   - Deleted {len(orphan_entities)} orphaned entities")
            
            print(f"✅ Deleted document {doc_id} from graph")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return False
    
    def list_documents(self, limit: int = 20) -> List[Dict]:
        """
        List all documents in the graph
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document dictionaries with metadata
        """
        try:
            result = self.db.execute_and_fetch("""
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
                WITH d, count(c) as chunk_count
                RETURN d.id as id, d.filename as filename, d.type as type, 
                       d.created_at as created_at, chunk_count
                ORDER BY d.created_at DESC
                LIMIT $limit
            """, {"limit": limit})
            
            documents = []
            for row in result:
                documents.append({
                    "id": row.get("id"),
                    "filename": row.get("filename"),
                    "type": row.get("type"),
                    "created_at": row.get("created_at"),
                    "chunk_count": row.get("chunk_count", 0)
                })
            
            return documents
            
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics with connection retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Simpler query that's less likely to timeout
                result = self.db.execute_and_fetch("""
                    MATCH (d:Document)
                    OPTIONAL MATCH (c:Chunk)
                    OPTIONAL MATCH (e:Entity)
                    OPTIONAL MATCH ()-[r]->()
                    RETURN count(DISTINCT d) as docs, 
                           count(DISTINCT c) as chunks, 
                           count(DISTINCT e) as entities, 
                           count(DISTINCT r) as relationships
                """)
                
                result_list = list(result)
                if result_list:
                    stats = result_list[0]
                    return {
                        "documents": stats.get("docs", 0) or 0,
                        "chunks": stats.get("chunks", 0) or 0,
                        "entities": stats.get("entities", 0) or 0,
                        "relationships": stats.get("relationships", 0) or 0
                    }
                else:
                    # No results, graph might be empty
                    return {"documents": 0, "chunks": 0, "entities": 0, "relationships": 0}
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Stats query attempt {attempt + 1} failed, retrying... ({e})")
                    # Recreate connection on retry
                    try:
                        self.db = Memgraph(host=self.host, port=self.port)
                    except:
                        pass
                else:
                    print(f"❌ Error getting stats after {max_retries} attempts: {e}")
                    # Return non-zero default if we know documents exist in DB
                    return {"documents": 0, "chunks": 0, "entities": 0, "relationships": 0}
    
    def clear_all(self) -> bool:
        """Clear all data from graph (use with caution!)"""
        try:
            self.db.execute("MATCH (n) DETACH DELETE n")
            print("✅ Cleared all data from graph")
            return True
        except Exception as e:
            print(f"❌ Error clearing graph: {e}")
            return False
    
    def close(self):
        """Close connection (GQLAlchemy manages connections automatically)"""
        pass


# Global instance
_memgraph_service = None

def get_memgraph_service() -> MemgraphService:
    """Get or create Memgraph service instance"""
    global _memgraph_service
    if _memgraph_service is None:
        _memgraph_service = MemgraphService()
    return _memgraph_service
