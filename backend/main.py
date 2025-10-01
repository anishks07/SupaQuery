from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from pathlib import Path
import uuid
from datetime import datetime

from app.services.document_processor import DocumentProcessor
from app.services.graph_rag import GraphRAGService
from app.models.schemas import ChatRequest, ChatResponse, FileInfo

# Initialize FastAPI app
app = FastAPI(
    title="SupaQuery Backend",
    description="GraphRAG-powered multimodal document analysis API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
graph_rag_service = GraphRAGService()

# Ensure upload directories exist
UPLOAD_DIR = Path("uploads")
STORAGE_DIR = Path("storage")
UPLOAD_DIR.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "SupaQuery Backend",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "document_processor": "ready",
            "graph_rag": "ready",
            "vector_store": "ready"
        }
    }


@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple files (PDF, DOCX, images, audio)
    Process them and add to the knowledge graph
    """
    try:
        uploaded_files = []
        
        for file in files:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            unique_filename = f"{file_id}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Process file based on type
            try:
                file_info = await document_processor.process_file(
                    file_path=str(file_path),
                    original_filename=file.filename,
                    file_id=file_id
                )
                
                # Add to GraphRAG
                await graph_rag_service.add_document(file_info)
                
                uploaded_files.append({
                    "id": file_id,
                    "name": file.filename,
                    "type": file_info.get("type"),
                    "size": len(content),
                    "status": "processed",
                    "chunks": file_info.get("chunks", 0)
                })
                
            except Exception as e:
                print(f"Error processing {file.filename}: {str(e)}")
                uploaded_files.append({
                    "id": file_id,
                    "name": file.filename,
                    "status": "error",
                    "error": str(e)
                })
        
        return JSONResponse({
            "success": True,
            "files": uploaded_files,
            "message": f"Processed {len(uploaded_files)} files"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint - query the GraphRAG system
    """
    try:
        # Query the GraphRAG system
        response = await graph_rag_service.query(
            query=request.message,
            document_ids=request.document_ids
        )
        
        return ChatResponse(
            success=True,
            response=response["answer"],
            citations=response.get("citations", []),
            sources=response.get("sources", []),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return ChatResponse(
            success=False,
            response=f"Error processing query: {str(e)}",
            citations=[],
            sources=[],
            timestamp=datetime.now().isoformat()
        )


@app.get("/api/documents")
async def list_documents():
    """List all processed documents"""
    try:
        documents = await graph_rag_service.list_documents()
        return {
            "success": True,
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the system"""
    try:
        await graph_rag_service.delete_document(document_id)
        return {
            "success": True,
            "message": f"Document {document_id} deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
