"""
Centralized startup logging for system initialization.

This module provides comprehensive startup logging that displays:
- Event bus configuration and Redis connectivity status
- Database URL with scrubbed credentials
- Available AI model API keys
- System configuration summary
"""

import logging
from settings import settings

logger = logging.getLogger(__name__)


def log_system_startup():
    """
    Log comprehensive system startup information.

    This function should be called early in application initialization
    to provide visibility into system configuration and connectivity.
    """
    try:
        # Get Redis connectivity status
        redis_connected = False
        if settings.EVENT_BUS == "redis":
            try:
                import redis

                client = redis.from_url(settings.get_redis_url(), decode_responses=True)
                client.ping()
                redis_connected = True
            except:
                redis_connected = False

        # Get available models
        models = settings.get_available_models()

        # Create startup summary
        logger.info("=" * 60)
        logger.info("🚀 MULTI-AGENT AI SYSTEM STARTUP")
        logger.info("=" * 60)
        logger.info(f"event_bus = {settings.EVENT_BUS}")
        logger.info(f"redis_connected = {redis_connected}")
        logger.info(f"database_url = {settings.scrub_url(settings.get_database_url())}")
        logger.info(
            f"models_detected = claude:{models['claude']}, gpt-4:{models['gpt-4']}, gemini:{models['gemini']}"
        )
        logger.info(f"streamlit_debug = {settings.STREAMLIT_DEBUG}")
        logger.info(f"host:port = {settings.HOST}:{settings.PORT}")
        logger.info("=" * 60)

        # Log warnings for missing configurations
        if settings.EVENT_BUS == "redis" and not redis_connected:
            logger.warning("⚠️  Redis event bus configured but connection failed")

        if not any(models.values()):
            logger.warning(
                "⚠️  No AI model API keys detected - system will have limited functionality"
            )

        logger.info("✅ System startup logging complete")

    except Exception as e:
        logger.error(f"❌ Error during startup logging: {e}")


def validate_critical_config():
    """
    Validate critical configuration and fail fast if issues detected.

    Raises:
        RuntimeError: If critical configuration is invalid
    """
    errors = []

    # Validate event bus configuration
    if settings.EVENT_BUS not in ["redis", "mock"]:
        errors.append(f"Invalid EVENT_BUS: {settings.EVENT_BUS}")

    # Validate Redis configuration if selected
    if settings.EVENT_BUS == "redis" and not settings.REDIS_URL:
        try:
            import redis

            # Test default Redis connection
            client = redis.from_url("redis://localhost:6379", decode_responses=True)
            client.ping()
        except Exception:
            errors.append(
                "Redis event bus selected but no REDIS_URL provided and localhost:6379 unreachable"
            )

    # Check for at least one AI model
    models = settings.get_available_models()
    if not any(models.values()):
        logger.warning("No AI model API keys configured - system will run in demo mode")

    # Fail fast on critical errors
    if errors:
        error_msg = "Critical configuration errors:\n" + "\n".join(
            f"- {error}" for error in errors
        )
        logger.error(f"❌ {error_msg}")
        raise RuntimeError(error_msg)

    logger.info("✅ Critical configuration validation passed")


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO)

    # Test startup logging
    log_system_startup()
    validate_critical_config()
