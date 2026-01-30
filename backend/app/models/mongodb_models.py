#backend/app/models/mongodb_models.py

"""
MongoDB Models
Beanie Document models for MongoDB
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from beanie import Document, Indexed, before_event, Replace, Insert, SaveChanges
from pydantic import Field, BaseModel
import uuid

from enum import Enum

logger = logging.getLogger(__name__)

def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())

class FileStatus(str, Enum):
    """Status for uploaded files"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"

class User(Document):
    """Model for users"""
    user_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    email: Indexed(str, unique=True)
    full_name: str
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False  # Email verification status
    active_balance: int = 0
    batches: List["CreditBatch"] = Field(default_factory=list)
    processed_payments: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @before_event([Replace, SaveChanges, Insert])
    def update_and_recalculate(self):
        """Update updated_at and refresh balance before save"""
        self.updated_at = datetime.now(timezone.utc)
        
        # Filter for valid, non-expired batches with remaining tokens
        # Standardize 'now' to be timezone-aware UTC
        now = datetime.now(timezone.utc)
        
        total = 0
        for b in self.batches:
            # Ensure batch expiry is also treated as UTC if naive
            expiry = b.expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
                
            if b.remaining_tokens > 0 and expiry > now:
                total += b.remaining_tokens
            else:
                logger.debug(f"Skipping batch {b.batch_id}: tokens={b.remaining_tokens}, expired={expiry <= now}")
                
        self.active_balance = total
        logger.info(f"Recalculated balance for {self.email}: {self.active_balance}")

    class Settings:
        name = "users"
        indexes = ["email", "created_at"]

class JobStatus(str, Enum):
    """Status for processing jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class FileUpload(Document):
    """Model for uploaded files"""
    file_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    user_id: Optional[Indexed(str)] = None
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    file_path: str
    status: FileStatus = FileStatus.UPLOADED
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

    class Settings:
        name = "file_uploads"
        indexes = ["status", "uploaded_at"]

class ProcessingJob(Document):
    """Model for file processing jobs"""
    job_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    user_id: Optional[Indexed(str)] = None
    status: JobStatus = JobStatus.PENDING
    progress: int = 0  # 0-100
    dataframes_count: int = 0
    total_rows: int = 0
    total_columns: int = 0
    processing_time: Optional[float] = None
    job_metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "processing_jobs"
        indexes = ["status", "started_at"]

class ChartData(Document):
    """Model for saved charts"""
    chart_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    user_id: Optional[Indexed(str)] = None
    chart_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    chart_json: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @before_event([Replace, SaveChanges, Insert])
    def update_timestamp(self):
        """Update updated_at timestamp on save"""
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "charts"
        indexes = ["chart_type", "created_at"]

class Dashboard(Document):
    """Model for dashboards"""
    dashboard_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    user_id: Optional[Indexed(str)] = None
    title: str
    description: Optional[str] = None
    layout: Dict[str, Any] = Field(default_factory=dict)
    chart_ids: List[str] = Field(default_factory=list)  # List of ChartData.chart_id
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @before_event([Replace, SaveChanges, Insert])
    def update_timestamp(self):
        """Update updated_at timestamp on save"""
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "dashboards"
        indexes = ["title", "created_at"]

class DataProfile(Document):
    """Model for saved data profiles"""
    profile_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    user_id: Optional[Indexed(str)] = None
    profile_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "data_profiles"
        indexes = ["file_id", "created_at"]

class QualityReport(Document):
    """Model for saved quality reports"""
    report_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    user_id: Optional[Indexed(str)] = None
    overall_score: float
    completeness_score: float
    consistency_score: float
    validity_score: float
    uniqueness_score: float
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "quality_reports"
        indexes = ["file_id", "overall_score", "created_at"]

# Pricing & Billing Models

class CreditBatchType(str, Enum):
    """Types of credit batches"""
    MONTHLY_FREE = "monthly_free"
    PAID_BASIC = "paid_basic"
    PAID_PREMIUM = "paid_premium"
    ADMIN_GRANT = "admin_grant"

class CreditBatch(BaseModel):
    """A specific batch of credits with its own expiry"""
    batch_id: str = Field(default_factory=generate_uuid)
    type: CreditBatchType
    amount_tokens: int
    remaining_tokens: int
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stripe_session_id: Optional[str] = None

# Removed UserCredits class as it's now merged into User model

class TokenUsage(Document):
    """Log of every AI interaction and its cost"""
    usage_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    user_id: Indexed(str)
    endpoint: str  # e.g., "insights", "chat", "query"
    model: str     # e.g., "gemini-2.0-flash"
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_estimated: float = 0.0 # Optional: compute cost at logging time
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "token_usage"
        indexes = ["user_id", "timestamp", "endpoint"]

class EmailVerification(Document):
    """Model for email verification codes"""
    verification_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    user_id: Indexed(str)
    email: Indexed(str)
    code: str  # 6-digit verification code
    type: str  # "email_verification" or "password_reset"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_used: bool = False
    attempts: int = 0
    verified_at: Optional[datetime] = None

    class Settings:
        name = "email_verifications"
        indexes = ["email", "type", "is_used", "expires_at"]
