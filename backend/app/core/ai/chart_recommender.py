"""
Chart Recommender - AI-Powered Visualization Suggestions
Combines rule-based logic with LLM intelligence
"""
#backend/app/core/ai/chart_recommender.py

from typing import List, Dict, Any, Optional
import pandas as pd
from dataclasses import dataclass
import logging

from .llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)


@dataclass
class ChartRecommendation:
    """Data class for chart recommendations"""
    chart_type: str
    confidence: float  # 0-1
    reasoning: str
    columns_required: List[str]
    config: Dict[str, Any]


class ChartRecommender:
    """Intelligent chart recommendation engine"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        
        # Rule-based chart mappings
        self.chart_rules = {
            "single_numeric": ["histogram", "box_plot", "violin_plot", "density_plot"],
            "single_categorical": ["bar_chart", "pie_chart", "donut_chart"],
            "two_numeric": ["line_chart", "area_chart", "bubble_chart"],
            "categorical_numeric": ["bar_chart", "violin_plot", "box_plot"],
            "time_series": ["line_chart", "area_chart"],
            "multi_numeric": ["pie_chart", "bar_chart", "bubble_chart"],
            "geographic": ["choropleth_map"],
            "hierarchical": ["treemap", "sunburst"],
        }
    
    def analyze_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze DataFrame structure for chart recommendations"""
        analysis = {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": {},
            "data_types": {},
            "patterns": []
        }
        
        for col in df.columns:
            col_data = {
                "name": col,
                "dtype": str(df[col].dtype),
                "nunique": df[col].nunique(),
                "null_count": df[col].isnull().sum(),
                "null_percentage": (df[col].isnull().sum() / len(df)) * 100
            }
            
            # Classify column type
            if pd.api.types.is_numeric_dtype(df[col]):
                col_data["type"] = "numeric"
                col_data["stats"] = {
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                    "median": float(df[col].median()) if not df[col].isnull().all() else None,
                }
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_data["type"] = "datetime"
                col_data["date_range"] = {
                    "min": str(df[col].min()),
                    "max": str(df[col].max())
                }
                analysis["patterns"].append("time_series")
            elif col_data["nunique"] / len(df) < 0.05:  # Less than 5% unique
                col_data["type"] = "categorical"
                col_data["categories"] = df[col].value_counts().head(10).to_dict()
            else:
                col_data["type"] = "text"
            
            analysis["columns"][col] = col_data
            
            # Track data types for pattern detection
            if col_data["type"] not in analysis["data_types"]:
                analysis["data_types"][col_data["type"]] = []
            analysis["data_types"][col_data["type"]].append(col)
        
        # Detect patterns
        num_numeric = len(analysis["data_types"].get("numeric", []))
        num_categorical = len(analysis["data_types"].get("categorical", []))
        num_datetime = len(analysis["data_types"].get("datetime", []))
        
        if num_datetime > 0:
            analysis["patterns"].append("time_series")
        if num_numeric >= 3:
            analysis["patterns"].append("multi_numeric")
        if num_numeric == 2:
            analysis["patterns"].append("two_numeric")
        if num_numeric == 1 and num_categorical == 0:
            analysis["patterns"].append("single_numeric")
        if num_categorical >= 1 and num_numeric >= 1:
            analysis["patterns"].append("categorical_numeric")
        if num_categorical >= 1 and num_numeric == 0:
            analysis["patterns"].append("single_categorical")
        
        return analysis
    
    def get_rule_based_recommendations(
        self, 
        analysis: Dict[str, Any]
    ) -> List[ChartRecommendation]:
        """Get recommendations based on hard-coded rules"""
        recommendations = []
        patterns = analysis["patterns"]
        
        for pattern in patterns:
            if pattern in self.chart_rules:
                for chart_type in self.chart_rules[pattern]:
                    recommendations.append(ChartRecommendation(
                        chart_type=chart_type,
                        confidence=0.7,  # Rule-based confidence
                        reasoning=f"Suitable for {pattern} data pattern",
                        columns_required=self._get_required_columns(chart_type, analysis),
                        config=self._get_default_config(chart_type)
                    ))
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _get_required_columns(self, chart_type: str, analysis: Dict[str, Any]) -> List[str]:
        """Determine which columns are needed for a chart type"""
        data_types = analysis["data_types"]
        
        if chart_type in ["histogram", "box_plot", "violin_plot", "density_plot"]:
            return data_types.get("numeric", [])[:1]
        elif chart_type in ["bar_chart", "pie_chart", "donut_chart"]:
            return data_types.get("categorical", [])[:1]
        elif chart_type in ["line_chart", "area_chart", "bubble_chart"]:
            return data_types.get("numeric", [])[:2]
        else:
            return []
    
    def _get_default_config(self, chart_type: str) -> Dict[str, Any]:
        """Get default configuration for chart type"""
        return {
            "height": 500,
            "width": 800,
            "theme": "plotly",
            "show_legend": True,
            "interactive": True
        }
    
    async def get_ai_recommendations(
        self,
        analysis: Dict[str, Any],
        user_intent: Optional[str] = None,
        user_id: str = "anonymous"
    ) -> List[ChartRecommendation]:
        """Get AI-powered recommendations using LLM"""
        
        # Prepare data summary for LLM
        data_summary = f"""
Dataset Overview:
- Rows: {analysis['num_rows']}
- Columns: {analysis['num_columns']}

Column Information:
"""
        
        for col_name, col_info in analysis['columns'].items():
            data_summary += f"\n- {col_name} ({col_info['type']})"
            if col_info['type'] == 'numeric' and 'stats' in col_info:
                data_summary += f" [Range: {col_info['stats'].get('min')} to {col_info['stats'].get('max')}]"
            elif col_info['type'] == 'categorical':
                data_summary += f" [{col_info['nunique']} unique values]"
        
        data_summary += f"\n\nDetected Patterns: {', '.join(analysis['patterns'])}"
        
        if user_intent:
            data_summary += f"\n\nUser Intent: {user_intent}"
        
        # LLM Prompt
        system_message = """You are an expert data visualization consultant. 
Your task is to recommend the most effective chart types for the given dataset.

Consider:
1. Data types and patterns
2. Best practices in data visualization
3. User intent (if provided)
4. Readability and clarity

Recommend 3-5 chart types with reasoning."""
        
        prompt = f"""{data_summary}

Provide chart recommendations in the following JSON format:
{{
    "recommendations": [
        {{
            "chart_type": "line_chart",
            "confidence": 0.9,
            "reasoning": "Perfect for showing trends and relationships between variables",
            "columns_required": ["column1", "column2"],
            "config": {{"markers": true}}
        }}
    ]
}}

Chart types to choose from:
- histogram, box_plot, violin_plot, density_plot (single numeric)
- bar_chart, pie_chart, donut_chart (categorical)
- line_chart, area_chart, bubble_chart (two numeric or time series)
- treemap, sunburst (hierarchical)
"""
        
        try:
            response = await self.llm.generate_structured(
                prompt=prompt,
                system_message=system_message,
                output_schema={
                    "recommendations": [
                        {
                            "chart_type": "string",
                            "confidence": "float",
                            "reasoning": "string",
                            "columns_required": ["string"],
                            "config": {}
                        }
                    ]
                },
                user_id=user_id,
                endpoint="chart_recommend"
            )
            
            # Convert to ChartRecommendation objects
            recommendations = []
            for rec in response.get("recommendations", []):
                recommendations.append(ChartRecommendation(
                    chart_type=rec["chart_type"],
                    confidence=rec["confidence"],
                    reasoning=rec["reasoning"],
                    columns_required=rec["columns_required"],
                    config=rec.get("config", {})
                ))
            
            return recommendations
        
        except Exception as e:
            logger.error(f"AI recommendation error: {str(e)}")
            return []
    
    async def recommend_charts(
        self,
        df: pd.DataFrame,
        user_intent: Optional[str] = None,
        use_ai: bool = True,
        user_id: str = "anonymous"
    ) -> List[ChartRecommendation]:
        """Main method to get chart recommendations"""
        
        # Analyze data structure
        analysis = self.analyze_data_structure(df)
        
        # Get rule-based recommendations
        rule_recommendations = self.get_rule_based_recommendations(analysis)
        
        # Get AI recommendations if enabled
        if use_ai:
            try:
                ai_recommendations = await self.get_ai_recommendations(analysis, user_intent, user_id=user_id)
                
                # Merge and deduplicate recommendations
                all_recs = ai_recommendations + rule_recommendations
                seen = set()
                unique_recs = []
                
                for rec in all_recs:
                    if rec.chart_type not in seen:
                        seen.add(rec.chart_type)
                        unique_recs.append(rec)
                
                # Sort by confidence
                unique_recs.sort(key=lambda x: x.confidence, reverse=True)
                return unique_recs[:5]
            
            except Exception as e:
                logger.warning(f"AI recommendations failed, using rule-based only: {str(e)}")
                return rule_recommendations
        
        return rule_recommendations