"""
Data API Endpoints
Data operations, profiling, and analysis
"""
#backend/app/api/v1/data.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import logging

from app.core.analyzers import DataProfiler, StatisticalAnalyzer, QualityChecker
from app.models.mongodb_models import FileUpload, DataProfile, QualityReport
from app.utils.cache import cache_manager
from app.utils.data_persistence import get_processed_data

router = APIRouter()
logger = logging.getLogger(__name__)


class DataRequest(BaseModel):
    file_id: str
    sheet_index: Optional[int] = 0


@router.get("/profile")
async def profile_data(file_id: str, sheet_index: int = 0):
    """
    Generate data profile for a dataset
    """
    try:
        data = await get_processed_data(file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        if sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Profile data
        profiler = DataProfiler()
        profile = profiler.profile(df)
        
        # Convert to serializable format
        columns_info = {}
        for col_name, col_profile in profile.columns.items():
            columns_info[col_name] = {
                "dtype": col_profile.dtype,
                "inferred_type": col_profile.inferred_type,
                "count": col_profile.count,
                "missing": col_profile.missing,
                "missing_percent": col_profile.missing_percent,
                "unique": col_profile.unique,
                "unique_percent": col_profile.unique_percent,
                "stats": col_profile.stats,
                "sample_values": [str(v) for v in col_profile.sample_values],
                "most_common": [(str(v), c) for v, c in col_profile.most_common],
                "patterns": col_profile.patterns,
                "warnings": col_profile.warnings
            }
        
        profile_result = {
            "file_id": file_id,
            "sheet_index": sheet_index,
            "total_rows": profile.total_rows,
            "total_columns": profile.total_columns,
            "memory_usage": profile.memory_usage,
            "type_distribution": profile.type_distribution,
            "columns": columns_info,
            "correlations": profile.correlations.to_dict() if profile.correlations is not None else None,
            "warnings": profile.warnings
        }
        
        # Save to MongoDB
        data_profile = DataProfile(
            file_id=file_id,
            profile_data=profile_result
        )
        await data_profile.insert()
        
        return profile_result
    
    except Exception as e:
        logger.error(f"Error profiling data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def analyze_statistics(file_id: str, sheet_index: int = 0):
    """
    Perform statistical analysis on dataset
    """
    try:
        data = await get_processed_data(file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        has_dataframes = data.get('dataframes') and len(data['dataframes']) > 0
        
        if not has_dataframes:
            return {
                "file_id": file_id,
                "sheet_index": sheet_index,
                "statistics": {},
                "message": "This is a text-based document. High-level statistical aggregates are not applicable.",
                "is_text_only": True
            }

        if sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Analyze
        analyzer = StatisticalAnalyzer()
        result = analyzer.analyze(df)
        
        # Convert to serializable format
        distribution_tests = {}
        for col, test in result.distribution_tests.items():
            distribution_tests[col] = {
                "test_name": test.test_name,
                "statistic": test.statistic,
                "p_value": test.p_value,
                "is_normal": test.is_normal,
                "conclusion": test.conclusion
            }
        
        outliers = None
        if result.outlier_analysis:
            outliers = {
                "method": result.outlier_analysis.method,
                "outlier_counts": result.outlier_analysis.outlier_counts,
                "outlier_percentages": result.outlier_analysis.outlier_percentages
            }
        
        correlation = None
        if result.correlation_analysis:
            correlation = {
                "method": result.correlation_analysis.method,
                "matrix": result.correlation_analysis.matrix.to_dict(),
                "significant_pairs": result.correlation_analysis.significant_pairs
            }
        
        return {
            "file_id": file_id,
            "sheet_index": sheet_index,
            "distribution_tests": distribution_tests,
            "correlation_analysis": correlation,
            "outlier_analysis": outliers,
            "variance_tests": result.variance_tests,
            "summary_stats": result.summary_stats.to_dict(),
            "warnings": result.warnings,
            "is_text_only": False
        }
    
    except Exception as e:
        logger.error(f"Error analyzing statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality")
async def check_quality(file_id: str, sheet_index: int = 0):
    """
    Check data quality
    """
    try:
        data = await get_processed_data(file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        has_dataframes = data.get('dataframes') and len(data['dataframes']) > 0
        
        if not has_dataframes:
            return {
                "file_id": file_id,
                "sheet_index": sheet_index,
                "overall_score": 100.0,
                "is_text_only": True,
                "message": "Text document integrity is verified.",
                "issues": []
            }

        if sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Check quality
        checker = QualityChecker()
        report = checker.check(df)
        
        # Convert issues to serializable format
        issues = []
        for issue in report.issues:
            issues.append({
                "category": issue.category,
                "severity": issue.severity.value,
                "column": issue.column,
                "description": issue.description,
                "affected_rows": issue.affected_rows,
                "affected_percentage": issue.affected_percentage,
                "recommendation": issue.recommendation
            })
        
        report_result = {
            "file_id": file_id,
            "sheet_index": sheet_index,
            "overall_score": report.overall_score,
            "scores": {
                "completeness": report.completeness_score,
                "consistency": report.consistency_score,
                "validity": report.validity_score,
                "uniqueness": report.uniqueness_score
            },
            "issues": issues,
            "issues_by_severity": report.issues_by_severity,
            "missing_data": report.missing_data,
            "duplicate_rows": report.duplicate_rows,
            "duplicate_percentage": report.duplicate_percentage,
            "checked_at": report.checked_at.isoformat() if hasattr(report.checked_at, 'isoformat') else str(report.checked_at),
            "is_text_only": False
        }
        
        # Save to MongoDB
        quality_report = QualityReport(
            file_id=file_id,
            overall_score=report.overall_score,
            completeness_score=report.completeness_score,
            consistency_score=report.consistency_score,
            validity_score=report.validity_score,
            uniqueness_score=report.uniqueness_score,
            issues=issues
        )
        await quality_report.insert()
        
        return report_result
    
    except Exception as e:
        logger.error(f"Error checking quality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns/{file_id}")
async def get_columns(file_id: str, sheet_index: int = 0):
    """
    Get column information for a dataset
    """
    data = await get_processed_data(file_id)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    if sheet_index >= len(data['dataframes']):
        raise HTTPException(status_code=400, detail="Sheet index out of range")
    
    sheet_data = data['dataframes'][sheet_index]
    
    return {
        "file_id": file_id,
        "sheet_index": sheet_index,
        "sheet_name": sheet_data['sheet_name'],
        "columns": sheet_data['column_names'],
        "dtypes": sheet_data['dtypes']
    }


@router.get("/{file_id}")
async def get_data(file_id: str, sheet_index: int = 0, limit: Optional[int] = 100):
    """
    Get data from a processed file
    """
    # Check if file exists in MongoDB
    file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
        
    data = await get_processed_data(file_id)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found. Please process the file first.")
    
    if sheet_index >= len(data['dataframes']):
        raise HTTPException(status_code=400, detail=f"Sheet index {sheet_index} out of range")
    
    sheet_data = data['dataframes'][sheet_index]
    
    # Limit rows if requested
    if limit and limit < len(sheet_data['data']):
        limited_data = sheet_data['data'][:limit]
    else:
        limited_data = sheet_data['data']
    
    return {
        "file_id": file_id,
        "sheet_name": sheet_data['sheet_name'],
        "total_rows": sheet_data['rows'],
        "total_columns": sheet_data['columns'],
        "columns": sheet_data['column_names'],
        "data": limited_data,
        "showing_rows": len(limited_data)
    }