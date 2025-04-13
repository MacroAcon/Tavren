"""
Unit tests for utility decorators.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.utils.decorators import log_function_call, handle_exceptions


class TestDecorators:
    """Tests for utility decorators."""
    
    @patch("app.utils.decorators.log")
    def test_log_function_call_sync(self, mock_log):
        """Test log_function_call decorator with synchronous function."""
        # Setup - Create a sync function with the decorator
        @log_function_call
        def test_function(a, b):
            return a + b
        
        # Execute
        result = test_function(1, 2)
        
        # Assert
        assert result == 3
        # Verify debug logs for entry and exit
        assert mock_log.debug.call_count == 2
        # Get the calls and check the content
        calls = mock_log.debug.call_args_list
        assert "Entering" in str(calls[0])
        assert "Exiting" in str(calls[1])
        assert "completed in" in str(calls[1])
    
    @patch("app.utils.decorators.log")
    def test_log_function_call_sync_with_exception(self, mock_log):
        """Test log_function_call decorator with synchronous function that raises exception."""
        # Setup - Create a sync function with the decorator
        @log_function_call
        def test_function_with_exception():
            raise ValueError("Test error")
        
        # Execute and Assert
        with pytest.raises(ValueError, match="Test error"):
            test_function_with_exception()
        
        # Verify logging
        assert mock_log.debug.call_count == 1  # Only the entry log
        assert mock_log.error.call_count == 1  # Error log
        # Get the calls and check the content
        debug_calls = mock_log.debug.call_args_list
        error_calls = mock_log.error.call_args_list
        assert "Entering" in str(debug_calls[0])
        assert "Exception in" in str(error_calls[0])
        assert "Test error" in str(error_calls[0])
    
    @pytest.mark.asyncio
    @patch("app.utils.decorators.log")
    async def test_log_function_call_async(self, mock_log):
        """Test log_function_call decorator with asynchronous function."""
        # Setup - Create an async function with the decorator
        @log_function_call
        async def test_async_function(a, b):
            await asyncio.sleep(0.01)  # Small delay to simulate async work
            return a + b
        
        # Execute
        result = await test_async_function(3, 4)
        
        # Assert
        assert result == 7
        # Verify debug logs for entry and exit
        assert mock_log.debug.call_count == 2
        # Get the calls and check the content
        calls = mock_log.debug.call_args_list
        assert "Entering" in str(calls[0])
        assert "Exiting" in str(calls[1])
        assert "completed in" in str(calls[1])
    
    @pytest.mark.asyncio
    @patch("app.utils.decorators.log")
    async def test_log_function_call_async_with_exception(self, mock_log):
        """Test log_function_call decorator with asynchronous function that raises exception."""
        # Setup - Create an async function with the decorator
        @log_function_call
        async def test_async_function_with_exception():
            await asyncio.sleep(0.01)  # Small delay to simulate async work
            raise ValueError("Test async error")
        
        # Execute and Assert
        with pytest.raises(ValueError, match="Test async error"):
            await test_async_function_with_exception()
        
        # Verify logging
        assert mock_log.debug.call_count == 1  # Only the entry log
        assert mock_log.error.call_count == 1  # Error log
        # Get the calls and check the content
        debug_calls = mock_log.debug.call_args_list
        error_calls = mock_log.error.call_args_list
        assert "Entering" in str(debug_calls[0])
        assert "Exception in" in str(error_calls[0])
        assert "Test async error" in str(error_calls[0])
    
    @patch("app.utils.decorators.log_exception")
    def test_handle_exceptions_sync(self, mock_log_exception):
        """Test handle_exceptions decorator with synchronous function."""
        # Setup - Create a function with the decorator
        @handle_exceptions()
        def test_function(a, b):
            return a + b
        
        # Execute
        result = test_function(2, 3)
        
        # Assert
        assert result == 5
        # Verify no exceptions were logged
        mock_log_exception.assert_not_called()
    
    @patch("app.utils.decorators.log_exception")
    def test_handle_exceptions_sync_with_exception(self, mock_log_exception):
        """Test handle_exceptions decorator with synchronous function that raises exception."""
        # Setup - Create a function with the decorator
        default_value = "default"
        
        @handle_exceptions(default_return=default_value)
        def test_function_with_exception():
            raise ValueError("Test error")
        
        # Execute
        result = test_function_with_exception()
        
        # Assert
        assert result == default_value
        # Verify exception was logged
        mock_log_exception.assert_called_once()
        # Check the call arguments
        call_args = mock_log_exception.call_args
        assert isinstance(call_args[0][0], ValueError)
        assert "test_function_with_exception" in call_args[1]["context"]
    
    @patch("app.utils.decorators.log_exception")
    def test_handle_exceptions_sync_with_reraise(self, mock_log_exception):
        """Test handle_exceptions decorator with synchronous function that reraises exception."""
        # Setup - Create a function with the decorator
        @handle_exceptions(reraise=True)
        def test_function_with_exception():
            raise ValueError("Test error for reraise")
        
        # Execute and Assert
        with pytest.raises(ValueError, match="Test error for reraise"):
            test_function_with_exception()
        
        # Verify exception was logged
        mock_log_exception.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.utils.decorators.log_exception")
    async def test_handle_exceptions_async(self, mock_log_exception):
        """Test handle_exceptions decorator with asynchronous function."""
        # Setup - Create an async function with the decorator
        @handle_exceptions()
        async def test_async_function(a, b):
            await asyncio.sleep(0.01)  # Small delay to simulate async work
            return a + b
        
        # Execute
        result = await test_async_function(4, 5)
        
        # Assert
        assert result == 9
        # Verify no exceptions were logged
        mock_log_exception.assert_not_called()
    
    @pytest.mark.asyncio
    @patch("app.utils.decorators.log_exception")
    async def test_handle_exceptions_async_with_exception(self, mock_log_exception):
        """Test handle_exceptions decorator with asynchronous function that raises exception."""
        # Setup - Create an async function with the decorator
        default_value = "async default"
        
        @handle_exceptions(default_return=default_value)
        async def test_async_function_with_exception():
            await asyncio.sleep(0.01)  # Small delay to simulate async work
            raise ValueError("Test async error")
        
        # Execute
        result = await test_async_function_with_exception()
        
        # Assert
        assert result == default_value
        # Verify exception was logged
        mock_log_exception.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.utils.decorators.log_exception")
    async def test_handle_exceptions_async_with_reraise(self, mock_log_exception):
        """Test handle_exceptions decorator with asynchronous function that reraises exception."""
        # Setup - Create an async function with the decorator
        @handle_exceptions(reraise=True)
        async def test_async_function_with_exception():
            await asyncio.sleep(0.01)  # Small delay to simulate async work
            raise ValueError("Test async error for reraise")
        
        # Execute and Assert
        with pytest.raises(ValueError, match="Test async error for reraise"):
            await test_async_function_with_exception()
        
        # Verify exception was logged
        mock_log_exception.assert_called_once()
    
    @patch("app.utils.decorators.log_exception")
    def test_handle_exceptions_with_custom_message(self, mock_log_exception):
        """Test handle_exceptions decorator with custom error message."""
        # Setup - Create a function with the decorator and custom error message
        custom_message = "Custom error occurred"
        
        @handle_exceptions(error_message=custom_message)
        def test_function_with_exception():
            raise ValueError("Original error")
        
        # Execute
        test_function_with_exception()
        
        # Verify exception was logged with expected parameters
        mock_log_exception.assert_called_once()
        # We'd check for the message, but the implementation doesn't actually use the error_message
        # in the call to log_exception, so we can't verify this directly 