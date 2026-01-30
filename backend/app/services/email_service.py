#backend/app/services/email_service.py

"""
Email Service
Handles email verification codes and password reset via Resend API
"""

import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import resend
from app.config import settings

logger = logging.getLogger(__name__)

# Configure Resend API
resend.api_key = settings.RESEND_API_KEY


def generate_code() -> str:
    """Generate a random 6-digit verification code"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


async def _store_code(
    email: str,
    code: str,
    code_type: str,
    user_id: str,
    expires_in_minutes: int = 15
) -> None:
    """
    Store verification code in database
    
    Args:
        email: User's email address (lowercase)
        code: 6-digit verification code
        code_type: "email_verification" or "password_reset"
        user_id: User's MongoDB ObjectId as string
        expires_in_minutes: Code expiration time in minutes
    """
    from app.models.mongodb_models import EmailVerification
    
    # Invalidate any existing unused codes for this email and type
    existing_codes = await EmailVerification.find(
        EmailVerification.email == email.lower(),
        EmailVerification.type == code_type,
        EmailVerification.is_used == False
    ).to_list()
    
    for old_code in existing_codes:
        old_code.is_used = True
        await old_code.save()
    
    # Create new verification code
    verification = EmailVerification(
        user_id=user_id,
        email=email.lower(),
        code=code,
        type=code_type,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
    )
    await verification.insert()
    logger.info(f"Stored {code_type} code for {email}")


def _send_email_via_resend(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str
) -> Dict[str, Any]:
    """
    Send email via Resend API
    
    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    try:
        params = {
            "from": settings.FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
            "text": text_content
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Email sent successfully to {to_email}: {response}")
        return {"success": True, "response": response}
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return {"success": False, "error": str(e)}


class EmailService:
    """Service for handling email verification and password reset"""
    
    @staticmethod
    async def send_verification_email(
        email: str,
        username: str,
        user_id: str
    ) -> bool:
        """
        Send email verification code
        
        Args:
            email: User's email address
            username: User's full name
            user_id: User's MongoDB ObjectId as string
            
        Returns:
            True if email sent successfully, False otherwise
        """
        code = generate_code()
        
        # Store code in database
        await _store_code(
            email=email,
            code=code,
            code_type="email_verification",
            user_id=user_id,
            expires_in_minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES
        )
        
        # Prepare email content
        subject = "Verify Your Email - AI Dashboard"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="max-width: 600px; margin: 40px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Email Verification</h1>
                </div>
                <div style="padding: 40px;">
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Hi {username},</p>
                    <p style="font-size: 16px; color: #555; margin-bottom: 30px;">Thank you for signing up! Please use the verification code below to complete your registration:</p>
                    
                    <div style="background: #f7f7f7; border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0;">
                        <div style="font-size: 32px; font-weight: 700; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                            {code}
                        </div>
                    </div>
                    
                    <p style="font-size: 14px; color: #888; margin-top: 30px; text-align: center;">
                        This code will expire in {settings.EMAIL_VERIFICATION_EXPIRY_MINUTES} minutes.
                    </p>
                    <p style="font-size: 14px; color: #888; margin-top: 10px; text-align: center;">
                        If you didn't request this, please ignore this email.
                    </p>
                </div>
                <div style="background: #f7f7f7; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
                    <p style="font-size: 12px; color: #999; margin: 0;">AI Data Visualization Dashboard</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Email Verification
        
        Hi {username},
        
        Thank you for signing up! Please use the verification code below to complete your registration:
        
        {code}
        
        This code will expire in {settings.EMAIL_VERIFICATION_EXPIRY_MINUTES} minutes.
        
        If you didn't request this, please ignore this email.
        
        AI Data Visualization Dashboard
        """
        
        result = _send_email_via_resend(email, subject, html_content, text_content)
        return result["success"]
    
    @staticmethod
    async def send_password_reset_email(
        email: str,
        username: str,
        user_id: str
    ) -> bool:
        """
        Send password reset code
        
        Args:
            email: User's email address
            username: User's full name
            user_id: User's MongoDB ObjectId as string
            
        Returns:
            True if email sent successfully, False otherwise
        """
        code = generate_code()
        
        # Store code in database
        await _store_code(
            email=email,
            code=code,
            code_type="password_reset",
            user_id=user_id,
            expires_in_minutes=settings.PASSWORD_RESET_EXPIRY_MINUTES
        )
        
        # Prepare email content
        subject = "Reset Your Password - AI Dashboard"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div style="max-width: 600px; margin: 40px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 40px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Password Reset</h1>
                </div>
                <div style="padding: 40px;">
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Hi {username},</p>
                    <p style="font-size: 16px; color: #555; margin-bottom: 30px;">We received a request to reset your password. Use the code below to proceed:</p>
                    
                    <div style="background: #f7f7f7; border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0;">
                        <div style="font-size: 32px; font-weight: 700; color: #f5576c; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                            {code}
                        </div>
                    </div>
                    
                    <p style="font-size: 14px; color: #888; margin-top: 30px; text-align: center;">
                        This code will expire in {settings.PASSWORD_RESET_EXPIRY_MINUTES} minutes.
                    </p>
                    <p style="font-size: 14px; color: #888; margin-top: 10px; text-align: center;">
                        If you didn't request this, please ignore this email and your password will remain unchanged.
                    </p>
                </div>
                <div style="background: #f7f7f7; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
                    <p style="font-size: 12px; color: #999; margin: 0;">AI Data Visualization Dashboard</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset
        
        Hi {username},
        
        We received a request to reset your password. Use the code below to proceed:
        
        {code}
        
        This code will expire in {settings.PASSWORD_RESET_EXPIRY_MINUTES} minutes.
        
        If you didn't request this, please ignore this email and your password will remain unchanged.
        
        AI Data Visualization Dashboard
        """
        
        result = _send_email_via_resend(email, subject, html_content, text_content)
        return result["success"]
    
    @staticmethod
    async def verify_code(
        email: str,
        code: str,
        code_type: str,
        mark_as_used: bool = True
    ) -> Dict[str, Any]:
        """
        Verify a code and optionally mark it as used
        
        Args:
            email: User's email address
            code: 6-digit verification code
            code_type: "email_verification" or "password_reset"
            mark_as_used: If True, mark code as used after verification (default: True)
            
        Returns:
            Dict with 'valid' boolean and optional 'error' message
        """
        from app.models.mongodb_models import EmailVerification
        
        # Normalize code (remove any non-digits)
        code = ''.join(filter(str.isdigit, code))
        
        # Find the code
        verification = await EmailVerification.find_one(
            EmailVerification.email == email.lower(),
            EmailVerification.code == code,
            EmailVerification.type == code_type,
            EmailVerification.is_used == False
        )
        
        if not verification:
            logger.warning(f"Invalid or already used code for {email}")
            return {
                "valid": False,
                "error": "Invalid or expired code. Please check and try again."
            }
        
        # Check if expired
        now = datetime.now(timezone.utc)
        
        # Ensure expires_at is timezone-aware for comparison
        expires_at = verification.expires_at
        if expires_at.tzinfo is None:
            # If naive, assume it's UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            logger.warning(f"Expired code for {email}")
            return {
                "valid": False,
                "error": "Code has expired. Please request a new one."
            }
        
        # Check attempt limit
        if verification.attempts >= 5:
            logger.warning(f"Too many attempts for {email}")
            return {
                "valid": False,
                "error": "Too many attempts. Please request a new code."
            }
        
        # Increment attempts
        verification.attempts += 1
        
        # Optionally mark as used
        if mark_as_used:
            verification.is_used = True
            verification.verified_at = now
            logger.info(f"Code verified and marked as used for {email}")
        else:
            logger.info(f"Code verified (not marked as used) for {email}")
        
        await verification.save()
        
        return {"valid": True}
