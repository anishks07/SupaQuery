"""
FastAPI main application with PostgreSQL and RBAC
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import asyncio
from pathlib import Path
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.services.document_processor import DocumentProcessor
from app.services.graph_rag_v2 import GraphRAGService
from app.services.graph_rag_enhanced import get_enhanced_graph_rag_service
from app.models.schemas import ChatRequest, ChatResponse, FileInfo
from app.database.postgres import db_service
from app.database.models import User
from app.auth import (
    get_current_user,
    get_current_superuser,
    authenticate_user,
    create_access_token,
    get_password_hash,
    require_documents_read,
    require_documents_create,
    require_documents_delete,
    require_chat_access,
    require_user_management,
    check_document_access,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RoleAssignment,
    DocumentShare,
)

# Initialize FastAPI app
app = FastAPI(
    title="SupaQuery Backend with RBAC",
    description="GraphRAG-powered multimodal document analysis API with PostgreSQL and Role-Based Access Control",
    version="2.0.0"
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

# Try to use enhanced GraphRAG service, fallback to original if it fails
try:
    from app.services.graph_rag_enhanced import get_enhanced_graph_rag_service
    graph_rag_service = get_enhanced_graph_rag_service()
    print("✅ Using Enhanced GraphRAG Service")
except Exception as e:
    print(f"⚠️  Enhanced GraphRAG failed to initialize: {e}")
    print("   Falling back to standard GraphRAG service")
    graph_rag_service = GraphRAGService()

# Ensure upload directories exist
UPLOAD_DIR = Path("uploads")
STORAGE_DIR = Path("storage")
UPLOAD_DIR.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting SupaQuery Backend with PostgreSQL + RBAC...")
    try:
        await db_service.init_db()
        print(f"   ✓ Database initialized")
        
        # Get document count from database
        try:
            docs = await db_service.list_documents(limit=1)
            # Get stats from graph
            stats = graph_rag_service.graph.get_stats()
            print(f"   - Documents indexed: {stats['documents']} (graph), {len(docs)} (db sample)")
        except Exception as count_error:
            print(f"   - Documents indexed: Unable to retrieve ({count_error})")
        
        print(f"   - Authentication: Enabled (JWT)")
        print(f"   - RBAC: Enabled")
    except Exception as e:
        print(f"   ✗ Database initialization error: {e}")
        print(f"   - Please ensure PostgreSQL is running and DATABASE_URL is correct")
        print(f"   - Run 'python init_db.py' to set up the database")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down SupaQuery Backend...")
    await db_service.close()


# ==================== PUBLIC ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "SupaQuery Backend",
        "version": "2.0.0",
        "features": ["GraphRAG", "PostgreSQL", "RBAC", "JWT Authentication"]
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
            "vector_store": "ready",
            "database": "ready",
            "authentication": "enabled"
        }
    }


# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if username or email already exists
        existing_user = await db_service.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = await db_service.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user (hash password in thread pool - bcrypt is blocking)
        hashed_password = await asyncio.to_thread(get_password_hash, user_data.password)
        user = await db_service.create_user(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        # Assign default 'user' role and get updated user with roles loaded
        user = await db_service.assign_role_to_user(user.id, 'user')
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign default role"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[role.name for role in user.roles]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login and get JWT token"""
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')))
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[role.name for role in user.roles]
        )
    )


# ==================== USER ENDPOINTS ====================

@app.get("/api/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        roles=[role.name for role in current_user.roles]
    )


@app.get("/api/users/me/permissions")
async def get_current_user_permissions(current_user: User = Depends(get_current_user)):
    """Get current user permissions (debug endpoint)"""
    permissions = []
    for role in current_user.roles:
        for perm in role.permissions:
            permissions.append(f"{perm.resource}:{perm.action}")
    
    return {
        "username": current_user.username,
        "roles": [role.name for role in current_user.roles],
        "permissions": permissions,
        "is_superuser": current_user.is_superuser
    }


from pydantic import BaseModel, EmailStr

class UserUpdate(BaseModel):
    """User profile update schema"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str


@app.put("/api/users/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        # Check if email is being changed and if it's already taken
        if user_update.email and user_update.email != current_user.email:
            existing_email = await db_service.get_user_by_email(user_update.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user
        updated_user = await db_service.update_user(
            user_id=current_user.id,
            full_name=user_update.full_name,
            email=user_update.email
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            is_active=updated_user.is_active,
            is_superuser=updated_user.is_superuser,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            roles=[role.name for role in updated_user.roles]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@app.post("/api/users/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change current user password"""
    try:
        # Verify current password
        user = await authenticate_user(current_user.username, password_change.current_password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(password_change.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        if len(password_change.new_password) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be 72 characters or less"
            )
        
        # Hash new password (in thread pool - bcrypt is blocking)
        hashed_password = await asyncio.to_thread(get_password_hash, password_change.new_password)
        
        # Update password
        success = await db_service.update_user_password(current_user.id, hashed_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


# ==================== DOCUMENT ENDPOINTS (WITH RBAC) ====================

@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    is_public: bool = Form(False),
    current_user: User = Depends(require_documents_create)
):
    """
    Upload multiple files (PDF, DOCX, images, audio)
    Process them and add to the knowledge graph
    Requires 'documents:create' permission
    """
    print(f"📤 Upload request from user: {current_user.username} (ID: {current_user.id})")
    print(f"   Files: {[f.filename for f in files]}")
    print(f"   Public: {is_public}")
    
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
            file_size = len(content)
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Process file based on type
            try:
                file_info = await document_processor.process_file(
                    file_path=str(file_path),
                    original_filename=file.filename,
                    file_id=file_id
                )
                
                # Save to database first
                document = await db_service.create_document(
                    user_id=current_user.id,
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_type=file_info.get("type", "unknown"),
                    file_size=file_size,
                    file_path=str(file_path),
                    status="processed",
                    total_chunks=file_info.get("chunks", 0),
                    is_public=is_public
                )
                
                # Add to GraphRAG with user context
                file_info['user_id'] = current_user.id
                file_info['document_db_id'] = document.id
                await graph_rag_service.add_document(file_info)
                
                uploaded_files.append({
                    "id": document.id,
                    "file_id": file_id,
                    "name": document.original_filename,  # Use from database, not from file object
                    "type": file_info.get("type"),
                    "size": file_size,
                    "status": "processed",
                    "chunks": file_info.get("chunks", 0),
                    "is_public": is_public
                })
                
            except Exception as e:
                import traceback
                print(f"Error processing {file.filename}: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
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


@app.get("/api/documents")
async def list_documents(
    include_shared: bool = True,
    current_user: User = Depends(require_documents_read)
):
    """
    List all documents accessible to the current user
    Includes: owned documents + shared documents + public documents
    Requires 'documents:read' permission
    """
    try:
        documents = await db_service.list_documents(
            user_id=current_user.id,
            include_shared=include_shared
        )
        
        return {
            "success": True,
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.original_filename,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "total_chunks": doc.total_chunks,
                    "is_public": doc.is_public,
                    "is_owner": doc.user_id == current_user.id,
                    "created_at": doc.created_at.isoformat(),
                }
                for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(require_documents_delete)
):
    """
    Delete a document from the system
    Only the owner can delete
    Requires 'documents:delete' permission
    """
    try:
        # Check document ownership
        await check_document_access(current_user, document_id, action='delete')
        
        # Get document info before deletion (to retrieve file path)
        document = await db_service.get_document(document_id, current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        
        file_path = document.file_path
        
        # Delete from database (cascades to chunks)
        success = await db_service.delete_document(document_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        
        # Remove from GraphRAG and delete physical file
        await graph_rag_service.delete_document(str(document_id), file_path=file_path)
        
        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/{document_id}/share")
async def share_document(
    document_id: int,
    share_data: DocumentShare,
    current_user: User = Depends(get_current_user)
):
    """
    Share a document with another user
    Only the owner can share
    """
    try:
        # Check document ownership
        document = await db_service.get_document(document_id, current_user.id)
        if not document or document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only document owner can share it"
            )
        
        # Share document
        success = await db_service.share_document(document_id, share_data.user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to share document")
        
        return {
            "success": True,
            "message": f"Document shared with user {share_data.user_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CHAT ENDPOINTS (WITH RBAC) ====================

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(require_chat_access)
):
    """
    Chat endpoint - query the GraphRAG system
    Results are filtered by accessible documents
    Requires 'chat:read' permission
    """
    print(f"💬 Chat request from user: {current_user.username}")
    print(f"   Message: {request.message}")
    print(f"   Document IDs: {request.document_ids}")
    print(f"   Session ID: {request.session_id}")
    try:
        # Get or create session ID
        session_id = request.session_id if hasattr(request, 'session_id') and request.session_id else str(uuid.uuid4())
        
        # Ensure session exists for this user
        existing_session = await db_service.get_chat_session(session_id, current_user.id)
        if not existing_session:
            await db_service.create_chat_session(session_id, current_user.id)
        
        # Save user message
        await db_service.create_message(
            session_id=session_id,
            role='user',
            content=request.message,
            query=request.message,
            document_ids=request.document_ids or []
        )
        
        # Verify user has access to requested documents and get file_ids
        file_ids = None
        if request.document_ids:
            print(f"   🔍 Converting {len(request.document_ids)} database IDs to file_ids...")
            file_ids = []
            for doc_id in request.document_ids:
                try:
                    doc = await db_service.get_document(doc_id, current_user.id)
                    if not doc:
                        print(f"   ❌ Access denied to document {doc_id}")
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Access denied to document {doc_id}"
                        )
                    # Extract file_id from filename (remove extension)
                    # filename format: "35572985-490b-43e2-93fa-7aebe1e05a8d.pdf"
                    file_id = doc.filename.rsplit('.', 1)[0]
                    file_ids.append(file_id)
                    print(f"   ✓ Document {doc_id} ({doc.original_filename}) -> file_id: {file_id}")
                except Exception as e:
                    print(f"   ❌ Error getting document {doc_id}: {e}")
                    raise
        
        # Get conversation history for context-aware multi-query generation
        conversation_history = []
        if existing_session:
            recent_messages = await db_service.get_chat_history(session_id, current_user.id, limit=5)
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in recent_messages
            ]
        
        # Query the GraphRAG system (enhanced or standard)
        # Use file_ids instead of document_ids for Memgraph queries
        # Try with conversation_history first (enhanced service), fallback without it (standard service)
        try:
            response = await graph_rag_service.query(
                query=request.message,
                document_ids=file_ids,  # Pass file_ids, not database IDs
                conversation_history=conversation_history
            )
        except TypeError:
            # Fallback for services that don't support conversation_history
            response = await graph_rag_service.query(
                query=request.message,
                document_ids=file_ids  # Pass file_ids, not database IDs
            )
        
        # Debug: Log response structure
        print(f"   Response keys: {response.keys()}")
        print(f"   Answer length: {len(response.get('answer', ''))}")
        print(f"   Citations count: {len(response.get('citations', []))}")
        print(f"   Sources count: {len(response.get('sources', []))}")
        
        # Save assistant response
        await db_service.create_message(
            session_id=session_id,
            role='assistant',
            content=response["answer"],
            response=response["answer"],
            citations=response.get("citations", []),
            sources=response.get("sources", []),
            document_ids=request.document_ids or []
        )
        
        # Build response carefully, ensuring all fields are properly formatted
        try:
            chat_response = ChatResponse(
                success=True,
                response=str(response.get("answer", "")),
                citations=response.get("citations", []),
                sources=response.get("sources", []),
                timestamp=datetime.now().isoformat(),
                evaluation=response.get("evaluation"),
                strategy=response.get("strategy")
            )
            
            print(f"   ✓ Chat response created successfully")
            return chat_response
        except Exception as validation_error:
            print(f"   ❌ Response validation error: {validation_error}")
            print(f"   Response data: {response}")
            raise
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return ChatResponse(
            success=False,
            response=f"Error processing query: {str(e)}",
            citations=[],
            sources=[],
            timestamp=datetime.now().isoformat()
        )


@app.get("/api/chat/sessions")
async def list_chat_sessions(
    limit: int = 50,
    current_user: User = Depends(require_chat_access)
):
    """List all chat sessions for the current user"""
    try:
        sessions = await db_service.list_chat_sessions(current_user.id, limit=limit)
        return {
            "success": True,
            "sessions": [
                {
                    "id": session.id,
                    "title": session.title,
                    "message_count": session.message_count,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                }
                for session in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(require_chat_access)
):
    """Get a specific chat session (only if owned by current user)"""
    try:
        session = await db_service.get_chat_session(session_id, current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "session": {
                "id": session.id,
                "title": session.title,
                "message_count": session.message_count,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/sessions/{session_id}/messages")
async def get_chat_history(
    session_id: str,
    limit: int = 100,
    current_user: User = Depends(require_chat_access)
):
    """Get chat history for a session (only if owned by current user)"""
    try:
        messages = await db_service.get_chat_history(session_id, current_user.id, limit)
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "citations": msg.citations,
                    "sources": msg.sources,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(require_chat_access)
):
    """Delete a chat session and its messages (only if owned by current user)"""
    try:
        success = await db_service.delete_chat_session(session_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "message": f"Session {session_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/search")
async def search_messages(
    q: str,
    limit: int = 20,
    current_user: User = Depends(require_chat_access)
):
    """Search through chat messages (only user's own messages)"""
    try:
        messages = await db_service.search_messages(current_user.id, q, limit)
        
        return {
            "success": True,
            "query": q,
            "results": [
                {
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADMIN ENDPOINTS ====================

@app.get("/api/admin/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_user_management)
):
    """List all users (admin only)"""
    try:
        users = await db_service.list_users(skip, limit)
        return {
            "success": True,
            "users": [
                UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    is_active=user.is_active,
                    is_superuser=user.is_superuser,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    roles=[role.name for role in user.roles]
                )
                for user in users
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/users/{user_id}/roles")
async def assign_role(
    user_id: int,
    role_data: RoleAssignment,
    admin_user: User = Depends(require_user_management)
):
    """Assign a role to a user (admin only)"""
    try:
        success = await db_service.assign_role_to_user(user_id, role_data.role_name)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign role")
        
        return {
            "success": True,
            "message": f"Role '{role_data.role_name}' assigned to user {user_id}"
        }
    except HTTPException:
        raise
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
