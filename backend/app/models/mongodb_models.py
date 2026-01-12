#backend/app/models/mongodb_models.py

"""
MongoDB Models
Beanie Document models for MongoDB
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from beanie import Document, Indexed, before_event, Replace, Insert, SaveChanges
from pydantic import Field
import uuid

from enum import Enum

def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())

class FileStatus(str, Enum):
    """Status for uploaded files"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatus(str, Enum):
    """Status for processing jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class FileUpload(Document):
    """Model for uploaded files"""
    file_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    file_path: str
    status: FileStatus = FileStatus.UPLOADED
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    class Settings:
        name = "file_uploads"
        indexes = ["status", "uploaded_at"]

class ProcessingJob(Document):
    """Model for file processing jobs"""
    job_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    status: JobStatus = JobStatus.PENDING
    progress: int = 0  # 0-100
    dataframes_count: int = 0
    total_rows: int = 0
    total_columns: int = 0
    processing_time: Optional[float] = None
    job_metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "processing_jobs"
        indexes = ["status", "started_at"]

class ChartData(Document):
    """Model for saved charts"""
    chart_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    chart_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    chart_json: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @before_event([Replace, SaveChanges, Insert])
    def update_timestamp(self):
        """Update updated_at timestamp on save"""
        self.updated_at = datetime.utcnow()

    class Settings:
        name = "charts"
        indexes = ["chart_type", "created_at"]

class Dashboard(Document):
    """Model for dashboards"""
    dashboard_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    title: str
    description: Optional[str] = None
    layout: Dict[str, Any] = Field(default_factory=dict)
    chart_ids: List[str] = Field(default_factory=list)  # List of ChartData.chart_id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @before_event([Replace, SaveChanges, Insert])
    def update_timestamp(self):
        """Update updated_at timestamp on save"""
        self.updated_at = datetime.utcnow()

    class Settings:
        name = "dashboards"
        indexes = ["title", "created_at"]

class DataProfile(Document):
    """Model for saved data profiles"""
    profile_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    profile_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "data_profiles"
        indexes = ["file_id", "created_at"]

class QualityReport(Document):
    """Model for saved quality reports"""
    report_id: Indexed(str, unique=True) = Field(default_factory=generate_uuid)
    file_id: Indexed(str)
    overall_score: float
    completeness_score: float
    consistency_score: float
    validity_score: float
    uniqueness_score: float
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "quality_reports"
        indexes = ["file_id", "overall_score", "created_at"]
