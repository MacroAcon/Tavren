"""
Utilities for common database operations.
"""
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import DeclarativeBase

from app.exceptions import ResourceNotFoundException

log = logging.getLogger("app")

# Define a generic type variable for SQLAlchemy models
Model = TypeVar('Model', bound=DeclarativeBase)

async def get_by_id(
    db: AsyncSession, 
    model: Type[Model], 
    id_value: Union[int, str], 
    column_name: str = "id"
) -> Optional[Model]:
    """
    Get a record by its ID.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        id_value: ID value to look up
        column_name: Column name to use for ID lookup (default: "id")
        
    Returns:
        Instance of the model or None if not found
    """
    query = select(model).filter(getattr(model, column_name) == id_value)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_by_id_or_404(
    db: AsyncSession, 
    model: Type[Model], 
    id_value: Union[int, str], 
    column_name: str = "id",
    error_message: Optional[str] = None
) -> Model:
    """
    Get a record by its ID or raise a 404 exception.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        id_value: ID value to look up
        column_name: Column name to use for ID lookup (default: "id")
        error_message: Custom error message, or None to use a default
        
    Returns:
        Instance of the model
        
    Raises:
        ResourceNotFoundException: If the record is not found
    """
    item = await get_by_id(db, model, id_value, column_name)
    
    if item is None:
        msg = error_message or f"{model.__name__} with {column_name}={id_value} not found"
        log.warning(f"Resource not found: {msg}")
        raise ResourceNotFoundException(msg)
        
    return item

async def safe_commit(
    db: AsyncSession,
    callback: Optional[Callable] = None
) -> None:
    """
    Safely commit changes to the database with error handling.
    
    Args:
        db: Database session
        callback: Optional callback function to execute after successful commit
        
    Raises:
        Exception: Reraises any exception that occurs during commit
    """
    try:
        await db.commit()
        if callback:
            await callback()
    except Exception as e:
        await db.rollback()
        log.error(f"Database commit failed: {str(e)}", exc_info=True)
        raise

async def count_rows(
    db: AsyncSession,
    model: Type[Model],
    filters: Optional[List] = None
) -> int:
    """
    Count rows in a table with optional filters.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        filters: Optional list of filter conditions
        
    Returns:
        Number of rows matching the filters
    """
    query = select(func.count()).select_from(model)
    if filters:
        query = query.filter(*filters)
        
    result = await db.execute(query)
    return result.scalar_one() or 0

async def create_item(
    db: AsyncSession,
    model: Type[Model],
    data: Dict[str, Any]
) -> Model:
    """
    Create a new database item.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        data: Dictionary of item data
        
    Returns:
        The created model instance
    """
    item = model(**data)
    db.add(item)
    await safe_commit(db)
    await db.refresh(item)
    return item 