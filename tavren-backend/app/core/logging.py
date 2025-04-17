import logging
import sys
from typing import Optional

def setup_logging(level: Optional[int] = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Optional logging level. If not provided, uses INFO.
        
    Returns:
        Logger instance configured for the application.
    """
    if level is None:
        level = logging.INFO
        
    # Create logger
    logger = logging.getLogger("app")
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
log = setup_logging() 