"""
Router factory module.

Generates standardized FastAPI routers with common CRUD operations.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, get_type_hints
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import inspect
from functools import wraps

from ..database import get_db
from .crud_utils import CrudHandler, format_success_response, format_error_response

# Type variables for generic functions
T = TypeVar('T')  # SQLAlchemy model
S = TypeVar('S')  # Pydantic schema

def generate_crud_router(
    model: Type[T],
    create_schema: Type[BaseModel],
    response_schema: Type[BaseModel],
    update_schema: Optional[Type[BaseModel]] = None,
    prefix: str = "",
    tags: List[str] = None,
    auth_dependency: Optional[Callable] = None,
    db_dependency: Callable = Depends(get_db),
    custom_handlers: Optional[Dict[str, Callable]] = None,
    include_routes: Optional[List[str]] = None,
    exclude_routes: Optional[List[str]] = None,
    route_config: Optional[Dict[str, Dict[str, Any]]] = None
) -> APIRouter:
    """
    Generate a CRUD router with standard endpoints.
    
    Args:
        model: SQLAlchemy model class
        create_schema: Pydantic schema for create operations
        response_schema: Pydantic schema for responses
        update_schema: Pydantic schema for update operations (default: create_schema)
        prefix: URL prefix for all routes
        tags: List of tags for API documentation
        auth_dependency: Optional authentication dependency
        db_dependency: Database session dependency
        custom_handlers: Custom route handlers to override defaults
        include_routes: List of route types to include (e.g. ["get", "create"])
        exclude_routes: List of route types to exclude
        route_config: Additional configuration for specific routes
        
    Returns:
        Configured APIRouter
    """
    # Initialize configuration
    if tags is None:
        tags = [model.__name__.lower()]
        
    if include_routes is None:
        include_routes = ["get", "get_all", "create", "update", "delete"]
        
    if exclude_routes is None:
        exclude_routes = []
        
    if route_config is None:
        route_config = {}
        
    # Determine what routes to include
    routes_to_include = [r for r in include_routes if r not in exclude_routes]
    
    # Initialize router
    router = APIRouter(prefix=prefix, tags=tags)
    
    # Initialize CRUD handler
    crud_handler = CrudHandler(
        model=model,
        create_schema=create_schema,
        response_schema=response_schema,
        update_schema=update_schema or create_schema
    )
    
    # Helper to add auth dependency if provided
    def get_dependencies(route_name: str) -> List[Depends]:
        """Get dependencies for a specific route."""
        deps = [db_dependency]
        
        # Add auth dependency if specified
        if auth_dependency:
            # Check if this route has a specific auth dependency override
            route_auth = route_config.get(route_name, {}).get("auth_dependency", auth_dependency)
            deps.append(Depends(route_auth))
            
        return deps
    
    # Helper to add route metadata
    def add_route_metadata(route_handler: Callable, route_name: str) -> Callable:
        """Add metadata to route handler."""
        route_cfg = route_config.get(route_name, {})
        
        # Get response model if specified
        response_model = route_cfg.get("response_model", None)
        
        # Get status code if specified
        status_code = route_cfg.get("status_code", None)
        
        # Get summary and description
        summary = route_cfg.get("summary", None)
        description = route_cfg.get("description", None)
        
        # Apply metadata using decorator
        if any([response_model, status_code, summary, description]):
            @wraps(route_handler)
            async def wrapper(*args, **kwargs):
                return await route_handler(*args, **kwargs)
                
            # Set FastAPI metadata
            if response_model:
                wrapper.__annotations__["return"] = response_model
            if summary:
                wrapper.__doc__ = summary
                if description:
                    wrapper.__doc__ += f"\n\n{description}"
            
            return wrapper
            
        return route_handler
    
    # GET - Get item by ID
    if "get" in routes_to_include:
        # Use custom handler if provided, else use default
        if custom_handlers and "get" in custom_handlers:
            get_handler = custom_handlers["get"]
        else:
            async def get_handler(
                item_id: int = Path(..., description=f"The ID of the {model.__name__} to retrieve"),
                db: AsyncSession = Depends(get_db)
            ):
                """Get item by ID."""
                return await crud_handler.get(db, item_id)
        
        # Add route
        router.add_api_route(
            "/{item_id}",
            add_route_metadata(get_handler, "get"),
            methods=["GET"],
            dependencies=get_dependencies("get"),
            response_model=route_config.get("get", {}).get("response_model", None),
            status_code=route_config.get("get", {}).get("status_code", 200),
            summary=route_config.get("get", {}).get("summary", f"Get {model.__name__} by ID"),
            description=route_config.get("get", {}).get("description", f"Retrieve a {model.__name__} by its ID")
        )
    
    # GET - Get all items
    if "get_all" in routes_to_include:
        # Use custom handler if provided, else use default
        if custom_handlers and "get_all" in custom_handlers:
            get_all_handler = custom_handlers["get_all"]
        else:
            async def get_all_handler(
                skip: int = Query(0, description="Number of records to skip"),
                limit: int = Query(100, description="Maximum number of records to return"),
                db: AsyncSession = Depends(get_db)
            ):
                """Get all items with pagination."""
                query = model.__table__.select().offset(skip).limit(limit)
                result = await db.execute(query)
                items = result.fetchall()
                return format_success_response(data=items)
        
        # Add route
        router.add_api_route(
            "/",
            add_route_metadata(get_all_handler, "get_all"),
            methods=["GET"],
            dependencies=get_dependencies("get_all"),
            response_model=route_config.get("get_all", {}).get("response_model", None),
            status_code=route_config.get("get_all", {}).get("status_code", 200),
            summary=route_config.get("get_all", {}).get("summary", f"Get all {model.__name__}s"),
            description=route_config.get("get_all", {}).get("description", f"Retrieve a list of {model.__name__}s with pagination")
        )
    
    # POST - Create item
    if "create" in routes_to_include:
        # Use custom handler if provided, else use default
        if custom_handlers and "create" in custom_handlers:
            create_handler = custom_handlers["create"]
        else:
            async def create_handler(
                data: create_schema,
                db: AsyncSession = Depends(get_db)
            ):
                """Create new item."""
                return await crud_handler.create(db, data)
        
        # Add route
        router.add_api_route(
            "/",
            add_route_metadata(create_handler, "create"),
            methods=["POST"],
            dependencies=get_dependencies("create"),
            response_model=route_config.get("create", {}).get("response_model", None),
            status_code=route_config.get("create", {}).get("status_code", 201),
            summary=route_config.get("create", {}).get("summary", f"Create {model.__name__}"),
            description=route_config.get("create", {}).get("description", f"Create a new {model.__name__}")
        )
    
    # PUT - Update item
    if "update" in routes_to_include:
        # Use custom handler if provided, else use default
        if custom_handlers and "update" in custom_handlers:
            update_handler = custom_handlers["update"]
        else:
            async def update_handler(
                item_id: int = Path(..., description=f"The ID of the {model.__name__} to update"),
                data: update_schema or create_schema = None,
                db: AsyncSession = Depends(get_db)
            ):
                """Update item by ID."""
                return await crud_handler.update(db, item_id, data)
        
        # Add route
        router.add_api_route(
            "/{item_id}",
            add_route_metadata(update_handler, "update"),
            methods=["PUT"],
            dependencies=get_dependencies("update"),
            response_model=route_config.get("update", {}).get("response_model", None),
            status_code=route_config.get("update", {}).get("status_code", 200),
            summary=route_config.get("update", {}).get("summary", f"Update {model.__name__}"),
            description=route_config.get("update", {}).get("description", f"Update a {model.__name__} by its ID")
        )
    
    # DELETE - Delete item
    if "delete" in routes_to_include:
        # Use custom handler if provided, else use default
        if custom_handlers and "delete" in custom_handlers:
            delete_handler = custom_handlers["delete"]
        else:
            async def delete_handler(
                item_id: int = Path(..., description=f"The ID of the {model.__name__} to delete"),
                db: AsyncSession = Depends(get_db)
            ):
                """Delete item by ID."""
                return await crud_handler.delete(db, item_id)
        
        # Add route
        router.add_api_route(
            "/{item_id}",
            add_route_metadata(delete_handler, "delete"),
            methods=["DELETE"],
            dependencies=get_dependencies("delete"),
            response_model=route_config.get("delete", {}).get("response_model", None),
            status_code=route_config.get("delete", {}).get("status_code", 200),
            summary=route_config.get("delete", {}).get("summary", f"Delete {model.__name__}"),
            description=route_config.get("delete", {}).get("description", f"Delete a {model.__name__} by its ID")
        )
    
    # Add any additional custom routes
    if custom_handlers:
        for route_name, handler in custom_handlers.items():
            # Skip routes that we've already added
            if route_name in ["get", "get_all", "create", "update", "delete"]:
                continue
                
            # Get route configuration if available
            route_cfg = route_config.get(route_name, {})
            
            # Extract path and method from config
            path = route_cfg.get("path", "/")
            methods = route_cfg.get("methods", ["GET"])
            
            # Add route
            router.add_api_route(
                path,
                add_route_metadata(handler, route_name),
                methods=methods,
                dependencies=get_dependencies(route_name),
                response_model=route_cfg.get("response_model", None),
                status_code=route_cfg.get("status_code", 200),
                summary=route_cfg.get("summary", f"Custom {route_name} route"),
                description=route_cfg.get("description", f"Custom route for {route_name}")
            )
    
    return router 