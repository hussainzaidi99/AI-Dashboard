"""
Base Exporter - Shared functionality for all exporters
Provides common utilities, error handling, and resource management
"""
#backend/app/core/exporters/base_exporter.py

import os
import tempfile
import shutil
import logging
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

from app.config import settings


class ExportDisabledError(Exception):
    """Raised when export feature is disabled in settings"""
    pass


class ExportFailedError(Exception):
    """Raised when export operation fails"""
    pass


class BaseExporter:
    """Base class for all exporters with shared functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure export directory exists
        self._ensure_output_dir(settings.EXPORT_DIR)
    
    def _ensure_enabled(self, setting_flag: bool, export_type: str):
        """
        Ensure export feature is enabled
        
        Args:
            setting_flag: Boolean setting flag to check
            export_type: Type of export (for error message)
        
        Raises:
            ExportDisabledError: If feature is disabled
        """
        if not setting_flag:
            error_msg = f"{export_type} export is disabled in settings"
            self.logger.error(error_msg)
            raise ExportDisabledError(error_msg)
    
    def _ensure_output_dir(self, path: str) -> str:
        """
        Ensure output directory exists
        
        Args:
            path: Directory or file path
        
        Returns:
            The directory path
        
        Raises:
            ExportFailedError: If directory creation fails
        """
        # If path is a file, get its directory
        if os.path.splitext(path)[1]:  # Has file extension
            directory = os.path.dirname(path)
        else:
            directory = path
        
        # Skip if empty (current directory)
        if not directory:
            return "."
        
        try:
            os.makedirs(directory, exist_ok=True)
            return directory
        except Exception as e:
            error_msg = f"Failed to create directory {directory}: {str(e)}"
            self.logger.error(error_msg)
            raise ExportFailedError(error_msg)
    
    @contextmanager
    def _temp_dir(self):
        """
        Context manager for temporary directory with automatic cleanup
        
        Yields:
            Path to temporary directory
        
        Example:
            with self._temp_dir() as temp_dir:
                # Use temp_dir
                pass
            # temp_dir is automatically cleaned up
        """
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            self.logger.debug(f"Created temporary directory: {temp_dir}")
            yield temp_dir
        except Exception as e:
            self.logger.error(f"Error in temporary directory context: {str(e)}")
            raise
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    self.logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp directory {temp_dir}: {str(e)}")
    
    def _validate_path(self, output_path: str) -> bool:
        """
        Validate output path and check write permissions
        
        Args:
            output_path: Path to validate
        
        Returns:
            True if valid and writable
        
        Raises:
            ExportFailedError: If path is invalid or not writable
        """
        output_dir = os.path.dirname(output_path) or "."
        
        # Ensure directory exists
        self._ensure_output_dir(output_dir)
        
        # Test write permissions
        try:
            temp_file = os.path.join(output_dir, f".write_test_{os.getpid()}")
            with open(temp_file, 'w') as f:
                f.write('test')
            os.remove(temp_file)
            return True
        except Exception as e:
            error_msg = f"Directory {output_dir} is not writable: {str(e)}"
            self.logger.error(error_msg)
            raise ExportFailedError(error_msg)
    
    def _log_export_success(self, output_path: str, export_type: str = "file"):
        """
        Log successful export
        
        Args:
            output_path: Path to exported file
            export_type: Type of export for log message
        """
        self.logger.info(f"Successfully exported {export_type} to: {output_path}")
    
    def _log_export_error(self, error: Exception, export_type: str = "file"):
        """
        Log export error
        
        Args:
            error: Exception that occurred
            export_type: Type of export for log message
        """
        self.logger.error(f"Failed to export {export_type}: {str(error)}")
