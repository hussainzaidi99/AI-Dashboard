#backend/app/services/export_service.py

"""
Export Service
Business logic for export operations
"""

import pandas as pd
import plotly.graph_objects as go
from typing import List, Optional
import logging

from app.core.exporters import (
    ImageExporter,
    HTMLExporter,
    PDFExporter,
    ExcelExporter
)
from app.config import get_export_path

logger = logging.getLogger(__name__)


class ExportService:
    """Service for export operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.image_exporter = ImageExporter()
        self.html_exporter = HTMLExporter()
        self.pdf_exporter = PDFExporter()
        self.excel_exporter = ExcelExporter()
    
    async def export_chart(
        self,
        fig: go.Figure,
        format: str,
        filename: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Export chart to file
        
        Args:
            fig: Plotly Figure
            format: Export format
            filename: Output filename
            **kwargs: Additional export options
        
        Returns:
            Path to exported file
        """
        try:
            if not filename:
                filename = f"chart_{int(pd.Timestamp.now().timestamp())}.{format}"
            
            output_path = get_export_path(filename)
            
            if format in ['png', 'jpg', 'jpeg', 'svg', 'webp']:
                return self.image_exporter.export(
                    figure=fig,
                    output_path=output_path,
                    format=format,
                    **kwargs
                )
            
            elif format == 'html':
                return self.html_exporter.export(
                    figure=fig,
                    output_path=output_path,
                    **kwargs
                )
            
            elif format == 'pdf':
                return self.pdf_exporter.export_figure(
                    figure=fig,
                    output_path=output_path,
                    **kwargs
                )
            
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        except Exception as e:
            self.logger.error(f"Error exporting chart: {str(e)}")
            raise
    
    async def export_data(
        self,
        df: pd.DataFrame,
        format: str,
        filename: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Export data to file
        
        Args:
            df: pandas DataFrame
            format: Export format (excel or csv)
            filename: Output filename
            **kwargs: Additional export options
        
        Returns:
            Path to exported file
        """
        try:
            if not filename:
                ext = "xlsx" if format == "excel" else format
                filename = f"data_{int(pd.Timestamp.now().timestamp())}.{ext}"
            
            output_path = get_export_path(filename)
            
            if format == 'excel':
                return self.excel_exporter.export_formatted(
                    df=df,
                    output_path=output_path,
                    **kwargs
                )
            
            elif format == 'csv':
                df.to_csv(output_path, index=False)
                return output_path
            
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
            raise
    
    async def export_dashboard(
        self,
        figures: List[go.Figure],
        format: str,
        filename: Optional[str] = None,
        title: str = "Dashboard",
        descriptions: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Export dashboard to file
        
        Args:
            figures: List of Plotly Figures
            format: Export format (html or pdf)
            filename: Output filename
            title: Dashboard title
            descriptions: Chart descriptions
            **kwargs: Additional export options
        
        Returns:
            Path to exported file
        """
        try:
            if not filename:
                filename = f"dashboard_{int(pd.Timestamp.now().timestamp())}.{format}"
            
            output_path = get_export_path(filename)
            
            if format == 'html':
                return self.html_exporter.export_dashboard(
                    figures=figures,
                    output_path=output_path,
                    title=title,
                    descriptions=descriptions,
                    **kwargs
                )
            
            elif format == 'pdf':
                dataframes = [pd.DataFrame() for _ in figures]
                return self.pdf_exporter.export_dashboard(
                    dataframes=dataframes,
                    figures=figures,
                    output_path=output_path,
                    title=title,
                    include_data_tables=False
                )
            
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        except Exception as e:
            self.logger.error(f"Error exporting dashboard: {str(e)}")
            raise