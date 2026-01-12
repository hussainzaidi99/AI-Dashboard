#backend/app/services/ai_service.py

"""
AI Service
Business logic for AI-powered operations
"""

import pandas as pd
from typing import Dict, Any, List, Optional
import logging

from app.core.ai import (
    ChartRecommender,
    InsightGenerator,
    QueryParser,
    get_llm_client
)

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.chart_recommender = ChartRecommender()
        self.insight_generator = InsightGenerator()
        self.query_parser = QueryParser()
        self.llm_client = get_llm_client()
    
    async def recommend_charts(
        self,
        df: pd.DataFrame,
        user_intent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chart recommendations for a dataset
        
        Args:
            df: pandas DataFrame
            user_intent: Optional user intent
        
        Returns:
            List of chart recommendations
        """
        try:
            recommendations = await self.chart_recommender.recommend_charts(
                df=df,
                user_intent=user_intent,
                use_ai=True
            )
            
            results = []
            for rec in recommendations:
                results.append({
                    "chart_type": rec.chart_type,
                    "confidence": rec.confidence,
                    "reasoning": rec.reasoning,
                    "columns_required": rec.columns_required,
                    "config": rec.config
                })
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error recommending charts: {str(e)}")
            raise
    
    async def generate_insights(
        self,
        df: pd.DataFrame,
        user_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate insights from data
        
        Args:
            df: pandas DataFrame
            user_question: Optional user question
        
        Returns:
            Insights dictionary
        """
        try:
            # Generate insights
            insights = self.insight_generator.analyze_dataframe(df)
            
            # Generate AI summary
            summary = await self.insight_generator.generate_ai_summary(
                df=df,
                insights=insights,
                user_question=user_question
            )
            
            # Convert to serializable format
            insights_list = []
            for insight in insights:
                insights_list.append({
                    "category": insight.category,
                    "severity": insight.severity.value,
                    "title": insight.title,
                    "description": insight.description,
                    "affected_columns": insight.affected_columns,
                    "numerical_evidence": insight.numerical_evidence,
                    "recommendation": insight.recommendation
                })
            
            return {
                "insights": insights_list,
                "summary": summary,
                "total_insights": len(insights_list)
            }
        
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            raise
    
    async def parse_query(
        self,
        query: str,
        df: pd.DataFrame,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Parse natural language query
        
        Args:
            query: Natural language query
            df: pandas DataFrame
            use_ai: Whether to use AI parsing
        
        Returns:
            Parsed query dictionary
        """
        try:
            parsed = await self.query_parser.parse_query(
                query=query,
                df=df,
                use_ai=use_ai
            )
            
            # Suggest chart type if not specified
            if not parsed.chart_type:
                parsed.chart_type = self.query_parser.suggest_chart_for_intent(parsed, df)
            
            return {
                "intent": parsed.intent.value,
                "chart_type": parsed.chart_type,
                "columns": parsed.columns,
                "filters": parsed.filters,
                "aggregations": parsed.aggregations,
                "groupby": parsed.groupby,
                "sort_by": parsed.sort_by,
                "limit": parsed.limit,
                "confidence": parsed.confidence
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing query: {str(e)}")
            raise
    
    async def answer_question(
        self,
        question: str,
        df: pd.DataFrame
    ) -> str:
        """
        Answer a question about the data
        
        Args:
            question: User question
            df: pandas DataFrame
        
        Returns:
            Answer string
        """
        try:
            # Safe Summary Statistics
            # Limit to first 30 columns/stats and include all types safely
            summary_stats = df.describe(include="all").transpose().head(30)
            
            # Prepare data context with compression
            # Only send first 5-10 rows and limited column info
            data_context = f"""
Dataset Information:
- Total Rows: {len(df)}
- Total Columns: {len(df.columns)}
- Sample Columns (upto 40): {', '.join(df.columns[:40].tolist())}
- Data Types: {df.dtypes.head(40).to_dict()}

Sample Data (first 5 rows):
{df.head(5).to_string()}

Summary Statistics (Sample):
{summary_stats.to_string()}
"""
            
            # Generate response
            system_message = """You are a data analysis expert. 
Answer questions about the dataset clearly and accurately.
If you need to calculate something, explain your reasoning."""
            
            response = await self.llm_client.generate(
                prompt=f"{data_context}\n\nUser Question: {question}\n\nProvide a clear, helpful answer.",
                system_message=system_message
            )
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error answering question: {str(e)}")
            raise