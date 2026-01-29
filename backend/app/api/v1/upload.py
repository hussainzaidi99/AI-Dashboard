"""
Upload API Endpoints
Handle file uploads and validation
"""
#backend/app/api/v1/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
from datetime import datetime
import logging

from app.config import settings, is_allowed_file, get_upload_path
from app.models.mongodb_models import FileUpload, User
from app.utils.cache import cache_manager
from app.api import deps
from fastapi import Depends

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: "User" = Depends(deps.get_current_user)
):
    """
    Upload a single file for processing
    
    Supported formats: PDF, Excel, CSV, Word, Images
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        saved_filename = f"{file_id}.{file_extension}"
        file_path = get_upload_path(saved_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Create and save FileUpload document
        file_upload = FileUpload(
            file_id=file_id,
            filename=file.filename,
            original_filename=file.filename,
            file_size=file_size,
            file_type=file_extension,
            file_path=file_path,
            status="uploaded",
            user_id=current_user.user_id
        )
        await file_upload.insert()
        
        logger.info(f"File uploaded: {file.filename} ({file_size} bytes) - ID: {file_id}")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_size": file_size,
            "file_type": file_extension,
            "status": "uploaded",
            "message": "File uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: "User" = Depends(deps.get_current_user)
):
    """
    Upload multiple files for batch processing
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
        
        results = []
        
        for file in files:
            try:
                # Validate and save each file
                if not is_allowed_file(file.filename):
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "error": "File type not allowed"
                    })
                    continue
                
                file_content = await file.read()
                file_size = len(file_content)
                
                if file_size > settings.MAX_FILE_SIZE:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "error": "File too large"
                    })
                    continue
                
                # Generate unique file ID
                file_id = str(uuid.uuid4())
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                saved_filename = f"{file_id}.{file_extension}"
                file_path = get_upload_path(saved_filename)
                
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                # Create and save FileUpload document
                file_upload = FileUpload(
                    file_id=file_id,
                    filename=file.filename,
                    original_filename=file.filename,
                    file_size=file_size,
                    file_type=file_extension,
                    file_path=file_path,
                    status="uploaded",
                    user_id=current_user.user_id
                )
                await file_upload.insert()
                
                results.append({
                    "file_id": file_id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "status": "success"
                })
            
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "total_files": len(files),
            "successful": len([r for r in results if r['status'] == 'success']),
            "failed": len([r for r in results if r['status'] == 'error']),
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading multiple files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Delete an uploaded file and clear all related cache
    """
    try:
        file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file info
        saved_filename = f"{file_id}.{file_upload.file_type}"
        file_path = get_upload_path(saved_filename)
        
        # Delete physical file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted physical file: {file_path}")
            
        # Delete persistence JSON file if exists
        try:
            persistence_path = get_upload_path(f"{file_id}.json")
            if os.path.exists(persistence_path):
                os.remove(persistence_path)
                logger.info(f"Deleted persistence file: {persistence_path}")
        except Exception as pe:
            logger.warning(f"Error deleting persistence file: {str(pe)}")
        
        # Delete from database
        await file_upload.delete()
        logger.info(f"Deleted from MongoDB: {file_id}")
        
        # Clear all related cache entries
        try:
            # Clear processed data cache
            processed_key = f"processed_result:{file_id}"
            if cache_manager.get(processed_key):
                cache_manager.delete(processed_key)
                logger.info(f"Cleared cache: {processed_key}")
            
            # Clear insights cache for all possible sheet indices (0-10)
            for sheet_idx in range(10):
                insights_key = f"insights:{file_id}:{sheet_idx}"
                if cache_manager.get(insights_key):
                    cache_manager.delete(insights_key)
                    logger.info(f"Cleared cache: {insights_key}")
            
            # Clear chatbot cache (pattern matching)
            # Note: This clears all chatbot answers for this file
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            chatbot_pattern = f"chatbot:{file_id}:*"
            chatbot_keys = r.keys(chatbot_pattern)
            if chatbot_keys:
                for key in chatbot_keys:
                    r.delete(key)
                logger.info(f"Cleared {len(chatbot_keys)} chatbot cache entries")
            
            logger.info(f"All cache cleared for file: {file_id}")
            
        except Exception as cache_error:
            logger.warning(f"Error clearing cache (non-critical): {str(cache_error)}")
        
        return {
            "file_id": file_id,
            "message": "File and all related cache deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{file_id}")
async def get_upload_status(file_id: str):
    """
    Get upload and processing status for a file
    """
    file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file_upload


@router.get("/list")
async def list_uploaded_files():
    """
    List all uploaded files with formatted file sizes
    """
    from app.utils.response_sanitizer import sanitize_dict
    
    def format_file_size(size_bytes):
        """Format bytes to human-readable size"""
        if not isinstance(size_bytes, (int, float)) or size_bytes < 0:
            return "0 KB"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    files = await FileUpload.find_all().to_list()
    
    # Convert MongoDB documents to dicts and sanitize
    sanitized_files = []
    for file in files:
        file_dict = file.dict() if hasattr(file, 'dict') else dict(file)
        file_dict = sanitize_dict(file_dict)
        
        # Add formatted file size
        file_size = file_dict.get('file_size', 0)
        file_dict['file_size_formatted'] = format_file_size(file_size)
        
        sanitized_files.append(file_dict)
    
    return sanitize_dict({
        "total_files": len(sanitized_files),
        "files": sanitized_files
    })