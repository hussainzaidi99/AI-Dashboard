"""
PDF Exporter - Export charts and dashboards to PDF format
Creates professional PDF reports with charts and data
"""
#backend/app/core/exporters/pdf_exporter.py

from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import plotly.graph_objects as go
import logging

from app.config import settings
from .base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class PDFExporter(BaseExporter):
    """Export charts and dashboards to PDF format"""
    
    def __init__(self):
        super().__init__()
        
        # Check if feature is enabled
        self._ensure_enabled(settings.ENABLE_EXPORT_PDF, "PDF")
    
    def export_figure(
        self,
        figure: go.Figure,
        output_path: str,
        width: int = 800,
        height: int = 600,
        **kwargs
    ) -> str:
        """
        Export single figure to PDF
        
        Args:
            figure: Plotly Figure object
            output_path: Output file path
            width: Image width
            height: Image height
            **kwargs: Additional options
        
        Returns:
            Path to exported file
        """
        try:
            # Ensure output directory exists
            self._ensure_output_dir(output_path)
            
            # Export figure to PDF using kaleido
            figure.write_image(
                output_path,
                format="pdf",
                width=width,
                height=height,
                engine="kaleido"
            )
            
            self.logger.info(f"Exported figure to PDF: {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Error exporting figure to PDF: {str(e)}")
            raise RuntimeError(
                f"PDF export failed. Ensure kaleido is installed: "
                f"pip install kaleido. Error: {str(e)}"
            )
    
    def export_dashboard(
        self,
        dataframes: List,
        figures: List[go.Figure],
        output_path: str,
        title: str = "Dashboard Report",
        include_data_tables: bool = True,
        **kwargs
    ) -> str:
        """
        Export dashboard with multiple charts and data to PDF
        
        Args:
            dataframes: List of pandas DataFrames
            figures: List of Plotly Figure objects
            output_path: Output file path
            title: Report title
            include_data_tables: Whether to include data tables
            **kwargs: Additional options
        
        Returns:
            Path to exported file
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Image,
                Table, TableStyle, PageBreak
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Ensure output directory exists
            self._ensure_output_dir(output_path)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=kwargs.get('pagesize', letter),
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            # Container for PDF elements
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            # Custom title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Add title
            elements.append(Paragraph(title, title_style))
            
            # Add timestamp
            timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
            timestamp_style = ParagraphStyle(
                'Timestamp',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(f"Generated on {timestamp}", timestamp_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Add charts and data using temp directory context manager
            with self._temp_dir() as temp_dir:
                for idx, fig in enumerate(figures):
                    # Add chart title if available
                    if fig.layout.title.text:
                        chart_title_style = ParagraphStyle(
                            'ChartTitle',
                            parent=styles['Heading2'],
                            fontSize=16,
                            textColor=colors.HexColor('#34495e'),
                            spaceAfter=10
                        )
                        elements.append(Paragraph(fig.layout.title.text, chart_title_style))
                    
                    # Export chart as temporary image
                    temp_image_path = os.path.join(temp_dir, f"chart_{idx}.png")
                    fig.write_image(
                        temp_image_path,
                        format="png",
                        width=700,
                        height=400,
                        scale=2,
                        engine="kaleido"
                    )
                    
                    # Add image to PDF
                    img = Image(temp_image_path, width=6.5*inch, height=3.7*inch)
                    elements.append(img)
                    elements.append(Spacer(1, 0.2*inch))
                    
                    # Add corresponding data table if requested
                    if include_data_tables and idx < len(dataframes):
                        df = dataframes[idx]
                        
                        if not df.empty:
                            elements.append(Paragraph("Data Table", styles['Heading3']))
                            elements.append(Spacer(1, 0.1*inch))
                            
                            # Convert dataframe to table (first 20 rows and limit columns)
                            max_cols = kwargs.get('max_cols', 8)
                            display_df = df.iloc[:20, :max_cols]
                            table_data = [display_df.columns.tolist()] + display_df.values.tolist()
                            
                            # Calculate column widths to avoid overflow (approximate)
                            available_width = doc.width
                            col_width = available_width / len(display_df.columns)
                            
                            # Create table
                            t = Table(table_data, repeatRows=1, colWidths=[col_width] * len(display_df.columns))
                            t.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ('FONTSIZE', (0, 1), (-1, -1), 8),
                                ('WORDWRAP', (0, 0), (-1, -1), True),
                            ]))
                            
                            elements.append(t)
                            elements.append(Spacer(1, 0.2*inch))
                    
                    # Add page break between charts (except last one)
                    if idx < len(figures) - 1:
                        elements.append(PageBreak())
            
            # Build PDF
            doc.build(elements)
            
            self._log_export_success(output_path, "dashboard PDF")
            return output_path
        
        except ImportError:
            raise RuntimeError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            )
        except Exception as e:
            self._log_export_error(e, "dashboard PDF")
            raise
    
    def export_report(
        self,
        content: Dict[str, Any],
        output_path: str,
        **kwargs
    ) -> str:
        """
        Export custom report to PDF
        
        Args:
            content: Dictionary with report sections
                {
                    'title': str,
                    'summary': str,
                    'sections': [
                        {
                            'title': str,
                            'text': str,
                            'figure': go.Figure (optional),
                            'table': pd.DataFrame (optional)
                        }
                    ]
                }
            output_path: Output file path
            **kwargs: Additional options
        
        Returns:
            Path to exported file
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Image,
                Table, TableStyle, PageBreak
            )
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Add title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                fontSize=28,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(content.get('title', 'Report'), title_style))
            
            # Add summary
            if 'summary' in content:
                summary_style = ParagraphStyle(
                    'Summary',
                    parent=styles['BodyText'],
                    fontSize=12,
                    alignment=TA_JUSTIFY,
                    spaceAfter=20
                )
                elements.append(Paragraph(content['summary'], summary_style))
                elements.append(Spacer(1, 0.3*inch))
            
            # Add sections using temp directory context manager
            with self._temp_dir() as temp_dir:
                for idx, section in enumerate(content.get('sections', [])):
                    # Section title
                    if 'title' in section:
                        elements.append(Paragraph(section['title'], styles['Heading2']))
                        elements.append(Spacer(1, 0.1*inch))
                    
                    # Section text
                    if 'text' in section:
                        elements.append(Paragraph(section['text'], styles['BodyText']))
                        elements.append(Spacer(1, 0.2*inch))
                    
                    # Section figure
                    if 'figure' in section:
                        temp_image_path = os.path.join(temp_dir, f"section_{idx}.png")
                        section['figure'].write_image(
                            temp_image_path,
                            format="png",
                            width=700,
                            height=400,
                            scale=2,
                            engine="kaleido"
                        )
                        
                        img = Image(temp_image_path, width=6.5*inch, height=3.7*inch)
                        elements.append(img)
                        elements.append(Spacer(1, 0.2*inch))
                    
                    # Section table
                    if 'table' in section:
                        df = section['table']
                        if not df.empty:
                            table_data = [df.columns.tolist()] + df.head(15).values.tolist()
                            t = Table(table_data)
                            t.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))
                            elements.append(t)
                            elements.append(Spacer(1, 0.2*inch))
                    
                    # Page break between sections
                    if idx < len(content['sections']) - 1:
                        elements.append(PageBreak())
            
            # Build PDF
            doc.build(elements)
            
            self._log_export_success(output_path, "report PDF")
            return output_path
        
        except ImportError:
            raise RuntimeError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            )
        except Exception as e:
            self._log_export_error(e, "report PDF")
            raise