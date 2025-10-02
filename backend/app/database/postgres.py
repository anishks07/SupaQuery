"""
PostgreSQL database service with async SQLAlchemy
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, func, or_
from contextlib import asynccontextmanager

from .models import Base, User, Role, Permission, Document, DocumentChunk, ChatSession, ChatMessage

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost/supaquery')

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_size=20,
    max_overflow=40,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session():
    """Async context manager for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseService:
    """Async database service for PostgreSQL operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = AsyncSessionLocal
    
    async def init_db(self):
        """Initialize database tables"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close database connections"""
        await engine.dispose()
    
    # User operations
    async def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        is_superuser: bool = False
    ) -> User:
        """Create a new user"""
        async with get_db_session() as session:
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                is_superuser=is_superuser
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.username == username)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.email == email)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.roles))
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields"""
        async with get_db_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                user.updated_at = datetime.utcnow()
                await session.flush()
                await session.refresh(user)
            return user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        async with get_db_session() as session:
            result = await session.execute(delete(User).where(User.id == user_id))
            return result.rowcount > 0
    
    # Role operations
    async def create_role(self, name: str, description: Optional[str] = None) -> Role:
        """Create a new role"""
        async with get_db_session() as session:
            role = Role(name=name, description=description)
            session.add(role)
            await session.flush()
            await session.refresh(role)
            return role
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Role)
                .options(selectinload(Role.permissions))
                .where(Role.name == name)
            )
            return result.scalar_one_or_none()
    
    async def assign_role_to_user(self, user_id: int, role_name: str) -> Optional[User]:
        """Assign a role to a user and return the updated user with roles loaded"""
        async with get_db_session() as session:
            # Fetch user with roles eagerly loaded
            result = await session.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Fetch role within the same session
            role_result = await session.execute(
                select(Role).where(Role.name == role_name)
            )
            role = role_result.scalar_one_or_none()
            
            if not role:
                return None
            
            user.roles.append(role)
            await session.flush()
            await session.refresh(user)
            return user
    
    # Permission operations
    async def create_permission(
        self,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Permission:
        """Create a new permission"""
        async with get_db_session() as session:
            permission = Permission(
                resource=resource,
                action=action,
                description=description
            )
            session.add(permission)
            await session.flush()
            await session.refresh(permission)
            return permission
    
    async def assign_permission_to_role(self, role_name: str, resource: str, action: str) -> bool:
        """Assign a permission to a role"""
        async with get_db_session() as session:
            role = await self.get_role_by_name(role_name)
            if role:
                result = await session.execute(
                    select(Permission)
                    .where(Permission.resource == resource)
                    .where(Permission.action == action)
                )
                permission = result.scalar_one_or_none()
                if permission:
                    role.permissions.append(permission)
                    return True
            return False
    
    async def user_has_permission(self, user_id: int, resource: str, action: str) -> bool:
        """Check if user has a specific permission"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        if user.is_superuser:
            return True
        for role in user.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False
    
    # Document operations
    async def create_document(
        self,
        user_id: int,
        filename: str,
        original_filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        status: str = 'processed',
        total_chunks: int = 0,
        is_public: bool = False
    ) -> Document:
        """Create a new document"""
        async with get_db_session() as session:
            document = Document(
                user_id=user_id,
                filename=filename,
                original_filename=original_filename,
                file_type=file_type,
                file_size=file_size,
                file_path=file_path,
                status=status,
                total_chunks=total_chunks,
                is_public=is_public
            )
            session.add(document)
            await session.flush()
            await session.refresh(document)
            return document
    
    async def get_document(self, document_id: int, user_id: Optional[int] = None) -> Optional[Document]:
        """Get a document by ID with access check"""
        async with get_db_session() as session:
            query = select(Document).where(Document.id == document_id)
            if user_id is not None:
                # Check if user owns the document or it's shared with them or it's public
                query = query.where(
                    or_(
                        Document.user_id == user_id,
                        Document.is_public == True,
                        Document.shared_with_users.any(User.id == user_id)
                    )
                )
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def list_documents(
        self,
        user_id: Optional[int] = None,
        include_shared: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """List documents accessible to a user"""
        async with get_db_session() as session:
            query = select(Document)
            if user_id is not None:
                if include_shared:
                    # User's documents + shared with them + public
                    query = query.where(
                        or_(
                            Document.user_id == user_id,
                            Document.is_public == True,
                            Document.shared_with_users.any(User.id == user_id)
                        )
                    )
                else:
                    # Only user's documents
                    query = query.where(Document.user_id == user_id)
            query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def update_document(self, document_id: int, **kwargs) -> Optional[Document]:
        """Update document fields"""
        async with get_db_session() as session:
            result = await session.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if document:
                for key, value in kwargs.items():
                    if hasattr(document, key):
                        setattr(document, key, value)
                document.updated_at = datetime.utcnow()
                await session.flush()
                await session.refresh(document)
            return document
    
    async def delete_document(self, document_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a document (with ownership check)"""
        async with get_db_session() as session:
            query = delete(Document).where(Document.id == document_id)
            if user_id is not None:
                query = query.where(Document.user_id == user_id)
            result = await session.execute(query)
            return result.rowcount > 0
    
    async def share_document(self, document_id: int, user_id: int) -> bool:
        """Share a document with a user"""
        async with get_db_session() as session:
            document = await session.get(Document, document_id)
            user = await session.get(User, user_id)
            if document and user:
                document.shared_with_users.append(user)
                return True
            return False
    
    # Document chunk operations
    async def create_chunks(self, document_id: int, chunks: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Create multiple document chunks"""
        async with get_db_session() as session:
            chunk_objects = []
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_id=chunk_data['chunk_id'],
                    text=chunk_data['text'],
                    chunk_metadata=chunk_data.get('metadata', {})
                )
                session.add(chunk)
                chunk_objects.append(chunk)
            await session.flush()
            for chunk in chunk_objects:
                await session.refresh(chunk)
            return chunk_objects
    
    async def get_document_chunks(self, document_id: int) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        async with get_db_session() as session:
            result = await session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.created_at)
            )
            return list(result.scalars().all())
    
    # Chat session operations
    async def create_chat_session(
        self,
        session_id: str,
        user_id: int,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        async with get_db_session() as session:
            chat_session = ChatSession(
                id=session_id,
                user_id=user_id,
                title=title or "New Conversation"
            )
            session.add(chat_session)
            await session.flush()
            await session.refresh(chat_session)
            return chat_session
    
    async def get_chat_session(
        self,
        session_id: str,
        user_id: Optional[int] = None
    ) -> Optional[ChatSession]:
        """Get a chat session by ID with access check"""
        async with get_db_session() as session:
            query = select(ChatSession).where(ChatSession.id == session_id)
            if user_id is not None:
                query = query.where(ChatSession.user_id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def list_chat_sessions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatSession]:
        """List chat sessions for a user"""
        async with get_db_session() as session:
            result = await session.execute(
                select(ChatSession)
                .where(ChatSession.user_id == user_id)
                .order_by(ChatSession.updated_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def delete_chat_session(
        self,
        session_id: str,
        user_id: Optional[int] = None
    ) -> bool:
        """Delete a chat session"""
        async with get_db_session() as session:
            query = delete(ChatSession).where(ChatSession.id == session_id)
            if user_id is not None:
                query = query.where(ChatSession.user_id == user_id)
            result = await session.execute(query)
            return result.rowcount > 0
    
    # Chat message operations
    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        query: Optional[str] = None,
        response: Optional[str] = None,
        citations: Optional[List[Dict]] = None,
        sources: Optional[List[str]] = None,
        document_ids: Optional[List[int]] = None
    ) -> ChatMessage:
        """Create a new chat message"""
        async with get_db_session() as session:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                query=query,
                response=response,
                citations=citations or [],
                sources=sources or [],
                document_ids=document_ids or []
            )
            session.add(message)
            
            # Update session message count and updated_at
            chat_session = await session.get(ChatSession, session_id)
            if chat_session:
                chat_session.message_count += 1
                chat_session.updated_at = datetime.utcnow()
            
            await session.flush()
            await session.refresh(message)
            return message
    
    async def get_chat_history(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> List[ChatMessage]:
        """Get chat history for a session"""
        # First verify user has access to this session
        if user_id is not None:
            chat_session = await self.get_chat_session(session_id, user_id)
            if not chat_session:
                return []
        
        async with get_db_session() as session:
            result = await session.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def search_messages(
        self,
        user_id: int,
        query: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Search messages across all user's sessions"""
        async with get_db_session() as session:
            # Get user's session IDs
            session_result = await session.execute(
                select(ChatSession.id).where(ChatSession.user_id == user_id)
            )
            session_ids = [row[0] for row in session_result.all()]
            
            if not session_ids:
                return []
            
            # Search messages in those sessions
            result = await session.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id.in_(session_ids))
                .where(
                    or_(
                        ChatMessage.content.ilike(f'%{query}%'),
                        ChatMessage.response.ilike(f'%{query}%')
                    )
                )
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())


# Global database instance
db_service = DatabaseService()
