"""
Charts API Endpoints
Chart generation and visualization
"""
#backend/app/api/v1/charts.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
import logging
import json

from app.core.visualizers import ChartFactory, DashboardBuilder
from app.models.mongodb_models import FileUpload, ChartData, Dashboard as MongoDBDashboard
from app.utils.cache import cache_manager
from app.utils.data_persistence import get_processed_data

router = APIRouter()
logger = logging.getLogger(__name__)


class ChartRequest(BaseModel):
    file_id: str
    sheet_index: int = 0
    chart_type: str
    x: Optional[str] = None
    y: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    title: Optional[str] = None
    options: Optional[Dict[str, Any]] = {}


class DashboardRequest(BaseModel):
    file_id: str
    sheet_index: int = 0
    title: Optional[str] = "Dashboard"
    max_charts: int = 6


@router.post("/create")
async def create_chart(request: ChartRequest):
    """
    Create a chart from data
    """
    try:
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == request.file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = await get_processed_data(request.file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        if request.sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][request.sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Create chart
        factory = ChartFactory()
        fig = factory.create(
            chart_type=request.chart_type,
            df=df,
            x=request.x,
            y=request.y,
            color=request.color,
            size=request.size,
            title=request.title,
            **request.options
        )
        
        # Convert to JSON
        chart_json = fig.to_json()
        
        return {
            "file_id": request.file_id,
            "chart_type": request.chart_type,
            "chart": json.loads(chart_json),
            "message": "Chart created successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_charts(
    file_id: str,
    sheet_index: int = 0,
    user_intent: Optional[str] = None
):
    """
    Get AI-powered chart recommendations
    """
    try:
        from app.core.ai import ChartRecommender
        
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = await get_processed_data(file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        if sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Get recommendations
        recommender = ChartRecommender()
        recommendations = await recommender.recommend_charts(
            df=df,
            user_intent=user_intent,
            use_ai=True
        )
        
        # Convert to serializable format
        results = []
        for rec in recommendations:
            results.append({
                "chart_type": rec.chart_type,
                "confidence": rec.confidence,
                "reasoning": rec.reasoning,
                "columns_required": rec.columns_required,
                "config": rec.config
            })
        
        return {
            "file_id": file_id,
            "sheet_index": sheet_index,
            "recommendations": results
        }
    
    except Exception as e:
        logger.error(f"Error recommending charts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard")
async def create_dashboard(request: DashboardRequest):
    """
    Create an auto-generated dashboard
    """
    try:
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == request.file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = await get_processed_data(request.file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        has_dataframes = data.get('dataframes') and len(data['dataframes']) > 0
        
        if not has_dataframes:
            # Return empty dashboard for text-only files
            return {
                "dashboard_id": "text_dashboard",
                "title": request.title,
                "description": "Document contains primarily text. Use the AI Intelligence Hub for analysis.",
                "widget_count": 0,
                "widgets": [],
                "created_at": None,
                "is_text_only": True
            }

        if request.sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][request.sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Create dashboard
        builder = DashboardBuilder()
        dashboard = builder.create_auto_dashboard(
            df=df,
            title=request.title,
            max_charts=request.max_charts
        )
        
        # Convert widgets to serializable format
        widgets = []
        for widget in dashboard.widgets:
            # Skip widgets with None figures
            if widget.figure is None:
                logger.warning(f"Skipping widget {widget.id} with None figure")
                continue
            
            widgets.append({
                "id": widget.id,
                "chart_type": widget.chart_type,
                "title": widget.title,
                "description": widget.description,
                "chart": json.loads(widget.figure.to_json())
            })
        
        return {
            "dashboard_id": dashboard.id,
            "title": dashboard.title,
            "description": dashboard.description,
            "widget_count": len(widgets),
            "widgets": widgets,
            "created_at": dashboard.created_at
        }
    
    except Exception as e:
        logger.error(f"Error creating dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_chart_types():
    """
    Get list of available chart types
    """
    from app.core.visualizers import ChartType
    
    chart_types = []
    for chart_type in ChartType:
        chart_types.append({
            "value": chart_type.value,
            "name": chart_type.name
        })
    
    return {
        "chart_types": chart_types,
        "total": len(chart_types)
    }


@router.post("/correlation")
async def create_correlation_matrix(
    file_id: str,
    sheet_index: int = 0
):
    """
    Create correlation matrix heatmap
    """
    try:
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = await get_processed_data(file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        if sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Create correlation matrix
        factory = ChartFactory()
        fig = factory.create_correlation_matrix(df)
        
        return {
            "file_id": file_id,
            "chart": json.loads(fig.to_json())
        }
    
    except Exception as e:
        logger.error(f"Error creating correlation matrix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))