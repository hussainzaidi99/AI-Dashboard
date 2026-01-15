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


class AskRequest(BaseModel):
    file_id: str
    question: str
    sheet_index: int = 0


@router.post("/insights")
async def generate_insights(request: InsightRequest):
    """
    Generate AI-powered insights from data with Redis caching
    """
    try:
        # Check cache first (1-hour TTL)
        cache_key = f"insights:{request.file_id}:{request.sheet_index}"
        cached_insights = cache_manager.get(cache_key)
        if cached_insights:
            logger.info(f"Returning cached insights for {request.file_id}")
            return cached_insights
        
        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == request.file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = cache_manager.get(f"processed_result:{request.file_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Data not found in cache")
        
        has_dataframes = data.get('dataframes') and len(data['dataframes']) > 0
        
        if has_dataframes and request.sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Initialize variables
        insights_list = []
        summary = ""
        
        if has_dataframes:
            # Get DataFrame
            sheet_data = data['dataframes'][request.sheet_index]
            df = pd.DataFrame(sheet_data['data'])
            
            # Generate insights from tabular data
            generator = InsightGenerator()
            insights = generator.analyze_dataframe(df)
            
            # Generate AI summary (GROQ API CALL)
            summary = await generator.generate_ai_summary(
                df=df,
                insights=insights,
                user_question=request.user_question
            )
            
            # Convert insights to serializable format
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
        elif data.get('text_content'):
            # Generate insights from text only
            from app.core.ai import get_llm_client
            llm = get_llm_client()
            text_snippet = data['text_content'][:4000]
            
            summary = await llm.generate(
                prompt=f"Please provide an executive summary and 3 key takeaways from this document content:\n\n{text_snippet}",
                system_message="You are a document analysis assistant."
            )
            
            insights_list.append({
                "category": "analysis",
                "severity": "info",
                "title": "Text Analysis Complete",
                "description": "This document consists primarily of unstructured text. Insights are derived from thematic analysis.",
                "affected_columns": [],
                "numerical_evidence": {},
                "recommendation": "Use the Intelligence Assistant to ask specific questions about the content."
            })
        
        result = {
            "file_id": request.file_id,
            "sheet_index": request.sheet_index,
            "insights": insights_list,
            "summary": summary,
            "total_insights": len(insights_list)
        }
        
        # Cache the result for 1 hour (3600 seconds)
        cache_manager.set(cache_key, result, ttl=3600)
        logger.info(f"Cached insights for {request.file_id} (1 hour TTL)")
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        # This catches our custom rate limit errors from LLM client
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        
        # Provide more helpful error messages
        error_detail = str(e)
        if "404" in error_detail or "not found" in error_detail.lower():
            error_detail = (
                "File not found. The file may have been deleted or was not properly uploaded. "
                "Please re-upload the file and try again."
            )
        
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/query")
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


@router.post("/ask")
async def ask_question(request: AskRequest):
    """
    Ask a question about the data and get AI response with caching and reduced context
    """
    try:
        import hashlib
        from app.core.ai import get_llm_client
        
        # Check cache first (30-minute TTL for chatbot)
        question_hash = hashlib.md5(request.question.lower().encode()).hexdigest()[:8]
        cache_key = f"chatbot:{request.file_id}:{question_hash}"
        cached_answer = cache_manager.get(cache_key)
        if cached_answer:
            logger.info(f"Returning cached chatbot answer for question: {request.question[:50]}...")
            return cached_answer
        
        data = cache_manager.get(f"processed_result:{request.file_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Data not found in cache")
        
        has_dataframes = data.get('dataframes') and len(data['dataframes']) > 0
        
        if has_dataframes and request.sheet_index >= len(data['dataframes']):
            raise HTTPException(status_code=400, detail="Sheet index out of range")
        
        # Prepare REDUCED data context (to save tokens)
        data_context = ""
        
        if has_dataframes:
            # Get DataFrame
            sheet_data = data['dataframes'][request.sheet_index]
            df = pd.DataFrame(sheet_data['data'])
            
            # OPTIMIZED: Limit columns to 20 and rows to 3
            limited_columns = df.columns[:20].tolist()
            
            data_context = f"""
Dataset Information:
- Rows: {len(df) if not df.empty else 0}
- Columns: {len(df.columns) if not df.empty else 0}
- Sample Columns (up to 20): {', '.join(limited_columns) if not df.empty else 'None'}

"""
            if not df.empty:
                # OPTIMIZED: Only 3 rows and limited columns
                data_context += f"""
Sample Data (first 3 rows, up to 20 columns):
{df[limited_columns].head(3).to_string()}

Summary Statistics (up to 30 columns):
{df.describe().iloc[:, :30].to_string()}
"""
        elif data.get('text_content'):
            # Use snippet of text content as context if no tables
            text_snippet = data['text_content'][:4000] # Cap at 4k chars
            data_context = f"""
Document Text Content (Snippet):
{text_snippet}
"""
        else:
            raise HTTPException(status_code=400, detail="No analyzable data (dataframes or text content) found for the file.")
        
        # Get LLM client
        llm = get_llm_client()
        
        # Generate response (GROQ API CALL)
        system_message = """You are a data analysis expert. 
Answer questions about the dataset clearly and accurately.
If you need to calculate something, explain your reasoning."""
        
        response = await llm.generate(
            prompt=f"{data_context}\n\nUser Question: {request.question}\n\nProvide a clear, helpful answer.",
            system_message=system_message
        )
        
        result = {
            "file_id": request.file_id,
            "question": request.question,
            "answer": response
        }
        
        # Cache the result for 30 minutes (1800 seconds)
        cache_manager.set(cache_key, result, ttl=1800)
        logger.info(f"Cached chatbot answer (30 min TTL)")
        
        return result
    
    except ValueError as e:
        # Rate limit errors
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
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