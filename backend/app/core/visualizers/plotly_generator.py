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
        """Generate bar chart with blue/orange beginner-friendly styling"""
        # Monochrome palette: White, Silver, Slate, Charcoal
        premium_palette = ['#ffffff', '#e2e8f0', '#94a3b8', '#475569', '#cbd5e1']
        
        fig = px.bar(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=premium_palette,
            barmode='group',
            **config.options
        )
        
        # Premium bar styling
        fig.update_traces(
            marker=dict(
                line=dict(color='rgba(255,255,255,0.1)', width=1),
                opacity=0.9
            ),
            width=0.4 if not config.color else None # Thinner bars like in screenshot
        )
        
        fig = self._apply_common_styling(fig, config)
        return fig
    
    def generate_line_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate smooth line/area chart with schedule-style markers"""
        # Monochrome palette
        premium_palette = ['#ffffff', '#cbd5e1', '#94a3b8', '#64748b']
        
        fig = px.line(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=premium_palette,
            markers=True,
            render_mode='svg', # Better for small datasets
            **{k: v for k, v in config.options.items() if k != 'markers'}
        )
        
        # Make line smooth (spline) and style markers like in screenshots
        fig.update_traces(
            line=dict(width=3, shape='spline'),
            marker=dict(
                size=12,
                line=dict(width=2, color='white'),
                opacity=1
            ),
            hovertemplate='<b>%{x}</b><br>Value: %{y:,.0f}<br><extra></extra>'
        )
        
        fig = self._apply_common_styling(fig, config)
        return fig
    
    def generate_histogram(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate histogram with dark theme and premium animations"""
        # Use optimal bins for clear visualization
        nbins = config.options.get('nbins', 20)
        
        # Get premium color palette based on config
        color_palette = self._get_premium_histogram_colors(config.color_palette)
        
        fig = px.histogram(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x} if config.x else None,
            hover_data=config.hover_data,
            nbins=nbins,
            color_discrete_sequence=color_palette,
            **{k: v for k, v in config.options.items() if k != 'nbins'}
        )
        
        # Premium bar styling with dark theme
        fig.update_traces(
            marker=dict(
                line=dict(
                    color='rgba(30,30,40,0.6)',  # Darker border for separation
                    width=1.5
                ),
                opacity=0.92
            ),
            hovertemplate='<b>%{x}</b><br>Count: %{y}<br><extra></extra>'
        )
        
        # Apply common styling
        fig = self._apply_common_styling(fig, config)
        
        # Add premium interactivity and animations with DARK THEME
        fig.update_layout(
            dragmode='zoom',
            xaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgba(255,255,255,0.08)',
                zeroline=False,
                showline=True,
                linewidth=2,
                linecolor='rgba(200,200,200,0.2)',
                tickfont=dict(color='rgba(200,200,200,0.8)', size=11)
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgba(255,255,255,0.08)',
                zeroline=False,
                showline=True,
                linewidth=2,
                linecolor='rgba(200,200,200,0.2)',
                tickfont=dict(color='rgba(200,200,200,0.8)', size=11)
            ),
            hovermode='x unified',
            plot_bgcolor='rgba(25,30,45,0.9)',  # Dark background
            paper_bgcolor='rgba(15,20,35,0.95)',  # Darker paper background
            font=dict(
                family="'Segoe UI', 'Roboto', sans-serif",
                size=12,
                color='rgba(220,220,230,0.9)'
            ),
            # Smooth animations
            transition=dict(
                duration=500,
                easing='cubic-in-out'
            ),
            # Enhanced legend styling
            legend=dict(
                bgcolor='rgba(25,30,45,0.8)',
                bordercolor='rgba(100,120,160,0.3)',
                borderwidth=1,
                font=dict(size=11, color='rgba(200,200,220,0.9)')
            ),
            # Title styling
            title=dict(
                font=dict(
                    size=18,
                    color='rgba(220,230,255,0.95)',
                    family="'Segoe UI', 'Roboto', sans-serif"
                )
            ),
            margin=dict(l=60, r=40, t=80, b=60),
            showlegend=config.show_legend
        )
        return fig
        
    def generate_scatter_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Redacted: Scatter Plot redirected to smooth Line Chart for beginner friendliness"""
        return self.generate_line_chart(df, config)

    def _get_premium_histogram_colors(self, palette_name: Optional[str] = None) -> List[str]:
        """Get premium color schemes optimized for dark theme histograms"""
        premium_palettes = {
            'default': [
                'rgba(255, 255, 255, 0.9)',    # Pure White
                'rgba(226, 232, 240, 0.8)',    # Silver
                'rgba(148, 163, 184, 0.7)',    # Grey
                'rgba(71, 85, 105, 0.6)',     # Slate
                'rgba(255, 255, 255, 0.5)',    # Translucent White
            ],
            'modern': [
                '#ffffff', '#f8fafc', '#f1f5f9', '#e2e8f0', '#cbd5e1'
            ],
            'cool': [
                '#ffffff', '#e2e8f0', '#94a3b8', '#64748b', '#475569'
            ],
            'warm': [
                '#ffffff', '#cbd5e1', '#94a3b8', '#64748b', '#475569'
            ],
            'gradient': [
                '#ffffff', '#e2e8f0', '#94a3b8', '#475569', '#1e293b'
            ],
        }
        
        palette_key = palette_name if palette_name in premium_palettes else 'default'
        return premium_palettes[palette_key]
    
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
        """Generate donut chart with center annotations matching the 'Business' screenshot"""
        # Monochrome palette: White, Silver, Grey, Slate
        premium_palette = ['#ffffff', '#e2e8f0', '#94a3b8', '#64748b', '#475569']
        
        # Determine values and names
        values = config.y if config.y else None
        names = config.x if config.x else df.columns[0]
        
        fig = px.pie(
            df,
            values=values,
            names=names,
            title=config.title,
            hover_data=config.hover_data,
            color_discrete_sequence=premium_palette,
            hole=0.65, # Larger hole for "Business" look
            **{k: v for k, v in config.options.items() if k != 'hole'}
        )
        
        # Calculate total for center annotation
        total_value = df[values].sum() if values and values in df.columns else len(df)
        total_str = f"{total_value:,.0f}"
        if total_value >= 1000:
            total_str = f"${total_value/1000:.1f}k" if values else f"{total_value:,.0f}"

        # Add center annotation
        fig.update_layout(
            annotations=[
                dict(
                    text=f"<b>{total_str}</b>",
                    x=0.5, y=0.5,
                    font_size=24,
                    font_color='white',
                    font_family="'Segoe UI', 'Roboto', sans-serif",
                    showarrow=False
                ),
                dict(
                    text="Total",
                    x=0.5, y=0.4,
                    font_size=12,
                    font_color='rgba(255,255,255,0.5)',
                    showarrow=False
                )
            ]
        )
        
        # Style slices
        fig.update_traces(
            textinfo='none', # Keep it clean like the screenshot
            marker=dict(
                line=dict(color='rgba(15,20,35,0.95)', width=2)
            ),
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig = self._apply_common_styling(fig, config)
        return fig
    
    def generate_heatmap(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate heatmap with dark theme"""
        # If df is a correlation matrix
        if config.options.get('is_correlation', False):
            fig = px.imshow(
                df,
                title=config.title,
                color_continuous_scale=config.options.get('colorscale', 'Greys'),
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
        
        fig = self._apply_common_styling(fig, config)
        
        # Apply dark theme to heatmap
        fig.update_layout(
            plot_bgcolor='rgba(25,30,45,0.9)',
            paper_bgcolor='rgba(15,20,35,0.95)',
            font=dict(
                family="'Segoe UI', 'Roboto', sans-serif",
                color='rgba(220,220,230,0.9)',
                size=12
            ),
            xaxis=dict(
                tickfont=dict(color='rgba(200,200,200,0.8)', size=11),
                showline=True,
                linewidth=2,
                linecolor='rgba(200,200,200,0.2)'
            ),
            yaxis=dict(
                tickfont=dict(color='rgba(200,200,200,0.8)', size=11),
                showline=True,
                linewidth=2,
                linecolor='rgba(200,200,200,0.2)'
            ),
            coloraxis=dict(
                colorbar=dict(
                    tickfont=dict(color='rgba(200,200,200,0.8)'),
                    outlinecolor='rgba(200,200,200,0.2)',
                    thickness=20
                )
            ),
            title=dict(
                font=dict(size=18, color='rgba(220,230,255,0.95)')
            ),
            transition=dict(duration=500, easing='cubic-in-out')
        )
        
        return fig
    
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

    def generate_scatter_matrix(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Redacted: Scatter Matrix removed for beginner friendliness"""
        return self.generate_bar_chart(df, config)
    
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
    
    def generate_gauge(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate high-end production gauge chart"""
        value = config.options.get('value')
        if value is None:
            # Try to get first numeric value if none provided
            numeric_cols = df.select_dtypes(include=['number']).columns
            if not numeric_cols.empty:
                value = df[numeric_cols[0]].iloc[0]
            else:
                value = 0
                
        title = config.title or "Metric Score"
        goal = config.options.get('goal', 100)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title, 'font': {'size': 14, 'color': 'rgba(255,255,255,0.7)'}},
            number = {'font': {'size': 32, 'color': 'white', 'family': 'Inter, sans-serif'}},
            gauge = {
                'axis': {'range': [None, goal], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.4)"},
                'bar': {'color': "#ffffff", 'thickness': 0.25},
                'bgcolor': "rgba(255,255,255,0.05)",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, goal*0.7], 'color': 'rgba(255,255,255,0.05)'},
                    {'range': [goal*0.7, goal], 'color': 'rgba(255,255,255,0.1)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 2},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        # Add sub-text like "Designation" from screenshot
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            height=config.height,
            width=config.width,
            font={'family': "Inter, sans-serif"}
        )
        
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