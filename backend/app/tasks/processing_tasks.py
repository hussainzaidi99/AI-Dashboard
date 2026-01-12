"""
Processing Tasks
Celery tasks for file processing operations
"""

#backend/app/tasks/processing_tasks.py

from typing import Dict, Any, List, Optional
import logging

from . import celery_app
from .async_utils import run_async
from app.services import FileService, ProcessingService
from app.utils.cache import cache_manager
from app.models.mongodb_models import ProcessingJob, FileUpload

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='tasks.process_file')
def process_file_task(
    self,
    file_id: str,
    file_extension: str,
    options: Optional[Dict[str, Any]] = None
):
    """
    Process a file asynchronously
    
    Args:
        file_id: File ID
        file_extension: File extension
        options: Processing options
    
    Returns:
        Processing result
    """
    options = options or {}
    try:
        logger.info(f"Processing file: {file_id}")
        
        # Update status in MongoDB
        job = run_async(ProcessingJob.find_one(ProcessingJob.file_id == file_id))
        if job:
            run_async(job.update({"$set": {"status": "running", "progress": 10}}))
        
        # Process file
        processing_service = ProcessingService()
        result = run_async(processing_service.process_file(
            file_id=file_id,
            file_extension=file_extension,
            options=options
        ))
        
        # Store result in Redis
        cache_manager.set(f"processed_result:{file_id}", result, expire=86400)
        
        # Update status in MongoDB
        if job:
            run_async(job.update({"$set": {
                "status": "completed",
                "progress": 100,
                "dataframes_count": len(result['dataframes']),
                "total_rows": result['total_rows'],
                "total_columns": result['total_columns']
            }}))
        
        logger.info(f"File processed successfully: {file_id}")
        
        return {
            "file_id": file_id,
            "status": "completed",
            "dataframes_count": len(result['dataframes']),
            "total_rows": result['total_rows'],
            "total_columns": result['total_columns']
        }
    
    except Exception as e:
        logger.error(f"Error processing file {file_id}: {str(e)}")
        
        # Update status with error in MongoDB
        job = run_async(ProcessingJob.find_one(ProcessingJob.file_id == file_id))
        if job:
            run_async(job.update({"$set": {
                "status": "failed",
                "error_message": str(e),
                "progress": 0
            }}))
        
        raise


@celery_app.task(name='tasks.batch_process_files')
def batch_process_files_task(files: List[Dict[str, str]]):
    """
    Process multiple files in batch
    
    Args:
        files: List of file dictionaries with file_id and file_extension
    
    Returns:
        Batch processing results
    """
    results = []
    
    for file_info in files:
        try:
            result = process_file_task.apply_async(
                args=[file_info['file_id'], file_info['file_extension']],
                kwargs={'options': file_info.get('options', {})}
            )
            
            results.append({
                "file_id": file_info['file_id'],
                "task_id": result.id,
                "status": "queued"
            })
        
        except Exception as e:
            logger.error(f"Error queuing file {file_info['file_id']}: {str(e)}")
            results.append({
                "file_id": file_info['file_id'],
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_files": len(files),
        "queued": len([r for r in results if r['status'] == 'queued']),
        "errors": len([r for r in results if r['status'] == 'error']),
        "results": results
    }


@celery_app.task(name='tasks.cleanup_old_files')
def cleanup_old_files_task(days: int = 7):
    """
    Clean up old files from upload directory
    
    Args:
        days: Delete files older than this many days
    
    Returns:
        Cleanup result
    """
    try:
        logger.info(f"Starting cleanup of files older than {days} days")
        
        file_service = FileService()
        deleted_count = file_service.cleanup_old_files(days=days)
        
        logger.info(f"Cleanup completed: {deleted_count} files deleted")
        
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "days": days
        }
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise


@celery_app.task(name='tasks.analyze_data')
def analyze_data_task(file_id: str, sheet_index: int = 0):
    """
    Perform comprehensive data analysis
    
    Args:
        file_id: File ID
        sheet_index: Sheet index
    
    Returns:
        Analysis results
    """
    try:
        from app.core.analyzers import DataProfiler, StatisticalAnalyzer, QualityChecker
        import pandas as pd
        
        logger.info(f"Analyzing data for file: {file_id}")
        
        # Get data from Redis cache
        data = cache_manager.get(f"processed_result:{file_id}")
        
        if not data:
            # If not in cache, we need to reload it via processing service
            logger.info(f"Cache miss for {file_id}, reloading...")
            file_upload = run_async(FileUpload.find_one(FileUpload.file_id == file_id))
            if not file_upload:
                raise ValueError("File not found")
            
            processing_service = ProcessingService()
            data = run_async(processing_service.process_file(
                file_id=file_id,
                file_extension=file_upload.file_type
            ))
            # Cache it again
            cache_manager.set(f"processed_result:{file_id}", data, expire=86400)
        
        if sheet_index >= len(data['dataframes']):
            raise ValueError("Sheet index out of range")
        
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Profile data
        profiler = DataProfiler()
        profile = profiler.profile(df)
        
        # Statistical analysis
        analyzer = StatisticalAnalyzer()
        stats = analyzer.analyze(df)
        
        # Quality check
        checker = QualityChecker()
        quality = checker.check(df)
        
        logger.info(f"Analysis completed for file: {file_id}")
        
        return {
            "file_id": file_id,
            "sheet_index": sheet_index,
            "profile_summary": {
                "total_rows": profile.total_rows,
                "total_columns": profile.total_columns,
                "memory_usage": profile.memory_usage
            },
            "quality_score": quality.overall_score,
            "issues_count": len(quality.issues),
            "status": "completed"
        }
    
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        raise


@celery_app.task(name='tasks.generate_insights')
def generate_insights_task(file_id: str, sheet_index: int = 0):
    """
    Generate AI-powered insights
    
    Args:
        file_id: File ID
        sheet_index: Sheet index
    
    Returns:
        Insights
    """
    try:
        from app.core.ai import InsightGenerator
        import pandas as pd
        
        logger.info(f"Generating insights for file: {file_id}")
        
        # Get data from Redis
        data = cache_manager.get(f"processed_result:{file_id}")
        
        if not data:
            logger.info(f"Cache miss for {file_id}, reloading...")
            file_upload = run_async(FileUpload.find_one(FileUpload.file_id == file_id))
            if not file_upload:
                raise ValueError("File not found")
            
            processing_service = ProcessingService()
            data = run_async(processing_service.process_file(
                file_id=file_id,
                file_extension=file_upload.file_type
            ))
            cache_manager.set(f"processed_result:{file_id}", data, expire=86400)
        
        if sheet_index >= len(data['dataframes']):
            raise ValueError("Sheet index out of range")
        
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Generate insights
        generator = InsightGenerator()
        insights = generator.analyze_dataframe(df)
        
        logger.info(f"Generated {len(insights)} insights for file: {file_id}")
        
        return {
            "file_id": file_id,
            "sheet_index": sheet_index,
            "insights_count": len(insights),
            "status": "completed"
        }
    
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise