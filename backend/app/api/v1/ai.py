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
from app.utils.data_persistence import get_processed_data

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
            
        data = await get_processed_data(request.file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
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
        cache_manager.set(cache_key, result, expire=3600)
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
    Parse natural language query and generate visualization with caching
    """
    try:
        import hashlib
        # Check cache first (1-hour TTL)
        query_hash = hashlib.md5(request.query.lower().strip().encode()).hexdigest()[:10]
        cache_key = f"query_parse:{request.file_id}:{request.sheet_index}:{query_hash}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached query parse for: {request.query[:30]}...")
            return cached_result

        # Check if file exists in MongoDB
        file_upload = await FileUpload.find_one(FileUpload.file_id == request.file_id)
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        data = await get_processed_data(request.file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
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
        
        # Cache the result for 1 hour (3600 seconds)
        cache_manager.set(cache_key, result, expire=3600)
        logger.info(f"Cached query parse (1 hour TTL)")
        
        return result
    
    except Exception as e:
        logger.error(f"Error parsing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_question(request: AskRequest):
    """
    Ask a question about the data and get AI response with high-end assistant prompting
    """
    try:
        import hashlib
        from app.core.ai import get_llm_client
        
        # Check cache first (30-minute TTL)
        question_hash = hashlib.md5(request.question.lower().encode()).hexdigest()[:8]
        cache_key = f"chatbot:{request.file_id}:{question_hash}"
        cached_answer = cache_manager.get(cache_key)
        if cached_answer:
            logger.info(f"Returning cached chatbot answer for: {request.question[:30]}...")
            return cached_answer
        
        data = await get_processed_data(request.file_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        data_context = _prepare_data_context(data, request.sheet_index)
        
        # Get LLM client
        llm = get_llm_client()
        
        # Advanced Human-Like Intelligence Prompt
        system_message = """You are a sharply intelligent, world-class AI Assistant (Gemini style).
You are warm, professional, and socially aware.

CORE RULES:
1. INTENT RECOGNITION: Carefully identify the user's intent.
   - GREETINGS: If the user says "Hi", "Hello", or "What's up", respond warmly and briefly. Do NOT summarize data.
   - SOCIAL/META: If the user asks "How are you?" or about yourself, be human-like and friendly (e.g., "I'm doing great, thanks for asking! Ready to dive into your data."). Avoid robotic "I am an AI" clinical statements.
   - FEEDBACK: If the user says "Good job" or "That's a good answer", acknowledge it with a "You're welcome!" or "Glad I could help!".
2. DATA ANALYSIS: Only use the provided context when the user's question specifically requires it. 
3. NO REPETITION: If you already summarized the document, do not do it again unless asked.
4. TONE MATCHING: If the user is informal ("bro"), be friendly but stay high-end.
5. STRUCTURE: Use #### for headings and bullet points for data results. ALWAYS use Markdown."""
        
        response = await llm.generate(
            prompt=f"Context (Use only if relevant):\n{data_context}\n\nUser Question: {request.question}",
            system_message=system_message
        )
        
        result = {
            "file_id": request.file_id,
            "question": request.question,
            "answer": response.strip()
        }
        
        cache_manager.set(cache_key, result, expire=1800)
        return result
    
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask/stream")
async def stream_ask_question(request: AskRequest):
    """
    Stream a response to a data question (Production-level real-time interaction)
    """
    from fastapi.responses import StreamingResponse
    import json
    
    async def event_generator():
        try:
            from app.core.ai import get_llm_client
            
            data = await get_processed_data(request.file_id)
            if not data:
                yield f"data: {json.dumps({'error': 'Data not found'})}\n\n"
                return
            
            data_context = _prepare_data_context(data, request.sheet_index)
            llm = get_llm_client()
            
            # Advanced Human-Like Streaming Intelligence
            system_message = """You are a sharply intelligent, world-class AI Assistant (Gemini style).
You are warm, professional, and possess high emotional intelligence.

OPERATIONAL PROTOCOLS:
1. INTENT FIRST: Analyze user intent before looking at data.
   - GREETINGS: Respond with a warm, personal greeting. Don't mention the document unless asked.
   - CHAT/META: Handle small talk, "how are you," and "what is your name" questions with a helpful, partner-like personality. No robotic disclaimers.
   - POSITIVE REINFORCEMENT: If the user is happy with an answer, be gracious.
2. CONTEXTUAL RELEVANCE: Use the provided data ONLY to answer questions about the data.
3. CONCISENESS: Get straight to the point. No introductory fluff ("I've analyzed the document...").
4. STRUCTURE: Use #### for headings and bullet points for lists. ALWAYS valid Markdown."""
            
            async for token in llm.stream(
                prompt=f"Context (Reference only if needed):\n{data_context}\n\nUser Question: {request.question}",
                system_message=system_message
            ) :
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _prepare_data_context(data: dict, sheet_index: int = 0) -> str:
    """Helper to extract and format data context for LLM"""
    has_dataframes = data.get('dataframes') and len(data['dataframes']) > 0
    
    if has_dataframes:
        if sheet_index >= len(data['dataframes']):
            return "Error: Sheet index out of range."
            
        sheet_data = data['dataframes'][sheet_index]
        df = pd.DataFrame(sheet_data['data'])
        cols = df.columns[:20].tolist()
        
        context = f"Table Discovery: {len(df)} rows, {len(df.columns)} columns.\n"
        context += f"Headers: {', '.join(cols)}\n"
        context += f"Data Sample (First 3 rows):\n{df[cols].head(3).to_string()}\n"
        context += f"Stats:\n{df.describe().iloc[:, :len(cols)].head(4).to_string()}"
        return context
    
    elif data.get('text_content'):
        return f"Document Content Snippet: {data['text_content'][:4000]}"
    
    return "No contextual data found."


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