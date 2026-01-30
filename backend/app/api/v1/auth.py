from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.mongodb_models import User, generate_uuid
from app.models.schemas import (
    UserCreate, UserResponse, Token, GoogleLoginRequest,
    EmailVerificationRequest, ResendVerificationRequest, MessageResponse,
    PasswordResetSendRequest, PasswordResetVerifyRequest, PasswordResetConfirmRequest
)
from app.services.email_service import EmailService
from typing import Any
from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=MessageResponse)
async def register(user_in: UserCreate) -> Any:
    """
    Register a new user and send email verification code.
    If user exists but is not verified, resend verification code.
    """
    # Check if user already exists
    user = await User.find_one(User.email == user_in.email)
    
    if user:
        # If user exists and is already verified, return error
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists in the system.",
            )
        
        # User exists but not verified - resend verification code
        logger.info(f"User {user.email} exists but not verified. Resending verification code.")
        
        # Update user details if they changed
        user.full_name = user_in.full_name
        user.hashed_password = get_password_hash(user_in.password)
        await user.save()
        
        # Send new verification email
        email_sent = await EmailService.send_verification_email(
            email=user.email,
            username=user.full_name,
            user_id=user.user_id
        )
        
        if not email_sent:
            logger.error(f"Failed to send verification email to {user.email}")
        
        return {
            "message": "Registration successful! Please check your email for a verification code.",
            "success": True
        }
    
    # Create new user (not verified yet)
    user_obj = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_verified=False
    )
    await user_obj.insert()
    
    # Send verification email
    email_sent = await EmailService.send_verification_email(
        email=user_obj.email,
        username=user_obj.full_name,
        user_id=user_obj.user_id
    )
    
    if not email_sent:
        # Still return success but log the error
        logger.error(f"Failed to send verification email to {user_obj.email}")
    
    return {
        "message": "Registration successful! Please check your email for a verification code.",
        "success": True
    }

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
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email first. Check your inbox for the verification code."
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
            # Google users are auto-verified since Google verified their email
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(generate_uuid()), # Random password
                role="user",
                is_verified=True  # Google OAuth users are pre-verified
            )
            await user.insert()
            
            # Grant initial free credits
            from app.core.billing import BillingService
            await BillingService.grant_initial_credits(user.user_id)
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


# ==================== Email Verification Endpoints ====================

@router.post("/verify-email", response_model=Token)
async def verify_email(request: EmailVerificationRequest) -> Any:
    """
    Verify email with code and complete registration
    """
    # Verify the code
    result = await EmailService.verify_code(
        email=request.email,
        code=request.code,
        code_type="email_verification"
    )
    
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Invalid verification code")
        )
    
    # Update user as verified
    user = await User.find_one(User.email == request.email.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    await user.save()
    
    # Grant initial free credits
    from app.core.billing import BillingService
    await BillingService.grant_initial_credits(user.user_id)
    
    # Return access token (auto-login after verification)
    return {
        "access_token": create_access_token(user.user_id),
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(request: ResendVerificationRequest) -> Any:
    """
    Resend verification code (public endpoint, no auth required)
    """
    # Get user
    user = await User.find_one(User.email == request.email.lower())
    
    if not user:
        # Security: Don't reveal if email exists
        return {
            "message": "If your email is registered and not verified, a new code has been sent.",
            "success": True
        }
    
    if user.is_verified:
        return {
            "message": "Email already verified. You can login now.",
            "success": True
        }
    
    # Send new verification email
    email_sent = await EmailService.send_verification_email(
        email=user.email,
        username=user.full_name,
        user_id=user.user_id
    )
    
    if not email_sent:
        import logging
        logging.error(f"Failed to resend verification email to {user.email}")
    
    return {
        "message": "Verification code sent to your email.",
        "success": True
    }


# ==================== Password Reset Endpoints ====================

@router.post("/password-reset/send-code", response_model=MessageResponse)
async def password_reset_send_code(request: PasswordResetSendRequest) -> Any:
    """
    Send password reset code (public endpoint)
    """
    # Get user
    user = await User.find_one(User.email == request.email.lower())
    
    if not user:
        # Security: Don't reveal if email exists
        return {
            "message": "If your email is registered, a password reset code has been sent.",
            "success": True
        }
    
    # Send password reset email
    email_sent = await EmailService.send_password_reset_email(
        email=user.email,
        username=user.full_name,
        user_id=user.user_id
    )
    
    if not email_sent:
        import logging
        logging.error(f"Failed to send password reset email to {user.email}")
    
    return {
        "message": "Password reset code sent to your email.",
        "success": True
    }


@router.post("/password-reset/verify-code", response_model=MessageResponse)
async def password_reset_verify_code(request: PasswordResetVerifyRequest) -> Any:
    """
    Verify password reset code (doesn't reset password yet)
    """
    # Verify the code without marking it as used
    result = await EmailService.verify_code(
        email=request.email,
        code=request.code,
        code_type="password_reset",
        mark_as_used=False  # Don't mark as used yet, will be marked in confirm step
    )
    
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Invalid or expired code")
        )
    
    return {
        "message": "Code verified successfully. You can now reset your password.",
        "success": True
    }


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def password_reset_confirm(request: PasswordResetConfirmRequest) -> Any:
    """
    Confirm password reset with code and new password
    """
    # Verify the code again
    result = await EmailService.verify_code(
        email=request.email,
        code=request.code,
        code_type="password_reset"
    )
    
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Invalid or expired code")
        )
    
    # Update user password
    user = await User.find_one(User.email == request.email.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.hashed_password = get_password_hash(request.new_password)
    await user.save()
    
    return {
        "message": "Password reset successfully. You can now login with your new password.",
        "success": True
    }
