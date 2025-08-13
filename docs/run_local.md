# CodeCompanion Web Applications - Local Setup Guide

This guide provides comprehensive instructions for setting up and running the CodeCompanion web applications locally.

## Overview

CodeCompanion includes two main web applications:

1. **Streamlit App** (`app.py`) - Interactive web interface for the multi-agent AI system
2. **FastAPI Server** (`api.py` via `server.py`) - RESTful API backend with authentication

## Prerequisites

- Python 3.9 or higher
- pip or uv package manager
- Git (for version control)

## Quick Start

### 1. Install Dependencies

All required dependencies are available in the current environment. Key packages include:

```bash
# Core web framework dependencies (already installed)
streamlit>=1.0.0
fastapi>=0.68.0
uvicorn>=0.15.0
httpx>=0.27.0
pydantic-settings>=2.0.0
pandas>=1.3.0
```

### 2. Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required for API authentication
export CODECOMPANION_TOKEN="your-secure-token-here"

# AI API Keys (at least one required for full functionality)
export ANTHROPIC_API_KEY="your-claude-api-key"
export OPENAI_API_KEY="your-openai-api-key" 
export GEMINI_API_KEY="your-gemini-api-key"

# Optional: Database configuration
export DATABASE_URL="sqlite:///./data/codecompanion.db"

# Optional: Feature flags
export USE_REAL_API="true"
export STREAMLIT_DEBUG="false"
export LOG_LEVEL="INFO"
```

### 3. Database Setup

The system will automatically create and initialize the SQLite database on first run:

```bash
python -c "from database.setup import initialize_database; initialize_database()"
```

## Running the Applications

### Option 1: Integrated Mode (Recommended)

The Streamlit app automatically starts the FastAPI backend:

```bash
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

Access the application at: `http://localhost:8501`

The FastAPI server will be available at: `http://localhost:5050`

### Option 2: Separate Processes

Start each service independently:

**Terminal 1 - FastAPI Server:**
```bash
python server.py
# Or alternatively:
uvicorn api:app --host 0.0.0.0 --port 5050
```

**Terminal 2 - Streamlit App:**
```bash
# Disable embedded API mode
export CC_EMBED_API="false"
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

### Option 3: Replit Environment

For Replit-specific deployments:

```bash
# Use the Replit-optimized startup
python -c "from codecompanion.bootstrap import main; main()"
```

### Option 4: Docker (if available)

```bash
# Build and run (if Dockerfile exists)
docker build -t codecompanion .
docker run -p 8501:8501 -p 5050:5050 codecompanion
```

## API Endpoints

### Public Endpoints

- `GET /` - Welcome page with API information
- `GET /health` - Health check (returns system status)

### Protected Endpoints (require authentication)

- `GET /keys` - Check available AI API keys
- `POST /run_real` - Execute AI pipeline with real models

### Authentication

All protected endpoints require either:

**Bearer Token:**
```bash
curl -H "Authorization: Bearer $CODECOMPANION_TOKEN" http://localhost:5050/keys
```

**API Key Header:**
```bash
curl -H "X-API-Key: $CODECOMPANION_TOKEN" http://localhost:5050/keys
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CODECOMPANION_TOKEN` | (required) | API authentication token |
| `ANTHROPIC_API_KEY` | None | Claude API key |
| `OPENAI_API_KEY` | None | OpenAI GPT-4 API key |
| `GEMINI_API_KEY` | None | Google Gemini API key |
| `DATABASE_URL` | `sqlite:///./data/codecompanion.db` | Database connection string |
| `USE_REAL_API` | `true` | Enable real AI API calls |
| `SIMULATION_MODE` | `false` | Force simulation mode |
| `EVENT_BUS` | `redis` | Event bus type (redis/mock) |
| `STREAMLIT_DEBUG` | `false` | Enable Streamlit debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CC_EMBED_API` | `true` | Embed API server in Streamlit |

### Performance Settings

The system includes performance optimizations:

- **Import times**: ~0.6s total for all core modules
- **API response times**: ~6ms average for health checks
- **Startup time**: ~3-5s for complete system initialization

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Check what's using port 5050
lsof -i :5050
# Kill the process if needed
kill -9 <PID>
```

**2. Missing Dependencies**
```bash
# Install missing packages
pip install streamlit fastapi uvicorn httpx pydantic-settings pandas
```

**3. Database Connection Issues**
```bash
# Ensure data directory exists
mkdir -p data
# Reset database if corrupted
rm -f data/codecompanion.db
python -c "from database.setup import initialize_database; initialize_database()"
```

**4. Redis Connection Failures**
```
Redis connection failed, falling back to MockBus
```
This is expected if Redis is not configured and the system will use a mock event bus.

**5. API Authentication Errors**
```json
{"detail": "Server missing CODECOMPANION_TOKEN"}
```
Set the `CODECOMPANION_TOKEN` environment variable.

**6. AI API Key Issues**
```
No AI models available
```
Configure at least one AI API key (ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY).

### Validation Commands

**Test API Server:**
```bash
curl http://localhost:5050/health
```

**Test Streamlit App:**
```bash
curl http://localhost:8501
```

**Test Authentication:**
```bash
curl -H "Authorization: Bearer $CODECOMPANION_TOKEN" http://localhost:5050/keys
```

**Check Configuration:**
```bash
python -c "from settings import settings; print(settings.get_available_models())"
```

## Development Mode

For development with auto-reload:

**FastAPI:**
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 5050
```

**Streamlit:**
```bash
streamlit run app.py --server.runOnSave=true
```

## Security Considerations

1. **Token Security**: Use a strong, randomly generated `CODECOMPANION_TOKEN`
2. **API Keys**: Store AI API keys securely and rotate regularly
3. **CORS**: The API allows all origins for CLI compatibility
4. **HTTPS**: Use a reverse proxy for HTTPS in production
5. **Database**: Consider PostgreSQL for production deployments

## Performance Monitoring

The system includes built-in performance tracking:

- Request latency monitoring
- Model response times
- System resource usage
- Error rate tracking

Access monitoring via the Streamlit interface quality dashboard.

## Support

For issues or questions:

1. Check this documentation
2. Review application logs
3. Test individual components using the validation commands
4. Check the project repository for updates

---

*Generated by CodeCompanion WebDoctor*