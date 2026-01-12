"""
Data Profiler - Comprehensive data profiling and characterization
Generates detailed profiles of DataFrames including column types, distributions, and patterns
"""
#backend/app/core/analyzers/data_profiler.py


from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ColumnProfile:
    """Profile information for a single column"""
    name: str
    dtype: str
    inferred_type: str  # numeric, categorical, datetime, text, boolean
    
    # Basic statistics
    count: int
    missing: int
    missing_percent: float
    unique: int
    unique_percent: float
    
    # Type-specific statistics
    stats: Dict[str, Any] = field(default_factory=dict)
    
    # Sample values
    sample_values: List[Any] = field(default_factory=list)
    most_common: List[tuple] = field(default_factory=list)
    
    # Patterns
    patterns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ProfileResult:
    """Complete profile result for a DataFrame"""
    # Dataset level
    total_rows: int
    total_columns: int
    memory_usage: float  # in MB
    
    # Column profiles
    columns: Dict[str, ColumnProfile]
    
    # Type distribution
    type_distribution: Dict[str, int]
    
    # Relationships
    correlations: Optional[pd.DataFrame] = None
    
    # Metadata
    profile_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    warnings: List[str] = field(default_factory=list)


class DataProfiler:
    """Generate comprehensive data profiles"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thresholds
        self.categorical_threshold = 0.05  # 5% unique values
        self.high_cardinality_threshold = 100
        self.sample_size = 10
    
    def profile(self, df: pd.DataFrame) -> ProfileResult:
        """
        Generate complete profile for a DataFrame
        
        Args:
            df: pandas DataFrame to profile
        
        Returns:
            ProfileResult with comprehensive analysis
        """
        self.logger.info(f"Profiling DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # Column profiles
        columns_profile = {}
        type_distribution = {}
        warnings = []
        
        for col in df.columns:
            try:
                col_profile = self._profile_column(df[col])
                columns_profile[col] = col_profile
                
                # Update type distribution
                inferred_type = col_profile.inferred_type
                type_distribution[inferred_type] = type_distribution.get(inferred_type, 0) + 1
            
            except Exception as e:
                self.logger.error(f"Error profiling column {col}: {str(e)}")
                warnings.append(f"Failed to profile column '{col}': {str(e)}")
        
        # Calculate correlations for numeric columns
        correlations = self._calculate_correlations(df)
        
        # Memory usage
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        return ProfileResult(
            total_rows=len(df),
            total_columns=len(df.columns),
            memory_usage=round(memory_mb, 2),
            columns=columns_profile,
            type_distribution=type_distribution,
            correlations=correlations,
            warnings=warnings
        )
    
    def _profile_column(self, series: pd.Series) -> ColumnProfile:
        """
        Profile a single column
        
        Args:
            series: pandas Series
        
        Returns:
            ColumnProfile with detailed information
        """
        col_name = series.name
        
        # Basic information
        count = len(series)
        missing = series.isnull().sum()
        missing_percent = (missing / count * 100) if count > 0 else 0
        unique = series.nunique()
        unique_percent = (unique / count * 100) if count > 0 else 0
        
        # Infer type
        inferred_type = self._infer_column_type(series)
        
        # Type-specific statistics
        stats = self._calculate_type_specific_stats(series, inferred_type)
        
        # Sample values
        sample_values = series.dropna().head(self.sample_size).tolist()
        
        # Most common values
        most_common = series.value_counts().head(5).items()
        most_common = [(val, int(count)) for val, count in most_common]
        
        # Detect patterns
        patterns = self._detect_patterns(series, inferred_type)
        
        # Generate warnings
        warnings = self._generate_column_warnings(
            series, inferred_type, missing_percent, unique_percent
        )
        
        return ColumnProfile(
            name=col_name,
            dtype=str(series.dtype),
            inferred_type=inferred_type,
            count=count,
            missing=int(missing),
            missing_percent=round(missing_percent, 2),
            unique=unique,
            unique_percent=round(unique_percent, 2),
            stats=stats,
            sample_values=sample_values,
            most_common=most_common,
            patterns=patterns,
            warnings=warnings
        )
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """
        Infer the semantic type of a column
        
        Args:
            series: pandas Series
        
        Returns:
            Inferred type: numeric, categorical, datetime, text, boolean
        """
        # Remove null values for analysis
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return "unknown"
        
        # Check for datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        
        # Check for boolean
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        
        # Check for numeric
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        
        # Check for categorical (low cardinality)
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < self.categorical_threshold:
            return "categorical"
        
        # Check if it's a high cardinality categorical
        if series.nunique() < self.high_cardinality_threshold:
            return "categorical"
        
        # Check for datetime strings
        if self._is_datetime_string(non_null):
            return "datetime"
        
        # Default to text
        return "text"
    
    def _is_datetime_string(self, series: pd.Series, sample_size: int = 100) -> bool:
        """Check if a series contains datetime strings"""
        try:
            sample = series.head(min(sample_size, len(series)))
            pd.to_datetime(sample, errors='raise')
            return True
        except:
            return False
    
    def _calculate_type_specific_stats(
        self,
        series: pd.Series,
        inferred_type: str
    ) -> Dict[str, Any]:
        """
        Calculate statistics specific to the column type
        
        Args:
            series: pandas Series
            inferred_type: Inferred column type
        
        Returns:
            Dictionary with type-specific statistics
        """
        stats = {}
        
        if inferred_type == "numeric":
            stats.update(self._numeric_stats(series))
        
        elif inferred_type == "categorical":
            stats.update(self._categorical_stats(series))
        
        elif inferred_type == "datetime":
            stats.update(self._datetime_stats(series))
        
        elif inferred_type == "text":
            stats.update(self._text_stats(series))
        
        elif inferred_type == "boolean":
            stats.update(self._boolean_stats(series))
        
        return stats
    
    def _numeric_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for numeric columns"""
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return {}
        
        return {
            "min": float(non_null.min()),
            "max": float(non_null.max()),
            "mean": float(non_null.mean()),
            "median": float(non_null.median()),
            "std": float(non_null.std()),
            "variance": float(non_null.var()),
            "q1": float(non_null.quantile(0.25)),
            "q3": float(non_null.quantile(0.75)),
            "iqr": float(non_null.quantile(0.75) - non_null.quantile(0.25)),
            "skewness": float(non_null.skew()),
            "kurtosis": float(non_null.kurtosis()),
            "zeros": int((non_null == 0).sum()),
            "negative": int((non_null < 0).sum()),
            "positive": int((non_null > 0).sum()),
        }
    
    def _categorical_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for categorical columns"""
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return {}
        
        value_counts = non_null.value_counts()
        
        return {
            "categories": list(value_counts.index[:20]),  # Top 20 categories
            "category_counts": {str(k): int(v) for k, v in value_counts.head(20).items()},
            "most_frequent": str(value_counts.index[0]) if len(value_counts) > 0 else None,
            "most_frequent_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
            "least_frequent": str(value_counts.index[-1]) if len(value_counts) > 0 else None,
            "least_frequent_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0,
        }
    
    def _datetime_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for datetime columns"""
        # Try to convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(series):
            try:
                series = pd.to_datetime(series, errors='coerce')
            except:
                return {}
        
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return {}
        
        return {
            "min": str(non_null.min()),
            "max": str(non_null.max()),
            "range_days": (non_null.max() - non_null.min()).days,
            "most_common_year": int(non_null.dt.year.mode()[0]) if len(non_null.dt.year.mode()) > 0 else None,
            "most_common_month": int(non_null.dt.month.mode()[0]) if len(non_null.dt.month.mode()) > 0 else None,
            "most_common_day": int(non_null.dt.day.mode()[0]) if len(non_null.dt.day.mode()) > 0 else None,
        }
    
    def _text_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for text columns"""
        non_null = series.dropna().astype(str)
        
        if len(non_null) == 0:
            return {}
        
        lengths = non_null.str.len()
        
        return {
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max()),
            "mean_length": float(lengths.mean()),
            "median_length": float(lengths.median()),
            "empty_strings": int((non_null == "").sum()),
            "whitespace_only": int(non_null.str.strip().eq("").sum()),
        }
    
    def _boolean_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for boolean columns"""
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return {}
        
        true_count = int(non_null.sum())
        false_count = len(non_null) - true_count
        
        return {
            "true_count": true_count,
            "false_count": false_count,
            "true_percent": round((true_count / len(non_null)) * 100, 2),
            "false_percent": round((false_count / len(non_null)) * 100, 2),
        }
    
    def _detect_patterns(self, series: pd.Series, inferred_type: str) -> List[str]:
        """
        Detect patterns in column data
        
        Args:
            series: pandas Series
            inferred_type: Inferred column type
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Constant values
        if series.nunique() == 1:
            patterns.append("constant_value")
        
        # All unique (potential ID)
        if series.nunique() == len(series):
            patterns.append("all_unique")
        
        # Increasing sequence
        if inferred_type == "numeric":
            non_null = series.dropna()
            if len(non_null) > 1 and non_null.is_monotonic_increasing:
                patterns.append("monotonic_increasing")
            elif len(non_null) > 1 and non_null.is_monotonic_decreasing:
                patterns.append("monotonic_decreasing")
        
        return patterns
    
    def _generate_column_warnings(
        self,
        series: pd.Series,
        inferred_type: str,
        missing_percent: float,
        unique_percent: float
    ) -> List[str]:
        """Generate warnings for column issues"""
        warnings = []
        
        # High missing percentage
        if missing_percent > 50:
            warnings.append(f"High missing data: {missing_percent:.1f}%")
        
        # All values unique (potential ID that shouldn't be analyzed)
        if unique_percent == 100 and len(series) > 10:
            warnings.append("All values unique - might be an identifier")
        
        # Single value (constant)
        if series.nunique() == 1:
            warnings.append("Column has only one unique value")
        
        # High cardinality categorical
        if inferred_type == "categorical" and series.nunique() > 50:
            warnings.append(f"High cardinality categorical ({series.nunique()} categories)")
        
        return warnings
    
    def _calculate_correlations(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Calculate correlation matrix for numeric columns"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) < 2:
                return None
            
            corr_matrix = df[numeric_cols].corr()
            return corr_matrix
        
        except Exception as e:
            self.logger.error(f"Error calculating correlations: {str(e)}")
            return None
    
    def generate_summary(self, profile: ProfileResult) -> str:
        """
        Generate human-readable summary of profile
        
        Args:
            profile: ProfileResult
        
        Returns:
            Summary string
        """
        summary = []
        summary.append(f"Dataset Profile Summary")
        summary.append(f"=" * 50)
        summary.append(f"Rows: {profile.total_rows:,}")
        summary.append(f"Columns: {profile.total_columns}")
        summary.append(f"Memory Usage: {profile.memory_usage:.2f} MB")
        summary.append(f"\nColumn Types:")
        
        for col_type, count in profile.type_distribution.items():
            summary.append(f"  - {col_type}: {count}")
        
        # High-level issues
        issues = []
        for col_name, col_profile in profile.columns.items():
            if col_profile.missing_percent > 20:
                issues.append(f"  - '{col_name}': {col_profile.missing_percent:.1f}% missing")
        
        if issues:
            summary.append(f"\nData Quality Issues:")
            summary.extend(issues)
        
        return "\n".join(summary)