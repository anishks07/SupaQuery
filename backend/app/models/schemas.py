from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[int]] = None  # Changed from str to int - frontend sends integers
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    citations: List[Dict[str, Any]]  # Enhanced with page numbers and timestamps
    sources: List[Dict[str, Any]]
    timestamp: str
    evaluation: Optional[Dict[str, Any]] = None  # Quality scores from evaluation agent
    strategy: Optional[str] = None  # Routing strategy used


class FileInfo(BaseModel):
    id: str
    name: str
    type: str
    size: int
    chunks: int
    uploaded_at: str


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    chunks: int
    embedding_model: str
    processed_at: str
