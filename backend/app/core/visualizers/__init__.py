"""
Visualizers Module
Chart generation, customization, and dashboard building with Plotly
"""
#backend/app/core/visualizers/__init__.py


import pandas as pd
import plotly.graph_objects as go
from typing import Union, List, Dict, Any, Optional

from .plotly_generator import PlotlyGenerator
from .chart_factory import ChartFactory, ChartType, ChartConfig
from .dashboard_builder import DashboardBuilder, VizDashboard, VizWidget
from .geo_utils import GeoUtils

__all__ = [
    "ChartFactory",
    "ChartType",
    "ChartConfig",
    "PlotlyGenerator",
    "DashboardBuilder",
    "VizDashboard",
    "VizWidget",
    "GeoUtils",
]


# Convenience function for quick chart generation
def create_chart(
    df: pd.DataFrame,
    chart_type: str,
    x: str = None,
    y: Union[str, List[str]] = None,
    **kwargs
) -> go.Figure:
    """
    Quick chart generation
    
    Args:
        df: pandas DataFrame
        chart_type: Type of chart (bar, line, scatter, etc.)
        x: X-axis column name
        y: Y-axis column name
        **kwargs: Additional chart configuration
    
    Returns:
        Plotly Figure object
    """
    factory = ChartFactory()
    return factory.create(
        chart_type=chart_type,
        df=df,
        x=x,
        y=y,
        **kwargs
    )