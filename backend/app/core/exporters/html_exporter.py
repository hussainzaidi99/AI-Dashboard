"""
HTML Exporter - Export charts and dashboards to interactive HTML
Creates standalone HTML files with embedded Plotly charts
"""
#backend/app/core/exporters/html_exporter.py


from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import plotly.graph_objects as go
import logging

from app.config import settings
from .base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class HTMLExporter(BaseExporter):
    """Export Plotly figures to interactive HTML files"""
    
    def __init__(self):
        super().__init__()
    
    def export(
        self,
        figure: go.Figure,
        output_path: str,
        title: Optional[str] = None,
        include_plotlyjs: str = 'cdn',
        full_html: bool = True,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Export single figure to HTML
        
        Args:
            figure: Plotly Figure object
            output_path: Output file path
            title: HTML page title
            include_plotlyjs: How to include Plotly.js ('cdn', True, False)
            full_html: Generate full HTML document
            config: Plotly config options
            **kwargs: Additional options
        
        Returns:
            Path to exported file
        """
        try:
            # Ensure output directory exists
            self._ensure_output_dir(output_path)
            
            # Default config
            if config is None:
                config = {
                    'displayModeBar': True,
                    'responsive': True,
                    'displaylogo': False,
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'chart',
                        'height': 600,
                        'width': 1000,
                        'scale': 2
                    }
                }
            
            # Export to HTML
            figure.write_html(
                output_path,
                include_plotlyjs=include_plotlyjs,
                full_html=full_html,
                config=config,
                auto_open=False
            )
            
            # Add custom title if provided and full_html is True
            if title and full_html:
                self._add_custom_title(output_path, title)
            
            self.logger.info(f"Exported HTML to {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Error exporting HTML: {str(e)}")
            raise
    
    def export_dashboard(
        self,
        figures: List[go.Figure],
        output_path: str,
        title: str = "Dashboard",
        descriptions: Optional[List[str]] = None,
        layout: str = "grid",
        columns: int = 2,
        **kwargs
    ) -> str:
        """
        Export multiple figures as a dashboard
        
        Args:
            figures: List of Plotly Figure objects
            output_path: Output file path
            title: Dashboard title
            descriptions: Optional descriptions for each chart
            layout: Layout type ('grid', 'vertical', 'tabs')
            columns: Number of columns for grid layout
            **kwargs: Additional options
        
        Returns:
            Path to exported file
        """
        try:
            # Ensure output directory exists
            self._ensure_output_dir(output_path)
            
            # Generate HTML based on layout type
            if layout == "grid":
                html = self._generate_grid_layout(
                    figures, title, descriptions, columns
                )
            elif layout == "vertical":
                html = self._generate_vertical_layout(
                    figures, title, descriptions
                )
            elif layout == "tabs":
                html = self._generate_tabbed_layout(
                    figures, title, descriptions
                )
            else:
                raise ValueError(f"Unsupported layout: {layout}")
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.logger.info(f"Exported dashboard to {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Error exporting dashboard: {str(e)}")
            raise
    
    def _generate_grid_layout(
        self,
        figures: List[go.Figure],
        title: str,
        descriptions: Optional[List[str]],
        columns: int
    ) -> str:
        """Generate grid layout HTML"""
        
        # Convert figures to HTML divs
        chart_htmls = []
        for idx, fig in enumerate(figures):
            chart_html = fig.to_html(
                include_plotlyjs=False,
                div_id=f'chart_{idx}',
                full_html=False,
                config={'responsive': True, 'displaylogo': False}
            )
            
            from html import escape
            
            description = ""
            if descriptions and idx < len(descriptions):
                escaped_desc = escape(descriptions[idx])
                description = f'<p class="chart-description">{escaped_desc}</p>'
            
            chart_htmls.append(f'''
            <div class="chart-container">
                {description}
                {chart_html}
            </div>
            ''')
        
        # Generate complete HTML
        html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat({columns}, 1fr);
            gap: 20px;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .chart-description {{
            color: #34495e;
            margin-bottom: 15px;
            font-size: 0.95em;
            line-height: 1.5;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p class="timestamp">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <div class="dashboard-grid">
        {''.join(chart_htmls)}
    </div>
</body>
</html>
'''
        return html
    
    def _generate_vertical_layout(
        self,
        figures: List[go.Figure],
        title: str,
        descriptions: Optional[List[str]]
    ) -> str:
        """Generate vertical layout HTML"""
        return self._generate_grid_layout(figures, title, descriptions, columns=1)
    
    def _generate_tabbed_layout(
        self,
        figures: List[go.Figure],
        title: str,
        descriptions: Optional[List[str]]
    ) -> str:
        """Generate tabbed layout HTML"""
        
        # Generate tabs and content
        tabs_html = []
        content_html = []
        
        for idx, fig in enumerate(figures):
            from html import escape
            tab_title = f"Chart {idx + 1}"
            if descriptions and idx < len(descriptions):
                tab_title = escape(descriptions[idx][:30])  # Truncate and escape for tab
            
            active_class = "active" if idx == 0 else ""
            
            tabs_html.append(f'''
            <button class="tab-button {active_class}" onclick="openTab(event, 'tab{idx}')">
                {tab_title}
            </button>
            ''')
            
            chart_html = fig.to_html(
                include_plotlyjs=False,
                div_id=f'chart_{idx}',
                full_html=False,
                config={'responsive': True, 'displaylogo': False}
            )
            
            description = ""
            if descriptions and idx < len(descriptions):
                description = f'<p class="chart-description">{descriptions[idx]}</p>'
            
            content_html.append(f'''
            <div id="tab{idx}" class="tab-content {active_class}">
                {description}
                {chart_html}
            </div>
            ''')
        
        html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .tabs {{
            background: white;
            border-radius: 10px 10px 0 0;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .tab-button {{
            background: #ecf0f1;
            border: none;
            padding: 15px 25px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }}
        
        .tab-button:hover {{
            background: #bdc3c7;
        }}
        
        .tab-button.active {{
            background: white;
            border-bottom: 3px solid #3498db;
        }}
        
        .tab-content {{
            display: none;
            background: white;
            padding: 30px;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .chart-description {{
            color: #34495e;
            margin-bottom: 20px;
            line-height: 1.6;
        }}
    </style>
    <script>
        function openTab(evt, tabName) {{
            var i, tabContent, tabButtons;
            
            tabContent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabContent.length; i++) {{
                tabContent[i].className = tabContent[i].className.replace(" active", "");
            }}
            
            tabButtons = document.getElementsByClassName("tab-button");
            for (i = 0; i < tabButtons.length; i++) {{
                tabButtons[i].className = tabButtons[i].className.replace(" active", "");
            }}
            
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
        }}
    </script>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p class="timestamp">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <div class="tabs">
        {''.join(tabs_html)}
    </div>
    
    {''.join(content_html)}
</body>
</html>
'''
        return html
    
    def _add_custom_title(self, html_path: str, title: str):
        """Add custom title to existing HTML file"""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        # More robust title replacement
        if '<title>' in content and '</title>' in content:
            content = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', content, flags=re.IGNORECASE)
        else:
            # If no title tag exists, inject it into head
            content = content.replace('<head>', f'<head><title>{title}</title>')
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def export_with_data_table(
        self,
        figure: go.Figure,
        df,
        output_path: str,
        title: str = "Chart with Data",
        max_rows: int = 100
    ) -> str:
        """
        Export figure with accompanying data table
        
        Args:
            figure: Plotly Figure object
            df: pandas DataFrame
            output_path: Output file path
            title: Page title
            max_rows: Maximum rows to display in table
        
        Returns:
            Path to exported file
        """
        import pandas as pd
        
        # Convert figure to HTML
        chart_html = figure.to_html(
            include_plotlyjs=False,
            div_id='chart',
            full_html=False,
            config={'responsive': True, 'displaylogo': False}
        )
        
        # Convert dataframe to HTML table with escaping
        table_html = df.head(max_rows).to_html(
            classes='data-table',
            index=False,
            border=0,
            escape=True
        )
        
        html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f7fa;
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 30px;
        }}
        
        .chart-container, .table-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .data-table th {{
            background: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        
        .data-table td {{
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .data-table tr:hover {{
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="chart-container">
        {chart_html}
    </div>
    
    <div class="table-container">
        <h2>Data Table (showing first {min(max_rows, len(df))} rows)</h2>
        {table_html}
    </div>
</body>
</html>
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Exported chart with data table to {output_path}")
        return output_path