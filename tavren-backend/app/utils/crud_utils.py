"""
CRUD utilities module.

Combines database operations and response formatting into a single utility.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Callable
from fastapi import HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
import logging

# Type variables for generic functions
T = TypeVar('T')  # SQLAlchemy model
S = TypeVar('S')  # Pydantic schema

# Get logger
logger = logging.getLogger(__name__)

# Response formatting functions
def format_success_response(
    data: Any = None, 
    message: str = "Operation successful",
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format a standardized success response."""
    response = {
        "status": "success",
        "message": message,
        "data": data
    }
    
    if meta:
        response["meta"] = meta
        
    return response

def format_error_response(
    message: str = "An error occurred",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
    details: Optional[Any] = None
) -> Dict[str, Any]:
    """Format a standardized error response."""
    response = {
        "status": "error",
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
        
    if details:
        response["details"] = details
        
    return response

# Database operation functions
async def get_by_id(
    db: AsyncSession, 
    model: Type[T], 
    item_id: Any,
    options: Optional[List] = None
) -> Optional[T]:
    """
    Get an item by ID with optional relationship loading.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        item_id: ID of the item to retrieve
        options: List of SQLAlchemy options like selectinload()
        
    Returns:
        The item or None if not found
    """
    query = select(model).filter(model.id == item_id)
    
    if options:
        for option in options:
            query = query.options(option)
            
    result = await db.execute(query)
    return result.scalars().first()

async def get_by_id_or_404(
    db: AsyncSession, 
    model: Type[T], 
    item_id: Any,
    detail: str = "Item not found",
    options: Optional[List] = None
) -> T:
    """
    Get an item by ID or raise 404 if not found.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        item_id: ID of the item to retrieve
        detail: Error message if not found
        options: List of SQLAlchemy options like selectinload()
        
    Returns:
        The item
        
    Raises:
        HTTPException: If item not found
    """
    item = await get_by_id(db, model, item_id, options)
    
    if not item:
        logger.warning(f"{model.__name__} with id {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        
    return item

async def create_item(
    db: AsyncSession, 
    model: Type[T], 
    data: Union[Dict[str, Any], BaseModel],
    commit: bool = True
) -> T:
    """
    Create an item in the database.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        data: Data to create the item with (dict or Pydantic model)
        commit: Whether to commit immediately
        
    Returns:
        The created item
    """
    # Convert Pydantic model to dict if needed
    if isinstance(data, BaseModel):
        create_data = data.dict(exclude_unset=True)
    else:
        create_data = data
        
    # Create and add the item
    item = model(**create_data)
    db.add(item)
    
    if commit:
        try:
            await db.commit()
            await db.refresh(item)
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating {model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
            
    return item

async def update_item(
    db: AsyncSession,
    model: Type[T],
    item_id: Any,
    data: Union[Dict[str, Any], BaseModel],
    commit: bool = True,
    auto_fetch: bool = True
) -> Optional[T]:
    """
    Update an item in the database.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        item_id: ID of the item to update
        data: Data to update the item with (dict or Pydantic model)
        commit: Whether to commit immediately
        auto_fetch: Whether to fetch and return the updated item
        
    Returns:
        The updated item if auto_fetch is True, otherwise None
    """
    # Convert Pydantic model to dict if needed
    if isinstance(data, BaseModel):
        update_data = data.dict(exclude_unset=True)
    else:
        update_data = data
        
    # Create update statement
    stmt = update(model).where(model.id == item_id).values(**update_data)
    
    try:
        await db.execute(stmt)
        
        if commit:
            await db.commit()
            
        if auto_fetch:
            return await get_by_id(db, model, item_id)
            
        return None
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating {model.__name__} with id {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def delete_item(
    db: AsyncSession,
    model: Type[T],
    item_id: Any,
    commit: bool = True
) -> bool:
    """
    Delete an item from the database.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        item_id: ID of the item to delete
        commit: Whether to commit immediately
        
    Returns:
        True if item was deleted, False otherwise
    """
    stmt = delete(model).where(model.id == item_id)
    
    try:
        result = await db.execute(stmt)
        
        if commit:
            await db.commit()
            
        # Check if anything was deleted
        return result.rowcount > 0
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting {model.__name__} with id {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def count_rows(
    db: AsyncSession,
    model: Type[T],
    filters: Optional[List] = None
) -> int:
    """
    Count rows in a table with optional filters.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        filters: Optional list of filter conditions
        
    Returns:
        Count of matching rows
    """
    query = select(func.count()).select_from(model)
    
    if filters:
        for filter_condition in filters:
            query = query.filter(filter_condition)
            
    result = await db.execute(query)
    return result.scalar() or 0

# Combined CRUD handler
class CrudHandler(Generic[T, S]):
    """
    Generic CRUD handler for FastAPI endpoints.
    
    This combines database operations and response formatting.
    """
    
    def __init__(
        self,
        model: Type[T],
        create_schema: Type[S],
        response_schema: Type[S],
        update_schema: Optional[Type[S]] = None,
        db_options: Optional[List] = None
    ):
        """
        Initialize the CRUD handler.
        
        Args:
            model: SQLAlchemy model class
            create_schema: Pydantic schema for create operations
            response_schema: Pydantic schema for responses
            update_schema: Pydantic schema for update operations (defaults to create_schema)
            db_options: List of SQLAlchemy options like selectinload()
        """
        self.model = model
        self.create_schema = create_schema
        self.response_schema = response_schema
        self.update_schema = update_schema or create_schema
        self.db_options = db_options or []
        
    async def get(
        self, 
        db: AsyncSession, 
        item_id: Any,
        error_detail: str = "Item not found"
    ) -> Dict[str, Any]:
        """Get item by ID and return formatted response."""
        item = await get_by_id_or_404(
            db, self.model, item_id, 
            detail=error_detail, 
            options=self.db_options
        )
        return format_success_response(data=item)
        
    async def create(
        self,
        db: AsyncSession,
        data: S
    ) -> Dict[str, Any]:
        """Create item and return formatted response."""
        item = await create_item(db, self.model, data)
        return format_success_response(
            data=item,
            message=f"{self.model.__name__} created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
    async def update(
        self,
        db: AsyncSession,
        item_id: Any,
        data: S,
        error_detail: str = "Item not found"
    ) -> Dict[str, Any]:
        """Update item and return formatted response."""
        # Verify item exists
        await get_by_id_or_404(
            db, self.model, item_id, 
            detail=error_detail
        )
        
        # Update the item
        updated_item = await update_item(
            db, self.model, item_id, data, 
            auto_fetch=True
        )
        
        return format_success_response(
            data=updated_item,
            message=f"{self.model.__name__} updated successfully"
        )
        
    async def delete(
        self,
        db: AsyncSession,
        item_id: Any,
        error_detail: str = "Item not found"
    ) -> Dict[str, Any]:
        """Delete item and return formatted response."""
        # Verify item exists
        await get_by_id_or_404(
            db, self.model, item_id, 
            detail=error_detail
        )
        
        # Delete the item
        success = await delete_item(db, self.model, item_id)
        
        if not success:
            return format_error_response(
                message=f"Failed to delete {self.model.__name__}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        return format_success_response(
            message=f"{self.model.__name__} deleted successfully",
            data={"id": item_id}
        ) 