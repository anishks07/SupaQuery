"""
Authentication and authorization module
"""
from .auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    authenticate_user,
)
from .rbac import (
    require_permission,
    require_role,
    check_document_access,
    check_chat_session_access,
    require_documents_read,
    require_documents_create,
    require_documents_update,
    require_documents_delete,
    require_chat_access,
    require_admin_role,
    require_user_management,
)
from .schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    TokenResponse,
    RoleCreate,
    RoleResponse,
    RoleAssignment,
    PermissionCreate,
    PermissionResponse,
    PermissionAssignment,
    DocumentShare,
)

__all__ = [
    # Auth functions
    'get_password_hash',
    'verify_password',
    'create_access_token',
    'decode_access_token',
    'get_current_user',
    'get_current_active_user',
    'get_current_superuser',
    'authenticate_user',
    # RBAC functions
    'require_permission',
    'require_role',
    'check_document_access',
    'check_chat_session_access',
    'require_documents_read',
    'require_documents_create',
    'require_documents_update',
    'require_documents_delete',
    'require_chat_access',
    'require_admin_role',
    'require_user_management',
    # Schemas
    'UserCreate',
    'UserUpdate',
    'UserResponse',
    'UserLogin',
    'TokenResponse',
    'RoleCreate',
    'RoleResponse',
    'RoleAssignment',
    'PermissionCreate',
    'PermissionResponse',
    'PermissionAssignment',
    'DocumentShare',
]
