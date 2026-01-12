"""
AI API Endpoints
AI-powered analysis, insights, and natural language queries
"""
#backend/app/api/v1/ai.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import logging

from app.core.ai import InsightGenerator, QueryParser
from app.models.mongodb_models import FileUpload
from app.utils.cache import cache_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class InsightRequest(BaseModel):
    file_id: str
    sheet_index: int = 0
    user_question: Optional[str] = None


class QueryRequest(BaseModel):
    file_id: str
    sheet_index: int = 0
    query: str
    use_ai: bool = True


@router.post("/ai/insights")
async def generate_insights(request: InsightRequest):
    """
    Generate AI-powered insights from data
    """
    try:
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == request.file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = cache_manager.get(f"processed_result:{request.file_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Data not found in cache")
        
        if request.sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][request.sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Generate insights
        generator = InsightGenerator()
        insights = generator.analyze_dataframe(df)
        
        # Generate AI summary
        summary = await generator.generate_ai_summary(
            df=df,
            insights=insights,
            user_question=request.user_question
        )
        
        # Convert insights to serializable format
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
            "file_id": request.file_id,
            "sheet_index": request.sheet_index,
            "insights": insights_list,
            "summary": summary,
            "total_insights": len(insights_list)
        }
    
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/query")
async def parse_natural_language_query(request: QueryRequest):
    """
    Parse natural language query and generate visualization
    """
    try:
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == request.file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = cache_manager.get(f"processed_result:{request.file_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Data not found in cache")
        
        if request.sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][request.sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Parse query
        parser = QueryParser()
        parsed = await parser.parse_query(
            query=request.query,
            df=df,
            use_ai=request.use_ai
        )
        
        # Suggest chart type if not specified
        if not parsed.chart_type:
            parsed.chart_type = parser.suggest_chart_for_intent(parsed, df)
        
        return {
            "file_id": request.file_id,
            "query": request.query,
            "parsed": {
                "intent": parsed.intent.value,
                "chart_type": parsed.chart_type,
                "columns": parsed.columns,
                "filters": parsed.filters,
                "aggregations": parsed.aggregations,
                "groupby": parsed.groupby,
                "sort_by": parsed.sort_by,
                "limit": parsed.limit,
                "confidence": parsed.confidence
            },
            "message": "Query parsed successfully. Use /charts/create to generate visualization."
        }
    
    except Exception as e:
        logger.error(f"Error parsing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/ask")
async def ask_question(
    file_id: str,
    question: str,
    sheet_index: int = 0
):
    """
    Ask a question about the data and get AI response
    """
    try:
        from app.core.ai import get_llm_client
        
        data = cache_manager.get(f"processed_result:{file_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Data not found in cache")
        
        if sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Get DataFrame
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        
        # Prepare data context
        data_context = f"""
Dataset Information:
- Rows: {len(df)}
- Columns: {len(df.columns)}
- Column Names: {', '.join(df.columns.tolist())}

Sample Data (first 5 rows):
{df.head(5).to_string()}

Summary Statistics:
{df.describe().to_string()}
"""
        
        # Get LLM client
        llm = get_llm_client()
        
        # Generate response
        system_message = """You are a data analysis expert. 
Answer questions about the dataset clearly and accurately.
If you need to calculate something, explain your reasoning."""
        
        response = await llm.generate(
            prompt=f"{data_context}\n\nUser Question: {question}\n\nProvide a clear, helpful answer.",
            system_message=system_message
        )
        
        return {
            "file_id": file_id,
            "question": question,
            "answer": response
        }
    
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/capabilities")
async def get_ai_capabilities():
    """
    Get information about AI capabilities
    """
    from app.config import settings
    
    return {
        "enabled": settings.ENABLE_AI_RECOMMENDATIONS,
        "model": settings.LLM_MODEL,
        "features": {
            "chart_recommendations": True,
            "insight_generation": True,
            "natural_language_queries": True,
            "question_answering": True,
            "data_summarization": True
        },
        "supported_intents": [
            "visualize",
            "analyze",
            "compare",
            "correlate",
            "trend",
            "distribution",
            "filter",
            "aggregate"
        ]
    }