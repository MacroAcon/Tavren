"""
Unit tests for API response utility functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.utils.response_utils import (
    format_success_response,
    format_error_response,
    handle_exception
)
from app.constants.status import (
    STATUS_SUCCESS,
    STATUS_ERROR,
    HTTP_500_INTERNAL_SERVER_ERROR,
    DETAIL_INTERNAL_SERVER_ERROR
)


class TestResponseUtils:
    """Tests for response utility functions."""
    
    def test_format_success_response_with_data_only(self):
        """Test formatting a success response with data only."""
        test_data = {"key": "value"}
        
        result = format_success_response(data=test_data)
        
        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == test_data
        assert "message" not in result
        assert "metadata" not in result
    
    def test_format_success_response_with_all_params(self):
        """Test formatting a success response with all parameters."""
        test_data = {"key": "value"}
        test_message = "Operation successful"
        test_metadata = {"total": 10, "page": 1}
        
        result = format_success_response(
            data=test_data,
            message=test_message,
            metadata=test_metadata
        )
        
        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == test_data
        assert result["message"] == test_message
        assert result["metadata"] == test_metadata
    
    def test_format_success_response_with_null_data(self):
        """Test formatting a success response with null data."""
        result = format_success_response(data=None)
        
        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is None
    
    def test_format_error_response_with_message_only(self):
        """Test formatting an error response with message only."""
        test_message = "An error occurred"
        
        result = format_error_response(message=test_message)
        
        assert result["status"] == STATUS_ERROR
        assert result["message"] == test_message
        assert "error_code" not in result
        assert "details" not in result
    
    def test_format_error_response_with_all_params(self):
        """Test formatting an error response with all parameters."""
        test_message = "An error occurred"
        test_error_code = 1001
        test_details = {"field": "username", "error": "already exists"}
        
        result = format_error_response(
            message=test_message,
            error_code=test_error_code,
            details=test_details
        )
        
        assert result["status"] == STATUS_ERROR
        assert result["message"] == test_message
        assert result["error_code"] == test_error_code
        assert result["details"] == test_details
    
    @patch("app.utils.response_utils.log")
    def test_handle_exception_with_message(self, mock_log):
        """Test handling an exception with a message."""
        test_exception = Exception("Test error message")
        
        with pytest.raises(HTTPException) as excinfo:
            handle_exception(test_exception)
        
        # Verify the exception details
        assert excinfo.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert excinfo.value.detail == "Test error message"
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @patch("app.utils.response_utils.log")
    def test_handle_exception_with_empty_message(self, mock_log):
        """Test handling an exception with an empty message."""
        test_exception = Exception("")
        
        with pytest.raises(HTTPException) as excinfo:
            handle_exception(test_exception)
        
        # Verify the exception details
        assert excinfo.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert excinfo.value.detail == DETAIL_INTERNAL_SERVER_ERROR
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @patch("app.utils.response_utils.log")
    def test_handle_exception_with_custom_status_code(self, mock_log):
        """Test handling an exception with a custom status code."""
        test_exception = Exception("Test error message")
        custom_status_code = 400
        
        with pytest.raises(HTTPException) as excinfo:
            handle_exception(test_exception, status_code=custom_status_code)
        
        # Verify the exception details
        assert excinfo.value.status_code == custom_status_code
        assert excinfo.value.detail == "Test error message"
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @patch("app.utils.response_utils.log")
    def test_handle_exception_with_custom_message(self, mock_log):
        """Test handling an exception with a custom default message."""
        test_exception = Exception("")
        custom_message = "Custom error message"
        
        with pytest.raises(HTTPException) as excinfo:
            handle_exception(test_exception, default_message=custom_message)
        
        # Verify the exception details
        assert excinfo.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert excinfo.value.detail == custom_message
        
        # Verify logging
        mock_log.error.assert_called_once()
    
    @patch("app.utils.response_utils.log")
    def test_handle_exception_with_logging_disabled(self, mock_log):
        """Test handling an exception with logging disabled."""
        test_exception = Exception("Test error message")
        
        with pytest.raises(HTTPException) as excinfo:
            handle_exception(test_exception, log_error=False)
        
        # Verify the exception details
        assert excinfo.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert excinfo.value.detail == "Test error message"
        
        # Verify logging is not called
        mock_log.error.assert_not_called() 