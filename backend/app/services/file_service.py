#backend/app/services/file_service.py

"""
File Service
Business logic for file operations
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List
import logging

from app.config import settings, get_upload_path, is_allowed_file

logger = logging.getLogger(__name__)


class FileService:
    """Service for file management operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.upload_dir = settings.UPLOAD_DIR
        self.max_file_size = settings.MAX_FILE_SIZE
    
    async def save_uploaded_file(
        self,
        file_content: bytes,
        original_filename: str
    ) -> dict:
        """
        Save uploaded file to disk
        
        Args:
            file_content: File content as bytes
            original_filename: Original filename from upload
        
        Returns:
            Dictionary with file information
        """
        try:
            # Validate filename
            if not is_allowed_file(original_filename):
                raise ValueError(
                    f"File type not allowed: {original_filename}. "
                    f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                )
            
            # Check file size
            file_size = len(file_content)
            if file_size > self.max_file_size:
                raise ValueError(
                    f"File too large: {file_size} bytes. "
                    f"Maximum: {self.max_file_size} bytes"
                )
            
            # Generate unique file ID and path
            file_id = str(uuid.uuid4())
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            saved_filename = f"{file_id}.{file_extension}"
            file_path = get_upload_path(saved_filename)
            
            # Ensure upload directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            self.logger.info(f"File saved: {saved_filename} ({file_size} bytes)")
            
            return {
                "file_id": file_id,
                "original_filename": original_filename,
                "saved_filename": saved_filename,
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_extension,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error saving file: {str(e)}")
            raise
    
    def delete_file(self, file_id: str, file_extension: str) -> bool:
        """
        Delete a file from disk
        
        Args:
            file_id: File ID
            file_extension: File extension
        
        Returns:
            True if deleted successfully
        """
        try:
            saved_filename = f"{file_id}.{file_extension}"
            file_path = get_upload_path(saved_filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"File deleted: {saved_filename}")
                return True
            else:
                self.logger.warning(f"File not found: {saved_filename}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error deleting file: {str(e)}")
            raise
    
    def get_file_path(self, file_id: str, file_extension: str) -> str:
        """
        Get full path for a file
        
        Args:
            file_id: File ID
            file_extension: File extension
        
        Returns:
            Full file path
        """
        saved_filename = f"{file_id}.{file_extension}"
        return get_upload_path(saved_filename)
    
    def file_exists(self, file_id: str, file_extension: str) -> bool:
        """
        Check if a file exists
        
        Args:
            file_id: File ID
            file_extension: File extension
        
        Returns:
            True if file exists
        """
        file_path = self.get_file_path(file_id, file_extension)
        return os.path.exists(file_path)
    
    def get_file_size(self, file_id: str, file_extension: str) -> Optional[int]:
        """
        Get file size in bytes
        
        Args:
            file_id: File ID
            file_extension: File extension
        
        Returns:
            File size in bytes or None if file doesn't exist
        """
        file_path = self.get_file_path(file_id, file_extension)
        
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return None
    
    def list_files(self) -> List[dict]:
        """
        List all files in upload directory
        
        Returns:
            List of file information dictionaries
        """
        files = []
        
        if not os.path.exists(self.upload_dir):
            return files
        
        for filename in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, filename)
            
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                
                files.append({
                    "filename": filename,
                    "file_size": file_stat.st_size,
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
        
        return files
    
    def cleanup_old_files(self, days: int = 7) -> int:
        """
        Clean up files older than specified days
        
        Args:
            days: Number of days
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        if not os.path.exists(self.upload_dir):
            return 0
        
        for filename in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, filename)
            
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                
                if file_mtime < cutoff_time:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        self.logger.info(f"Cleaned up old file: {filename}")
                    except Exception as e:
                        self.logger.error(f"Error deleting old file {filename}: {str(e)}")
        
        return deleted_count