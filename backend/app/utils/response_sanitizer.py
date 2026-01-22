"""
Response Sanitizer - Convert NumPy and Pandas types to native Python types
Ensures all response data is JSON-serializable by FastAPI
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Union
import logging

logger = logging.getLogger(__name__)


def sanitize_value(value: Any) -> Any:
    """
    Convert a single value from NumPy/Pandas type to native Python type.
    
    Args:
        value: Value to sanitize
        
    Returns:
        JSON-serializable value
    """
    # Handle None
    if value is None:
        return None
    
    # Handle Pandas NaT (Not a Time) - must check before Timestamp
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    
    # Handle Pandas NA/NaT through pd.isna check (for Series/scalar NA values)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    
    # Handle standard float NaN/Inf
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return None
        return value
    
    # Handle NumPy types
    if isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        # Handle NaN and Inf
        try:
            if np.isnan(value) or np.isinf(value):
                return None
        except (TypeError, ValueError):
            pass
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    
    # Handle Pandas Series
    elif isinstance(value, pd.Series):
        return value.tolist()
    
    # Handle Pandas DataFrame
    elif isinstance(value, pd.DataFrame):
        return value.to_dict(orient='records')
    
    # Already serializable
    return value


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary, converting all NumPy/Pandas types.
    
    Args:
        data: Dictionary to sanitize
        
    Returns:
        Sanitized dictionary with only JSON-serializable types
    """
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        result[key] = sanitize_item(value)
    return result


def sanitize_list(data: List[Any]) -> List[Any]:
    """
    Recursively sanitize a list, converting all NumPy/Pandas types.
    
    Args:
        data: List to sanitize
        
    Returns:
        Sanitized list with only JSON-serializable types
    """
    if not isinstance(data, list):
        return data
    
    return [sanitize_item(item) for item in data]


def sanitize_item(item: Any) -> Any:
    """
    Recursively sanitize any item - dict, list, or value.
    
    Args:
        item: Item to sanitize
        
    Returns:
        Sanitized item
    """
    if isinstance(item, dict):
        return sanitize_dict(item)
    elif isinstance(item, list):
        return sanitize_list(item)
    elif isinstance(item, pd.DataFrame):
        # Convert DataFrame to list of records and sanitize each record
        records = item.to_dict(orient='records')
        return sanitize_list(records)
    elif isinstance(item, pd.Series):
        return sanitize_list(item.tolist())
    else:
        return sanitize_value(item)


def convert_dataframe_to_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convert a DataFrame to a dictionary with all values sanitized.
    Preserves the original to_dict() behavior but sanitizes all values.
    
    Args:
        df: DataFrame to convert
        
    Returns:
        Dictionary with sanitized values
    """
    if df.empty:
        return {}
    
    # Convert to dict with 'dict' orientation (column -> values dict)
    data_dict = df.to_dict()
    
    # Sanitize all values
    sanitized = {}
    for col, values in data_dict.items():
        if isinstance(values, dict):
            sanitized[col] = {k: sanitize_value(v) for k, v in values.items()}
        else:
            sanitized[col] = sanitize_value(values)
    
    return sanitized


def convert_dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert a DataFrame to list of records with all values sanitized.
    
    Args:
        df: DataFrame to convert
        
    Returns:
        List of record dictionaries with sanitized values
    """
    if df.empty:
        return []
    
    records = df.to_dict('records')
    return [sanitize_dict(record) for record in records]
