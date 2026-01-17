#backend/app/config.py

"""
Configuration Management
Handles all environment variables and application settings
"""

import os
from typing import Optional, List, Set
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application Settings - Loaded from environment variables"""
    
    # ==================== Application ====================
    APP_NAME: str = os.getenv("APP_NAME")
    APP_VERSION: str = os.getenv("APP_VERSION")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # ==================== API ====================
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX")
    
    # ==================== CORS ====================
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        origins_str = os.getenv("CORS_ORIGINS")
        if not origins_str:
            raise ValueError("CORS_ORIGINS not set in .env file")
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    # ==================== File Upload ====================
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB default
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    EXPORT_DIR: str = os.getenv("EXPORT_DIR", "./exports")
    
    @property
    def ALLOWED_EXTENSIONS(self) -> Set[str]:
        """Convert ALLOWED_EXTENSIONS string to set"""
        extensions_str = os.getenv("ALLOWED_EXTENSIONS")
        if not extensions_str:
            raise ValueError("ALLOWED_EXTENSIONS not set in .env file")
        return {ext.strip().lower() for ext in extensions_str.split(",") if ext.strip()}
    
    # ==================== Database ====================
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ai_dashboard")
    
    # ==================== Redis ====================
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # ==================== Celery ====================
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # ==================== AI/LLM Configuration ====================
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "") # If provided, overrides provider-specific model
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # Options: groq, gemini
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    
    # ==================== OCR ====================
    TESSERACT_PATH: Optional[str] = os.getenv("TESSERACT_PATH") or None
    
    # ==================== File Processing Limits ====================
    PDF_MAX_PAGES: int = int(os.getenv("PDF_MAX_PAGES", "100"))
    IMAGE_MAX_WIDTH: int = int(os.getenv("IMAGE_MAX_WIDTH", "4096"))
    IMAGE_MAX_HEIGHT: int = int(os.getenv("IMAGE_MAX_HEIGHT", "4096"))
    
    @property
    def IMAGE_MAX_SIZE(self) -> tuple:
        """Return image max size as tuple"""
        return (self.IMAGE_MAX_WIDTH, self.IMAGE_MAX_HEIGHT)
    
    # ==================== Visualization ====================
    CHART_DEFAULT_HEIGHT: int = int(os.getenv("CHART_DEFAULT_HEIGHT", "600"))
    CHART_DEFAULT_WIDTH: int = int(os.getenv("CHART_DEFAULT_WIDTH", "800"))
    CHART_THEME: str = os.getenv("CHART_THEME", "plotly_white")
    
    # ==================== Security ====================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    
    # ==================== Logging ====================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/app.log")
    
    # ==================== Feature Flags ====================
    ENABLE_AI_RECOMMENDATIONS: bool = os.getenv("ENABLE_AI_RECOMMENDATIONS", "False").lower() == "true"
    ENABLE_EXPORT_PDF: bool = os.getenv("ENABLE_EXPORT_PDF", "False").lower() == "true"
    ENABLE_EXPORT_EXCEL: bool = os.getenv("ENABLE_EXPORT_EXCEL", "False").lower() == "true"
    ENABLE_WEBSOCKET: bool = os.getenv("ENABLE_WEBSOCKET", "False").lower() == "true"
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "False").lower() == "true"
    
    # ==================== Conversation ====================
    CONVERSATION_MAX_HISTORY: int = int(os.getenv("CONVERSATION_MAX_HISTORY", "50"))
    CONVERSATION_TIMEOUT_MINUTES: int = int(os.getenv("CONVERSATION_TIMEOUT_MINUTES", "30"))
    
    # ==================== Forecasting ====================
    FORECAST_DEFAULT_PERIODS: int = int(os.getenv("FORECAST_DEFAULT_PERIODS", "30"))
    FORECAST_CONFIDENCE_INTERVAL: float = float(os.getenv("FORECAST_CONFIDENCE_INTERVAL", "0.95"))
    
    # ==================== Clustering ====================
    CLUSTERING_MAX_CLUSTERS: int = int(os.getenv("CLUSTERING_MAX_CLUSTERS", "10"))
    CLUSTERING_MIN_SAMPLES: int = int(os.getenv("CLUSTERING_MIN_SAMPLES", "5"))
    
    def __init__(self):
        """Initialize settings and create necessary directories"""
        self._validate_required_settings()
        self._create_directories()
    
    def _validate_required_settings(self):
        """Validate that required environment variables are set"""
        required_vars = {
            "APP_NAME": self.APP_NAME,
            "APP_VERSION": self.APP_VERSION,
            "API_V1_PREFIX": self.API_V1_PREFIX,
        }
        
        # Only require API key if AI recommendations are enabled
        if self.ENABLE_AI_RECOMMENDATIONS:
            if self.LLM_PROVIDER == "gemini":
                required_vars["GEMINI_API_KEY"] = self.GEMINI_API_KEY
            else:
                required_vars["GROQ_API_KEY"] = self.GROQ_API_KEY
        
        missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables in .env file:\n"
                f"   {', '.join(missing_vars)}\n\n"
                f"Please check your .env file and ensure all variables are set."
            )
        
        # Special validation for API keys based on provider
        if self.ENABLE_AI_RECOMMENDATIONS:
            if self.LLM_PROVIDER == "gemini":
                if not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "your_gemini_api_key_here":
                    raise ValueError(
                        "GEMINI_API_KEY is not configured but ENABLE_AI_RECOMMENDATIONS is True and provider is Gemini!\n"
                        "   Please add your actual API key to the .env file."
                    )
            else:
                if not self.GROQ_API_KEY or self.GROQ_API_KEY == "your_groq_api_key_here":
                    raise ValueError(
                        "GROQ_API_KEY is not configured but ENABLE_AI_RECOMMENDATIONS is True and provider is Groq!\n"
                        "   Please add your actual API key from: https://console.groq.com/\n"
                        "   Edit the .env file and set: GROQ_API_KEY=your_actual_key"
                    )
        
        # Special validation for SECRET_KEY
        if self.SECRET_KEY == "your_secret_key_here_generate_a_secure_random_string":
            print(
                "WARNING: Using default SECRET_KEY!\n"
                "   For production, generate a secure key with: openssl rand -hex 32\n"
                "   And update it in your .env file"
            )
        
        # Special validation for JWT_SECRET_KEY
        if self.JWT_SECRET_KEY == "your_jwt_secret_key_here":
            print(
                "WARNING: Using default JWT_SECRET_KEY!\n"
                "   For production, generate a secure key and update it in your .env file"
            )
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.UPLOAD_DIR,
            self.EXPORT_DIR,
            os.path.dirname(self.LOG_FILE) if self.LOG_FILE and os.path.dirname(self.LOG_FILE) else None
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                if self.DEBUG:
                    print(f"Created directory: {directory}")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    This ensures we only load the environment variables once
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()


# ==================== Helper Functions ====================

def get_upload_path(filename: str) -> str:
    """Get full upload path for a file"""
    return os.path.join(settings.UPLOAD_DIR, filename)


def get_export_path(filename: str) -> str:
    """Get full export path for a file"""
    return os.path.join(settings.EXPORT_DIR, filename)


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    if not filename or "." not in filename:
        return False
    
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in settings.ALLOWED_EXTENSIONS


def get_file_size_limit_mb() -> float:
    """Get file size limit in MB"""
    return settings.MAX_FILE_SIZE / (1024 * 1024)


# Print configuration summary on load (only in debug mode)
if settings.DEBUG:
    print("\n" + "="*50)
    print("AI Data Visualization Dashboard - Backend")
    print("="*50)
    print(f"App Version: {settings.APP_VERSION}")
    print(f"API Prefix: {settings.API_V1_PREFIX}")
    print(f"CORS Origins: {', '.join(settings.CORS_ORIGINS)}")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"LLM Model: {settings.LLM_MODEL}")
    print(f"Chart Theme: {settings.CHART_THEME}")
    print(f"Upload Directory: {settings.UPLOAD_DIR}")
    print(f"Export Directory: {settings.EXPORT_DIR}")
    print("="*50 + "\n")