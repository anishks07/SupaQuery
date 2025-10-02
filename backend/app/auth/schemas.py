"""
Pydantic schemas for authentication and user management
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    roles: List[str] = []
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


# Token schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None


# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleAssignment(BaseModel):
    user_id: int
    role_name: str


# Permission schemas
class PermissionBase(BaseModel):
    resource: str
    action: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: int
    
    class Config:
        from_attributes = True


class PermissionAssignment(BaseModel):
    role_name: str
    resource: str
    action: str


# Document sharing schema
class DocumentShare(BaseModel):
    document_id: int
    user_id: int
