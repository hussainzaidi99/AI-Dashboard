"""
LLM Client - Core LangChain Integration
Handles all LLM interactions with Groq
"""
#backend/app/core/ai/llm_client.py

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import BaseMessage
from typing import Optional, Dict, Any, List
from functools import lru_cache
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Centralized LLM Client for all AI operations"""
    
    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        """Initialize LLM client with Groq"""
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        # Initialize ChatGroq
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        logger.info(f"LLM Client initialized with model: {self.model}")
    
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
        **kwargs
    ) -> str:
        """Generate response from LLM"""
        try:
            messages = []
            
            if system_message:
                messages.append(("system", system_message))
            
            messages.append(("human", prompt))
            
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content
        
        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            raise
    
    def generate_sync(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """Synchronous version of generate"""
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
        output_schema: Dict[str, Any]
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
        
        response = await self.generate(prompt, enhanced_system)
        
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