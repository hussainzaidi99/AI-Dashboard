"""
Data Analyzers Module
Comprehensive data analysis, profiling, and quality assessment
"""
#backend/app/core/analyzers/__init__.py

from .data_profiler import DataProfiler, ProfileResult
from .statistical_analyzer import StatisticalAnalyzer, StatisticalResult
from .quality_checker import QualityChecker, QualityReport

__all__ = [
    "DataProfiler",
    "ProfileResult",
    "StatisticalAnalyzer",
    "StatisticalResult",
    "QualityChecker",
    "QualityReport",
]


# Convenience function for complete analysis
def analyze_dataframe(df, include_quality: bool = True):
    """
    Perform complete analysis on a DataFrame
    
    Args:
        df: pandas DataFrame to analyze
        include_quality: Whether to include quality checks
    
    Returns:
        Dictionary with all analysis results
    """
    results = {}
    
    # Profile data
    profiler = DataProfiler()
    results['profile'] = profiler.profile(df)
    
    # Statistical analysis
    stats_analyzer = StatisticalAnalyzer()
    results['statistics'] = stats_analyzer.analyze(df)
    
    # Quality checks
    if include_quality:
        quality_checker = QualityChecker()
        results['quality'] = quality_checker.check(df)
    
    return results