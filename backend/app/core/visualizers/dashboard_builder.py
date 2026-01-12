"""
Dashboard Builder - Create comprehensive dashboards with multiple visualizations
Combines charts, layouts, and interactivity
"""
#backend/app/core/visualizers/dashboard_builder.py

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging

from .chart_factory import ChartFactory
from .plotly_generator import PlotlyGenerator

logger = logging.getLogger(__name__)


@dataclass
class VizWidget:
    """Single widget in dashboard"""
    id: str
    chart_type: str
    figure: go.Figure
    title: str
    description: Optional[str] = None
    position: Dict[str, int] = field(default_factory=dict)  # row, col, width, height
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VizDashboard:
    """Complete dashboard configuration"""
    id: str
    title: str
    description: Optional[str] = None
    widgets: List[VizWidget] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class DashboardBuilder:
    """Build comprehensive dashboards with multiple visualizations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.chart_factory = ChartFactory()
        self.generator = PlotlyGenerator()
        
        # Dashboard registry
        self.dashboards: Dict[str, VizDashboard] = {}
    
    def create_dashboard(
        self,
        title: str,
        description: Optional[str] = None,
        dashboard_id: Optional[str] = None
    ) -> VizDashboard:
        """
        Create a new dashboard
        
        Args:
            title: Dashboard title
            description: Dashboard description
            dashboard_id: Optional custom ID
        
        Returns:
            Dashboard object
        """
        if not dashboard_id:
            dashboard_id = f"dashboard_{len(self.dashboards) + 1}"
        
        dashboard = VizDashboard(
            id=dashboard_id,
            title=title,
            description=description
        )
        
        self.dashboards[dashboard_id] = dashboard
        self.logger.info(f"Created dashboard: {dashboard_id}")
        
        return dashboard
    
    def add_widget(
        self,
        dashboard: VizDashboard,
        chart_type: str,
        df: pd.DataFrame,
        widget_id: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> VizWidget:
        """
        Add a widget to dashboard
        
        Args:
            dashboard: Dashboard to add widget to
            chart_type: Type of chart
            df: Data for the chart
            widget_id: Optional widget ID
            title: Widget title
            **kwargs: Additional chart configuration
        
        Returns:
            DashboardWidget
        """
        if not widget_id:
            widget_id = f"widget_{len(dashboard.widgets) + 1}"
        
        # Create chart
        fig = self.chart_factory.create(
            chart_type=chart_type,
            df=df,
            **kwargs
        )
        
        # Create widget
        widget = VizWidget(
            id=widget_id,
            chart_type=chart_type,
            figure=fig,
            title=title or kwargs.get('title', f'{chart_type.title()} Chart'),
            description=kwargs.get('description'),
            config=kwargs
        )
        
        dashboard.widgets.append(widget)
        self.logger.info(f"Added widget {widget_id} to dashboard {dashboard.id}")
        
        return widget
    
    def create_grid_layout(
        self,
        dashboard: VizDashboard,
        rows: int,
        cols: int,
        **kwargs
    ) -> go.Figure:
        """
        Create grid layout for dashboard widgets
        
        Args:
            dashboard: Dashboard with widgets
            rows: Number of rows
            cols: Number of columns
            **kwargs: Additional subplot options
        
        Returns:
            Combined Plotly Figure
        """
        if not dashboard.widgets:
            raise ValueError("Dashboard has no widgets")
        
        # Extract titles
        subplot_titles = [w.title for w in dashboard.widgets[:rows*cols]]
        
        # Create subplots
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=kwargs.get('vertical_spacing', 0.1),
            horizontal_spacing=kwargs.get('horizontal_spacing', 0.1),
            **{k: v for k, v in kwargs.items() if k not in ['vertical_spacing', 'horizontal_spacing']}
        )
        
        # Add widgets to subplots
        for idx, widget in enumerate(dashboard.widgets[:rows*cols]):
            row = (idx // cols) + 1
            col = (idx % cols) + 1
            
            # Add traces
            fig.add_traces(widget.figure.data, rows=[row]*len(widget.figure.data), cols=[col]*len(widget.figure.data))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"<b>{dashboard.title}</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            height=kwargs.get('height', 300 * rows),
            width=kwargs.get('width', 1200),
            showlegend=kwargs.get('showlegend', True)
        )
        
        return fig
    
    def create_auto_dashboard(
        self,
        df: pd.DataFrame,
        title: str = "Auto Dashboard",
        max_charts: int = 6
    ) -> VizDashboard:
        """
        Automatically create dashboard based on data
        
        Args:
            df: pandas DataFrame
            title: Dashboard title
            max_charts: Maximum number of charts to create
        
        Returns:
            Dashboard with auto-generated widgets
        """
        dashboard = self.create_dashboard(title=title)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        charts_added = 0
        
        # 1. Add correlation heatmap if multiple numeric columns
        if len(numeric_cols) >= 2 and charts_added < max_charts:
            try:
                fig = self.chart_factory.create_correlation_matrix(df)
                widget = VizWidget(
                    id=f"widget_{charts_added + 1}",
                    chart_type='heatmap',
                    figure=fig,
                    title='Correlation Matrix'
                )
                dashboard.widgets.append(widget)
                charts_added += 1
            except Exception as e:
                self.logger.debug(f"Failed to add correlation matrix to auto-dashboard: {str(e)}")
        
        # 2. Add distributions for numeric columns
        for col in numeric_cols[:min(2, max_charts - charts_added)]:
            try:
                self.add_widget(
                    dashboard=dashboard,
                    chart_type='histogram',
                    df=df,
                    x=col,
                    title=f'Distribution: {col}'
                )
                charts_added += 1
            except Exception as e:
                self.logger.debug(f"Failed to add distribution to auto-dashboard: {str(e)}")
        
        # 3. Add time series if datetime column exists
        if datetime_cols and numeric_cols and charts_added < max_charts:
            try:
                self.add_widget(
                    dashboard=dashboard,
                    chart_type='line',
                    df=df,
                    x=datetime_cols[0],
                    y=numeric_cols[0],
                    title=f'{numeric_cols[0]} over Time'
                )
                charts_added += 1
            except Exception as e:
                self.logger.debug(f"Failed to add time series to auto-dashboard: {str(e)}")
        
        # 4. Add categorical vs numeric comparisons
        if categorical_cols and numeric_cols and charts_added < max_charts:
            for cat_col in categorical_cols[:min(2, max_charts - charts_added)]:
                try:
                    # Aggregate data
                    agg_df = df.groupby(cat_col)[numeric_cols[0]].mean().reset_index()
                    
                    self.add_widget(
                        dashboard=dashboard,
                        chart_type='bar',
                        df=agg_df,
                        x=cat_col,
                        y=numeric_cols[0],
                        title=f'{numeric_cols[0]} by {cat_col}'
                    )
                    charts_added += 1
                except Exception as e:
                    self.logger.debug(f"Failed to add categorical comparison to auto-dashboard: {str(e)}")
        
        # 5. Add scatter plot if multiple numeric columns
        if len(numeric_cols) >= 2 and charts_added < max_charts:
            try:
                self.add_widget(
                    dashboard=dashboard,
                    chart_type='scatter',
                    df=df,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f'{numeric_cols[1]} vs {numeric_cols[0]}'
                )
                charts_added += 1
            except Exception as e:
                self.logger.debug(f"Failed to add scatter plot to auto-dashboard: {str(e)}")
        
        self.logger.info(f"Auto-generated dashboard with {charts_added} widgets")
        return dashboard
    
    def create_summary_dashboard(
        self,
        df: pd.DataFrame,
        profile_result=None,
        quality_report=None
    ) -> VizDashboard:
        """
        Create summary dashboard with data overview
        
        Args:
            df: pandas DataFrame
            profile_result: Optional ProfileResult from data_profiler
            quality_report: Optional QualityReport from quality_checker
        
        Returns:
            Dashboard with summary visualizations
        """
        dashboard = self.create_dashboard(
            title="Data Summary Dashboard",
            description="Overview of data characteristics and quality"
        )
        
        # 1. Data types distribution (pie chart)
        if profile_result and hasattr(profile_result, 'type_distribution'):
            type_df = pd.DataFrame(
                list(profile_result.type_distribution.items()),
                columns=['Type', 'Count']
            )
            self.add_widget(
                dashboard=dashboard,
                chart_type='pie',
                df=type_df,
                x='Type',
                y='Count',
                title='Column Types Distribution'
            )
        
        # 2. Missing data by column (bar chart)
        missing_data = {}
        for col in df.columns:
            missing_pct = (df[col].isnull().sum() / len(df)) * 100
            if missing_pct > 0:
                missing_data[col] = missing_pct
        
        if missing_data:
            missing_df = pd.DataFrame(
                list(missing_data.items()),
                columns=['Column', 'Missing %']
            ).sort_values('Missing %', ascending=False)
            
            self.add_widget(
                dashboard=dashboard,
                chart_type='bar',
                df=missing_df,
                x='Column',
                y='Missing %',
                title='Missing Data by Column'
            )
        
        # 3. Quality scores (bar chart)
        if quality_report:
            scores_df = pd.DataFrame({
                'Metric': ['Completeness', 'Consistency', 'Validity', 'Uniqueness'],
                'Score': [
                    quality_report.completeness_score,
                    quality_report.consistency_score,
                    quality_report.validity_score,
                    quality_report.uniqueness_score
                ]
            })
            
            self.add_widget(
                dashboard=dashboard,
                chart_type='bar',
                df=scores_df,
                x='Metric',
                y='Score',
                title='Data Quality Scores',
                y_label='Score (0-100)'
            )
        
        # 4. Numeric columns summary statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats_data = []
            for col in numeric_cols[:5]:  # Top 5 numeric columns
                stats_data.append({
                    'Column': col,
                    'Mean': df[col].mean(),
                    'Median': df[col].median(),
                    'Std': df[col].std()
                })
            
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                stats_melted = stats_df.melt(
                    id_vars=['Column'],
                    var_name='Statistic',
                    value_name='Value'
                )
                
                self.add_widget(
                    dashboard=dashboard,
                    chart_type='bar',
                    df=stats_melted,
                    x='Column',
                    y='Value',
                    color='Statistic',
                    title='Summary Statistics',
                    options={'barmode': 'group'}
                )
        
        return dashboard
    
    def export_to_html(
        self,
        dashboard: VizDashboard,
        output_path: str,
        include_plotlyjs: str = 'cdn'
    ):
        """
        Export dashboard to HTML file
        
        Args:
            dashboard: Dashboard to export
            output_path: Output file path
            include_plotlyjs: Plotly JS inclusion method ('cdn', True, False)
        """
        # Create grid layout
        rows = (len(dashboard.widgets) + 1) // 2  # 2 columns
        cols = 2 if len(dashboard.widgets) > 1 else 1
        
        fig = self.create_grid_layout(dashboard, rows, cols)
        
        # Export to HTML
        fig.write_html(
            output_path,
            include_plotlyjs=include_plotlyjs,
            full_html=True,
            config={'displayModeBar': True, 'responsive': True}
        )
        
        self.logger.info(f"Exported dashboard to {output_path}")
    
    def export_to_json(
        self,
        dashboard: VizDashboard,
        output_path: str
    ):
        """
        Export dashboard configuration to JSON
        
        Args:
            dashboard: Dashboard to export
            output_path: Output file path
        """
        # Convert dashboard to dict
        dashboard_dict = {
            'id': dashboard.id,
            'title': dashboard.title,
            'description': dashboard.description,
            'created_at': dashboard.created_at,
            'widgets': [
                {
                    'id': w.id,
                    'chart_type': w.chart_type,
                    'title': w.title,
                    'description': w.description,
                    'config': w.config,
                    'chart': json.loads(w.figure.to_json())
                }
                for w in dashboard.widgets
            ],
            'metadata': dashboard.metadata
        }
        
        # Write to JSON
        with open(output_path, 'w') as f:
            json.dump(dashboard_dict, f, indent=2)
        
        self.logger.info(f"Exported dashboard config to {output_path}")
    
    def get_dashboard(self, dashboard_id: str) -> Optional[VizDashboard]:
        """Get dashboard by ID"""
        return self.dashboards.get(dashboard_id)
    
    def list_dashboards(self) -> List[Dict[str, Any]]:
        """List all dashboards"""
        return [
            {
                'id': d.id,
                'title': d.title,
                'description': d.description,
                'widget_count': len(d.widgets),
                'created_at': d.created_at
            }
            for d in self.dashboards.values()
        ]
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard by ID"""
        if dashboard_id in self.dashboards:
            del self.dashboards[dashboard_id]
            self.logger.info(f"Deleted dashboard: {dashboard_id}")
            return True
        return False