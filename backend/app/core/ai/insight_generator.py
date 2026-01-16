"""
Insight Generator - AI-Powered Data Analysis
Generates natural language insights from data analysis
"""
#backend/app/core/ai/insight_generator.py

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import logging

from .llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)


@dataclass
class DataInsight:
    """Data class for a single insight"""
    category: str  # trend, correlation, anomaly, distribution, quality
    severity: str  # high, medium, low
    title: str
    description: str
    affected_columns: List[str]
    numerical_evidence: Dict[str, Any]
    recommendation: Optional[str] = None


class InsightGenerator:
    """Generate intelligent insights from data analysis"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        
        # Insight categories
        self.categories = {
            "trend": "Temporal patterns and trends",
            "correlation": "Relationships between variables",
            "anomaly": "Outliers and unusual patterns",
            "distribution": "Data distribution characteristics",
            "quality": "Data quality issues"
        }
    
    def analyze_dataframe(self, df: pd.DataFrame) -> List[DataInsight]:
        """Main method to generate all insights from a DataFrame"""
        insights = []
        
        # 1. Statistical Analysis
        insights.extend(self._analyze_distributions(df))
        
        # 2. Correlation Analysis
        insights.extend(self._analyze_correlations(df))
        
        # 3. Time Series Analysis (if datetime columns exist)
        insights.extend(self._analyze_time_series(df))
        
        # 4. Data Quality Analysis
        insights.extend(self._analyze_data_quality(df))
        
        # 5. Anomaly Detection
        insights.extend(self._detect_anomalies(df))
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: severity_order.get(x.severity, 3))
        
        return insights
    
    def _analyze_distributions(self, df: pd.DataFrame) -> List[DataInsight]:
        """Analyze distribution characteristics"""
        insights = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if df[col].isnull().all():
                continue
            
            # Calculate statistics
            mean_val = df[col].mean()
            median_val = df[col].median()
            std_val = df[col].std()
            skewness = df[col].skew()
            
            # Check for high skewness
            if abs(skewness) > 1:
                direction = "right" if skewness > 0 else "left"
                insights.append(DataInsight(
                    category="distribution",
                    severity="medium",
                    title=f"Skewed Distribution in {col}",
                    description=f"The {col} column shows a {direction}-skewed distribution (skewness: {skewness:.2f}). This means most values are concentrated on one side.",
                    affected_columns=[col],
                    numerical_evidence={
                        "skewness": float(skewness),
                        "mean": float(mean_val),
                        "median": float(median_val),
                        "std": float(std_val)
                    },
                    recommendation="Consider log transformation or using median instead of mean for analysis."
                ))
            
            # Check for high variance
            if std_val > mean_val * 2:
                insights.append(DataInsight(
                    category="distribution",
                    severity="low",
                    title=f"High Variance in {col}",
                    description=f"The {col} column has high variance (std: {std_val:.2f}), indicating significant spread in the data.",
                    affected_columns=[col],
                    numerical_evidence={
                        "std": float(std_val),
                        "mean": float(mean_val),
                        "coefficient_of_variation": float(std_val / mean_val) if mean_val != 0 else None
                    }
                ))
        
        return insights
    
    def _analyze_correlations(self, df: pd.DataFrame) -> List[DataInsight]:
        """Analyze correlations between numeric columns"""
        insights = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return insights
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Find strong correlations (excluding diagonal)
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if pd.isna(corr_value):
                    continue
                
                # Strong positive correlation
                if corr_value > 0.7:
                    insights.append(DataInsight(
                        category="correlation",
                        severity="high" if corr_value > 0.9 else "medium",
                        title=f"Strong Positive Correlation: {col1} & {col2}",
                        description=f"There is a strong positive correlation ({corr_value:.2f}) between {col1} and {col2}. As one increases, the other tends to increase as well.",
                        affected_columns=[col1, col2],
                        numerical_evidence={
                            "correlation": float(corr_value),
                            "type": "positive"
                        },
                        recommendation="These variables move together. Consider using one as a predictor for the other."
                    ))
                
                # Strong negative correlation
                elif corr_value < -0.7:
                    insights.append(DataInsight(
                        category="correlation",
                        severity="high" if corr_value < -0.9 else "medium",
                        title=f"Strong Negative Correlation: {col1} & {col2}",
                        description=f"There is a strong negative correlation ({corr_value:.2f}) between {col1} and {col2}. As one increases, the other tends to decrease.",
                        affected_columns=[col1, col2],
                        numerical_evidence={
                            "correlation": float(corr_value),
                            "type": "negative"
                        },
                        recommendation="These variables have an inverse relationship. This could indicate a tradeoff or constraint."
                    ))
        
        return insights
    
    def _analyze_time_series(self, df: pd.DataFrame) -> List[DataInsight]:
        """Analyze time series patterns"""
        insights = []
        
        # Find datetime columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        if len(datetime_cols) == 0:
            return insights
        
        for date_col in datetime_cols:
            # Sort by date
            df_sorted = df.sort_values(by=date_col)
            
            # Analyze numeric columns over time
            numeric_cols = df_sorted.select_dtypes(include=[np.number]).columns
            
            for num_col in numeric_cols:
                if df_sorted[num_col].isnull().all():
                    continue
                
                # Calculate trend
                values = df_sorted[num_col].dropna().values
                if len(values) < 2:
                    continue
                
                # Simple linear trend
                x = np.arange(len(values))
                slope = np.polyfit(x, values, 1)[0]
                
                # Detect significant trend
                mean_val = values.mean()
                if abs(slope) > mean_val * 0.01:  # 1% change per period
                    direction = "increasing" if slope > 0 else "decreasing"
                    percentage_change = (slope / mean_val) * 100
                    
                    insights.append(DataInsight(
                        category="trend",
                        severity="high",
                        title=f"{direction.capitalize()} Trend in {num_col}",
                        description=f"The {num_col} shows a clear {direction} trend over time ({percentage_change:.1f}% change per period).",
                        affected_columns=[date_col, num_col],
                        numerical_evidence={
                            "slope": float(slope),
                            "percentage_change": float(percentage_change),
                            "direction": direction,
                            "first_value": float(values[0]),
                            "last_value": float(values[-1])
                        },
                        recommendation=f"Monitor this {'growth' if slope > 0 else 'decline'} trend for strategic planning."
                    ))
        
        return insights
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> List[DataInsight]:
        """Analyze data quality issues"""
        insights = []
        
        total_rows = len(df)
        
        for col in df.columns:
            # Missing values
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / total_rows) * 100
            
            if missing_pct > 5:
                severity = "high" if missing_pct > 20 else "medium"
                insights.append(DataInsight(
                    category="quality",
                    severity=severity,
                    title=f"Missing Values in {col}",
                    description=f"The {col} column has {missing_count} missing values ({missing_pct:.1f}% of total data).",
                    affected_columns=[col],
                    numerical_evidence={
                        "missing_count": int(missing_count),
                        "missing_percentage": float(missing_pct),
                        "total_rows": total_rows
                    },
                    recommendation="Consider imputation strategies or investigate why data is missing."
                ))
        
        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            duplicate_pct = (duplicate_count / total_rows) * 100
            insights.append(DataInsight(
                category="quality",
                severity="medium" if duplicate_pct > 5 else "low",
                title="Duplicate Rows Detected",
                description=f"Found {duplicate_count} duplicate rows ({duplicate_pct:.1f}% of data).",
                affected_columns=list(df.columns),
                numerical_evidence={
                    "duplicate_count": int(duplicate_count),
                    "duplicate_percentage": float(duplicate_pct)
                },
                recommendation="Review and remove duplicates if they are not intentional."
            ))
        
        return insights
    
    def _detect_anomalies(self, df: pd.DataFrame) -> List[DataInsight]:
        """Detect anomalies using IQR method"""
        insights = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if df[col].isnull().all():
                continue
            
            # Calculate IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier boundaries
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Count outliers
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            outlier_count = len(outliers)
            
            if outlier_count > 0:
                outlier_pct = (outlier_count / len(df)) * 100
                
                if outlier_pct > 1:  # More than 1% outliers
                    insights.append(DataInsight(
                        category="anomaly",
                        severity="medium" if outlier_pct > 5 else "low",
                        title=f"Outliers Detected in {col}",
                        description=f"Found {outlier_count} outlier values ({outlier_pct:.1f}%) in {col} that fall outside the normal range.",
                        affected_columns=[col],
                        numerical_evidence={
                            "outlier_count": int(outlier_count),
                            "outlier_percentage": float(outlier_pct),
                            "lower_bound": float(lower_bound),
                            "upper_bound": float(upper_bound),
                            "min_outlier": float(outliers[col].min()),
                            "max_outlier": float(outliers[col].max())
                        },
                        recommendation="Investigate these outliers - they could be errors or important exceptions."
                    ))
        
        return insights
    
    async def generate_ai_summary(
        self,
        df: pd.DataFrame,
        insights: List[DataInsight],
        user_question: Optional[str] = None
    ) -> str:
        """Generate a production-level, high-impact summary of data insights"""
        
        # Prepare distilled context
        data_summary = f"""
Dataset: {len(df)} rows, {len(df.columns)} columns.
Top Findings: {len(insights)} total.
{"User Interest: " + user_question if user_question else ""}
"""
        
        # Add distilled insights (only top 3, very brief)
        for i, insight in enumerate(insights[:3], 1):
            data_summary += f"\n- {insight.title}: {insight.description}"
        
        # Production-level high-end prompt
        system_message = """You are a high-end AI Data Scientist (Gemini/ChatGPT style).
Your goal is to provide extreme value with minimal words.
Tone: Professional, authoritative, and concise.
Rules:
- NO introductory boilerplate (e.g., "Here is the summary...")
- NO redundant explanations of what the data/information is (unless asked)
- Use brief bullet points for takeaways
- Focus on quality, density, and impact
- Max length: 150 words."""
        
        prompt = f"""{data_summary}

Synthesize these findings into a "Document Discovery" overview:
1. One-sentence high-level verdict.
2. 3-4 ultra-concise takeaways (impact-focused).
3. One critical next step.

Keep it tight. Quality > Quantity."""
        
        try:
            summary = await self.llm.generate(
                prompt=prompt,
                system_message=system_message
            )
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Failed to generate AI summary: {str(e)}")
            return self._generate_basic_summary(insights)
    
    def _generate_basic_summary(self, insights: List[DataInsight]) -> str:
        """Generate basic text summary without AI"""
        if not insights:
            return "No significant insights found in the data."
        
        summary = f"Analysis complete: {len(insights)} insights discovered.\n\n"
        
        # Group by category
        by_category = {}
        for insight in insights:
            if insight.category not in by_category:
                by_category[insight.category] = []
            by_category[insight.category].append(insight)
        
        for category, items in by_category.items():
            summary += f"{category.upper()}: {len(items)} insights\n"
            for item in items[:3]:  # Top 3 per category
                summary += f"  - {item.title}\n"
        
        return summary