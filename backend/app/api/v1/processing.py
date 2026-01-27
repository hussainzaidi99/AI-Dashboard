"""
Processing API Endpoints
Handle file processing and data extraction
"""
#backend/app/api/v1/processing.py
#Notes : Functionality implemented

# processed_data = {}

# stores processed results in RAM (memory)

# comment already warns: in production use Redis or proper storage

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import numpy as np
import pandas as pd

from app.config import get_upload_path 
from app.core.processors import get_processor
from app.models.mongodb_models import FileUpload, ProcessingJob
from app.utils.cache import cache_manager
from app.utils.json_encoder import serialize_to_json
from app.utils.response_sanitizer import sanitize_dict

router = APIRouter()
logger = logging.getLogger(__name__)

# Store processed results (in production, use Redis/dedicated result store)
# results are now stored in Redis via cache_manager


class ProcessRequest(BaseModel):
    file_id: str
    options: Optional[Dict[str, Any]] = {}


@router.post("")
async def process_file(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Process an uploaded file and extract data
    """
    try:
        file_id = request.file_id
        
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if already processed
        cached_result = cache_manager.get(f"processed_result:{file_id}")
        if cached_result:
            return {
                "file_id": file_id,
                "status": "already_processed",
                "message": "File already processed. Use /data endpoint to retrieve results."
            }
        
        # Create or update processing job in MongoDB
        job = await ProcessingJob.find_one(ProcessingJob.file_id == file_id)
        if not job:
            job = ProcessingJob(file_id=file_id, status="running", progress=10)
            await job.insert()
        else:
            await job.update({"$set": {"status": "running", "progress": 10}})
        
        # Update file status
        await file_upload.update({"$set": {"status": "processing"}})
        
        # Get file path
        file_extension = file_upload.file_type
        saved_filename = f"{file_id}.{file_extension}"
        file_path = get_upload_path(saved_filename)
        
        # Get appropriate processor
        processor = get_processor(file_extension)
        
        # Process file
        # Note: In a real app, this should be a Celery task or background task
        result = processor.process(file_path, **request.options)
        
        if not result.success:
            await job.update({"$set": {"status": "failed", "error_message": result.error_message}})
            await file_upload.update({"$set": {"status": "failed"}})
            raise HTTPException(status_code=500, detail=result.error_message)
        
        # Convert DataFrames to serializable format
        serialized_dataframes = []
        for idx, df in enumerate(result.dataframes):
            serialized_dataframes.append({
                "sheet_name": result.sheet_names[idx] if idx < len(result.sheet_names) else f"Sheet_{idx+1}",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "data": df.replace({np.nan: None}).to_dict('records'),
                "dtypes": df.dtypes.astype(str).to_dict()
            })
        
        # Store processed data in Redis (with 24h expiration)
        result_payload = {
            "file_id": file_id,
            "filename": file_upload.filename,
            "file_type": file_extension,
            "success": True,
            "dataframes": serialized_dataframes,
            "text_content": result.text_content,
            "metadata": result.metadata,
            "total_rows": result.total_rows,
            "total_columns": result.total_columns,
            "processing_time": result.processing_time,
            "warnings": result.warnings
        }
        cache_manager.set(f"processed_result:{file_id}", result_payload, expire=86400)
        
        # Store on disk for persistence across restarts (avoids 404s)
        try:
            persistence_path = get_upload_path(f"{file_id}.json")
            with open(persistence_path, 'w') as f:
                # Use custom encoder to handle Pandas types (Timestamp, etc.)
                f.write(serialize_to_json(result_payload))
            logger.info(f"Saved persistence file: {persistence_path}")
        except Exception as pe:
            logger.warning(f"Failed to save persistence file: {str(pe)}")
        
        # Update job status in MongoDB
        await job.update({"$set": {
            "status": "completed",
            "progress": 100,
            "dataframes_count": len(serialized_dataframes),
            "total_rows": result.total_rows,
            "total_columns": result.total_columns,
            "processing_time": result.processing_time,
            "job_metadata": result.metadata,
            "warnings": result.warnings,
            "completed_at": datetime.utcnow()
        }})
        
        # Update file status
        await file_upload.update({"$set": {
            "status": "completed",
            "processed_at": datetime.utcnow()
        }})
        
        logger.info(f"File processed successfully: {file_id}")
        
        return {
            "file_id": file_id,
            "status": "completed",
            "dataframes_count": len(serialized_dataframes),
            "total_rows": result.total_rows,
            "total_columns": result.total_columns,
            "processing_time": round(result.processing_time, 2),
            "message": "File processed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        if 'job' in locals():
            await job.update({"$set": {"status": "failed", "error_message": str(e)}})
        if 'file_upload' in locals():
            await file_upload.update({"$set": {"status": "failed"}})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """
    Get processing status for a file
    """
    job = await ProcessingJob.find_one(ProcessingJob.file_id == file_id)
    if not job:
        # Check if file even exists
        file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        return {"status": "uploaded", "file_id": file_id}
    
    return job


@router.get("/result/{file_id}")
async def get_processing_result(file_id: str):
    """
    Get full processing result
    """
    cached_result = cache_manager.get(f"processed_result:{file_id}")
    if not cached_result:
        raise HTTPException(status_code=404, detail="Processed data not found. Process the file first.")
    
    return sanitize_dict(cached_result)


@router.delete("/result/{file_id}")
async def delete_processing_result(file_id: str):
    """
    Delete processing result from memory
    """
    if not cache_manager.exists(f"processed_result:{file_id}"):
        raise HTTPException(status_code=404, detail="Processed data not found")
    
    cache_manager.delete(f"processed_result:{file_id}")
    
    return {
        "file_id": file_id,
        "message": "Processing result deleted successfully"
    }