"""
Database Schema for SupaQuery
SQLite database with tables for documents, chunks, chat sessions, and messages
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json


class Database:
    def __init__(self, db_path: str = "storage/supaquery.db"):
        """Initialize database connection"""
        # Ensure storage directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Documents table - stores metadata about uploaded files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                file_path TEXT,
                status TEXT DEFAULT 'processing',
                total_chunks INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Document chunks table - stores processed text chunks with embeddings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                chunk_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE(document_id, chunk_id)
            )
        """)
        
        # Chat sessions table - groups related messages together
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        """)
        
        # Chat messages table - stores conversation history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                query TEXT,
                response TEXT,
                citations TEXT,
                sources TEXT,
                document_ids TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id 
            ON document_chunks(document_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id 
            ON chat_messages(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_created_at 
            ON chat_messages(created_at)
        """)
        
        conn.commit()
        print("✅ Database initialized successfully")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # Document operations
    
    def create_document(self, doc_data: Dict[str, Any]) -> str:
        """Create a new document record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (id, filename, original_filename, file_type, 
                                  file_size, file_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_data['id'],
            doc_data['filename'],
            doc_data['original_filename'],
            doc_data['file_type'],
            doc_data.get('file_size'),
            doc_data.get('file_path'),
            doc_data.get('status', 'processing')
        ))
        
        conn.commit()
        return doc_data['id']
    
    def update_document(self, doc_id: str, updates: Dict[str, Any]):
        """Update document metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        values = list(updates.values()) + [doc_id]
        
        cursor.execute(f"""
            UPDATE documents 
            SET {set_clause}
            WHERE id = ?
        """, values)
        
        conn.commit()
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all documents"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_document(self, doc_id: str):
        """Delete document and associated chunks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
    
    # Chunk operations
    
    def create_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]):
        """Batch insert document chunks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for chunk in chunks:
            cursor.execute("""
                INSERT INTO document_chunks (document_id, chunk_id, text, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                doc_id,
                chunk['chunk_id'],
                chunk['text'],
                json.dumps(chunk.get('metadata', {}))
            ))
        
        # Update document chunk count
        cursor.execute("""
            UPDATE documents 
            SET total_chunks = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (len(chunks), doc_id))
        
        conn.commit()
    
    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM document_chunks 
            WHERE document_id = ? 
            ORDER BY chunk_id
        """, (doc_id,))
        
        chunks = []
        for row in cursor.fetchall():
            chunk = dict(row)
            chunk['metadata'] = json.loads(chunk['metadata']) if chunk['metadata'] else {}
            chunks.append(chunk)
        
        return chunks
    
    # Chat session operations
    
    def create_chat_session(self, session_id: str, title: Optional[str] = None) -> str:
        """Create a new chat session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO chat_sessions (id, title)
            VALUES (?, ?)
        """, (session_id, title or "New Conversation"))
        
        conn.commit()
        return session_id
    
    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get chat session by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def list_chat_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all chat sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM chat_sessions 
            ORDER BY updated_at DESC 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_chat_session(self, session_id: str):
        """Delete chat session and associated messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        conn.commit()
    
    # Chat message operations
    
    def create_message(self, message_data: Dict[str, Any]) -> int:
        """Create a new chat message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO chat_messages (session_id, role, content, query, response, 
                                      citations, sources, document_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_data['session_id'],
            message_data['role'],
            message_data['content'],
            message_data.get('query'),
            message_data.get('response'),
            json.dumps(message_data.get('citations', [])),
            json.dumps(message_data.get('sources', [])),
            json.dumps(message_data.get('document_ids', []))
        ))
        
        # Update session
        cursor.execute("""
            UPDATE chat_sessions 
            SET updated_at = CURRENT_TIMESTAMP, 
                message_count = message_count + 1
            WHERE id = ?
        """, (message_data['session_id'],))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_chat_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY created_at ASC 
            LIMIT ?
        """, (session_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            msg['citations'] = json.loads(msg['citations']) if msg['citations'] else []
            msg['sources'] = json.loads(msg['sources']) if msg['sources'] else []
            msg['document_ids'] = json.loads(msg['document_ids']) if msg['document_ids'] else []
            messages.append(msg)
        
        return messages
    
    def search_messages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search messages by content"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM chat_messages 
            WHERE content LIKE ? OR query LIKE ? OR response LIKE ?
            ORDER BY created_at DESC 
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        
        return [dict(row) for row in cursor.fetchall()]


# Global database instance
db = Database()
