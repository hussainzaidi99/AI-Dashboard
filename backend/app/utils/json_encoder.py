"""
Custom JSON Encoder for Pandas and NumPy types
Provides production-grade serialization for complex data types
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, date, time
from typing import Any
import logging

logger = logging.getLogger(__name__)


class PandasJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles Pandas and NumPy types.
    
    Supported types:
    - pd.Timestamp -> ISO 8601 string
    - pd.NaT -> null
    - pd.Series -> list
    - pd.DataFrame -> list of dicts
    - np.ndarray -> list
    - np.integer -> int
    - np.floating -> float
    - np.bool_ -> bool
    - datetime/date/time -> ISO 8601 string
    - NaN/Inf -> null
    """
    
    def default(self, obj: Any) -> Any:
        """
        Override default serialization for unsupported types.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable representation
        """
        # Handle standard Python float NaN and Inf FIRST (before isinstance checks)
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        
        # Handle pandas Timestamp
        if isinstance(obj, pd.Timestamp):
            if pd.isna(obj):
                return None
            return obj.isoformat()
        
        # Handle pandas NaT (Not a Time) - check with pd.isna
        try:
            if pd.isna(obj) and not isinstance(obj, (str, int, float, bool)):
                return None
        except (TypeError, ValueError):
            pass
        
        # Handle pandas Series
        if isinstance(obj, pd.Series):
            return obj.tolist()
        
        # Handle pandas DataFrame
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        
        # Handle numpy arrays - check this early to avoid boolean ambiguity
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # Handle numpy bool (check before numpy integer/float)
        if isinstance(obj, (np.bool_, np.bool8)):
            return bool(obj)
        
        # Handle numpy integer types
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        
        # Handle numpy floating types
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            # Handle special float values
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        if isinstance(obj, date):
            return obj.isoformat()
        
        if isinstance(obj, time):
            return obj.isoformat()
        
        # Fallback to parent class default
        return super().default(obj)


def serialize_to_json(data: Any, **kwargs) -> str:
    """
    Serialize data to JSON string with support for Pandas and NumPy types.
    
    Args:
        data: Data to serialize
        **kwargs: Additional arguments to pass to json.dumps
        
    Returns:
        JSON string
        
    Raises:
        TypeError: If data contains non-serializable types
        ValueError: If serialization fails
    """
    try:
        return json.dumps(data, cls=PandasJSONEncoder, **kwargs)
    except Exception as e:
        logger.error(f"JSON serialization error: {str(e)}")
        raise


def deserialize_from_json(json_str: str, **kwargs) -> Any:
    """
    Deserialize JSON string to Python object.
    
    Args:
        json_str: JSON string to deserialize
        **kwargs: Additional arguments to pass to json.loads
        
    Returns:
        Deserialized Python object
        
    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    try:
        return json.loads(json_str, **kwargs)
    except json.JSONDecodeError as e:
        logger.error(f"JSON deserialization error: {str(e)}")
        raise
