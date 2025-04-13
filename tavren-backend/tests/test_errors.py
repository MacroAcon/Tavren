"""
Unit tests for error handling utilities.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.errors.handlers import (
    handle_custom_exception,
    handle_validation_exception,
    get_exception_handlers
)
from app.exceptions.custom_exceptions import (
    ResourceNotFoundException,
    InsufficientBalanceError,
    InvalidStatusTransitionError,
    BelowMinimumThresholdError,
    PayoutProcessingError
)
from app.constants.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    STATUS_ERROR
)


class TestErrorHandlers:
    """Tests for error handling utilities."""
    
    @pytest.mark.asyncio
    @patch("app.errors.handlers.log")
    async def test_handle_custom_exception_resource_not_found(self, mock_log):
        """Test handling ResourceNotFoundException."""
        # Setup
        mock_request = MagicMock(spec=Request)
        exception = ResourceNotFoundException("User with id=123 not found")
        
        # Execute
        response = await handle_custom_exception(mock_request, exception)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == HTTP_404_NOT_FOUND
        
        content = response.body.decode()
        assert "ResourceNotFoundException" in content
        assert "User with id=123 not found" in content
        assert f'"{STATUS_ERROR}"' in content
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.errors.handlers.log")
    async def test_handle_custom_exception_insufficient_balance(self, mock_log):
        """Test handling InsufficientBalanceError."""
        # Setup
        mock_request = MagicMock(spec=Request)
        exception = InsufficientBalanceError("Wallet has insufficient balance")
        
        # Execute
        response = await handle_custom_exception(mock_request, exception)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == HTTP_400_BAD_REQUEST
        
        content = response.body.decode()
        assert "InsufficientBalanceError" in content
        assert "Wallet has insufficient balance" in content
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.errors.handlers.log")
    async def test_handle_custom_exception_database_error(self, mock_log):
        """Test handling SQLAlchemyError."""
        # Setup
        mock_request = MagicMock(spec=Request)
        exception = SQLAlchemyError("Database connection error")
        
        # Execute
        response = await handle_custom_exception(mock_request, exception)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        
        content = response.body.decode()
        assert "SQLAlchemyError" in content
        assert "Database connection error" in content
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.errors.handlers.log")
    async def test_handle_custom_exception_unknown_exception(self, mock_log):
        """Test handling an unknown exception type."""
        # Setup
        mock_request = MagicMock(spec=Request)
        exception = KeyError("Unknown key")
        
        # Execute
        response = await handle_custom_exception(mock_request, exception)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        
        content = response.body.decode()
        assert "KeyError" in content
        assert "Unknown key" in content
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.errors.handlers.log")
    async def test_handle_custom_exception_empty_message(self, mock_log):
        """Test handling an exception with an empty message."""
        # Setup
        mock_request = MagicMock(spec=Request)
        exception = ResourceNotFoundException("")
        
        # Execute
        response = await handle_custom_exception(mock_request, exception)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == HTTP_404_NOT_FOUND
        
        content = response.body.decode()
        assert "ResourceNotFoundException" in content
        assert "The requested resource was not found" in content
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.errors.handlers.log")
    async def test_handle_validation_exception(self, mock_log):
        """Test handling validation exception."""
        # Setup
        mock_request = MagicMock(spec=Request)
        
        # Create a validation error
        validation_errors = [
            {
                "loc": ("body", "username"),
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        exception = RequestValidationError(errors=validation_errors)
        
        # Execute
        response = await handle_validation_exception(mock_request, exception)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        
        content = response.body.decode()
        assert f'"{STATUS_ERROR}"' in content
        assert "Validation error" in content
        assert "username" in content
        assert "field required" in content
        
        # Verify logging
        mock_log.warning.assert_called_once()
    
    def test_get_exception_handlers(self):
        """Test getting all exception handlers."""
        # Execute
        handlers = get_exception_handlers()
        
        # Assert
        # Check that all expected exception types are covered
        assert ResourceNotFoundException in handlers
        assert InsufficientBalanceError in handlers
        assert InvalidStatusTransitionError in handlers
        assert BelowMinimumThresholdError in handlers
        assert PayoutProcessingError in handlers
        assert SQLAlchemyError in handlers
        assert RequestValidationError in handlers
        
        # Verify handler functions
        assert handlers[ResourceNotFoundException] == handle_custom_exception
        assert handlers[RequestValidationError] == handle_validation_exception 