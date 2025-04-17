"""
Dependency utilities for FastAPI routes.
"""
from __future__ import annotations
from typing import Any, Callable
from fastapi import Depends, HTTPException, status

# Import models directly since it's not part of the circular dependency
from .models import User

# Reference auth functions only in function bodies to avoid circular imports
# Don't import the following at module level:
# from .auth import get_current_user, get_current_active_user

async def get_current_admin_user(current_user: Any = Depends(lambda: get_current_user())):
    """
    Dependency to get the current admin user.
    Checks if the authenticated user has admin privileges.
    
    Raises:
        HTTPException: If the user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

def get_current_user():
    """Late import to avoid circular dependency"""
    from .auth import get_current_user as auth_get_current_user
    return auth_get_current_user

def get_current_active_user():
    """Late import to avoid circular dependency"""
    from .auth import get_current_active_user as auth_get_current_active_user
    return auth_get_current_active_user 