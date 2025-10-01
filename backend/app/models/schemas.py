from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    citations: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    timestamp: str


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
