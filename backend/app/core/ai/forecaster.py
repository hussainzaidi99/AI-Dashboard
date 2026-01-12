"""
Time Series Forecaster - Predictive analytics with Prophet
Provides automated time series forecasting with seasonality detection
"""
#backend/app/core/ai/forecaster.py

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ForecastConfig:
    """Configuration for time series forecasting"""
    periods: int = 30  # Number of periods to forecast
    freq: str = "D"  # Frequency: D=daily, W=weekly, M=monthly
    include_history: bool = True  # Include historical data in output
    confidence_interval: float = 0.95  # Confidence interval (0-1)
    seasonality_mode: str = "additive"  # additive or multiplicative
    yearly_seasonality: Optional[bool] = None  # Auto-detect if None
    weekly_seasonality: Optional[bool] = None  # Auto-detect if None
    daily_seasonality: Optional[bool] = None  # Auto-detect if None
    growth: str = "linear"  # linear or logistic
    changepoint_prior_scale: float = 0.05  # Flexibility of trend
    seasonality_prior_scale: float = 10.0  # Flexibility of seasonality


@dataclass
class ForecastResult:
    """Results from time series forecasting"""
    forecast_df: pd.DataFrame  # Forecast with yhat, yhat_lower, yhat_upper
    historical_df: pd.DataFrame  # Historical data
    metrics: Dict[str, float]  # Accuracy metrics (MAPE, RMSE, MAE)
    seasonality_components: Dict[str, pd.DataFrame]  # Seasonal components
    trend: pd.DataFrame  # Trend component
    changepoints: List[datetime]  # Detected changepoints
    config: ForecastConfig
    warnings: List[str] = field(default_factory=list)


class TimeSeriesForecaster:
    """Time series forecasting using Prophet"""
    
    def __init__(self):
        """Initialize forecaster"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._check_prophet_available()
    
    def _check_prophet_available(self):
        """Check if Prophet is installed"""
        try:
            import prophet
            self.prophet_available = True
            self.logger.info("Prophet library is available")
        except ImportError:
            self.prophet_available = False
            self.logger.warning(
                "Prophet library not installed. "
                "Install with: pip install prophet"
            )
    
    def forecast(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        config: Optional[ForecastConfig] = None
    ) -> ForecastResult:
        """
        Generate time series forecast
        
        Args:
            df: DataFrame with time series data
            date_column: Name of date/datetime column
            value_column: Name of value column to forecast
            config: Optional forecast configuration
        
        Returns:
            ForecastResult with predictions and analysis
        
        Raises:
            ImportError: If Prophet is not installed
            ValueError: If data is invalid
        """
        if not self.prophet_available:
            raise ImportError(
                "Prophet library is required for forecasting. "
                "Install with: pip install prophet"
            )
        
        from prophet import Prophet
        
        config = config or ForecastConfig()
        warnings = []
        
        # Validate and prepare data
        df_clean = self._prepare_data(df, date_column, value_column)
        
        if len(df_clean) < 10:
            raise ValueError(
                f"Insufficient data for forecasting. "
                f"Need at least 10 data points, got {len(df_clean)}"
            )
        
        # Detect frequency if not specified
        if config.freq == "D":
            detected_freq = self._detect_frequency(df_clean['ds'])
            if detected_freq:
                config.freq = detected_freq
                self.logger.info(f"Detected frequency: {detected_freq}")
        
        # Create and configure Prophet model
        model = Prophet(
            growth=config.growth,
            seasonality_mode=config.seasonality_mode,
            yearly_seasonality=config.yearly_seasonality,
            weekly_seasonality=config.weekly_seasonality,
            daily_seasonality=config.daily_seasonality,
            changepoint_prior_scale=config.changepoint_prior_scale,
            seasonality_prior_scale=config.seasonality_prior_scale,
            interval_width=config.confidence_interval
        )
        
        # Fit model
        self.logger.info(f"Training Prophet model on {len(df_clean)} data points")
        model.fit(df_clean)
        
        # Create future dataframe
        future = model.make_future_dataframe(
            periods=config.periods,
            freq=config.freq,
            include_history=config.include_history
        )
        
        # Generate forecast
        forecast = model.predict(future)
        
        # Extract components
        seasonality_components = {}
        if 'yearly' in forecast.columns:
            seasonality_components['yearly'] = forecast[['ds', 'yearly']].copy()
        if 'weekly' in forecast.columns:
            seasonality_components['weekly'] = forecast[['ds', 'weekly']].copy()
        if 'daily' in forecast.columns:
            seasonality_components['daily'] = forecast[['ds', 'daily']].copy()
        
        # Get trend
        trend_df = forecast[['ds', 'trend']].copy()
        
        # Get changepoints
        changepoints = model.changepoints.tolist() if hasattr(model, 'changepoints') else []
        
        # Calculate accuracy metrics on historical data
        metrics = self._calculate_metrics(df_clean, forecast)
        
        # Separate historical and forecast data
        historical_df = df_clean.copy()
        forecast_only = forecast[forecast['ds'] > df_clean['ds'].max()].copy()
        
        # Check for warnings
        if metrics.get('mape', 0) > 20:
            warnings.append(
                f"High forecast error (MAPE: {metrics['mape']:.1f}%). "
                "Predictions may be unreliable."
            )
        
        if len(df_clean) < 30:
            warnings.append(
                "Limited historical data. Forecast accuracy may be reduced."
            )
        
        return ForecastResult(
            forecast_df=forecast_only,
            historical_df=historical_df,
            metrics=metrics,
            seasonality_components=seasonality_components,
            trend=trend_df,
            changepoints=changepoints,
            config=config,
            warnings=warnings
        )
    
    def _prepare_data(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str
    ) -> pd.DataFrame:
        """
        Prepare data for Prophet (requires 'ds' and 'y' columns)
        
        Args:
            df: Input DataFrame
            date_column: Date column name
            value_column: Value column name
        
        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        # Create copy
        df_prep = df[[date_column, value_column]].copy()
        
        # Rename columns
        df_prep.columns = ['ds', 'y']
        
        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(df_prep['ds']):
            df_prep['ds'] = pd.to_datetime(df_prep['ds'])
        
        # Remove missing values
        df_prep = df_prep.dropna()
        
        # Sort by date
        df_prep = df_prep.sort_values('ds').reset_index(drop=True)
        
        # Remove duplicates (keep last)
        df_prep = df_prep.drop_duplicates(subset=['ds'], keep='last')
        
        return df_prep
    
    def _detect_frequency(self, dates: pd.Series) -> Optional[str]:
        """
        Detect time series frequency
        
        Args:
            dates: Series of datetime values
        
        Returns:
            Frequency string or None
        """
        if len(dates) < 2:
            return None
        
        # Calculate median time difference
        diffs = dates.diff().dropna()
        median_diff = diffs.median()
        
        # Map to frequency
        if median_diff <= timedelta(hours=1):
            return "H"  # Hourly
        elif median_diff <= timedelta(days=1):
            return "D"  # Daily
        elif median_diff <= timedelta(days=7):
            return "W"  # Weekly
        elif median_diff <= timedelta(days=31):
            return "M"  # Monthly
        elif median_diff <= timedelta(days=92):
            return "Q"  # Quarterly
        else:
            return "Y"  # Yearly
    
    def _calculate_metrics(
        self,
        historical: pd.DataFrame,
        forecast: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics
        
        Args:
            historical: Historical data with 'ds' and 'y'
            forecast: Forecast data with 'ds' and 'yhat'
        
        Returns:
            Dictionary with MAPE, RMSE, MAE
        """
        # Merge historical and forecast on date
        merged = historical.merge(
            forecast[['ds', 'yhat']],
            on='ds',
            how='inner'
        )
        
        if len(merged) == 0:
            return {'mape': 0.0, 'rmse': 0.0, 'mae': 0.0}
        
        actual = merged['y'].values
        predicted = merged['yhat'].values
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # Mean Absolute Error
        mae = np.mean(np.abs(actual - predicted))
        
        return {
            'mape': float(mape),
            'rmse': float(rmse),
            'mae': float(mae),
            'samples': len(merged)
        }
    
    def detect_seasonality(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str
    ) -> Dict[str, Any]:
        """
        Detect seasonal patterns in time series
        
        Args:
            df: DataFrame with time series
            date_column: Date column name
            value_column: Value column name
        
        Returns:
            Dictionary with seasonality information
        """
        df_clean = self._prepare_data(df, date_column, value_column)
        
        # Simple seasonality detection using autocorrelation
        from scipy import stats
        
        values = df_clean['y'].values
        n = len(values)
        
        seasonality_info = {
            'has_trend': False,
            'has_yearly': False,
            'has_weekly': False,
            'has_daily': False,
            'strength': 'none'
        }
        
        # Check for trend
        x = np.arange(n)
        slope, _, r_value, _, _ = stats.linregress(x, values)
        if abs(r_value) > 0.3:
            seasonality_info['has_trend'] = True
            seasonality_info['trend_direction'] = 'increasing' if slope > 0 else 'decreasing'
        
        # Check for yearly seasonality (if enough data)
        if n >= 365:
            yearly_autocorr = self._calculate_autocorrelation(values, lag=365)
            if yearly_autocorr > 0.5:
                seasonality_info['has_yearly'] = True
        
        # Check for weekly seasonality
        if n >= 14:
            weekly_autocorr = self._calculate_autocorrelation(values, lag=7)
            if weekly_autocorr > 0.5:
                seasonality_info['has_weekly'] = True
        
        # Determine overall strength
        max_autocorr = max(
            yearly_autocorr if n >= 365 else 0,
            weekly_autocorr if n >= 14 else 0
        )
        
        if max_autocorr > 0.7:
            seasonality_info['strength'] = 'strong'
        elif max_autocorr > 0.5:
            seasonality_info['strength'] = 'moderate'
        elif max_autocorr > 0.3:
            seasonality_info['strength'] = 'weak'
        
        return seasonality_info
    
    def _calculate_autocorrelation(
        self,
        series: np.ndarray,
        lag: int
    ) -> float:
        """Calculate autocorrelation at given lag"""
        if len(series) < lag + 1:
            return 0.0
        
        # Normalize
        series_norm = (series - np.mean(series)) / np.std(series)
        
        # Calculate autocorrelation
        autocorr = np.corrcoef(
            series_norm[:-lag],
            series_norm[lag:]
        )[0, 1]
        
        return float(autocorr) if not np.isnan(autocorr) else 0.0
    
    def evaluate_forecast(
        self,
        actual: pd.DataFrame,
        forecast: pd.DataFrame,
        date_column: str = 'ds',
        value_column: str = 'y'
    ) -> Dict[str, float]:
        """
        Evaluate forecast accuracy against actual values
        
        Args:
            actual: DataFrame with actual values
            forecast: DataFrame with forecast values
            date_column: Date column name
            value_column: Value column name (actual) or 'yhat' (forecast)
        
        Returns:
            Dictionary with evaluation metrics
        """
        # Prepare actual data
        actual_prep = actual[[date_column, value_column]].copy()
        actual_prep.columns = ['ds', 'y']
        
        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(actual_prep['ds']):
            actual_prep['ds'] = pd.to_datetime(actual_prep['ds'])
        
        # Calculate metrics
        return self._calculate_metrics(actual_prep, forecast)
