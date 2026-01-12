#backend/app/utils/helpers.py

"""
Helper Utilities
Common helper functions used across the application
"""

import uuid
import hashlib
import mimetypes
import re
from typing import Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def generate_unique_id() -> str:
    """
    Generate a unique ID using UUID4
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def calculate_hash(data: bytes, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of data
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm (md5, sha1, sha256)
    
    Returns:
        Hex digest of hash
    """
    if algorithm == 'md5':
        return hashlib.md5(data).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(data).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(data).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def get_mime_type(filename: str) -> Optional[str]:
    """
    Get MIME type for a file
    
    Args:
        filename: Filename
    
    Returns:
        MIME type string or None
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate string to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_time_range(time_str: str) -> tuple:
    """
    Parse time range string like "1h", "30m", "7d"
    
    Args:
        time_str: Time range string
    
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    now = datetime.now()
    
    # Extract number and unit
    match = re.match(r'(\d+)([smhd])', time_str.lower())
    if not match:
        raise ValueError(f"Invalid time range format: {time_str}")
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    # Calculate time delta
    if unit == 's':
        delta = timedelta(seconds=amount)
    elif unit == 'm':
        delta = timedelta(minutes=amount)
    elif unit == 'h':
        delta = timedelta(hours=amount)
    elif unit == 'd':
        delta = timedelta(days=amount)
    else:
        raise ValueError(f"Invalid time unit: {unit}")
    
    start_time = now - delta
    return start_time, now


def deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (overwrites dict1)
    
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
    
    Returns:
        Result of division or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def percentage(part: float, whole: float, decimals: int = 2) -> float:
    """
    Calculate percentage
    
    Args:
        part: Part value
        whole: Whole value
        decimals: Number of decimal places
    
    Returns:
        Percentage value
    """
    if whole == 0:
        return 0.0
    
    return round((part / whole) * 100, decimals)


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: dict, parent_key: str = '', separator: str = '.') -> dict:
    """
    Flatten nested dictionary
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Key separator
    
    Returns:
        Flattened dictionary
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    
    return dict(items)


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "2h 15m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {seconds:.0f}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    return f"{hours}h {minutes}m {seconds:.0f}s"


def is_valid_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address
    
    Returns:
        True if valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def retry_on_exception(func, max_attempts: int = 3, delay: float = 1.0):
    """
    Retry function on exception
    
    Args:
        func: Function to retry
        max_attempts: Maximum retry attempts
        delay: Delay between retries in seconds
    
    Returns:
        Function result
    """
    import time
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
            time.sleep(delay)