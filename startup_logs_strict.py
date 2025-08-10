"""
Startup logging for strict configuration system
"""
import logging
from settings import settings
from bus import bus

logger = logging.getLogger(__name__)

def log_startup_configuration():
    """Print startup log with configuration status"""
    # Scrub credentials from DATABASE_URL
    db_url = settings.DATABASE_URL or "sqlite:///./data/codecompanion.db"
    if "://" in db_url and "@" in db_url:
        # Scrub credentials from URL like postgresql://user:pass@host:port/db
        parts = db_url.split("://")
        if len(parts) == 2:
            scheme = parts[0]
            rest = parts[1]
            if "@" in rest:
                credentials, host_db = rest.split("@", 1)
                db_url_safe = f"{scheme}://***:***@{host_db}"
            else:
                db_url_safe = db_url
        else:
            db_url_safe = db_url
    else:
        db_url_safe = db_url
    
    print(f"🚀 STRICT CONFIG STARTUP")
    print(f"EVENT_BUS = {settings.EVENT_BUS}")  
    print(f"DATABASE_URL = {db_url_safe}")
    print(f"STREAMLIT_DEBUG = {settings.STREAMLIT_DEBUG}")
    
    # Show bus type
    bus_type = "MockBus" if hasattr(bus, 'queues') else "RedisStreamsBus"
    print(f"Bus initialized: {bus_type}")

if __name__ == "__main__":
    log_startup_configuration()