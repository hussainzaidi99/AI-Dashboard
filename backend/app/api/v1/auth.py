from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.mongodb_models import User, generate_uuid
from app.models.schemas import UserCreate, UserResponse, Token, GoogleLoginRequest
from typing import Any
from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    user = await User.find_one(User.email == user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists in the system.",
        )
    
    # Create new user
    user_obj = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role
    )
    await user_obj.insert()
    return user_obj

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return {
        "access_token": create_access_token(user.user_id),
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.post("/google", response_model=Token)
async def google_login(data: GoogleLoginRequest) -> Any:
    """
    Authenticate with Google ID token.
    Verify the token, get user info, and return an access token.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Received Google login request")
        logger.info(f"Token (first 50 chars): {data.token[:50] if len(data.token) > 50 else data.token}...")
        logger.info(f"GOOGLE_CLIENT_ID configured: {settings.GOOGLE_CLIENT_ID[:20] if settings.GOOGLE_CLIENT_ID else 'NOT SET'}...")
        
        # Verify Google Token
        idinfo = id_token.verify_oauth2_token(
            data.token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )

        logger.info(f"Token verified successfully for email: {idinfo.get('email')}")
        
        # ID token is valid. Get user's Google ID and email.
        email = idinfo['email']
        full_name = idinfo.get('name', '')
        
        # Check if user already exists
        user = await User.find_one(User.email == email)
        
        if not user:
            logger.info(f"Creating new user for Google login: {email}")
            # Create new user for Google login
            # We use a random password since they use Google to log in
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(generate_uuid()), # Random password
                role="user"
            )
            await user.insert()
        elif not user.is_active:
            logger.warning(f"Inactive user attempted login: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        logger.info(f"Google authentication successful for: {email}")
        return {
            "access_token": create_access_token(user.user_id),
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
        
    except ValueError as e:
        # Invalid token
        logger.error(f"Google token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during Google auth: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

