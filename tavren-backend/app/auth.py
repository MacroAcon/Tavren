from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from .database import get_db
from .models import User # Assuming you have a User model
from .config import settings
from .schemas import Token, TokenData, UserInDB, UserDisplay, UserCreate # Assuming UserInDB, UserDisplay, and UserCreate schemas exist

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Admin API key security
admin_api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

# --- Utility Functions --- #

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(db: AsyncSession, username: str) -> Optional[UserInDB]:
    query = select(User).filter(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user:
        # Assuming User model can be easily converted or used as UserInDB
        # You might need to adjust this based on your actual User model and UserInDB schema
        return UserInDB(**user.__dict__)
    return None

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[UserInDB]:
    user = await get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Admin API Key Validation --- #
async def validate_admin_api_key(api_key: str = Security(admin_api_key_header)) -> bool:
    """
    Validate the admin API key for protected endpoints.
    
    The API key should be set in environment variables and never hardcoded.
    For production use, consider using a more robust API key management system.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Compare with the admin API key stored in settings/environment variables
    # This key should be loaded from environment variables, not hardcoded
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return True

# --- Dependency --- #

async def get_current_user(db = Depends(get_db), token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    # You can add checks here, e.g., if the user is active
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_id(current_user: UserInDB = Depends(get_current_user)) -> str:
    """Return just the user ID from the current user for use in APIs that only need the ID."""
    return current_user.id

# --- Auth Router --- #

from fastapi import APIRouter

auth_router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(db = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/refresh", response_model=Token)
async def refresh_access_token(current_user: UserInDB = Depends(get_current_user)):
    """
    Refresh the access token for the currently authenticated user.
    
    This endpoint requires a valid, unexpired access token and returns a new token
    with an extended expiration time.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected registration endpoint that requires an admin API key
@auth_router.post("/register", response_model=UserDisplay, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, 
    db = Depends(get_db),
    is_admin: bool = Depends(validate_admin_api_key)
):
    """
    Register a new user. Protected by admin API key requirement.
    
    To use this endpoint, include the X-Admin-API-Key header with a valid admin API key.
    Example: curl -X POST -H "X-Admin-API-Key: your_admin_api_key" -d '{"username":"user", ...}' /api/auth/register
    """
    # Verify admin access (handled by the dependency)
    
    # Check if user already exists
    existing_user = await get_user(db, user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # Check if email already exists (if provided)
    if user_in.email:
        query = select(User).filter(User.email == user_in.email)
        result = await db.execute(query)
        existing_email = result.scalar_one_or_none()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    hashed_password = get_password_hash(user_in.password)
    db_user = User(username=user_in.username, email=user_in.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user 