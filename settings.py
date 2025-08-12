from pydantic_settings import BaseSettings
from typing import Optional, Dict

class Settings(BaseSettings):
    # API keys
    OPENAI_API_KEY: Optional[str] = None       # for GPT-4 direct API
    ANTHROPIC_API_KEY: Optional[str] = None    # Claude
    GEMINI_API_KEY: Optional[str] = None       # Gemini
    OPENROUTER_API_KEY: Optional[str] = None   # OpenRouter unified API

    # Feature flags
    USE_REAL_API: bool = True                  # Enable real API calls vs simulation
    USE_OPENROUTER: bool = False               # Use OpenRouter as primary API
    SIMULATION_MODE: bool = False              # Force simulation for testing
    
    # Bus (kept for later; not used in this path)
    EVENT_BUS: str = "mock"
    REDIS_URL: Optional[str] = None

    # App
    DATABASE_URL: str = "sqlite:///./data/codecompanion.db"
    STREAMLIT_DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

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
            "gpt4":   bool(self.OPENAI_API_KEY),
            "gemini": bool(self.GEMINI_API_KEY),
            "openrouter": bool(self.OPENROUTER_API_KEY),
        }
    
    def should_use_real_api(self) -> bool:
        """Determine if real API calls should be used based on feature flags"""
        if self.SIMULATION_MODE:
            return False
        return self.USE_REAL_API and any(self.get_available_models().values())

settings = Settings()