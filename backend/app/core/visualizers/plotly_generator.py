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

    def _sanitize_data(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Sanitize dataframe columns for Plotly consumption"""
        df_clean = df.copy()
        for col in columns:
            if col in df_clean.columns:
                # Convert to numeric, force invalid to NaN, then fill with 0
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                # Replace Inf with 0
                import numpy as np
                df_clean[col] = df_clean[col].replace([np.inf, -np.inf], 0)
        return df_clean

    def _ensure_valid_range(self, fig: go.Figure, df: pd.DataFrame, y_cols: List[str]) -> go.Figure:
        """Ensure axes have a valid range to prevent 'axis scaling' errors"""
        try:
            # Check if all data is zero or constant
            is_constant = True
            for col in y_cols:
                if col in df.columns and df[col].nunique() > 1:
                    is_constant = False
                    break
                if col in df.columns and df[col].sum() != 0:
                    is_constant = False
                    break
            
            if is_constant:
                fig.update_layout(
                    yaxis=dict(range=[0, 1], autorange=False),
                )
            else:
                fig.update_layout(yaxis=dict(autorange=True))
        except:
            pass
        return fig
    
    def generate_bar_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate bar chart with premium blue template styling"""
        # Blue palette: Deep Blue, Electric Blue, Sky Blue, Soft Blue
        blue_palette = ['#0062ff', '#00a3ff', '#33b5ff', '#66c7ff', '#99daff']
        
        # Sanitize
        y_cols = [config.y] if isinstance(config.y, str) else config.y if config.y else []
        df = self._sanitize_data(df, y_cols)

        fig = px.bar(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            title=config.title,
            labels={config.x: config.x_label or config.x,
                   (config.y if isinstance(config.y, str) else "Values"): config.y_label or (config.y if isinstance(config.y, str) else "Values")} if config.x and config.y else None,
            hover_data=config.hover_data,
            color_discrete_sequence=blue_palette,
            barmode='stack', # Stacked like in the template
            **config.options
        )
        
        # Premium bar styling with rounded corners
        fig.update_traces(
            marker=dict(
                line=dict(width=0), # No border for cleaner look
                opacity=1.0
            ),
            width=0.4 if not config.color else None # Thinner bars
        )
        
        fig = self._apply_common_styling(fig, config)
        fig = self._ensure_valid_range(fig, df, y_cols)
        return fig
    
    def generate_line_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate smooth line/area chart with schedule-style markers"""
        # Monochrome palette
        premium_palette = ['#ffffff', '#cbd5e1', '#94a3b8', '#64748b']
        
        # Sanitize
        y_cols = [config.y] if isinstance(config.y, str) else config.y if config.y else []
        df = self._sanitize_data(df, y_cols)

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
        fig = self._ensure_valid_range(fig, df, y_cols)
        return fig
    
    def generate_histogram(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate histogram with dark theme and premium animations"""
        # Use optimal bins for clear visualization
        nbins = config.options.get('nbins', 20)
        
        # Sanitize
        y_cols = [config.x] # Histogram main axis is x
        df = self._sanitize_data(df, y_cols)

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
        fig = self._ensure_valid_range(fig, df, y_cols)
        
        # Add premium interactivity and animations with DARK THEME
        fig.update_layout(
            dragmode='zoom',
            xaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgba(255,255,255,0.08)',
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='rgba(200,200,200,0.2)',
                tickfont=dict(color='rgba(200,200,200,0.8)', size=10)
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgba(255,255,255,0.08)',
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='rgba(200,200,200,0.2)',
                tickfont=dict(color='rgba(200,200,200,0.8)', size=10)
            ),
            hovermode='x unified',
            plot_bgcolor='rgba(25,30,45,0.9)',  # Dark background
            paper_bgcolor='rgba(15,20,35,0.95)',  # Darker paper background
            font=dict(
                family="'Segoe UI', 'Roboto', sans-serif",
                size=11,
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
                font=dict(size=10, color='rgba(200,200,220,0.9)')
            ),
            # Title styling (consistent with common styling)
            title=dict(
                x=0.05,
                xanchor='left',
                font=dict(
                    size=15,
                    color='rgba(220,230,255,0.95)',
                    family="'Segoe UI', 'Roboto', sans-serif"
                )
            ),
            margin=dict(l=50, r=30, t=60, b=50),
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
                '#0062ff', '#00a3ff', '#33b5ff', '#66c7ff', '#99daff'
            ],
            'modern': [
                '#0062ff', '#00a3ff', '#33b5ff', '#66c7ff', '#99daff'
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
    
    def generate_donut_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate high-end donut chart with center annotations"""
        # Blue-Slate palette for professional look
        premium_palette = ['#3b82f6', '#64748b', '#475569', '#334155', '#1e293b']
        
        # Determine values and names
        values = config.y if config.y else None
        names = config.x if config.x else df.columns[0]
        
        # Sort for top 5 for cleaner representation
        df_sorted = df.sort_values(by=values, ascending=False).head(5) if values else df
        
        fig = px.pie(
            df_sorted,
            values=values,
            names=names,
            title=None,
            hover_data=config.hover_data,
            color_discrete_sequence=premium_palette,
            hole=0.75, # Deep hole for centered metric
            **{k: v for k, v in config.options.items() if k not in ['hole', 'description']}
        )
        
        # Calculate total for center annotation
        total_val = df_sorted[values].sum() if values and values in df_sorted.columns else len(df_sorted)
        if total_val >= 1000000: total_str = f"{total_val/1000000:.1f}M"
        elif total_val >= 1000: total_str = f"{total_val/1000:.1f}K"
        else: total_str = str(int(total_val))

        # Add metric value in center
        fig.update_layout(
            showlegend=False, 
            annotations=[
                dict(
                    text=f"<b>{total_str}</b>",
                    x=0.5, y=0.5,
                    xref="paper", yref="paper",
                    font=dict(size=32, color="white", family="Inter, sans-serif"),
                    showarrow=False
                )
            ],
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # Style slices (minimal/clean)
        fig.update_traces(
            textinfo='none', 
            marker=dict(line=dict(color='rgba(15,20,35,1)', width=2)),
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig = self._apply_common_styling(fig, config)
        fig.update_layout(showlegend=False)
        return fig

    def generate_pie_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate vibrant classic pie chart with outside labels"""
        vibrant_palette = ['#3b82f6', '#4ade80', '#fbbf24', '#f87171', '#94a3b8']
        
        values = config.y if config.y else None
        names = config.x if config.x else df.columns[0]
        df_sorted = df.sort_values(by=values, ascending=False).head(8) if values else df
        
        fig = px.pie(
            df_sorted,
            values=values,
            names=names,
            title=None,
            hover_data=config.hover_data,
            color_discrete_sequence=vibrant_palette,
            hole=0, # Classic pie
            **{k: v for k, v in config.options.items() if k not in ['hole', 'description']}
        )
        
        fig.update_traces(
            textinfo='label+percent',
            textposition='outside',
            marker=dict(line=dict(color='rgba(15,20,35,0.6)', width=1.5)),
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig = self._apply_common_styling(fig, config)
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=40, b=80)
        )
        
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
                size=11
            ),
            xaxis=dict(
                tickfont=dict(color='rgba(200,200,200,0.8)', size=10),
                tickangle=-45,
                showline=True,
                linewidth=1,
                linecolor='rgba(200,200,200,0.2)',
                automargin=True,
                showgrid=False, # Removed teeth
                zeroline=False # Removed teeth
            ),
            yaxis=dict(
                tickfont=dict(color='rgba(200,200,200,0.8)', size=10),
                showline=True,
                linewidth=1,
                linecolor='rgba(200,200,200,0.2)',
                automargin=True,
                showgrid=False, # Removed teeth
                zeroline=False # Removed teeth
            ),
            coloraxis=dict(
                colorbar=dict(
                    tickfont=dict(color='rgba(200,200,200,0.8)', size=10),
                    outlinecolor='rgba(200,200,200,0.2)',
                    thickness=10,
                    len=0.8,
                    orientation='h',
                    y=-0.25, # Position at bottom
                    x=0.5,
                    xanchor='center'
                )
            ),
            title=dict(
                font=dict(size=14, color='rgba(220,230,255,0.95)')
            ),
            margin=dict(l=60, r=30, t=50, b=60), # Tightened margins
            transition=dict(duration=500, easing='cubic-in-out')
        )
        
        # Force square aspect for correlation heatmaps for professional grid look
        if config.options.get('is_correlation', False):
            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            fig.update_layout(width=None, height=None) # Trust container for height
        
        return fig
    
    def generate_metric_area_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate high-end area chart with metric header (Big Number + Trend)"""
        # Get current value and trend
        y_col = config.y if isinstance(config.y, str) else config.y[0]
        current_value = df[y_col].iloc[-1]
        previous_value = df[y_col].iloc[-2] if len(df) > 1 else current_value
        
        change_pct = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
        trend_color = "#4ade80" if change_pct >= 0 else "#f87171"
        trend_icon = "▲" if change_pct >= 0 else "▼"
        
        # Formatting values
        fmt_val = f"{current_value:,.0f}" if current_value >= 1 else f"{current_value:.2f}"
        if current_value >= 1000000: fmt_val = f"{current_value/1000000:.1f}M"
        elif current_value >= 1000: fmt_val = f"{current_value/1000:.1f}k"
        
        # Create base area chart
        fig = px.area(
            df,
            x=config.x,
            y=config.y,
            color_discrete_sequence=['rgba(59, 130, 246, 0.5)'],
            **{k: v for k, v in config.options.items() if k not in ['value', 'trend']}
        )
        
        # Smooth spline and high-end styling
        fig.update_traces(
            line=dict(width=4, color='#3b82f6', shape='spline'), # Thicker line
            fillcolor='rgba(59, 130, 246, 0.08)', # Subtle fill
            hovertemplate='<b>%{x}</b><br>Value: %{y:,.0f}<extra></extra>'
        )
        
        # Add metric annotations (Big Number and Trend)
        fig.update_layout(
            annotations=[
                # Value
                dict(
                    x=0.02, y=1.35, # More space
                    xref="paper", yref="paper",
                    text=f"<b>{fmt_val}</b>",
                    showarrow=False,
                    font=dict(size=36, color="white", family="Inter, sans-serif"),
                    align="left"
                ),
                # Trend Badge
                dict(
                    x=0.28, y=1.30,
                    xref="paper", yref="paper",
                    text=f" <span style='color:{trend_color}; background:rgba(255,255,255,0.05); padding:2px 8px; border-radius:4px;'>{trend_icon} {abs(change_pct):.0f}%</span>",
                    showarrow=False,
                    font=dict(size=14, family="Inter, sans-serif"),
                    align="left"
                )
            ],
            margin=dict(l=40, r=20, t=120, b=40), # More top margin for big number
            xaxis=dict(
                showgrid=False, 
                showline=False,
                zeroline=False,
                automargin=True,
                tickfont=dict(size=10, color='rgba(255,255,255,0.4)')
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.03)', 
                automargin=True,
                showticklabels=False # Hide Y ticks for focus on trend
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
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
            **{k: v for k, v in config.options.items() if k not in ['size_max', 'description']}
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
            **{k: v for k, v in config.options.items() if k not in ['path', 'description']}
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
            **{k: v for k, v in config.options.items() if k not in ['path', 'description']}
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
        """Apply common styling with production-grade scaling for dashboard cards"""
        # Update layout
        fig.update_layout(
            template=config.theme,
            width=None, # Allow container to define width
            height=None, # Allow container to define height
            autosize=True,
            showlegend=config.show_legend,
            hovermode='x unified' if config.chart_type in ['bar', 'histogram', 'line', 'area'] else 'closest',
            font=dict(size=11, family="Inter, 'Segoe UI', sans-serif"),
            margin=dict(l=50, r=30, t=50, b=60), # Breathable margins
            title=dict(
                text=f"<b>{config.title}</b>" if config.title else None,
                x=0.03,
                xanchor='left',
                font=dict(size=14, color='rgba(255,255,255,0.9)')
            ) if config.title else None,
            # Hide modebar but keep orientation clear
            modebar=dict(
                bgcolor='rgba(0,0,0,0)',
                color='rgba(255,255,255,0.3)',
                orientation='h'
            ),
            # Automatic margin and label rotation for all categorical charts
            xaxis=dict(
                automargin=True, 
                tickfont=dict(size=10, color='rgba(255,255,255,0.7)'),
                tickangle=-0 if config.chart_type in ['bar', 'histogram', 'pie'] else 0,
                showgrid=False, # Hide vertical grid lines
                zeroline=False
            ),
            yaxis=dict(
                automargin=True,
                tickfont=dict(size=10, color='rgba(255,255,255,0.7)'),
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)', # Subtle dashed grid lines
                gridwidth=1,
                griddash='dash',
                zeroline=False
            )
        )
        
        # Consistent label styling
        if config.x_label:
            fig.update_xaxes(title_text=config.x_label, title_font=dict(size=11, color='rgba(255,255,255,0.8)'))
        if config.y_label:
            fig.update_yaxes(title_text=config.y_label, title_font=dict(size=11, color='rgba(255,255,255,0.8)'))
        
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
        
        # Ensure goal is valid
        if not isinstance(goal, (int, float)) or goal <= 0:
            goal = 100
        
        # Ensure value is valid
        if not isinstance(value, (int, float)) or pd.isna(value):
            value = 0
            
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            domain = {'x': [0.1, 0.9], 'y': [0.1, 0.95]}, # Optimized domain
            title = {'text': title, 'font': {'size': 12, 'color': 'rgba(255,255,255,0.7)'}, 'align': 'center'},
            number = {'font': {'size': 32, 'color': 'white', 'family': 'Inter, sans-serif'}},
            gauge = {
                'axis': {'range': [0, goal], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.3)", 'tickfont': {'size': 9}},
                'bar': {'color': "#ffffff", 'thickness': 0.22},
                'bgcolor': "rgba(255,255,255,0.03)",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, goal*0.7], 'color': 'rgba(255,255,255,0.04)'},
                    {'range': [goal*0.7, goal], 'color': 'rgba(255,255,255,0.07)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 2},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        # High-end production layout overrides for Gauge - Minimal footprint
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10), # Minimal margins
            height=None, 
            width=None, 
            font={'family': "Inter, 'Segoe UI', sans-serif"}
        )
        
        return fig

    def generate_triple_area_chart(
        self,
        df: pd.DataFrame,
        config: ChartConfig
    ) -> go.Figure:
        """Generate a triple-layered area chart comparing actual features from the dataset"""
        # Determine y columns to compare (top 3)
        y_cols = config.y if isinstance(config.y, list) else [config.y] if config.y else []
        if not y_cols:
            y_cols = df.select_dtypes(include=['number']).columns[:3].tolist()
        
        x_col = config.x or df.columns[0]

        # Sanitize data
        df = self._sanitize_data(df, y_cols)
        
        # Create figure
        fig = go.Figure()

        # Premium palette for comparison
        colors = [
            {'color': 'rgba(255, 255, 255, 0.4)', 'fill': 'rgba(255, 255, 255, 0.05)'},
            {'color': 'rgba(59, 130, 246, 0.6)', 'fill': 'rgba(59, 130, 246, 0.1)'},
            {'color': 'rgba(37, 99, 235, 0.8)', 'fill': 'rgba(37, 99, 235, 0.2)'}
        ]

        for idx, col in enumerate(y_cols[:3]):
            style = colors[idx % len(colors)]
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[col],
                mode='lines',
                name=col,
                fill='tonexty' if idx > 0 else 'tozeroy',
                fillcolor=style['fill'],
                line=dict(color=style['color'], width=2, shape='spline'),
                hoverinfo='skip'
            ))

        # Premium layout matching the design
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=10, t=10, b=30),
            xaxis=dict(
                title=dict(text=x_col, font=dict(size=10, color='rgba(255,255,255,0.8)')),
                showgrid=False,
                showline=False,
                zeroline=False,
                tickfont=dict(color='rgba(255,255,255,0.6)', size=10),
                automargin=True,
                nticks=6
            ),
            yaxis=dict(
                title=dict(text=', '.join(y_cols[:3]), font=dict(size=10, color='rgba(255,255,255,0.8)')),
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(color='rgba(255,255,255,0.6)', size=10),
                zeroline=False,
                automargin=True,
                range=[0, max(1, df[y_cols].max().max() * 1.1)] # Force valid range across all features
            ),
            showlegend=True, # Backend legend for internal tracking
            hovermode=False,
            height=300
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