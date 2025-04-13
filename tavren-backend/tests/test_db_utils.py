"""
Unit tests for database utility functions.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String

from app.utils.db_utils import (
    get_by_id, 
    get_by_id_or_404, 
    safe_commit, 
    count_rows, 
    create_item
)
from app.exceptions import ResourceNotFoundException


class TestDBUtils:
    """Tests for database utility functions."""
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test getting an item by ID when it exists."""
        # Setup
        mock_model = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = MagicMock()
        
        # Execute
        result = await get_by_id(mock_db, mock_model, 1)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is not None
        assert result == mock_result.scalar_one_or_none.return_value
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test getting an item by ID when it doesn't exist."""
        # Setup
        mock_model = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = None
        
        # Execute
        result = await get_by_id(mock_db, mock_model, 1)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_id_custom_column(self):
        """Test getting an item by a custom column name."""
        # Setup
        mock_model = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = MagicMock()
        
        # Execute
        result = await get_by_id(mock_db, mock_model, "test-uuid", column_name="uuid")
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_by_id_or_404_found(self):
        """Test getting an item by ID or 404 when it exists."""
        # Setup
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = MagicMock()
        
        # Execute
        result = await get_by_id_or_404(mock_db, mock_model, 1)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_by_id_or_404_not_found(self):
        """Test getting an item by ID or 404 when it doesn't exist."""
        # Setup
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = None
        
        # Execute and Assert
        with pytest.raises(ResourceNotFoundException):
            await get_by_id_or_404(mock_db, mock_model, 1)
    
    @pytest.mark.asyncio
    async def test_get_by_id_or_404_custom_error_message(self):
        """Test getting an item by ID or 404 with custom error message."""
        # Setup
        mock_model = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = None
        custom_message = "Custom error message"
        
        # Execute and Assert
        with pytest.raises(ResourceNotFoundException) as excinfo:
            await get_by_id_or_404(mock_db, mock_model, 1, error_message=custom_message)
        
        assert str(excinfo.value) == custom_message
    
    @pytest.mark.asyncio
    async def test_safe_commit_success(self):
        """Test safe commit succeeds."""
        # Setup
        mock_db = AsyncMock(spec=AsyncSession)
        mock_callback = AsyncMock()
        
        # Execute
        await safe_commit(mock_db, mock_callback)
        
        # Assert
        mock_db.commit.assert_called_once()
        mock_callback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_safe_commit_exception(self):
        """Test safe commit with exception."""
        # Setup
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.commit.side_effect = Exception("Commit failed")
        
        # Execute and Assert
        with pytest.raises(Exception):
            await safe_commit(mock_db)
        
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_rows_no_filters(self):
        """Test counting rows without filters."""
        # Setup
        mock_model = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one.return_value = 5
        
        # Execute
        result = await count_rows(mock_db, mock_model)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_count_rows_with_filters(self):
        """Test counting rows with filters."""
        # Setup
        mock_model = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one.return_value = 3
        mock_filters = [MagicMock(), MagicMock()]
        
        # Execute
        result = await count_rows(mock_db, mock_model, mock_filters)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_count_rows_zero_results(self):
        """Test counting rows with no results."""
        # Setup
        mock_model = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one.return_value = None
        
        # Execute
        result = await count_rows(mock_db, mock_model)
        
        # Assert
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_create_item(self):
        """Test creating a new item."""
        # Setup
        mock_model = MagicMock()
        mock_model.return_value = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)
        
        item_data = {"name": "Test Item", "value": 123}
        
        # Execute
        result = await create_item(mock_db, mock_model, item_data)
        
        # Assert
        mock_model.assert_called_once_with(**item_data)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result is not None 