"""
Unit tests for logging utility functions.
"""
import pytest
import json
import logging
from unittest.mock import patch, MagicMock, call

from app.logging.log_utils import (
    get_logger,
    log_api_request,
    log_exception,
    log_event
)


class TestLogUtils:
    """Tests for logging utility functions."""
    
    def test_get_logger_default_name(self):
        """Test getting a logger with default name."""
        with patch("logging.getLogger") as mock_get_logger:
            logger = get_logger()
            mock_get_logger.assert_called_once_with("app")
    
    def test_get_logger_custom_name(self):
        """Test getting a logger with custom name."""
        custom_name = "custom_logger"
        with patch("logging.getLogger") as mock_get_logger:
            logger = get_logger(name=custom_name)
            mock_get_logger.assert_called_once_with(custom_name)
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_api_request_basic(self, mock_get_logger):
        """Test logging an API request with basic information."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        endpoint = "/api/v1/users"
        method = "GET"
        log_api_request(endpoint=endpoint, method=method)
        
        # Assert
        mock_get_logger.assert_called_once()
        mock_logger.info.assert_called_once()
        # Check that the log contains the endpoint and method
        log_message = mock_logger.info.call_args[0][0]
        assert "API Request" in log_message
        assert endpoint in log_message
        assert method in log_message
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_api_request_with_params_and_user(self, mock_get_logger):
        """Test logging an API request with parameters and user ID."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        endpoint = "/api/v1/users"
        method = "POST"
        params = {"name": "Test User", "email": "test@example.com"}
        user_id = "user-123"
        log_api_request(endpoint=endpoint, method=method, params=params, user_id=user_id)
        
        # Assert
        mock_get_logger.assert_called_once()
        mock_logger.info.assert_called_once()
        # Check that the log contains the parameters and user ID
        log_message = mock_logger.info.call_args[0][0]
        assert "API Request" in log_message
        assert endpoint in log_message
        assert method in log_message
        assert "test@example.com" in log_message
        assert user_id in log_message
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_api_request_with_sensitive_data(self, mock_get_logger):
        """Test logging an API request with sensitive data that should be masked."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        endpoint = "/api/v1/auth/login"
        method = "POST"
        params = {
            "username": "testuser",
            "password": "s3cr3t",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        }
        log_api_request(endpoint=endpoint, method=method, params=params)
        
        # Assert
        mock_logger.info.assert_called_once()
        # Check that sensitive data is masked
        log_message = mock_logger.info.call_args[0][0]
        assert "s3cr3t" not in log_message
        assert "********" in log_message
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in log_message
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_exception_basic(self, mock_get_logger):
        """Test logging an exception with basic information."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        exception = ValueError("Test error message")
        log_exception(exception)
        
        # Assert
        mock_get_logger.assert_called_once()
        # Verify the error log calls
        assert mock_logger.error.call_count == 2  # One for exception, one for traceback
        # Check the first call - exception message
        first_call = mock_logger.error.call_args_list[0]
        assert "Exception" in first_call[0][0]
        assert "ValueError" in first_call[0][0]
        assert "Test error message" in first_call[0][0]
        # Check the second call - traceback
        second_call = mock_logger.error.call_args_list[1]
        assert "Traceback" in second_call[0][0]
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_exception_with_context_and_user(self, mock_get_logger):
        """Test logging an exception with context and user ID."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        exception = ValueError("Test error message")
        context = "user_validation"
        user_id = "user-456"
        log_exception(exception, context=context, user_id=user_id)
        
        # Assert
        mock_get_logger.assert_called_once()
        # Check the first call - should include context and user ID
        first_call = mock_logger.error.call_args_list[0]
        assert context in str(first_call)
        assert user_id in str(first_call)
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_exception_without_traceback(self, mock_get_logger):
        """Test logging an exception without traceback."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        exception = ValueError("Test error message")
        log_exception(exception, include_traceback=False)
        
        # Assert
        mock_get_logger.assert_called_once()
        # Verify only one error log call (no traceback)
        assert mock_logger.error.call_count == 1
        # Check the call
        call_args = mock_logger.error.call_args[0][0]
        assert "Exception" in call_args
        assert "ValueError" in call_args
        assert "Test error message" in call_args
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_event_basic(self, mock_get_logger):
        """Test logging an event with basic information."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        event_type = "user_login"
        message = "User logged in successfully"
        log_event(event_type=event_type, message=message)
        
        # Assert
        mock_get_logger.assert_called_once()
        # Verify info log call
        mock_logger.info.assert_called_once()
        # Check the call
        call_args = mock_logger.info.call_args[0][0]
        assert "Event" in call_args
        assert event_type in call_args
        assert message in call_args
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_event_with_details_and_user(self, mock_get_logger):
        """Test logging an event with details and user ID."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Execute
        event_type = "data_export"
        message = "Data export completed"
        details = {"records": 100, "format": "csv"}
        user_id = "user-789"
        log_event(event_type=event_type, message=message, details=details, user_id=user_id)
        
        # Assert
        mock_get_logger.assert_called_once()
        # Verify info log call
        mock_logger.info.assert_called_once()
        # Check the call
        call_args = mock_logger.info.call_args[0][0]
        assert event_type in call_args
        assert message in call_args
    
    @patch("app.logging.log_utils.get_logger")
    def test_log_event_with_different_levels(self, mock_get_logger):
        """Test logging events with different log levels."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        log_levels = ["debug", "info", "warning", "error", "critical"]
        
        # Execute
        for level in log_levels:
            event_type = f"test_{level}"
            message = f"Test {level} message"
            log_event(event_type=event_type, message=message, level=level)
        
        # Assert
        assert mock_get_logger.call_count == len(log_levels)
        
        # Check that each log level method was called
        for level in log_levels:
            log_method = getattr(mock_logger, level)
            log_method.assert_called_once()
            call_args = log_method.call_args[0][0]
            assert f"test_{level}" in call_args 