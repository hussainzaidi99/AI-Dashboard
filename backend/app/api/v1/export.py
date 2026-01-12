"""
Export API Endpoints
Export charts and data to various formats
"""
#backend/app/api/v1/export.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import plotly.graph_objects as go
from plotly.io import from_json
import os
import json
import logging

from app.core.exporters import ImageExporter, HTMLExporter, PDFExporter, ExcelExporter
from app.config import get_export_path
from app.utils.cache import cache_manager
from app.models.mongodb_models import FileUpload

router = APIRouter()
logger = logging.getLogger(__name__)


class ExportChartRequest(BaseModel):
    chart_json: dict
    format: str  # png, jpg, svg, html, pdf
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ExportDataRequest(BaseModel):
    file_id: str
    sheet_index: int = 0
    format: str  # excel, csv
    filename: Optional[str] = None


class ExportDashboardRequest(BaseModel):
    dashboard_json: dict
    format: str  # html, pdf
    filename: Optional[str] = None


@router.post("/export/chart")
async def export_chart(request: ExportChartRequest):
    """
    Export a chart to image or HTML format
    """
    try:
        # Reconstruct Plotly figure from JSON
        fig = go.Figure(request.chart_json)
        
        # Generate filename
        if not request.filename:
            request.filename = f"chart_{int(pd.Timestamp.now().timestamp())}.{request.format}"
        
        output_path = get_export_path(request.filename)
        
        # Export based on format
        if request.format in ['png', 'jpg', 'jpeg', 'svg', 'webp']:
            exporter = ImageExporter()
            exporter.export(
                figure=fig,
                output_path=output_path,
                format=request.format,
                width=request.width,
                height=request.height
            )
        
        elif request.format == 'html':
            exporter = HTMLExporter()
            exporter.export(
                figure=fig,
                output_path=output_path,
                title=request.filename.rsplit('.', 1)[0]
            )
        
        elif request.format == 'pdf':
            exporter = PDFExporter()
            exporter.export_figure(
                figure=fig,
                output_path=output_path,
                width=request.width or 800,
                height=request.height or 600
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        # Return file
        return FileResponse(
            path=output_path,
            filename=request.filename,
            media_type=f"image/{request.format}" if request.format != 'html' else "text/html"
        )
    
    except Exception as e:
        logger.error(f"Error exporting chart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/data")
async def export_data(request: ExportDataRequest):
    """
    Export data to Excel or CSV format
    """
    try:
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == request.file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = cache_manager.get(f"processed_result:{request.file_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Data not found in cache")
        
        if request.sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][request.sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Generate filename
        if not request.filename:
            request.filename = f"data_{int(pd.Timestamp.now().timestamp())}.{request.format}"
        
        output_path = get_export_path(request.filename)
        
        # Export based on format
        if request.format == 'excel':
            exporter = ExcelExporter()
            exporter.export_formatted(
                df=df,
                output_path=output_path,
                sheet_name=sheet_data['sheet_name']
            )
        
        elif request.format == 'csv':
            df.to_csv(output_path, index=False)
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        # Return file
        return FileResponse(
            path=output_path,
            filename=request.filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" 
                      if request.format == 'excel' else "text/csv"
        )
    
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/dashboard")
async def export_dashboard(request: ExportDashboardRequest):
    """
    Export dashboard to HTML or PDF
    """
    try:
        # Extract figures from dashboard JSON
        widgets = request.dashboard_json.get('widgets', [])
        figures = []
        descriptions = []
        
        for widget in widgets:
            fig = go.Figure(widget['chart'])
            figures.append(fig)
            descriptions.append(widget.get('title', ''))
        
        if not figures:
            raise HTTPException(status_code=400, detail="No charts in dashboard")
        
        # Generate filename
        if not request.filename:
            request.filename = f"dashboard_{int(pd.Timestamp.now().timestamp())}.{request.format}"
        
        output_path = get_export_path(request.filename)
        
        # Export based on format
        if request.format == 'html':
            exporter = HTMLExporter()
            exporter.export_dashboard(
                figures=figures,
                output_path=output_path,
                title=request.dashboard_json.get('title', 'Dashboard'),
                descriptions=descriptions,
                layout='grid'
            )
        
        elif request.format == 'pdf':
            exporter = PDFExporter()
            # Convert figures for PDF
            dataframes = [pd.DataFrame() for _ in figures]  # Empty dataframes
            exporter.export_dashboard(
                dataframes=dataframes,
                figures=figures,
                output_path=output_path,
                title=request.dashboard_json.get('title', 'Dashboard'),
                include_data_tables=False
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        # Return file
        return FileResponse(
            path=output_path,
            filename=request.filename,
            media_type="text/html" if request.format == 'html' else "application/pdf"
        )
    
    except Exception as e:
        logger.error(f"Error exporting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/formats")
async def get_export_formats():
    """
    Get available export formats
    """
    return {
        "chart_formats": ["png", "jpg", "jpeg", "svg", "webp", "html", "pdf"],
        "data_formats": ["excel", "csv"],
        "dashboard_formats": ["html", "pdf"]
    }