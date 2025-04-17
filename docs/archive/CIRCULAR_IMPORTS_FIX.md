# Circular Import Resolution

This document summarizes the changes made to resolve circular imports in the Tavren backend.

## Problem Identified

The application was failing to start due to circular imports between modules, specifically:

1. Between `app.schemas.insight` and `app.utils.insight_processor`
2. Between `app.utils.consent_validator` and `app.services.consent_ledger`
3. Type annotation issues with `AsyncSession` in route handlers

## Solution Applied

### 1. Insight Module Fixes

- Added `__future__ import annotations` to both modules
- Used `TYPE_CHECKING` to avoid runtime imports
- Moved imports inside functions where needed
- Duplicated enums in `insight_processor.py` and imported them in `insight.py`
- Added string type annotations for `AsyncSession`

```python
# In app/utils/insight_processor.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
```

### 2. Consent Module Fixes

- Moved imports inside functions to avoid circular dependencies:

```python
async def check_dsr_restrictions(user_id: str) -> Tuple[bool, Dict[str, Any]]:
    # Import inside method to avoid circular imports
    from app.services.consent_ledger import ConsentLedgerService
    # ...
```

### 3. AsyncSession Type Annotation Fixes

- Used string type annotations for `AsyncSession` in function signatures:

```python
async def process_insight(
    # ...
    db: Optional["AsyncSession"] = None
) -> Dict[str, Any]:
    # ...
```

- Removed explicit type annotations in route parameters:

```python
@router.post("/message", response_model=None)
async def process_agent_message(
    message: Dict[str, Any] = Body(...),
    db = Depends(get_db),  # No explicit type annotation
    # ...
):
```

- Modified the database dependency to prevent AsyncSession from being used as a response type:

```python
def get_db() -> Callable:
    """
    Returns a dependency that provides a database session.
    Use this in FastAPI endpoints instead of referencing get_db_session directly.
    """
    return Depends(get_db_session)
```

## Verification

The primary circular imports have been resolved, as confirmed by successful execution of `test_specific_imports.py`.

There may still be some issues with FastAPI and AsyncSession type annotations, but these are separate from the circular import problems that were preventing the application from starting.

## Next Steps

1. Consider upgrading FastAPI and Pydantic to latest versions which have better support for type annotations
2. Address any Pydantic warnings regarding deprecated config keys
3. Fix the Redis URL configuration issue for rate limiting 