"""
Image Exporter - Export charts to image formats (PNG, JPG, SVG, WebP)
Uses kaleido for high-quality static image export
"""
#backend/app/core/exporters/image_exporter.py


from typing import Optional, Union
from enum import Enum
import os
import logging
from pathlib import Path
import plotly.graph_objects as go

from app.config import settings
from .base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """Supported image formats"""
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    SVG = "svg"
    WEBP = "webp"


class ImageExporter(BaseExporter):
    """Export Plotly figures to static image formats"""
    
    def __init__(self):
        super().__init__()
        
        # Default dimensions
        self.default_width = settings.CHART_DEFAULT_WIDTH
        self.default_height = settings.CHART_DEFAULT_HEIGHT
    
    def export(
        self,
        figure: go.Figure,
        output_path: str,
        format: str = "png",
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: float = 1.0,
        **kwargs
    ) -> str:
        """
        Export figure to image file
        
        Args:
            figure: Plotly Figure object
            output_path: Output file path
            format: Image format (png, jpg, svg, webp)
            width: Image width in pixels
            height: Image height in pixels
            scale: Scale factor for resolution (1.0 = normal, 2.0 = 2x, etc.)
            **kwargs: Additional export options
        
        Returns:
            Path to exported file
        """
        try:
            # Validate format
            format = format.lower()
            try:
                ImageFormat(format)
            except ValueError:
                raise ValueError(
                    f"Unsupported format: {format}. "
                    f"Supported: {[f.value for f in ImageFormat]}"
                )
            
            # Use default dimensions if not provided
            width = width or self.default_width
            height = height or self.default_height
            
            # Ensure output directory exists
            self._ensure_output_dir(output_path)
            
            # Export based on format
            if format == "svg":
                self._export_svg(figure, output_path, width, height, **kwargs)
            else:
                self._export_raster(
                    figure, output_path, format, width, height, scale, **kwargs
                )
            
            self.logger.info(f"Exported figure to {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Error exporting figure: {str(e)}")
            raise
    
    def _export_raster(
        self,
        figure: go.Figure,
        output_path: str,
        format: str,
        width: int,
        height: int,
        scale: float,
        **kwargs
    ):
        """Export to raster format (PNG, JPG, WebP)"""
        try:
            # Try using kaleido
            figure.write_image(
                output_path,
                format=format,
                width=width,
                height=height,
                scale=scale,
                engine="kaleido"
            )
        except Exception as e:
            raise RuntimeError(
                f"Image export failed. Please ensure kaleido is installed: "
                f"pip install kaleido. Original error: {str(e)}"
            )
    
    def _export_svg(
        self,
        figure: go.Figure,
        output_path: str,
        width: int,
        height: int,
        **kwargs
    ):
        """Export to SVG format"""
        try:
            figure.write_image(
                output_path,
                format="svg",
                width=width,
                height=height,
                engine="kaleido"
            )
        except Exception as e:
            raise RuntimeError(
                f"SVG export failed. Error: {str(e)}"
            )
    
    def export_high_res(
        self,
        figure: go.Figure,
        output_path: str,
        format: str = "png",
        dpi: int = 300
    ) -> str:
        """
        Export high-resolution image suitable for printing
        
        Args:
            figure: Plotly Figure object
            output_path: Output file path
            format: Image format
            dpi: Dots per inch (300 recommended for print)
        
        Returns:
            Path to exported file
        """
        # Calculate scale factor based on DPI
        # 96 DPI is the default for web
        scale = dpi / 96.0
        
        return self.export(
            figure=figure,
            output_path=output_path,
            format=format,
            scale=scale
        )
    
    def export_thumbnail(
        self,
        figure: go.Figure,
        output_path: str,
        format: str = "png",
        max_width: int = 400,
        max_height: int = 300
    ) -> str:
        """
        Export thumbnail version of chart
        
        Args:
            figure: Plotly Figure object
            output_path: Output file path
            format: Image format
            max_width: Maximum width
            max_height: Maximum height
        
        Returns:
            Path to exported file
        """
        return self.export(
            figure=figure,
            output_path=output_path,
            format=format,
            width=max_width,
            height=max_height,
            scale=1.0
        )
    
    def export_multiple(
        self,
        figures: list,
        output_dir: str,
        format: str = "png",
        prefix: str = "chart",
        **kwargs
    ) -> list:
        """
        Export multiple figures to image files
        
        Args:
            figures: List of Plotly Figure objects
            output_dir: Output directory
            format: Image format
            prefix: Filename prefix
            **kwargs: Additional export options
        
        Returns:
            List of exported file paths
        """
        self._ensure_output_dir(output_dir)
        
        exported_paths = []
        
        for idx, fig in enumerate(figures, 1):
            output_path = os.path.join(
                output_dir,
                f"{prefix}_{idx}.{format}"
            )
            
            try:
                self.export(fig, output_path, format=format, **kwargs)
                exported_paths.append(output_path)
            except Exception as e:
                self.logger.error(f"Failed to export figure {idx}: {str(e)}")
        
        self.logger.info(f"Exported {len(exported_paths)} figures to {output_dir}")
        return exported_paths
    
    def export_with_transparent_background(
        self,
        figure: go.Figure,
        output_path: str,
        format: str = "png"
    ) -> str:
        """
        Export figure with transparent background
        
        Args:
            figure: Plotly Figure object
            output_path: Output file path
            format: Image format (png or svg recommended)
        
        Returns:
            Path to exported file
        """
        # Clone figure to avoid modifying original
        fig_copy = go.Figure(figure)
        
        # Set transparent background
        fig_copy.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return self.export(fig_copy, output_path, format=format)
    
    def get_supported_formats(self) -> list:
        """Get list of supported image formats"""
        return [f.value for f in ImageFormat]
    
    def validate_path(self, output_path: str) -> bool:
        """
        Validate output path
        
        Args:
            output_path: Path to validate
        
        Returns:
            True if valid
        
        Raises:
            ExportFailedError: If path is invalid or not writable
        """
        return self._validate_path(output_path)