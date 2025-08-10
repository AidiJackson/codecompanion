from pydantic_settings import BaseSettings
from typing import Optional, Dict

class Settings(BaseSettings):
    OPENROUTER_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    EVENT_BUS: str = "mock"           # "redis" or "mock"
    REDIS_URL: Optional[str] = None

    DATABASE_URL: Optional[str] = "sqlite:///./data/codecompanion.db"
    STREAMLIT_DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_available_models(self) -> Dict[str, bool]:
        """Return availability of AI models based on API keys"""
        return {
            "claude": bool(self.ANTHROPIC_API_KEY),
            "gpt-4": bool(self.OPENROUTER_API_KEY),
            "gemini": bool(self.GEMINI_API_KEY)
        }

settings = Settings()