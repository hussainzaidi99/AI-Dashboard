"""
Quality Checker - Data quality assessment and validation
Identifies data quality issues, inconsistencies, and potential problems
"""
#backend/app/core/analyzers/quality_checker.py


from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import re
import logging

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """Severity levels for data quality issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class QualityIssue:
    """Single data quality issue"""
    category: str
    severity: IssueSeverity
    column: Optional[str]
    description: str
    affected_rows: int
    affected_percentage: float
    recommendation: str


@dataclass
class QualityReport:
    """Complete data quality report"""
    overall_score: float  # 0-100
    issues: List[QualityIssue]
    completeness_score: float
    consistency_score: float
    validity_score: float
    uniqueness_score: float
    
    # Detailed metrics
    missing_data: Dict[str, float]
    duplicate_rows: int
    duplicate_percentage: float
    
    # Summary by severity
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    
    # Timestamp
    checked_at: str = field(default_factory=lambda: pd.Timestamp.now().isoformat())


class QualityChecker:
    """Comprehensive data quality assessment"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thresholds
        self.missing_threshold_critical = 50  # %
        self.missing_threshold_high = 20  # %
        self.duplicate_threshold = 5  # %
        
        # Email regex pattern
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Phone regex pattern (basic)
        self.phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]{10,}$')
    
    def check(self, df: pd.DataFrame) -> QualityReport:
        """
        Perform comprehensive quality check
        
        Args:
            df: pandas DataFrame
        
        Returns:
            QualityReport with all issues and scores
        """
        self.logger.info(f"Performing quality check on DataFrame")
        
        issues = []
        
        # 1. Check completeness (missing data)
        completeness_issues = self._check_completeness(df)
        issues.extend(completeness_issues)
        
        # 2. Check consistency
        consistency_issues = self._check_consistency(df)
        issues.extend(consistency_issues)
        
        # 3. Check validity
        validity_issues = self._check_validity(df)
        issues.extend(validity_issues)
        
        # 4. Check uniqueness (duplicates)
        uniqueness_issues = self._check_uniqueness(df)
        issues.extend(uniqueness_issues)
        
        # 5. Check data types
        type_issues = self._check_data_types(df)
        issues.extend(type_issues)
        
        # Calculate scores
        completeness_score = self._calculate_completeness_score(df)
        consistency_score = self._calculate_consistency_score(issues)
        validity_score = self._calculate_validity_score(issues)
        uniqueness_score = self._calculate_uniqueness_score(df)
        
        overall_score = np.mean([
            completeness_score,
            consistency_score,
            validity_score,
            uniqueness_score
        ])
        
        # Missing data summary
        missing_data = {}
        for col in df.columns:
            missing_pct = (df[col].isnull().sum() / len(df)) * 100
            if missing_pct > 0:
                missing_data[col] = round(missing_pct, 2)
        
        # Duplicate summary
        duplicate_count = df.duplicated().sum()
        duplicate_pct = (duplicate_count / len(df)) * 100
        
        # Issues by severity
        issues_by_severity = {}
        for issue in issues:
            severity = issue.severity.value
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
        
        return QualityReport(
            overall_score=round(overall_score, 2),
            issues=issues,
            completeness_score=round(completeness_score, 2),
            consistency_score=round(consistency_score, 2),
            validity_score=round(validity_score, 2),
            uniqueness_score=round(uniqueness_score, 2),
            missing_data=missing_data,
            duplicate_rows=int(duplicate_count),
            duplicate_percentage=round(duplicate_pct, 2),
            issues_by_severity=issues_by_severity
        )
    
    def _check_completeness(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Check for missing data"""
        issues = []
        
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / len(df)) * 100
            
            if missing_pct > self.missing_threshold_critical:
                issues.append(QualityIssue(
                    category="completeness",
                    severity=IssueSeverity.CRITICAL,
                    column=col,
                    description=f"Column '{col}' has {missing_pct:.1f}% missing values",
                    affected_rows=int(missing_count),
                    affected_percentage=round(missing_pct, 2),
                    recommendation="Consider removing this column or investigating why data is missing"
                ))
            
            elif missing_pct > self.missing_threshold_high:
                issues.append(QualityIssue(
                    category="completeness",
                    severity=IssueSeverity.HIGH,
                    column=col,
                    description=f"Column '{col}' has {missing_pct:.1f}% missing values",
                    affected_rows=int(missing_count),
                    affected_percentage=round(missing_pct, 2),
                    recommendation="Consider imputation or investigate missing data pattern"
                ))
        
        return issues
    
    def _check_consistency(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Check for data consistency issues"""
        issues = []
        
        for col in df.columns:
            # Check for mixed data types in object columns
            if df[col].dtype == 'object':
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    type_counts = non_null.apply(type).value_counts()
                    
                    if len(type_counts) > 1:
                        issues.append(QualityIssue(
                            category="consistency",
                            severity=IssueSeverity.MEDIUM,
                            column=col,
                            description=f"Column '{col}' contains mixed data types",
                            affected_rows=len(non_null),
                            affected_percentage=100.0,
                            recommendation="Standardize data types for this column"
                        ))
            
            # Check for inconsistent casing in text columns
            if df[col].dtype == 'object':
                non_null = df[col].dropna().astype(str)
                if len(non_null) > 0:
                    # Check if same values with different casing exist
                    lower_counts = non_null.str.lower().value_counts()
                    original_counts = non_null.value_counts()
                    
                    if len(lower_counts) < len(original_counts):
                        diff = len(original_counts) - len(lower_counts)
                        issues.append(QualityIssue(
                            category="consistency",
                            severity=IssueSeverity.LOW,
                            column=col,
                            description=f"Column '{col}' has inconsistent casing ({diff} values)",
                            affected_rows=diff,
                            affected_percentage=round((diff / len(non_null)) * 100, 2),
                            recommendation="Standardize text casing (e.g., lowercase all values)"
                        ))
            
            # Check for leading/trailing whitespace
            if df[col].dtype == 'object':
                non_null = df[col].dropna().astype(str)
                if len(non_null) > 0:
                    whitespace_count = non_null[non_null != non_null.str.strip()].count()
                    
                    if whitespace_count > 0:
                        issues.append(QualityIssue(
                            category="consistency",
                            severity=IssueSeverity.LOW,
                            column=col,
                            description=f"Column '{col}' has {whitespace_count} values with extra whitespace",
                            affected_rows=int(whitespace_count),
                            affected_percentage=round((whitespace_count / len(non_null)) * 100, 2),
                            recommendation="Trim leading/trailing whitespace"
                        ))
        
        return issues
    
    def _check_validity(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Check for invalid values"""
        issues = []
        
        for col in df.columns:
            # Check numeric columns for unrealistic values
            if pd.api.types.is_numeric_dtype(df[col]):
                non_null = df[col].dropna()
                
                if len(non_null) > 0:
                    # Check for infinite values
                    inf_count = np.isinf(non_null).sum()
                    if inf_count > 0:
                        issues.append(QualityIssue(
                            category="validity",
                            severity=IssueSeverity.HIGH,
                            column=col,
                            description=f"Column '{col}' contains {inf_count} infinite values",
                            affected_rows=int(inf_count),
                            affected_percentage=round((inf_count / len(non_null)) * 100, 2),
                            recommendation="Remove or replace infinite values"
                        ))
                    
                    # Check for extreme outliers (beyond 5 standard deviations)
                    mean = non_null.mean()
                    std = non_null.std()
                    if std > 0:
                        extreme_outliers = ((non_null - mean).abs() > 5 * std).sum()
                        if extreme_outliers > 0:
                            issues.append(QualityIssue(
                                category="validity",
                                severity=IssueSeverity.MEDIUM,
                                column=col,
                                description=f"Column '{col}' has {extreme_outliers} extreme outliers",
                                affected_rows=int(extreme_outliers),
                                affected_percentage=round((extreme_outliers / len(non_null)) * 100, 2),
                                recommendation="Investigate extreme values - they may be errors"
                            ))
            
            # Check for potential email columns
            if df[col].dtype == 'object' and 'email' in col.lower():
                non_null = df[col].dropna().astype(str)
                if len(non_null) > 0:
                    invalid_emails = ~non_null.apply(lambda x: bool(self.email_pattern.match(x)))
                    invalid_count = invalid_emails.sum()
                    
                    if invalid_count > 0:
                        issues.append(QualityIssue(
                            category="validity",
                            severity=IssueSeverity.MEDIUM,
                            column=col,
                            description=f"Column '{col}' has {invalid_count} invalid email formats",
                            affected_rows=int(invalid_count),
                            affected_percentage=round((invalid_count / len(non_null)) * 100, 2),
                            recommendation="Validate and correct email formats"
                        ))
            
            # Check for potential phone columns
            if df[col].dtype == 'object' and 'phone' in col.lower():
                non_null = df[col].dropna().astype(str)
                if len(non_null) > 0:
                    invalid_phones = ~non_null.apply(lambda x: bool(self.phone_pattern.match(x)))
                    invalid_count = invalid_phones.sum()
                    
                    if invalid_count > 0:
                        issues.append(QualityIssue(
                            category="validity",
                            severity=IssueSeverity.MEDIUM,
                            column=col,
                            description=f"Column '{col}' has {invalid_count} invalid phone formats",
                            affected_rows=int(invalid_count),
                            affected_percentage=round((invalid_count / len(non_null)) * 100, 2),
                            recommendation="Standardize phone number formats"
                        ))
        
        return issues
    
    def _check_uniqueness(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Check for duplicate rows"""
        issues = []
        
        duplicate_count = df.duplicated().sum()
        duplicate_pct = (duplicate_count / len(df)) * 100
        
        if duplicate_pct > self.duplicate_threshold:
            issues.append(QualityIssue(
                category="uniqueness",
                severity=IssueSeverity.HIGH,
                column=None,
                description=f"Dataset has {duplicate_count} duplicate rows ({duplicate_pct:.1f}%)",
                affected_rows=int(duplicate_count),
                affected_percentage=round(duplicate_pct, 2),
                recommendation="Remove duplicate rows or investigate if they are intentional"
            ))
        
        return issues
    
    def _check_data_types(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Check for potential data type issues"""
        issues = []
        
        for col in df.columns:
            # Check if numeric columns stored as strings
            if df[col].dtype == 'object':
                non_null = df[col].dropna().astype(str)
                if len(non_null) > 0:
                    # Try to convert to numeric
                    numeric_count = pd.to_numeric(non_null, errors='coerce').notna().sum()
                    numeric_pct = (numeric_count / len(non_null)) * 100
                    
                    if numeric_pct > 80:  # If 80%+ are numeric
                        issues.append(QualityIssue(
                            category="data_type",
                            severity=IssueSeverity.INFO,
                            column=col,
                            description=f"Column '{col}' appears to be numeric but stored as text",
                            affected_rows=len(non_null),
                            affected_percentage=100.0,
                            recommendation="Convert to numeric data type for better analysis"
                        ))
        
        return issues
    
    def _calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate completeness score (0-100)"""
        if df.empty:
            return 0.0
        
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells) * 100
        
        return completeness
    
    def _calculate_consistency_score(self, issues: List[QualityIssue]) -> float:
        """Calculate consistency score based on issues"""
        consistency_issues = [i for i in issues if i.category == "consistency"]
        
        if not consistency_issues:
            return 100.0
        
        # Deduct points based on severity
        deductions = sum(
            10 if i.severity == IssueSeverity.CRITICAL else
            5 if i.severity == IssueSeverity.HIGH else
            2 if i.severity == IssueSeverity.MEDIUM else 1
            for i in consistency_issues
        )
        
        return max(0, 100 - deductions)
    
    def _calculate_validity_score(self, issues: List[QualityIssue]) -> float:
        """Calculate validity score based on issues"""
        validity_issues = [i for i in issues if i.category == "validity"]
        
        if not validity_issues:
            return 100.0
        
        # Deduct points based on severity
        deductions = sum(
            15 if i.severity == IssueSeverity.CRITICAL else
            10 if i.severity == IssueSeverity.HIGH else
            5 if i.severity == IssueSeverity.MEDIUM else 2
            for i in validity_issues
        )
        
        return max(0, 100 - deductions)
    
    def _calculate_uniqueness_score(self, df: pd.DataFrame) -> float:
        """Calculate uniqueness score"""
        if len(df) == 0:
            return 100.0
        
        duplicate_count = df.duplicated().sum()
        uniqueness = ((len(df) - duplicate_count) / len(df)) * 100
        
        return uniqueness
    
    def generate_report_summary(self, report: QualityReport) -> str:
        """
        Generate human-readable summary of quality report
        
        Args:
            report: QualityReport
        
        Returns:
            Summary string
        """
        summary = []
        summary.append("Data Quality Report")
        summary.append("=" * 50)
        summary.append(f"Overall Quality Score: {report.overall_score:.1f}/100")
        summary.append("")
        
        summary.append("Component Scores:")
        summary.append(f"  - Completeness: {report.completeness_score:.1f}/100")
        summary.append(f"  - Consistency: {report.consistency_score:.1f}/100")
        summary.append(f"  - Validity: {report.validity_score:.1f}/100")
        summary.append(f"  - Uniqueness: {report.uniqueness_score:.1f}/100")
        summary.append("")
        
        if report.issues:
            summary.append(f"Issues Found: {len(report.issues)}")
            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                count = report.issues_by_severity.get(severity, 0)
                if count > 0:
                    summary.append(f"  - {severity.capitalize()}: {count}")
            summary.append("")
            
            # List top issues
            summary.append("Top Issues:")
            for issue in report.issues[:5]:
                summary.append(f"  [{issue.severity.value.upper()}] {issue.description}")
        else:
            summary.append("No issues found!")
        
        return "\n".join(summary)