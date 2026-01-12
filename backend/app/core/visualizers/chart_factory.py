"""
Chart Factory - High-level chart creation interface
Simplifies chart generation with intelligent defaults
"""
#backend/app/core/visualizers/chart_factory.py

from typing import Dict, Any, List, Optional, Union
from enum import Enum
import pandas as pd
import plotly.graph_objects as go
import logging

from .plotly_generator import PlotlyGenerator, ChartConfig

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    PIE = "pie"
    DONUT = "donut"
    HEATMAP = "heatmap"
    AREA = "area"
    BUBBLE = "bubble"
    SUNBURST = "sunburst"
    TREEMAP = "treemap"
    DENSITY_HEATMAP = "density_heatmap"
    PARALLEL_COORDINATES = "parallel_coordinates"
    CHOROPLETH = "choropleth"
    SCATTER_MAP = "scatter_map"
    DENSITY_MAP = "density_map"
    CLUSTER = "cluster"
    FORECAST = "forecast"


class ChartFactory:
    """Factory for creating charts with intelligent defaults"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.generator = PlotlyGenerator()
        
        # Map chart types to generator methods
        self.chart_methods = {
            ChartType.BAR: self.generator.generate_bar_chart,
            ChartType.LINE: self.generator.generate_line_chart,
            ChartType.SCATTER: self.generator.generate_scatter_chart,
            ChartType.HISTOGRAM: self.generator.generate_histogram,
            ChartType.BOX: self.generator.generate_box_plot,
            ChartType.VIOLIN: self.generator.generate_violin_plot,
            ChartType.PIE: self.generator.generate_pie_chart,
            ChartType.DONUT: self._create_donut_chart,
            ChartType.HEATMAP: self.generator.generate_heatmap,
            ChartType.AREA: self.generator.generate_area_chart,
            ChartType.BUBBLE: self.generator.generate_bubble_chart,
            ChartType.SUNBURST: self.generator.generate_sunburst,
            ChartType.TREEMAP: self.generator.generate_treemap,
            ChartType.DENSITY_HEATMAP: self.generator.generate_density_heatmap,
            ChartType.PARALLEL_COORDINATES: self.generator.generate_parallel_coordinates,
            ChartType.CHOROPLETH: self.generator.generate_choropleth,
            ChartType.SCATTER_MAP: self.generator.generate_scatter_map,
            ChartType.DENSITY_MAP: self.generator.generate_density_map,
            ChartType.CLUSTER: self.generator.generate_cluster_plot,
            ChartType.FORECAST: self.generator.generate_forecast_plot,
        }
    
    def create(
        self,
        chart_type: str,
        df: pd.DataFrame,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        **kwargs
    ) -> go.Figure:
        """
        Create a chart with intelligent defaults
        
        Args:
            chart_type: Type of chart to create
            df: pandas DataFrame
            x: X-axis column name
            y: Y-axis column name (or list of column names)
            **kwargs: Additional configuration options
        
        Returns:
            Plotly Figure object
        """
        try:
            # Normalize chart type
            # Normalize chart type: lowercase, replace separators with underscore, collapse multiple underscores
            import re
            chart_type = chart_type.lower().strip()
            chart_type = re.sub(r'[\s\-_]+', '_', chart_type)
            
            # Validate chart type
            try:
                chart_enum = ChartType(chart_type)
            except ValueError:
                raise ValueError(
                    f"Unsupported chart type: {chart_type}. "
                    f"Supported types: {[t.value for t in ChartType]}"
                )
            
            # Infer missing parameters
            if not x and not y:
                x, y = self._infer_columns(df, chart_type)
            
            # Build configuration
            config = self._build_config(
                chart_type=chart_type,
                df=df,
                x=x,
                y=y,
                **kwargs
            )
            
            # Get generator method
            method = self.chart_methods.get(chart_enum)
            if not method:
                raise ValueError(f"No generator found for chart type: {chart_type}")
            
            # Generate chart
            fig = method(df, config)
            
            self.logger.info(f"Successfully created {chart_type} chart")
            return fig
        
        except Exception as e:
            self.logger.error(f"Error creating chart: {str(e)}")
            raise
    
    def _build_config(
        self,
        chart_type: str,
        df: pd.DataFrame,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        **kwargs
    ) -> ChartConfig:
        """Build chart configuration with defaults"""
        
        # Generate default title if not provided
        title = kwargs.get('title')
        if not title:
            title = self._generate_title(chart_type, x, y)
        
        # Build config
        config = ChartConfig(
            chart_type=chart_type,
            x=x,
            y=y,
            color=kwargs.get('color'),
            size=kwargs.get('size'),
            title=title,
            x_label=kwargs.get('x_label'),
            y_label=kwargs.get('y_label'),
            width=kwargs.get('width'),
            height=kwargs.get('height'),
            color_palette=kwargs.get('color_palette'),
            theme=kwargs.get('theme'),
            show_legend=kwargs.get('show_legend', True),
            hover_data=kwargs.get('hover_data'),
            options=kwargs.get('options', {})
        )
        
        return config
    
    def _infer_columns(
        self,
        df: pd.DataFrame,
        chart_type: str
    ) -> tuple:
        """
        Infer appropriate columns based on chart type and data
        """
        if len(df.columns) < 1:
            raise ValueError("DataFrame must have at least one column to generate a chart.")

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
        datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        
        # New: Geographic column detection
        from .geo_utils import GeoUtils
        geo_cols = GeoUtils.detect_geographic_columns(df)
        
        # Default selections based on chart type
        if chart_type in ['histogram', 'box', 'violin']:
            # Single numeric column
            x = numeric_cols[0] if numeric_cols else df.columns[0]
            y = None
        
        elif chart_type in ['pie', 'donut']:
            # Categorical + numeric
            if len(df.columns) < 2:
                raise ValueError("Pie/Donut charts require at least 2 columns (categorical and numeric) to infer.")
            x = categorical_cols[0] if categorical_cols else df.columns[0]
            y = numeric_cols[0] if numeric_cols else df.columns[1]
        
        elif chart_type in ['line', 'area']:
            # Prefer datetime on x-axis
            if datetime_cols and numeric_cols:
                x = datetime_cols[0]
                y = numeric_cols[0]
            elif len(df.columns) >= 2:
                x = df.columns[0]
                y = numeric_cols[0] if numeric_cols else df.columns[1]
            else:
                x = df.columns[0]
                y = numeric_cols[0] if numeric_cols else None
        
        elif chart_type in ['scatter', 'bubble']:
            # Two numeric columns
            if len(df.columns) < 2:
                raise ValueError("Scatter/Bubble charts require at least 2 columns to infer x and y.")
            x = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]
            y = numeric_cols[1] if len(numeric_cols) > 1 else df.columns[1]
        
        elif chart_type == 'bar':
            # Categorical + numeric
            if categorical_cols and numeric_cols:
                x = categorical_cols[0]
                y = numeric_cols[0]
            else:
                x = df.columns[0]
                y = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        elif chart_type == 'choropleth':
            # Needs locations (country/state) + value
            x = geo_cols.get('country') or geo_cols.get('state') or (categorical_cols[0] if categorical_cols else df.columns[0])
            y = numeric_cols[0] if numeric_cols else (df.columns[1] if len(df.columns) > 1 else None)
            
        elif chart_type in ['scatter_map', 'density_map']:
            # Needs lat/lon
            x = geo_cols.get('latitude') or (numeric_cols[0] if len(numeric_cols) > 0 else None)
            y = geo_cols.get('longitude') or (numeric_cols[1] if len(numeric_cols) > 1 else None)
        
        elif chart_type == 'cluster':
            # Use all numeric cols
            x = numeric_cols[0] if numeric_cols else df.columns[0]
            y = numeric_cols[1] if len(numeric_cols) > 1 else None
            
        elif chart_type == 'forecast':
            # Needs time + value
            x = datetime_cols[0] if datetime_cols else df.columns[0]
            y = numeric_cols[0] if numeric_cols else (df.columns[1] if len(df.columns) > 1 else None)
        
        else:
            # Default: first two columns
            x = df.columns[0]
            y = df.columns[1] if len(df.columns) > 1 else None
        
        return x, y
    
    def _generate_title(
        self,
        chart_type: str,
        x: Optional[str],
        y: Optional[Union[str, List[str]]]
    ) -> str:
        """Generate default chart title"""
        chart_name = chart_type.replace('_', ' ').title()
        
        if x and y:
            if isinstance(y, list):
                y_str = ', '.join(y)
            else:
                y_str = y
            return f"{y_str} by {x}"
        elif x:
            return f"{chart_name}: {x}"
        else:
            return chart_name
    
    def _create_donut_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Create donut chart (pie chart with hole)"""
        # Copy options to avoid side effects
        from dataclasses import replace
        new_options = config.options.copy()
        new_options['hole'] = new_options.get('hole', 0.4)
        config = replace(config, options=new_options)
        return self.generator.generate_pie_chart(df, config)
    
    def create_correlation_matrix(
        self,
        df: pd.DataFrame,
        **kwargs
    ) -> go.Figure:
        """
        Create correlation matrix heatmap
        
        Args:
            df: pandas DataFrame
            **kwargs: Additional options
        
        Returns:
            Plotly Figure
        """
        # Calculate correlation
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty or numeric_df.shape[1] < 2:
            raise ValueError("Correlation matrix requires at least 2 numeric columns.")
        corr_matrix = numeric_df.corr()
        
        config = ChartConfig(
            chart_type='heatmap',
            title=kwargs.get('title', 'Correlation Matrix'),
            width=kwargs.get('width'),
            height=kwargs.get('height'),
            options={
                'is_correlation': True,
                'colorscale': kwargs.get('colorscale', 'RdBu_r')
            }
        )
        
        return self.generator.generate_heatmap(corr_matrix, config)
    
    def create_distribution_plot(
        self,
        df: pd.DataFrame,
        column: str,
        plot_type: str = 'histogram',
        **kwargs
    ) -> go.Figure:
        """
        Create distribution plot (histogram, box, or violin)
        
        Args:
            df: pandas DataFrame
            column: Column to plot distribution
            plot_type: 'histogram', 'box', or 'violin'
            **kwargs: Additional options
        
        Returns:
            Plotly Figure
        """
        title = kwargs.pop("title", f'Distribution of {column}')
        return self.create(
            chart_type=plot_type,
            df=df,
            x=column,
            title=title,
            **kwargs
        )
    
    def create_comparison_chart(
        self,
        df: pd.DataFrame,
        category_col: str,
        value_col: str,
        chart_type: str = 'bar',
        **kwargs
    ) -> go.Figure:
        """
        Create comparison chart (bar, line, or area)
        
        Args:
            df: pandas DataFrame
            category_col: Column for categories
            value_col: Column for values
            chart_type: 'bar', 'line', or 'area'
            **kwargs: Additional options
        
        Returns:
            Plotly Figure
        """
        title = kwargs.pop("title", f'{value_col} by {category_col}')
        return self.create(
            chart_type=chart_type,
            df=df,
            x=category_col,
            y=value_col,
            title=title,
            **kwargs
        )
    
    def create_time_series(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: Union[str, List[str]],
        chart_type: str = 'line',
        **kwargs
    ) -> go.Figure:
        """
        Create time series chart
        
        Args:
            df: pandas DataFrame
            date_col: Date column
            value_col: Value column(s)
            chart_type: 'line' or 'area'
            **kwargs: Additional options
        
        Returns:
            Plotly Figure
        """
        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col])
        
        # Sort by date
        df = df.sort_values(date_col)
        
        title = kwargs.pop("title", 'Time Series')
        return self.create(
            chart_type=chart_type,
            df=df,
            x=date_col,
            y=value_col,
            title=title,
            **kwargs
        )
    
    def create_grouped_bar(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        **kwargs
    ) -> go.Figure:
        """
        Create grouped bar chart
        
        Args:
            df: pandas DataFrame
            x: X-axis column
            y: Y-axis column
            color: Grouping column
            **kwargs: Additional options
        
        Returns:
            Plotly Figure
        """
        title = kwargs.pop("title", f'{y} by {x} and {color}')
        return self.create(
            chart_type='bar',
            df=df,
            x=x,
            y=y,
            color=color,
            title=title,
            options={'barmode': 'group'},
            **kwargs
        )
    
    def create_stacked_bar(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        **kwargs
    ) -> go.Figure:
        """
        Create stacked bar chart
        
        Args:
            df: pandas DataFrame
            x: X-axis column
            y: Y-axis column
            color: Stacking column
            **kwargs: Additional options
        
        Returns:
            Plotly Figure
        """
        return self.create(
            chart_type='bar',
            df=df,
            x=x,
            y=y,
            color=color,
            title=kwargs.get('title', f'{y} by {x} (Stacked by {color})'),
            options={'barmode': 'stack'},
            **kwargs
        )
    
    def create_multi_line(
        self,
        df: pd.DataFrame,
        x: str,
        y_columns: List[str],
        **kwargs
    ) -> go.Figure:
        """
        Create multi-line chart
        
        Args:
            df: pandas DataFrame
            x: X-axis column
            y_columns: List of Y-axis columns
            **kwargs: Additional options
        
        Returns:
            Plotly Figure
        """
        # Melt dataframe for multiple lines
        df_melted = df.melt(
            id_vars=[x],
            value_vars=y_columns,
            var_name='series',
            value_name='value'
        )
        
        return self.create(
            chart_type='line',
            df=df_melted,
            x=x,
            y='value',
            color='series',
            title=kwargs.get('title', f'Multi-line Chart: {", ".join(y_columns)}'),
            **kwargs
        )