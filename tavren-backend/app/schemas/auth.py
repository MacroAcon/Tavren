"""
Pydantic schemas for authentication operations.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None

class UserBase(BaseModel):
    """Base schema for users."""
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    """Schema for creating users."""
    password: str

class UserInDB(UserBase):
    """Schema for user in database."""
    id: int
    hashed_password: str
    is_active: bool

    class Config:
        orm_mode = True

class UserDisplay(UserBase):
    """Schema for displaying user info safely."""
    id: int
    is_active: bool

    class Config:
        orm_mode = True 