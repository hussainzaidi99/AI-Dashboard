"""
LLM Client - Core LangChain Integration
Handles all LLM interactions with Groq
"""
#backend/app/core/ai/llm_client.py

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import BaseMessage
from typing import Optional, Dict, Any, List
from functools import lru_cache
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Centralized LLM Client for all AI operations"""
    
    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        provider: str = None
    ):
        """Initialize LLM client with Groq or Gemini"""
        self.provider = provider or settings.LLM_PROVIDER
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        # Determine model based on provider if not explicitly passed
        if model:
            self.model = model
        elif settings.LLM_MODEL:
            self.model = settings.LLM_MODEL
        else:
            # Fallback to provider-specific defaults from config
            self.model = settings.GEMINI_MODEL if self.provider == "gemini" else settings.GROQ_MODEL
        
        if self.provider == "gemini":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.api_key = api_key or settings.GEMINI_API_KEY
                self.llm = ChatGoogleGenerativeAI(
                    google_api_key=self.api_key,
                    model=self.model,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            except ImportError:
                logger.error("langchain-google-genai not installed. Run: pip install langchain-google-genai")
                raise ImportError("langchain-google-genai not installed")
        else:
            try:
                from langchain_groq import ChatGroq
                self.api_key = api_key or settings.GROQ_API_KEY
                # Initialize ChatGroq with a clean http_client to avoid proxy issues
                self.llm = ChatGroq(
                    groq_api_key=self.api_key,
                    model_name=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    http_client=httpx.Client()
                )
            except ImportError:
                logger.error("langchain-groq not installed. Run: pip install langchain-groq")
                raise ImportError("langchain-groq not installed")
        
        logger.info(f"LLM Client initialized with provider: {self.provider}, model: {self.model}")
    
    def create_chain(
        self,
        system_template: str,
        human_template: str,
        input_variables: List[str]
    ) -> LLMChain:
        """Create a LangChain chain with system and human prompts"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=settings.DEBUG
        )
    

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        user_id: str = "anonymous",
        endpoint: str = "generate",
        **kwargs
    ) -> str:
        """Generate response from LLM with rate limit handling, history support, and Billing"""
        try:
            from app.core.billing import BillingService
            
            messages = []
            
            if system_message:
                messages.append(("system", system_message))
            
            if history:
                for msg in history:
                    role = msg.get("role", "human")
                    content = msg.get("content", "")
                    if role == "user": role = "human"
                    if role == "assistant": role = "ai"
                    messages.append((role, content))
            
            messages.append(("human", prompt))
            
            response = await self.llm.ainvoke(messages, **kwargs)
            
            # --- Billing Integration ---
            try:
                # Use info level for now to debug token extraction in production
                logger.info(f"LLM Response Metadata: {response.response_metadata}")
                
                input_tokens = 0
                output_tokens = 0
                
                # Try multiple extraction paths for Gemini and others
                # 1. LangChain 0.3+ usage_metadata attribute
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    input_tokens = response.usage_metadata.get('input_tokens', 0)
                    output_tokens = response.usage_metadata.get('output_tokens', 0)
                
                # 2. Response Metadata usage_metadata (Standard)
                if not input_tokens and response.response_metadata:
                    usage = response.response_metadata.get('usage_metadata', {})
                    if usage:
                        input_tokens = usage.get('input_tokens', 0)
                        output_tokens = usage.get('output_tokens', 0)

                # 3. Groq / OpenAI style keys
                if not input_tokens and response.response_metadata:
                    if 'token_usage' in response.response_metadata:
                        token_usage = response.response_metadata['token_usage']
                        input_tokens = token_usage.get('prompt_tokens', 0)
                        output_tokens = token_usage.get('completion_tokens', 0)

                logger.info(f"Final extracted tokens: Input={input_tokens}, Output={output_tokens} for user={user_id}")

                if user_id and user_id != "anonymous" and (input_tokens or output_tokens):
                    await BillingService.log_usage(
                        user_id=user_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        endpoint=endpoint,
                        model=self.model
                    )
                elif user_id and user_id != "anonymous":
                    logger.warning(f"No tokens extracted for active user {user_id}. Skipping billing.")
            except Exception as e:
                logger.error(f"Billing logging failed (non-blocking): {str(e)}")
            # ---------------------------

            return response.content
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limiting errors
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                logger.error(f"{self.provider.capitalize()} API rate limit exceeded: {str(e)}")
                raise ValueError(
                    "AI service is temporarily unavailable due to rate limits. "
                    "Please try again in a few moments. "
                    f"Tip: Reduce the frequency of AI requests or contact support for higher limits."
                )
            
            # Check for connection errors (often rate limiting in disguise)
            elif "connection" in error_msg:
                logger.error(f"{self.provider.capitalize()} API connection error (likely rate limiting): {str(e)}")
                raise ValueError(
                    "AI service is experiencing connectivity issues. "
                    "This is often caused by rate limiting. Please wait 30-60 seconds and try again."
                )
            
            # Generic error
            logger.error(f"LLM generation error: {str(e)}")
            raise ValueError(f"AI service error: {str(e)}")

    async def stream(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        user_id: str = "anonymous",
        endpoint: str = "stream",
        **kwargs
    ):
        """Stream response from LLM token by token with history support and Billing"""
        try:
            from app.core.billing import BillingService

            messages = []
            
            if system_message:
                messages.append(("system", system_message))
            
            if history:
                for msg in history:
                    role = msg.get("role", "human")
                    content = msg.get("content", "")
                    if role == "user": role = "human"
                    if role == "assistant": role = "ai"
                    messages.append((role, content))
            
            messages.append(("human", prompt))
            
            # Accumulate usage for streaming
            accumulated_usage = {"input_tokens": 0, "output_tokens": 0}
            logged = False

            async for chunk in self.llm.astream(messages, **kwargs):
                # Check for usage metadata in chunk
                if chunk.response_metadata:
                     # Gemini / LangChain often sends usage in the last chunk
                     usage = chunk.response_metadata.get('usage_metadata', {})
                     if usage:
                         accumulated_usage = usage 
                
                # Fallback for newer langchain-google-genai versions
                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                    accumulated_usage = chunk.usage_metadata

                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)
            
            # --- Billing Integration (End of Stream) ---
            try:
                input_tokens = accumulated_usage.get('input_tokens', 0)
                output_tokens = accumulated_usage.get('output_tokens', 0)

                if user_id and user_id != "anonymous" and (input_tokens or output_tokens):
                     await BillingService.log_usage(
                        user_id=user_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        endpoint=endpoint,
                        model=self.model
                    )
            except Exception as e:
                logger.error(f"Billing logging failed (non-blocking): {str(e)}")
            # -------------------------------------------
                    
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"LLM streaming error: {str(e)}")
            
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                yield f"\n[Rate Limit Exceeded: {str(e)}]"
            else:
                yield f"\n[AI Service Error: {str(e)}]"
    
    def generate_sync(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """Synchronous version of generate (No billing support yet)"""
        try:
            messages = []
            
            if system_message:
                messages.append(("system", system_message))
            
            messages.append(("human", prompt))
            
            response = self.llm.invoke(messages, **kwargs)
            return response.content
        
        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        system_message: str,
        output_schema: Dict[str, Any],
        user_id: str = "anonymous", 
        endpoint: str = "structured"
    ) -> Dict[str, Any]:
        """Generate structured output (JSON) from LLM"""
        enhanced_system = f"""{system_message}

You MUST respond with valid JSON following this exact schema:
{output_schema}

Important:
- Only return the JSON object, no additional text
- Ensure all keys match the schema exactly
- Use proper JSON formatting
"""
        
        response = await self.generate(
            prompt, 
            enhanced_system, 
            user_id=user_id, 
            endpoint=endpoint
        )
        
        # Parse JSON response
        import json
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"LLM returned invalid JSON: {str(e)}")


@lru_cache()
def get_llm_client() -> LLMClient:
    """Get cached LLM client instance"""
    return LLMClient()