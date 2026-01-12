#backend/app/utils/validators.py

"""
Validators
Data validation utilities
"""

import pandas as pd
from typing import List, Optional, Dict, Any
import re
import logging

from app.config import settings, is_allowed_file

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_file_upload(
    filename: str,
    file_size: int,
    file_content: Optional[bytes] = None
) -> dict:
    """
    Validate file upload
    
    Args:
        filename: Filename
        file_size: File size in bytes
        file_content: Optional file content for validation
    
    Returns:
        Validation result dictionary
    
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    warnings = []
    
    # Check filename
    if not filename:
        errors.append("Filename is required")
    
    # Check file extension
    if not is_allowed_file(filename):
        errors.append(
            f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    if file_size > settings.MAX_FILE_SIZE:
        errors.append(
            f"File too large ({file_size} bytes). Maximum: {settings.MAX_FILE_SIZE} bytes"
        )
    
    if file_size == 0:
        errors.append("File is empty")
    
    # Check filename length
    if len(filename) > 255:
        warnings.append("Filename is very long and will be truncated")
    
    # Check for special characters
    if re.search(r'[<>:"/\\|?*]', filename):
        warnings.append("Filename contains special characters that will be sanitized")
    
    # Validate content if provided
    if file_content:
        # Check magic bytes for common file types
        if filename.endswith('.pdf') and not file_content.startswith(b'%PDF'):
            errors.append("File does not appear to be a valid PDF")
        
        elif filename.endswith(('.xlsx', '.xls')) and not (
            file_content.startswith(b'PK') or file_content.startswith(b'\xd0\xcf')
        ):
            errors.append("File does not appear to be a valid Excel file")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings
    }


def validate_chart_config(config: Dict[str, Any]) -> dict:
    """
    Validate chart configuration
    
    Args:
        config: Chart configuration dictionary
    
    Returns:
        Validation result
    
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    warnings = []
    
    required_fields = ['chart_type']
    
    # Check required fields
    for field in required_fields:
        if field not in config:
            errors.append(f"Required field missing: {field}")
    
    # Validate chart type
    if 'chart_type' in config:
        valid_types = [
            'bar', 'line', 'scatter', 'histogram', 'box', 'violin',
            'pie', 'donut', 'heatmap', 'area', 'bubble', 'sunburst', 'treemap',
            'density_heatmap', 'parallel_coordinates'
        ]
        
        if config['chart_type'] not in valid_types:
            errors.append(
                f"Invalid chart type: {config['chart_type']}. "
                f"Valid types: {', '.join(valid_types)}"
            )
    
    # Validate dimensions
    if 'width' in config:
        if not isinstance(config['width'], (int, float)) or config['width'] <= 0:
            errors.append("Width must be a positive number")
        elif config['width'] > 5000:
            warnings.append("Width is very large (>5000px)")
    
    if 'height' in config:
        if not isinstance(config['height'], (int, float)) or config['height'] <= 0:
            errors.append("Height must be a positive number")
        elif config['height'] > 5000:
            warnings.append("Height is very large (>5000px)")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings
    }


def validate_dataframe(df: pd.DataFrame) -> dict:
    """
    Validate pandas DataFrame
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Validation result
    
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    warnings = []
    
    # Check if empty
    if df.empty:
        errors.append("DataFrame is empty")
    
    # Check shape
    if len(df) == 0:
        errors.append("DataFrame has no rows")
    
    if len(df.columns) == 0:
        errors.append("DataFrame has no columns")
    
    # Check for duplicate column names
    if len(df.columns) != len(set(df.columns)):
        duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
        warnings.append(f"Duplicate column names found: {set(duplicates)}")
    
    # Check for all-null columns
    null_columns = df.columns[df.isnull().all()].tolist()
    if null_columns:
        warnings.append(f"Columns with all null values: {null_columns}")
    
    # Check for extremely large DataFrames
    if len(df) > 1_000_000:
        warnings.append(f"Very large DataFrame ({len(df)} rows). Processing may be slow.")
    
    if len(df.columns) > 1000:
        warnings.append(f"Many columns ({len(df.columns)}). Some operations may be limited.")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings,
        "shape": df.shape,
        "memory_usage": df.memory_usage(deep=True).sum()
    }


def validate_column_names(
    columns: List[str],
    df: pd.DataFrame
) -> dict:
    """
    Validate that column names exist in DataFrame
    
    Args:
        columns: List of column names to validate
        df: DataFrame to check against
    
    Returns:
        Validation result
    
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    warnings = []
    
    if not columns:
        errors.append("No columns specified")
    
    # Check if columns exist
    missing = [col for col in columns if col not in df.columns]
    if missing:
        errors.append(f"Columns not found in DataFrame: {missing}")
    
    # Check for empty columns
    for col in columns:
        if col in df.columns:
            if df[col].isnull().all():
                warnings.append(f"Column '{col}' contains only null values")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings
    }


def validate_export_format(format: str, export_type: str = 'chart') -> dict:
    """
    Validate export format
    
    Args:
        format: Export format
        export_type: Type of export ('chart', 'data', 'dashboard')
    
    Returns:
        Validation result
    
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    
    valid_formats = {
        'chart': ['png', 'jpg', 'jpeg', 'svg', 'webp', 'html', 'pdf'],
        'data': ['excel', 'csv', 'json'],
        'dashboard': ['html', 'pdf']
    }
    
    if export_type not in valid_formats:
        errors.append(f"Invalid export type: {export_type}")
    elif format not in valid_formats[export_type]:
        errors.append(
            f"Invalid format '{format}' for {export_type}. "
            f"Valid formats: {', '.join(valid_formats[export_type])}"
        )
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return {
        "valid": True,
        "errors": errors
    }


def validate_query_params(params: Dict[str, Any]) -> dict:
    """
    Validate query parameters
    
    Args:
        params: Query parameters dictionary
    
    Returns:
        Validation result
    
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    warnings = []
    
    # Validate pagination
    if 'limit' in params:
        if not isinstance(params['limit'], int) or params['limit'] <= 0:
            errors.append("Limit must be a positive integer")
        elif params['limit'] > 10000:
            warnings.append("Limit is very large (>10000)")
    
    if 'offset' in params:
        if not isinstance(params['offset'], int) or params['offset'] < 0:
            errors.append("Offset must be a non-negative integer")
    
    # Validate sort
    if 'sort_by' in params:
        if not isinstance(params['sort_by'], str):
            errors.append("sort_by must be a string")
    
    if 'sort_order' in params:
        if params['sort_order'] not in ['asc', 'desc']:
            errors.append("sort_order must be 'asc' or 'desc'")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings
    }