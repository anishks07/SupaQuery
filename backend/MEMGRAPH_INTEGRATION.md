# Memgraph Integration for Knowledge Graph

## Overview

SupaQuery uses **Memgraph** as a true graph database for knowledge graph functionality, replacing the in-memory FAISS approach with a persistent, queryable graph structure.

## Architecture

```
┌─────────────────────────────────────────┐
│     PostgreSQL (Auth + Metadata)        │
│  • Users, roles, permissions            │
│  • Document metadata, file paths        │
│  • Chat sessions, messages              │
└─────────────────────────────────────────┘
                 ↕
┌─────────────────────────────────────────┐
│     Memgraph (Knowledge Graph)          │
│  • Document nodes                       │
│  • Entity nodes (people, places, etc)   │
│  • Concept relationships                │
│  • Citation networks                    │
│  • Semantic relationships               │
└─────────────────────────────────────────┘
                 ↕
┌─────────────────────────────────────────┐
│     Vector Embeddings (Optional)        │
│  • Stored as node properties            │
│  • Used for hybrid search               │
└─────────────────────────────────────────┘
                 ↕
┌─────────────────────────────────────────┐
│         Ollama (LLM Backend)            │
│  • llama3.2:latest model                │
│  • Query understanding                  │
│  • Answer generation                    │
└─────────────────────────────────────────┘
```

## Why Memgraph?

### Advantages over FAISS
- ✅ **True graph database** - explicit relationships between entities
- ✅ **Persistent storage** - data survives restarts
- ✅ **Complex queries** - multi-hop traversals, pattern matching
- ✅ **Real-time analytics** - built-in streaming support
- ✅ **Cypher support** - familiar query language
- ✅ **Fast performance** - in-memory graph engine
- ✅ **Hybrid search** - combine graph + vector operations

### Advantages over Neo4j
- ✅ **Faster** - 120x faster for real-time queries
- ✅ **Lighter** - lower memory footprint
- ✅ **Modern** - built for streaming and real-time data
- ✅ **Open source** - community edition is powerful
- ✅ **Better for RAG** - optimized for AI/ML workloads
- ✅ **Python native** - excellent GQLAlchemy library

## Installation

### Docker (Recommended)

```bash
# Pull Memgraph Platform (includes MemgraphDB + Lab UI)
docker pull memgraph/memgraph-platform:latest

# Run Memgraph
docker run -d \
  --name memgraph \
  -p 7687:7687 \
  -p 7444:7444 \
  -p 3000:3000 \
  -v mg_data:/var/lib/memgraph \
  memgraph/memgraph-platform:latest
```

### Ports:
- **7687** - Bolt protocol (database connection)
- **7444** - Websocket for monitoring
- **3000** - Memgraph Lab (UI)

### Access Memgraph Lab:
Open browser: `http://localhost:3000`

## Python Setup

```bash
# Install required packages
pip install gqlalchemy pymgclient neo4j-driver
```

Add to `requirements.txt`:
```
gqlalchemy>=1.4.0
pymgclient>=1.3.1
neo4j-driver>=5.14.0
```

## Graph Schema

### Node Types

1. **Document**
   ```cypher
   (:Document {
     id: String,
     filename: String,
     file_type: String,
     user_id: Integer,
     upload_date: DateTime,
     content: String,
     embedding: List<Float>  // Optional vector
   })
   ```

2. **Chunk**
   ```cypher
   (:Chunk {
     id: String,
     text: String,
     chunk_index: Integer,
     embedding: List<Float>,
     doc_id: String
   })
   ```

3. **Entity**
   ```cypher
   (:Entity {
     name: String,
     type: String,  // PERSON, ORG, LOCATION, CONCEPT
     description: String
   })
   ```

4. **Concept**
   ```cypher
   (:Concept {
     name: String,
     category: String,
     definition: String
   })
   ```

### Relationship Types

1. **CONTAINS**
   ```cypher
   (Document)-[:CONTAINS]->(Chunk)
   ```

2. **MENTIONS**
   ```cypher
   (Chunk)-[:MENTIONS {count: Integer, context: String}]->(Entity)
   ```

3. **RELATES_TO**
   ```cypher
   (Concept)-[:RELATES_TO {strength: Float, type: String}]->(Concept)
   ```

4. **CITES**
   ```cypher
   (Document)-[:CITES {page: Integer, context: String}]->(Document)
   ```

5. **SIMILAR_TO**
   ```cypher
   (Chunk)-[:SIMILAR_TO {similarity: Float}]->(Chunk)
   ```

6. **PART_OF**
   ```cypher
   (Entity)-[:PART_OF]->(Entity)
   ```

## Usage Examples

### 1. Add Document to Graph

```python
from gqlalchemy import Memgraph

# Connect to Memgraph
memgraph = Memgraph(host="localhost", port=7687)

# Create document node
memgraph.execute("""
    CREATE (d:Document {
        id: $id,
        filename: $filename,
        file_type: $file_type,
        user_id: $user_id,
        upload_date: datetime()
    })
""", {
    "id": "doc_123",
    "filename": "research_paper.pdf",
    "file_type": "pdf",
    "user_id": 1
})
```

### 2. Add Chunks with Relationships

```python
# Add chunks and link to document
memgraph.execute("""
    MATCH (d:Document {id: $doc_id})
    CREATE (c:Chunk {
        id: $chunk_id,
        text: $text,
        chunk_index: $index,
        embedding: $embedding
    })
    CREATE (d)-[:CONTAINS]->(c)
""", {
    "doc_id": "doc_123",
    "chunk_id": "chunk_1",
    "text": "Introduction...",
    "index": 0,
    "embedding": [0.1, 0.2, ...]
})
```

### 3. Extract and Link Entities

```python
# Create entity and link to chunks
memgraph.execute("""
    MATCH (c:Chunk {id: $chunk_id})
    MERGE (e:Entity {name: $entity_name, type: $entity_type})
    CREATE (c)-[:MENTIONS {context: $context}]->(e)
""", {
    "chunk_id": "chunk_1",
    "entity_name": "Machine Learning",
    "entity_type": "CONCEPT",
    "context": "discusses ML algorithms"
})
```

### 4. Query: Find Related Documents

```cypher
// Find documents that mention the same entities
MATCH (d1:Document)-[:CONTAINS]->(:Chunk)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(:Chunk)<-[:CONTAINS]-(d2:Document)
WHERE d1.id = 'doc_123' AND d1 <> d2
RETURN DISTINCT d2.filename, COUNT(e) as shared_entities
ORDER BY shared_entities DESC
LIMIT 10
```

### 5. Query: Citation Network

```cypher
// Find citation chain
MATCH path = (d1:Document {id: 'doc_123'})-[:CITES*1..3]->(d2:Document)
RETURN path
```

### 6. Query: Concept Relationships

```cypher
// Find related concepts
MATCH (c1:Concept {name: 'Neural Networks'})-[:RELATES_TO*1..2]-(c2:Concept)
RETURN c2.name, c2.category
```

### 7. Hybrid Search (Graph + Vector)

```cypher
// Find semantically similar chunks that mention specific entity
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {name: 'Deep Learning'})
WHERE vector.cosine_similarity(c.embedding, $query_embedding) > 0.7
RETURN c.text, c.id
ORDER BY vector.cosine_similarity(c.embedding, $query_embedding) DESC
LIMIT 5
```

## Integration with SupaQuery

### Service Architecture

```
app/services/
├── graph_service.py       # Memgraph operations
├── entity_extractor.py    # NER and entity linking
├── document_processor.py  # File processing (existing)
└── rag_service.py         # RAG with graph context
```

### Example: Enhanced RAG Query

```python
async def query_with_graph(query: str, doc_ids: List[str]):
    # 1. Extract entities from query
    query_entities = extract_entities(query)
    
    # 2. Find related documents via graph
    related_docs = memgraph.execute("""
        MATCH (d:Document)-[:CONTAINS]->(:Chunk)-[:MENTIONS]->(e:Entity)
        WHERE e.name IN $entities AND d.id IN $doc_ids
        RETURN d.id, COUNT(e) as relevance
        ORDER BY relevance DESC
    """, {"entities": query_entities, "doc_ids": doc_ids})
    
    # 3. Get relevant chunks
    chunks = memgraph.execute("""
        MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(c:Chunk)
        RETURN c.text
    """, {"doc_id": related_docs[0]["d.id"]})
    
    # 4. Generate answer with LLM
    answer = await llm.generate(query, chunks)
    
    return {
        "answer": answer,
        "sources": related_docs,
        "entities": query_entities
    }
```

## Performance Tuning

### Indexing

```cypher
// Create indexes for faster queries
CREATE INDEX ON :Document(id);
CREATE INDEX ON :Chunk(id);
CREATE INDEX ON :Entity(name);
CREATE INDEX ON :Concept(name);
```

### Memory Configuration

```bash
# In docker run, add memory settings
--env MEMGRAPH_MEMORY_LIMIT=8GB
```

## Monitoring

### Memgraph Lab Features:
- **Query execution** - Run Cypher queries
- **Graph visualization** - See relationships
- **Performance metrics** - Monitor query speed
- **Schema viewer** - Understand graph structure

### Access Lab:
```
http://localhost:3000
```

## Migration Path

### Phase 1: Setup (Week 1)
- [x] Install Memgraph
- [ ] Create graph schema
- [ ] Set up Python connectors

### Phase 2: Core Integration (Week 2)
- [ ] Implement GraphService class
- [ ] Add document ingestion to graph
- [ ] Create entity extraction pipeline

### Phase 3: Enhanced Queries (Week 3)
- [ ] Update RAG service to use graph
- [ ] Add relationship-based search
- [ ] Implement citation tracking

### Phase 4: Optimization (Week 4)
- [ ] Add hybrid vector+graph search
- [ ] Performance tuning
- [ ] Graph visualization in UI

## Benefits for SupaQuery

### Immediate Benefits:
1. **Better context** - Documents connected by concepts, not just keywords
2. **Citation tracking** - "Show me papers that cite this work"
3. **Entity linking** - "Find all mentions of 'Neural Networks' across documents"
4. **Relationship queries** - "What connects these two documents?"

### Future Possibilities:
1. **Knowledge graph visualization** - Interactive graph UI
2. **Recommendation engine** - "Documents related to your interests"
3. **Temporal analysis** - "How has this concept evolved?"
4. **Collaboration networks** - "Who cites whom?"

## Resources

- **Memgraph Docs**: https://memgraph.com/docs
- **Cypher Tutorial**: https://memgraph.com/docs/cypher-manual
- **GQLAlchemy**: https://github.com/memgraph/gqlalchemy
- **Example Projects**: https://github.com/memgraph/memgraph-examples

## Comparison

| Feature | FAISS | Memgraph | Neo4j |
|---------|-------|----------|-------|
| Graph Queries | ❌ | ✅ | ✅ |
| Vector Search | ✅ | ✅ (hybrid) | ✅ (plugin) |
| Performance | ⚡⚡⚡ | ⚡⚡ | ⚡ |
| Persistence | ❌ | ✅ | ✅ |
| Real-time | ✅ | ✅ | ⚠️ |
| Memory Usage | Low | Medium | High |
| Setup Complexity | Easy | Medium | Medium |
| Best For | Vector similarity | Hybrid RAG + Graph | Enterprise graphs |

## Next Steps

1. **Install Memgraph** following the Docker instructions above
2. **Update backend dependencies** with graph libraries
3. **Implement GraphService** for document ingestion
4. **Migrate existing documents** to graph structure
5. **Enhance RAG queries** with graph context

---

Built with ❤️ using Memgraph for intelligent knowledge graphs! 🚀
