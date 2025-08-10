"""
Strict Configuration Management for Multi-Agent AI System

This module provides centralized configuration management using Pydantic BaseSettings
with fail-fast validation to eliminate ad-hoc environment variable handling.
"""

from pydantic_settings import BaseSettings
from pydantic import AnyUrl, validator
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Centralized application settings with strict validation.
    
    All environment variables are loaded and validated at startup,
    eliminating the need for ad-hoc env.get() calls throughout the codebase.
    """
    
    # API Keys for AI Models
    OPENROUTER_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Event Bus Configuration - Default to mock for development environment
    EVENT_BUS: str = "mock"  # allowed: "redis", "mock"
    REDIS_URL: Optional[AnyUrl] = None  # e.g., redis://localhost:6379 or rediss://:password@host:port

    # Database Configuration
    DATABASE_URL: Optional[str] = None  # if None, defaults to sqlite:///./data/codecompanion.db
    
    # Application Configuration
    STREAMLIT_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @validator('EVENT_BUS')
    def validate_event_bus(cls, v):
        """Validate event bus selection"""
        allowed = ['redis', 'mock']
        if v not in allowed:
            raise ValueError(f"EVENT_BUS must be one of {allowed}, got: {v}")
        return v
    
    @validator('REDIS_URL')
    def validate_redis_url(cls, v, values):
        """Validate Redis URL when redis event bus is selected"""
        if values.get('EVENT_BUS') == 'redis' and not v:
            logger.warning("Redis event bus selected but REDIS_URL not provided - will attempt localhost:6379")
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got: {v}")
        return v.upper()
    
    def get_database_url(self) -> str:
        """Get database URL with default fallback"""
        return self.DATABASE_URL or "sqlite:///./data/codecompanion.db"
    
    def get_redis_url(self) -> str:
        """Get Redis URL with default fallback"""
        if self.REDIS_URL:
            return str(self.REDIS_URL)
        return "redis://localhost:6379"
    
    def has_api_key(self, provider: str) -> bool:
        """Check if API key is available for given provider"""
        key_map = {
            'openrouter': self.OPENROUTER_API_KEY,
            'anthropic': self.ANTHROPIC_API_KEY,
            'openai': self.OPENAI_API_KEY,
            'gemini': self.GEMINI_API_KEY,
            'claude': self.ANTHROPIC_API_KEY,
            'gpt': self.OPENAI_API_KEY,
            'gpt-4': self.OPENAI_API_KEY
        }
        return bool(key_map.get(provider.lower()))
    
    def get_available_models(self) -> dict:
        """Get dictionary of available AI models based on API keys"""
        return {
            'claude': bool(self.ANTHROPIC_API_KEY),
            'gpt-4': bool(self.OPENAI_API_KEY),
            'gemini': bool(self.GEMINI_API_KEY),
            'openrouter': bool(self.OPENROUTER_API_KEY)
        }
    
    def scrub_url(self, url: str) -> str:
        """Scrub credentials from URL for safe logging"""
        if not url:
            return "None"
        
        # Remove password from URLs like redis://:password@host:port
        scrubbed = re.sub(r'://([^:]*):([^@]*)@', r'://\1:***@', url)
        return scrubbed
    
    def log_startup_config(self) -> None:
        """Log startup configuration for debugging"""
        models = self.get_available_models()
        
        logger.info("=== SYSTEM STARTUP CONFIGURATION ===")
        logger.info(f"event_bus = {self.EVENT_BUS}")
        logger.info(f"redis_url = {self.scrub_url(self.get_redis_url())}")
        logger.info(f"database_url = {self.scrub_url(self.get_database_url())}")
        logger.info(f"models_detected = claude:{models['claude']}, gpt-4:{models['gpt-4']}, gemini:{models['gemini']}")
        logger.info(f"streamlit_debug = {self.STREAMLIT_DEBUG}")
        logger.info(f"log_level = {self.LOG_LEVEL}")
        logger.info("=====================================")


# Global settings instance - import this throughout the application
settings = Settings()