from pydantic_settings import BaseSettings
from typing import Optional, Dict

class Settings(BaseSettings):
    # API keys
    OPENROUTER_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Bus
    EVENT_BUS: str = "mock"             # overridden by ENV/Secrets
    REDIS_URL: Optional[str] = None     # rediss://... from Upstash

    # DB & app
    DATABASE_URL: str = "sqlite:///./data/codecompanion.db"
    STREAMLIT_DEBUG: bool = True        # Enable debug mode for MockBus
    LOG_LEVEL: str = "INFO"

    # Helpers used elsewhere
    def scrub_url(self, url: Optional[str] = None) -> str:
        val = url or self.DATABASE_URL
        try:
            if "://" in val and "@" in val:
                scheme, rest = val.split("://", 1)
                after_at = rest.split("@", 1)[1]
                return f"{scheme}://***:***@{after_at}"
        except Exception:
            pass
        return val

    def get_database_url(self) -> str:
        return self.DATABASE_URL

    def get_available_models(self) -> Dict[str, bool]:
        return {
            "claude": bool(self.ANTHROPIC_API_KEY),
            "gpt4":   bool(self.OPENROUTER_API_KEY or self.OPENAI_API_KEY),
            "gemini": bool(self.GEMINI_API_KEY),
        }

settings = Settings()