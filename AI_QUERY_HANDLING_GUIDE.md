# AI Query Handling & Accuracy Guide

## Overview
This document explains how SupaQuery handles different types of queries and ensures accurate responses.

---

## Query Processing Pipeline

```
User Query
    ↓
1. Greeting Detection (Simple messages)
    ↓
2. Document Availability Check
    ↓
3. Query Classification (entity/date/summary/fact/etc.)
    ↓
4. Entity Extraction from Query
    ↓
5. Semantic Search in Knowledge Graph
    ↓
6. Context Building with Entities
    ↓
7. LLM Response Generation with Type-Specific Instructions
    ↓
8. Return Answer with Citations
```

---

## Query Classification System

### 1. **Entity/People Queries** (Highest Priority)
**Patterns Detected:**
- `who is`, `who are`, `who were`, `who mentioned`
- `key people`, `main people`, `people mentioned`
- `authors`, `researchers`, `scientists`, `participants`
- `list people`, `list organizations`

**LLM Instruction:**
```
List ALL people, organizations, or entities mentioned. Format as:
- **Name** (Type): Brief description or role
Focus only on listing the actual entities found, not explaining concepts.
```

**Example:**
- Q: "Who are the key people mentioned?"
- A: Lists actual people with roles, NOT study explanations

### 2. **Date/Event Queries**
**Patterns Detected:**
- `key dates`, `key events`, `important dates`
- `timeline`, `when did`, `when was`, `when were`
- `dates mentioned`, `events mentioned`, `chronology`

**LLM Instruction:**
```
Provide a structured list with clear bullet points. Format dates/events as:
- **Date/Year**: Event description
```

**Example:**
- Q: "What are the key dates and events?"
- A: Lists specific dates and events, NOT general content

### 3. **Summary Queries**
**Patterns:**
- `summarize`, `summary`, `overview`
- `about this`, `main topic`, `what is this`

**Response:** Comprehensive summary with bullet points

### 4. **Factual Queries**
**Patterns:**
- Starts with: `what is`, `what are`, `where`, `which`, `how many`

**Response:** Precise, factual answer with citations

### 5. **Analytical Queries**
**Patterns:**
- Starts with: `why`, `how does`, `how do`, `explain`, `analyze`

**Response:** Detailed analysis with reasoning

### 6. **Comparison Queries**
**Patterns:**
- `compare`, `difference between`, `vs`, `versus`, `contrast`

**Response:** Side-by-side comparison

### 7. **List Queries**
**Patterns:**
- `list all`, `list the`, `what are all`, `enumerate`
- `key points`, `main points`, `main findings`

**Response:** Structured list with bullets

---

## Handling Ambiguous/OOV Queries

### ✅ **Current Implementation**

When no relevant chunks are found:

```python
1. Get knowledge base statistics
2. Show what's available (docs, chunks, entities)
3. If entities found: Suggest asking about them
4. Else: Provide query refinement tips
5. Suggest general questions that work
```

### 📝 **Example Response for OOV Query**

```
User: "Tell me about quantum computing"

Bot: I couldn't find any relevant information in your uploaded 
     documents for that query.

**Your knowledge base contains:**
- 2 document(s)
- 40 text chunks
- 302 extracted entities

**Related entities I found:**
- GPT-4 (Technology)
- LLM (Concept)
- Needle-in-a-haystack (Method)

Try asking about these entities specifically.

**Or try these general questions:**
- 'What is this document about?'
- 'Summarize the main topics'
- 'What are the key findings?'
```

---

## Advanced Strategies for Better Accuracy

### 1. **Query Expansion** (Not Yet Implemented)
Expand user queries with synonyms:
- "people" → "people, persons, individuals, authors, researchers"
- "dates" → "dates, timeline, chronology, time periods"

### 2. **Spell Correction** (Not Yet Implemented)
Use fuzzy matching for entity names:
```python
from difflib import get_close_matches
suggestions = get_close_matches(query_term, entity_names, n=3, cutoff=0.6)
```

### 3. **Context-Aware Follow-ups** (Partial Implementation)
Track conversation history to understand:
- "them" → refers to people mentioned earlier
- "that" → refers to previous topic
- "more about X" → retrieve additional context

### 4. **Confidence Scoring** (Recommended Addition)
```python
def calculate_confidence(chunks, threshold=0.7):
    if not chunks:
        return 0.0
    avg_score = sum(c['similarity_score'] for c in chunks) / len(chunks)
    return avg_score

# Use confidence to qualify responses:
if confidence < 0.5:
    prefix = "I'm not very confident, but based on limited information: "
elif confidence < 0.7:
    prefix = "Based on some relevant information: "
else:
    prefix = "Based on the documents: "
```

### 5. **Multi-step Reasoning** (Future Enhancement)
For complex queries, break them down:
```
Q: "Compare the performance of GPT-4 and Claude on recall tasks"
   ↓
Step 1: Find info about GPT-4 performance
Step 2: Find info about Claude performance  
Step 3: Compare the findings
Step 4: Synthesize answer
```

---

## Best Practices

### ✅ **DO:**
1. **Classify queries before processing** - Understand intent first
2. **Provide structured responses** - Use bullets, sections, formatting
3. **Extract entities first** - They provide key context
4. **Give helpful guidance** - Don't just say "no results"
5. **Stay focused** - Answer ONLY what was asked
6. **Cite sources** - Always attribute information

### ❌ **DON'T:**
1. Don't provide general summaries when asked for specific info
2. Don't fabricate information not in documents
3. Don't use external knowledge
4. Don't go off on tangents
5. Don't assume ambiguous terms without clarification

---

## Testing Scenarios

### Test 1: Entity Query
```
Input: "Who are the key people mentioned?"
Expected: List of people with roles
Not: General document summary
```

### Test 2: Date Query
```
Input: "What are the key dates and events?"
Expected: Bullet list of dates with events
Not: Overall document description
```

### Test 3: Identity Statement
```
Input: "I am John"
Expected: "Nice to meet you, John! ..."
Not: Generic greeting
```

### Test 4: OOV Query
```
Input: "Tell me about cooking recipes"
Expected: "I couldn't find relevant info..." + suggestions
Not: Error or empty response
```

### Test 5: Ambiguous Query
```
Input: "What about them?"
Expected: Ask for clarification OR use conversation context
Not: Random information
```

---

## Configuration

Key settings in `graph_rag.py`:

```python
# Query classification patterns (lines 594-642)
query_patterns = {
    'entity': ['who is', 'who are', 'key people', ...],
    'date': ['key dates', 'key events', 'timeline', ...],
    ...
}

# LLM instructions per query type (lines 619-630)
query_instructions = {
    'entity': "List ALL entities...",
    'list': "Provide structured list...",
    ...
}

# Entity context formatting (lines 566-570)
entity_context = "=== EXTRACTED ENTITIES ===\n..."
```

---

## Improvements Made (Oct 4, 2025)

### 1. Enhanced Query Classification
- Added 15+ new patterns for entity detection
- Added 10+ new patterns for date/event detection
- Reordered checks (most specific first)

### 2. Improved LLM Instructions
- Type-specific instructions for each query category
- Added "CRITICAL" constraint to stay focused
- Enhanced entity instruction to list ONLY entities

### 3. Better Entity Context
- Clear section headers (=== EXTRACTED ENTITIES ===)
- Up to 10 entities shown (was 5)
- Better formatting for LLM parsing

### 4. Enhanced No-Results Handling
- Shows knowledge base stats
- Suggests related entities if found
- Provides query refinement tips
- Recommends working general questions

### 5. Updated System Prompt
- Added explicit guidance for entity queries
- Emphasized answering only what's asked

---

## Future Enhancements

1. **Query Expansion**: Auto-expand with synonyms
2. **Spell Correction**: Fuzzy matching for entity names
3. **Confidence Scoring**: Quality assessment of answers
4. **Multi-step Reasoning**: Break down complex queries
5. **Context Tracking**: Better conversation memory
6. **Query Rewriting**: Rephrase ambiguous queries
7. **Semantic Caching**: Store common query patterns
8. **Active Learning**: Improve from user feedback

---

## Conclusion

The key to accurate query handling is:

1. **Understand intent** through classification
2. **Extract relevant context** through entity-aware search
3. **Provide focused answers** with type-specific instructions
4. **Handle edge cases** gracefully with helpful guidance
5. **Continuously improve** based on user feedback

This approach ensures the AI responds accurately to what users actually ask, not what it thinks they might want.
