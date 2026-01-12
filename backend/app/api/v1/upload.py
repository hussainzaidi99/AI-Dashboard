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
from app.models.mongodb_models import FileUpload

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
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
            status="uploaded"
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


@router.post("/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...)
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
                    status="uploaded"
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


@router.delete("/upload/{file_id}")
async def delete_file(file_id: str):
    """
    Delete an uploaded file
    """
    try:
        file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file info
        saved_filename = f"{file_id}.{file_upload.file_type}"
        file_path = get_upload_path(saved_filename)
        
        # Delete file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        await file_upload.delete()
        
        logger.info(f"File deleted: {file_id}")
        
        return {
            "file_id": file_id,
            "message": "File deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload/status/{file_id}")
async def get_upload_status(file_id: str):
    """
    Get upload and processing status for a file
    """
    file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file_upload


@router.get("/upload/list")
async def list_uploaded_files():
    """
    List all uploaded files
    """
    files = await FileUpload.find_all().to_list()
    return {
        "total_files": len(files),
        "files": files
    }