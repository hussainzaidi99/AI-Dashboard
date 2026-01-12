"""
Exporters Module
Multi-format export capabilities for charts, dashboards, and data
"""
#backend/app/core/exporters/__init__.py

from .base_exporter import BaseExporter, ExportDisabledError, ExportFailedError
from .image_exporter import ImageExporter, ImageFormat
from .html_exporter import HTMLExporter
from .pdf_exporter import PDFExporter
from .excel_exporter import ExcelExporter

__all__ = [
    "BaseExporter",
    "ExportDisabledError",
    "ExportFailedError",
    "ImageExporter",
    "ImageFormat",
    "HTMLExporter",
    "PDFExporter",
    "ExcelExporter",
]


# Convenience function for quick export
def export_figure(
    figure,
    output_path: str,
    format: str = None,
    **kwargs
):
    """
    Quick export of a Plotly figure
    
    Args:
        figure: Plotly Figure object
        output_path: Output file path
        format: Export format (auto-detected from path if not provided)
        **kwargs: Additional export options
    
    Returns:
        Path to exported file
    """
    import os
    
    # Auto-detect format from file extension
    if not format:
        _, ext = os.path.splitext(output_path)
        format = ext.lstrip('.').lower()
    
    # Select appropriate exporter
    if format in ['png', 'jpg', 'jpeg', 'svg', 'webp']:
        exporter = ImageExporter()
        return exporter.export(figure, output_path, format=format, **kwargs)
    
    elif format == 'html':
        exporter = HTMLExporter()
        return exporter.export(figure, output_path, **kwargs)
    
    elif format == 'pdf':
        exporter = PDFExporter()
        return exporter.export_figure(figure, output_path, **kwargs)
    
    else:
        raise ValueError(f"Unsupported export format: {format}")


# Convenience function for exporting data with charts
def export_dashboard(
    dataframes: list,
    figures: list,
    output_path: str,
    format: str = 'excel',
    **kwargs
):
    """
    Export data and charts together
    
    Args:
        dataframes: List of pandas DataFrames
        figures: List of Plotly Figures
        output_path: Output file path
        format: Export format ('excel' or 'pdf')
        **kwargs: Additional export options
    
    Returns:
        Path to exported file
    """
    if format == 'excel':
        exporter = ExcelExporter()
        return exporter.export_with_charts(
            dataframes, figures, output_path, **kwargs
        )
    
    elif format == 'pdf':
        exporter = PDFExporter()
        return exporter.export_dashboard(
            dataframes, figures, output_path, **kwargs
        )
    
    else:
        raise ValueError(f"Unsupported dashboard format: {format}")