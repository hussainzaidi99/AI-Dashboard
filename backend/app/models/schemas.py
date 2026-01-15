#backend/app/models/schemas.py

"""
Pydantic Schemas
Request and response models for API validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema"""
    email: str
    full_name: str
    role: str = "user"

class UserCreate(UserBase):
    """User creation schema"""
    password: str

class UserResponse(UserBase):
    """User response schema"""
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class Token(BaseModel):
    """Token schema"""
    access_token: str
    token_type: str = "bearer"
    user: Optional[Dict[str, Any]] = None

class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: Optional[str] = None

class GoogleLoginRequest(BaseModel):
    """Request model for Google login"""
    token: str


# ==================== File Upload Schemas ====================

class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    file_id: str
    filename: str
    file_size: int
    file_type: str
    status: str
    message: str
    uploaded_at: Optional[datetime] = None


class FileInfo(BaseModel):
    """File information model"""
    file_id: str
    filename: str
    file_size: int
    file_type: str
    status: str
    uploaded_at: datetime


# ==================== Processing Schemas ====================

class ProcessingStatus(BaseModel):
    """Processing status model"""
    file_id: str
    status: str  # uploaded, processing, completed, failed
    progress: int = Field(ge=0, le=100)
    dataframes_count: Optional[int] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class ProcessingResultResponse(BaseModel):
    """Processing result model"""
    file_id: str
    filename: str
    file_type: str
    success: bool
    dataframes_count: int
    total_rows: int
    total_columns: int
    processing_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


# ==================== Data Schemas ====================

class DataFrameInfo(BaseModel):
    """DataFrame information"""
    sheet_name: str
    rows: int
    columns: int
    column_names: List[str]
    dtypes: Dict[str, str]


class DataResponse(BaseModel):
    """Data retrieval response"""
    file_id: str
    sheet_name: str
    total_rows: int
    total_columns: int
    columns: List[str]
    data: List[Dict[str, Any]]
    showing_rows: int


# ==================== Profile Schemas ====================

class ColumnProfile(BaseModel):
    """Column profile information"""
    dtype: str
    inferred_type: str
    count: int
    missing: int
    missing_percent: float
    unique: int
    unique_percent: float
    stats: Dict[str, Any]
    sample_values: List[str]
    most_common: List[List[Any]] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DataProfileResponse(BaseModel):
    """Data profile response"""
    file_id: str
    sheet_index: int
    total_rows: int
    total_columns: int
    memory_usage: float
    type_distribution: Dict[str, int]
    columns: Dict[str, ColumnProfile] = Field(default_factory=dict)
    correlations: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


# ==================== Quality Schemas ====================

class QualityIssue(BaseModel):
    """Quality issue model"""
    category: str
    severity: str
    column: Optional[str]
    description: str
    affected_rows: int
    affected_percentage: float
    recommendation: str


class QualityReportResponse(BaseModel):
    """Quality report response"""
    file_id: str
    sheet_index: int
    overall_score: float
    scores: Dict[str, float]
    issues: List[QualityIssue] = Field(default_factory=list)
    issues_by_severity: Dict[str, int] = Field(default_factory=dict)
    missing_data: Dict[str, float] = Field(default_factory=dict)
    duplicate_rows: int
    duplicate_percentage: float
    checked_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Chart Schemas ====================

class ChartRequest(BaseModel):
    """Chart creation request"""
    file_id: str
    sheet_index: int = 0
    chart_type: str
    x: Optional[str] = None
    y: Optional[Union[str, List[str]]] = None
    color: Optional[str] = None
    size: Optional[str] = None
    title: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class ChartResponse(BaseModel):
    """Chart creation response"""
    file_id: str
    chart_type: str
    chart: Dict[str, Any] = Field(default_factory=dict)
    message: str


class ChartRecommendation(BaseModel):
    """Chart recommendation model"""
    chart_type: str
    confidence: float
    reasoning: str
    columns_required: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


# ==================== AI Schemas ====================

class InsightItem(BaseModel):
    """Single insight item"""
    category: str
    severity: str
    title: str
    description: str
    affected_columns: List[str] = Field(default_factory=list)
    numerical_evidence: Dict[str, Any] = Field(default_factory=dict)
    recommendation: Optional[str]


class InsightResponse(BaseModel):
    """Insight generation response"""
    file_id: str
    sheet_index: int
    insights: List[InsightItem]
    summary: str
    total_insights: int


class QueryParseResult(BaseModel):
    """Natural language query parse result"""
    intent: str
    chart_type: Optional[str]
    columns: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    aggregations: Dict[str, str] = Field(default_factory=dict)
    groupby: Optional[str]
    sort_by: Optional[str]
    limit: Optional[int]
    confidence: float


class QueryResponse(BaseModel):
    """Query parsing response"""
    file_id: str
    query: str
    parsed: QueryParseResult
    message: str


# ==================== Dashboard Schemas ====================

class VizWidgetSchema(BaseModel):
    """Dashboard widget model"""
    id: str
    chart_type: str
    title: str
    description: Optional[str] = None
    chart: Dict[str, Any] = Field(default_factory=dict)


class VizDashboardResponse(BaseModel):
    """Dashboard creation response"""
    dashboard_id: str
    title: str
    description: Optional[str] = None
    widget_count: int
    widgets: List[VizWidgetSchema] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Export Schemas ====================

class ExportRequest(BaseModel):
    """Generic export request"""
    format: str
    filename: Optional[str] = None


class ExportChartRequest(ExportRequest):
    """Chart export request"""
    chart_json: Dict[str, Any]
    width: Optional[int] = None
    height: Optional[int] = None


class ExportDataRequest(ExportRequest):
    """Data export request"""
    file_id: str
    sheet_index: int = 0


class ExportDashboardRequest(ExportRequest):
    """Dashboard export request"""
    dashboard_json: Dict[str, Any]


# ==================== Statistics Schemas ====================

class DistributionTest(BaseModel):
    """Distribution test result"""
    test_name: str
    statistic: float
    p_value: float
    is_normal: bool
    conclusion: str


class CorrelationAnalysis(BaseModel):
    """Correlation analysis result"""
    method: str
    matrix: Dict[str, Any] = Field(default_factory=dict)
    significant_pairs: List[tuple] = Field(default_factory=list)


class OutlierAnalysis(BaseModel):
    """Outlier analysis result"""
    method: str
    outlier_counts: Dict[str, int] = Field(default_factory=dict)
    outlier_percentages: Dict[str, float] = Field(default_factory=dict)


class StatisticsResponse(BaseModel):
    """Statistical analysis response"""
    file_id: str
    sheet_index: int
    distribution_tests: Dict[str, DistributionTest]
    correlation_analysis: Optional[CorrelationAnalysis]
    outlier_analysis: Optional[OutlierAnalysis]
    variance_tests: Dict[str, Any]
    summary_stats: Dict[str, Any]
    warnings: List[str]