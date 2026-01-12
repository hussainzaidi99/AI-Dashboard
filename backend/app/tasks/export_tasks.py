#backend/app/tasks/export_tasks.py

"""
Export Tasks
Celery tasks for export operations
"""

from typing import Dict, Any, List, Optional
import os
import json
from datetime import datetime, timedelta
import logging
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

from . import celery_app
from .async_utils import run_async
from app.services import ExportService, ProcessingService
from app.config import settings, get_export_path
from app.utils.cache import cache_manager
from app.models.mongodb_models import FileUpload

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='tasks.export_chart')
def export_chart_task(
    self,
    chart_json: Dict[str, Any],
    format: str,
    filename: Optional[str] = None,
    **kwargs
):
    """
    Export chart asynchronously
    
    Args:
        chart_json: Plotly chart JSON or dict
        format: Export format
        filename: Output filename
        **kwargs: Additional export options
    
    Returns:
        Export result
    """
    try:
        logger.info(f"Exporting chart to {format}")
        
        # Robust Reconstruct figure
        if isinstance(chart_json, str):
            fig = pio.from_json(chart_json)
        else:
            fig = pio.from_json(json.dumps(chart_json))
        
        # Export
        export_service = ExportService()
        output_path = run_async(export_service.export_chart(
            fig=fig,
            format=format,
            filename=filename,
            **kwargs
        ))
        
        logger.info(f"Chart exported successfully: {output_path}")
        
        return {
            "status": "completed",
            "output_path": output_path,
            "filename": os.path.basename(output_path),
            "format": format
        }
    
    except Exception as e:
        logger.error(f"Error exporting chart: {str(e)}")
        raise


@celery_app.task(bind=True, name='tasks.export_data')
def export_data_task(
    self,
    data: List[Dict[str, Any]],
    format: str,
    filename: Optional[str] = None,
    **kwargs
):
    """
    Export data asynchronously
    
    Args:
        data: Data to export (list of records)
        format: Export format
        filename: Output filename
        **kwargs: Additional export options
    
    Returns:
        Export result
    """
    try:
        logger.info(f"Exporting data to {format}")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Export
        export_service = ExportService()
        output_path = run_async(export_service.export_data(
            df=df,
            format=format,
            filename=filename,
            **kwargs
        ))
        
        logger.info(f"Data exported successfully: {output_path}")
        
        return {
            "status": "completed",
            "output_path": output_path,
            "filename": os.path.basename(output_path),
            "format": format,
            "rows_exported": len(data)
        }
    
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise


@celery_app.task(bind=True, name='tasks.export_dashboard')
def export_dashboard_task(
    self,
    dashboard_json: Dict[str, Any],
    format: str,
    filename: Optional[str] = None,
    **kwargs
):
    """
    Export dashboard asynchronously
    
    Args:
        dashboard_json: Dashboard JSON
        format: Export format
        filename: Output filename
        **kwargs: Additional export options
    
    Returns:
        Export result
    """
    try:
        logger.info(f"Exporting dashboard to {format}")
        
        # Extract figures
        widgets = dashboard_json.get('widgets', [])
        figures = []
        descriptions = []
        
        for widget in widgets:
            chart_data = widget['chart']
            if isinstance(chart_data, str):
                fig = pio.from_json(chart_data)
            else:
                fig = pio.from_json(json.dumps(chart_data))
            
            figures.append(fig)
            descriptions.append(widget.get('title', ''))
        
        # Export
        export_service = ExportService()
        output_path = run_async(export_service.export_dashboard(
            figures=figures,
            format=format,
            filename=filename,
            title=dashboard_json.get('title', 'Dashboard'),
            descriptions=descriptions,
            **kwargs
        ))
        
        logger.info(f"Dashboard exported successfully: {output_path}")
        
        return {
            "status": "completed",
            "output_path": output_path,
            "filename": os.path.basename(output_path),
            "format": format,
            "widgets_count": len(widgets)
        }
    
    except Exception as e:
        logger.error(f"Error exporting dashboard: {str(e)}")
        raise


@celery_app.task(name='tasks.batch_export_charts')
def batch_export_charts_task(
    charts: List[Dict[str, Any]],
    format: str = 'png'
):
    """
    Export multiple charts in batch
    
    Args:
        charts: List of chart dictionaries
        format: Export format
    
    Returns:
        Batch export results
    """
    results = []
    
    for idx, chart_info in enumerate(charts):
        try:
            result = export_chart_task.apply_async(
                args=[chart_info['chart_json'], format],
                kwargs={'filename': chart_info.get('filename')}
            )
            
            results.append({
                "chart_index": idx,
                "task_id": result.id,
                "status": "queued"
            })
        
        except Exception as e:
            logger.error(f"Error queuing chart {idx}: {str(e)}")
            results.append({
                "chart_index": idx,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_charts": len(charts),
        "queued": len([r for r in results if r['status'] == 'queued']),
        "errors": len([r for r in results if r['status'] == 'error']),
        "results": results
    }


@celery_app.task(name='tasks.cleanup_old_exports')
def cleanup_old_exports_task(days: int = 1):
    """
    Clean up old export files
    
    Args:
        days: Delete files older than this many days
    
    Returns:
        Cleanup result
    """
    try:
        logger.info(f"Starting cleanup of exports older than {days} days")
        
        deleted_count = 0
        export_dir = settings.EXPORT_DIR
        
        if not os.path.exists(export_dir):
            return {
                "status": "completed",
                "deleted_count": 0,
                "message": "Export directory does not exist"
            }
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(export_dir):
            file_path = os.path.join(export_dir, filename)
            
            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_time:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.debug(f"Deleted old export: {filename}")
                    except Exception as e:
                        logger.error(f"Error deleting {filename}: {str(e)}")
        
        logger.info(f"Cleanup completed: {deleted_count} exports deleted")
        
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "days": days
        }
    
    except Exception as e:
        logger.error(f"Error during exports cleanup: {str(e)}")
        raise


@celery_app.task(name='tasks.generate_report')
def generate_report_task(
    file_id: str,
    sheet_index: int = 0,
    format: str = 'pdf'
):
    """
    Generate comprehensive report
    
    Args:
        file_id: File ID
        sheet_index: Sheet index
        format: Report format (pdf or html)
    
    Returns:
        Report generation result
    """
    try:
        from app.core.analyzers import DataProfiler, QualityChecker
        from app.core.visualizers import DashboardBuilder
        from app.services import ProcessingService
        
        logger.info(f"Generating report for file: {file_id}")
        
        # Get data from Redis cache
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
        
        # Generate analysis
        profiler = DataProfiler()
        profile = profiler.profile(df)
        
        checker = QualityChecker()
        quality = checker.check(df)
        
        # Create dashboard
        builder = DashboardBuilder()
        dashboard = builder.create_summary_dashboard(
            df=df,
            profile_result=profile,
            quality_report=quality
        )
        
        # Export dashboard as report
        figures = [widget.figure for widget in dashboard.widgets]
        
        export_service = ExportService()
        output_path = run_async(export_service.export_dashboard(
            figures=figures,
            format=format,
            filename=f"report_{file_id}_{int(datetime.now().timestamp())}.{format}",
            title=f"Data Report - {data['filename']}"
        ))
        
        logger.info(f"Report generated successfully: {output_path}")
        
        return {
            "status": "completed",
            "output_path": output_path,
            "filename": os.path.basename(output_path),
            "format": format,
            "quality_score": quality.overall_score
        }
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise