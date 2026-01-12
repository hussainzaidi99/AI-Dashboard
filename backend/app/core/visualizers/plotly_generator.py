"""
Plotly Generator - Core chart generation with Plotly
Handles all chart types and customizations
"""
#backend/app/core/visualizers/plotly_generator.py


from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ChartConfig:
    """Configuration for chart generation"""
    # Chart type
    chart_type: str
    
    # Data columns
    x: Optional[str] = None
    y: Optional[Union[str, List[str]]] = None
    color: Optional[str] = None
    size: Optional[str] = None
    facet_col: Optional[str] = None
    facet_row: Optional[str] = None
    
    # Dimensions
    width: int = field(default_factory=lambda: settings.CHART_DEFAULT_WIDTH)
    height: int = field(default_factory=lambda: settings.CHART_DEFAULT_HEIGHT)
    
    # Appearance
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    color_palette: Optional[str] = None
    theme: str = field(default_factory=lambda: settings.CHART_THEME)
    
    # Interactivity
    show_legend: bool = True
    hover_data: Optional[List[str]] = None
    
    # Additional options
    options: Dict[str, Any] = field(default_factory=dict)


class PlotlyGenerator:
    """Generate Plotly charts with various configurations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Color palettes
        self.color_palettes = {
            'default': px.colors.qualitative.Plotly,
            'vivid': px.colors.qualitative.Vivid,
            'bold': px.colors.qualitative.Bold,
            'pastel': px.colors.qualitative.Pastel,
            'safe': px.colors.qualitative.Safe,
            'dark': px.colors.qualitative.Dark24,
        }
    
    def generate_bar_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate bar chart"""
        fig = px.bar(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            **config.options
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_line_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate line chart"""
        fig = px.line(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            markers=config.options.get('markers', True),
            **{k: v for k, v in config.options.items() if k != 'markers'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_scatter_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate scatter plot"""
        fig = px.scatter(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            size=config.size,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            trendline=config.options.get('trendline'),
            **{k: v for k, v in config.options.items() if k != 'trendline'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_histogram(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate histogram"""
        fig = px.histogram(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x} if config.x else None,
            hover_data=config.hover_data,
            nbins=config.options.get('nbins', 30),
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            **{k: v for k, v in config.options.items() if k != 'nbins'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_box_plot(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate box plot"""
        fig = px.box(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            **config.options
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_violin_plot(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate violin plot"""
        fig = px.violin(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            box=config.options.get('box', True),
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            **{k: v for k, v in config.options.items() if k != 'box'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_pie_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate pie chart"""
        fig = px.pie(
            df,
            values=config.y,
            names=config.x,
            title=config.title,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            hole=config.options.get('hole', 0),  # 0 = pie, >0 = donut
            **{k: v for k, v in config.options.items() if k != 'hole'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_heatmap(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate heatmap"""
        # If df is a correlation matrix
        if config.options.get('is_correlation', False):
            fig = px.imshow(
                df,
                title=config.title,
                color_continuous_scale=config.options.get('colorscale', 'RdBu_r'),
                aspect='auto',
                labels=dict(color="Correlation"),
                **{k: v for k, v in config.options.items() if k not in ['is_correlation', 'colorscale']}
            )
        elif config.x and config.y and isinstance(config.options.get('values'), str):
            pivot_df = df.pivot_table(
                values=config.options['values'],
                index=config.y,
                columns=config.x,
                aggfunc=config.options.get('aggfunc', 'mean')
            )
            
            fig = px.imshow(
                pivot_df,
                title=config.title,
                color_continuous_scale=config.options.get('colorscale', 'Viridis'),
                aspect='auto',
                **{k: v for k, v in config.options.items() 
                   if k not in ['values', 'aggfunc', 'colorscale']}
            )
        elif config.options.get('matrix', True) and df.shape[1] > 0:
            # Direct matrix support
            fig = px.imshow(
                df,
                title=config.title,
                color_continuous_scale=config.options.get('colorscale', 'Viridis'),
                aspect='auto',
                **{k: v for k, v in config.options.items() if k not in ['matrix', 'colorscale']}
            )
        else:
            raise ValueError("Heatmap requires x, y, and values columns or a 2D matrix")
        
        return self._apply_common_styling(fig, config)
    
    def generate_area_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate area chart"""
        fig = px.area(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            **config.options
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_bubble_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate bubble chart (scatter with size)"""
        if not config.size:
            raise ValueError("Bubble chart requires 'size' parameter")
        
        fig = px.scatter(
            df,
            x=config.x,
            y=config.y,
            size=config.size,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            size_max=config.options.get('size_max', 60),
            **{k: v for k, v in config.options.items() if k != 'size_max'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_sunburst(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate sunburst chart"""
        path = config.options.get('path', [])
        if not path:
            raise ValueError("Sunburst requires 'path' parameter (list of columns)")
        
        fig = px.sunburst(
            df,
            path=path,
            values=config.y,
            color=config.color,
            title=config.title,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            **{k: v for k, v in config.options.items() if k != 'path'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_treemap(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate treemap"""
        path = config.options.get('path', [])
        if not path:
            raise ValueError("Treemap requires 'path' parameter (list of columns)")
        
        fig = px.treemap(
            df,
            path=path,
            values=config.y,
            color=config.color,
            title=config.title,
            hover_data=config.hover_data,
            color_discrete_sequence=self._get_color_palette(config.color_palette),
            **{k: v for k, v in config.options.items() if k != 'path'}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_density_heatmap(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate density heatmap"""
        fig = px.density_heatmap(
            df,
            x=config.x,
            y=config.y,
            z=config.options.get('z'),
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            color_continuous_scale=config.options.get('colorscale', 'Viridis'),
            **{k: v for k, v in config.options.items() if k not in ['z', 'colorscale']}
        )
        
        return self._apply_common_styling(fig, config)
    
    def generate_parallel_coordinates(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate parallel coordinates plot"""
        dimensions = config.options.get('dimensions', [])
        if not dimensions:
            # Use all numeric columns
            dimensions = df.select_dtypes(include=['number']).columns.tolist()
        
        # Validate color column is numeric for parallel_coordinates
        color_col = config.color
        if color_col and not pd.api.types.is_numeric_dtype(df[color_col]):
            self.logger.warning(f"Parallel coordinates: {color_col} is not numeric. Skipping color mapping.")
            color_col = None

        fig = px.parallel_coordinates(
            df,
            dimensions=dimensions,
            color=color_col,
            title=config.title,
            color_continuous_scale=config.options.get('colorscale', 'Viridis'),
            **{k: v for k, v in config.options.items() if k not in ['dimensions', 'colorscale']}
        )
        
        return self._apply_common_styling(fig, config)
    
    def _get_color_palette(self, palette_name: Optional[str]) -> List[str]:
        """Get color palette by name"""
        if not palette_name:
            palette_name = 'default'
        
        return self.color_palettes.get(palette_name, self.color_palettes['default'])
    
    def _apply_common_styling(
        self,
        fig: go.Figure,
        config: ChartConfig
    ) -> go.Figure:
        """Apply common styling to all charts"""
        # Update layout
        fig.update_layout(
            template=config.theme,
            width=config.width,
            height=config.height,
            showlegend=config.show_legend,
            hovermode='closest',
            font=dict(size=12),
            title=dict(
                text=f"<b>{config.title}</b>" if config.title else None,
                x=0.5,
                xanchor='center',
                font=dict(size=16)
            ) if config.title else None
        )
        
        # Update axes labels if specified
        if config.x_label:
            fig.update_xaxes(title_text=config.x_label)
        if config.y_label:
            fig.update_yaxes(title_text=config.y_label)
        
        return fig
    
    def create_subplots(
        self,
        figures: List[go.Figure],
        rows: int,
        cols: int,
        subplot_titles: Optional[List[str]] = None,
        **kwargs
    ) -> go.Figure:
        """
        Create subplot grid from multiple figures
        
        Args:
            figures: List of Plotly figures
            rows: Number of rows
            cols: Number of columns
            subplot_titles: Titles for each subplot
            **kwargs: Additional subplot options
        
        Returns:
            Combined figure with subplots
        """
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            **kwargs
        )
        
        # Add traces from each figure
        for idx, source_fig in enumerate(figures):
            row = (idx // cols) + 1
            col = (idx % cols) + 1
            
            for trace in source_fig.data:
                fig.add_trace(trace, row=row, col=col)
        
        # Update layout
        fig.update_layout(
            height=settings.CHART_DEFAULT_HEIGHT * rows,
            width=settings.CHART_DEFAULT_WIDTH,
            showlegend=True
        )
        
        return fig