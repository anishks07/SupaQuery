# Database Implementation

## Overview

SupaQuery now includes a SQLite database for persistent storage of documents, chat history, and metadata.

## Database Schema

### Tables

#### 1. **documents**
Stores metadata about uploaded files.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Unique document identifier (UUID) |
| filename | TEXT | Stored filename |
| original_filename | TEXT | Original uploaded filename |
| file_type | TEXT | File type (pdf, docx, image, audio) |
| file_size | INTEGER | File size in bytes |
| file_path | TEXT | Path to stored file |
| status | TEXT | Processing status (processing/completed/failed) |
| total_chunks | INTEGER | Number of text chunks |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### 2. **document_chunks**
Stores processed text chunks from documents.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| document_id | TEXT (FK) | References documents.id |
| chunk_id | INTEGER | Chunk number within document |
| text | TEXT | Chunk content |
| metadata | TEXT (JSON) | Additional chunk metadata |
| created_at | TIMESTAMP | Creation timestamp |

#### 3. **chat_sessions**
Groups related chat messages together.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Session identifier (UUID) |
| title | TEXT | Session title |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last message timestamp |
| message_count | INTEGER | Number of messages |

#### 4. **chat_messages**
Stores conversation history.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| session_id | TEXT (FK) | References chat_sessions.id |
| role | TEXT | Message role (user/assistant) |
| content | TEXT | Message content |
| query | TEXT | User query (for user messages) |
| response | TEXT | AI response (for assistant messages) |
| citations | TEXT (JSON) | Source citations |
| sources | TEXT (JSON) | Retrieved sources |
| document_ids | TEXT (JSON) | Referenced documents |
| created_at | TIMESTAMP | Creation timestamp |

## New API Endpoints

### Chat History

#### **GET /api/chat/sessions**
List all chat sessions.

**Query Parameters:**
- `limit` (optional): Maximum sessions to return (default: 50)

**Response:**
```json
{
  "success": true,
  "sessions": [
    {
      "id": "session-uuid",
      "title": "Conversation about document X",
      "created_at": "2025-10-02T...",
      "updated_at": "2025-10-02T...",
      "message_count": 10
    }
  ]
}
```

#### **GET /api/chat/sessions/{session_id}**
Get a specific chat session.

**Response:**
```json
{
  "success": true,
  "session": {
    "id": "session-uuid",
    "title": "Conversation title",
    "created_at": "2025-10-02T...",
    "updated_at": "2025-10-02T...",
    "message_count": 10
  }
}
```

#### **GET /api/chat/sessions/{session_id}/messages**
Get all messages in a session.

**Query Parameters:**
- `limit` (optional): Maximum messages to return (default: 100)

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "messages": [
    {
      "id": 1,
      "session_id": "session-uuid",
      "role": "user",
      "content": "What are the key points?",
      "query": "What are the key points?",
      "created_at": "2025-10-02T..."
    },
    {
      "id": 2,
      "session_id": "session-uuid",
      "role": "assistant",
      "content": "The key points are...",
      "response": "The key points are...",
      "citations": [...],
      "sources": [...],
      "created_at": "2025-10-02T..."
    }
  ]
}
```

#### **DELETE /api/chat/sessions/{session_id}**
Delete a chat session and all its messages.

**Response:**
```json
{
  "success": true,
  "message": "Session deleted"
}
```

#### **GET /api/chat/search?q=query**
Search through chat messages.

**Query Parameters:**
- `q`: Search query string
- `limit` (optional): Maximum results (default: 20)

**Response:**
```json
{
  "success": true,
  "query": "search term",
  "results": [
    {
      "id": 1,
      "session_id": "session-uuid",
      "role": "user",
      "content": "Message containing search term...",
      "created_at": "2025-10-02T..."
    }
  ]
}
```

## Usage Examples

### Python Client

```python
import requests

# List all chat sessions
response = requests.get("http://localhost:8000/api/chat/sessions")
sessions = response.json()["sessions"]

# Get chat history for a session
session_id = sessions[0]["id"]
response = requests.get(f"http://localhost:8000/api/chat/sessions/{session_id}/messages")
messages = response.json()["messages"]

# Search messages
response = requests.get("http://localhost:8000/api/chat/search?q=skills")
results = response.json()["results"]
```

### JavaScript Client

```javascript
// List all chat sessions
const response = await fetch('http://localhost:8000/api/chat/sessions');
const { sessions } = await response.json();

// Get chat history
const sessionId = sessions[0].id;
const historyResponse = await fetch(`http://localhost:8000/api/chat/sessions/${sessionId}/messages`);
const { messages } = await historyResponse.json();

// Search messages
const searchResponse = await fetch('http://localhost:8000/api/chat/search?q=skills');
const { results } = await searchResponse.json();
```

## Benefits

### 1. **Persistence**
- Documents and chat history survive server restarts
- No data loss between sessions

### 2. **Conversation Context**
- Resume conversations across sessions
- Track conversation history
- Analyze query patterns

### 3. **Search & Discovery**
- Search through previous conversations
- Find relevant discussions
- Track document usage

### 4. **Analytics**
- Track document upload trends
- Monitor popular queries
- Analyze system usage

### 5. **Data Management**
- Clean up old sessions
- Export conversation history
- Backup and restore data

## Database Location

The SQLite database is stored at:
```
backend/storage/supaquery.db
```

## Backup

To backup the database:
```bash
cp backend/storage/supaquery.db backend/storage/supaquery.db.backup
```

To restore:
```bash
cp backend/storage/supaquery.db.backup backend/storage/supaquery.db
```

## Migration

The database schema is automatically created on first run. No manual migration required.

## Performance

- **Indexes** on frequently queried columns (document_id, session_id, created_at)
- **Cascading deletes** for related records
- **Connection pooling** for concurrent requests
- **Optimized queries** with proper JOINs and WHERE clauses

## Security Notes

1. Database is local to the server (no external access)
2. No sensitive data is stored in plain text
3. Session IDs use UUIDs for unpredictability
4. All timestamps are UTC

## Future Enhancements

- [ ] Add user authentication and user_id tracking
- [ ] Implement conversation tagging/categorization
- [ ] Add document sharing between sessions
- [ ] Export chat history to various formats
- [ ] Add analytics dashboard
- [ ] Implement full-text search with FTS5
