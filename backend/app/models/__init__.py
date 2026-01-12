#backend/app/models/__init__.py

"""
Models Module
Database models and Pydantic schemas
"""

from .mongodb_models import (
    FileUpload, 
    ProcessingJob, 
    ChartData, 
    Dashboard, 
    DataProfile, 
    QualityReport
)
from .schemas import (
    FileUploadResponse,
    ProcessingStatus,
    ChartRequest,
    ChartResponse,
    DataProfileResponse,
    QualityReportResponse,
    InsightResponse
)

__all__ = [
    # Database models
    "FileUpload",
    "ProcessingJob",
    "ChartData",
    "Dashboard",
    "DataProfile",
    "QualityReport",
    
    # Pydantic schemas
    "FileUploadResponse",
    "ProcessingStatus",
    "ChartRequest",
    "ChartResponse",
    "DataProfileResponse",
    "QualityReportResponse",
    "InsightResponse",
]