"""
Role-Based Access Control (RBAC) middleware and decorators
"""
from typing import List, Optional
from functools import wraps
from fastapi import Depends, HTTPException, status

from .auth import get_current_user
from ..database.postgres import db_service
from ..database.models import User


async def require_permission(
    user: User,
    resource: str,
    action: str
) -> bool:
    """Check if user has a specific permission"""
    has_permission = await db_service.user_has_permission(user.id, resource, action)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {resource}:{action}"
        )
    return True


async def require_role(
    user: User,
    role_names: List[str]
) -> bool:
    """Check if user has one of the required roles"""
    user_roles = [role.name for role in user.roles]
    if not any(role in user_roles for role in role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role required: one of {', '.join(role_names)}"
        )
    return True


async def check_document_access(
    user: User,
    document_id: int,
    action: str = 'read'
) -> bool:
    """Check if user has access to a specific document"""
    # Superusers have access to everything
    if user.is_superuser:
        return True
    
    # Get the document
    document = await db_service.get_document(document_id, user.id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    # Check ownership for write/delete actions
    if action in ['update', 'delete']:
        if document.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only document owner can perform this action"
            )
    
    return True


async def check_chat_session_access(
    user: User,
    session_id: str
) -> bool:
    """Check if user has access to a specific chat session"""
    # Superusers have access to everything
    if user.is_superuser:
        return True
    
    # Get the chat session
    session = await db_service.get_chat_session(session_id, user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or access denied"
        )
    
    return True


# Dependency functions for FastAPI
async def require_documents_read(
    user: User = Depends(get_current_user)
) -> User:
    """Require permission to read documents"""
    await require_permission(user, 'documents', 'read')
    return user


async def require_documents_create(
    user: User = Depends(get_current_user)
) -> User:
    """Require permission to create documents"""
    await require_permission(user, 'documents', 'create')
    return user


async def require_documents_update(
    user: User = Depends(get_current_user)
) -> User:
    """Require permission to update documents"""
    await require_permission(user, 'documents', 'update')
    return user


async def require_documents_delete(
    user: User = Depends(get_current_user)
) -> User:
    """Require permission to delete documents"""
    await require_permission(user, 'documents', 'delete')
    return user


async def require_chat_access(
    user: User = Depends(get_current_user)
) -> User:
    """Require permission to access chat"""
    await require_permission(user, 'chat', 'read')
    return user


async def require_admin_role(
    user: User = Depends(get_current_user)
) -> User:
    """Require admin role"""
    await require_role(user, ['admin'])
    return user


async def require_user_management(
    user: User = Depends(get_current_user)
) -> User:
    """Require permission to manage users"""
    await require_permission(user, 'users', 'manage')
    return user
