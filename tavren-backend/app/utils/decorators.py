"""
Utility decorators for common patterns in the application.
"""
import logging
import functools
import time
import inspect
from typing import Callable, Any, Dict, Optional, TypeVar, cast
import traceback

from app.logging.log_utils import log_exception, log_event

log = logging.getLogger("app")

F = TypeVar('F', bound=Callable[..., Any])

def log_function_call(func: F) -> F:
    """
    Decorator to log function entry and exit with timing information.
    Works for both async and sync functions.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Extract function metadata
        module_name = func.__module__
        func_name = func.__qualname__
        full_name = f"{module_name}.{func_name}"
        
        # Log entry
        log.debug(f"Entering {full_name}")
        start_time = time.time()
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Log exit
            elapsed_time = (time.time() - start_time) * 1000
            log.debug(f"Exiting {full_name} - completed in {elapsed_time:.2f}ms")
            
            return result
        except Exception as e:
            # Log exception
            elapsed_time = (time.time() - start_time) * 1000
            log.error(f"Exception in {full_name} after {elapsed_time:.2f}ms: {str(e)}")
            raise
            
    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Extract function metadata
        module_name = func.__module__
        func_name = func.__qualname__
        full_name = f"{module_name}.{func_name}"
        
        # Log entry
        log.debug(f"Entering {full_name}")
        start_time = time.time()
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log exit
            elapsed_time = (time.time() - start_time) * 1000
            log.debug(f"Exiting {full_name} - completed in {elapsed_time:.2f}ms")
            
            return result
        except Exception as e:
            # Log exception
            elapsed_time = (time.time() - start_time) * 1000
            log.error(f"Exception in {full_name} after {elapsed_time:.2f}ms: {str(e)}")
            raise
    
    # Determine if function is async or sync
    if inspect.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    else:
        return cast(F, sync_wrapper)

def handle_exceptions(
    error_message: Optional[str] = None, 
    default_return: Any = None,
    log_traceback: bool = True,
    reraise: bool = False
) -> Callable[[F], F]:
    """
    Decorator to handle exceptions in functions.
    Works for both async and sync functions.
    
    Args:
        error_message: Optional custom error message
        default_return: Optional default return value if exception occurs and reraise is False
        log_traceback: Whether to log the traceback
        reraise: Whether to reraise the exception or return the default value
        
    Returns:
        A decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Determine function name for logging
                func_name = func.__qualname__
                msg = error_message or f"Error in {func_name}: {str(e)}"
                
                # Log the exception
                log_exception(
                    e, 
                    context=func_name,
                    include_traceback=log_traceback
                )
                
                if reraise:
                    raise
                return default_return
                
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Determine function name for logging
                func_name = func.__qualname__
                msg = error_message or f"Error in {func_name}: {str(e)}"
                
                # Log the exception
                log_exception(
                    e, 
                    context=func_name,
                    include_traceback=log_traceback
                )
                
                if reraise:
                    raise
                return default_return
        
        # Determine if function is async or sync
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
            
    return decorator 