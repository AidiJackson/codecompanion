# CodeCompanion Orchestra - Multi-Agent AI Development System

## Overview
CodeCompanion Orchestra is an advanced multi-agent AI development system that orchestrates specialized AI agents (Claude, GPT-4, Gemini) to deliver complete software solutions. It provides a project initiation interface where users define requirements, and AI agents collaborate in real-time to generate software. The system's core orchestration engine analyzes project complexity, assigns optimal AI models, and coordinates intelligent handoffs with live monitoring. It includes robust crash prevention, error handling, automatic session recovery, and comprehensive configuration management. The system supports real multi-agent execution, making actual API calls to generate authentic artifacts, and features an intelligent model router with learning capabilities for adaptive model selection and cost governance. It also provides a real-time collaboration system for live monitoring of agent activities and artifact creation.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes
- **August 11, 2025**: DATABASE SCHEMA IMPROVEMENTS: Fixed SQLite schema migrations in storage/runs.py to prevent crashes. Added robust column existence checking and graceful error handling for ALTER TABLE operations. Ensured artifacts table has proper run_id column with automatic migration. Database operations now never crash the endpoint.
- **August 11, 2025**: BACKEND ERROR HANDLING: Enhanced API endpoints with /health and /keys for monitoring. Added comprehensive try/catch wrapping in /run_real with readable error messages and stack traces. Hardened external API calls in services/real_models.py to return error strings instead of crashing. Improved UI error display with JSON details and status indicators.
- **August 11, 2025**: STABILITY IMPROVEMENTS: Disabled background worker threads during Streamlit startup to eliminate RuntimeError exceptions. Commented out log_consumer imports and asyncio.run calls that were causing event loop conflicts. Ensured only single API server runs on port 5050 via server_launcher.start_api_once() pattern. Development environment now starts cleanly with MockBus fallback when Redis unavailable.
- **August 10, 2025**: MAJOR CLEANUP: Removed all MockBus fallbacks and duplicate event bus factories. Eliminated EventBus class from core/event_streaming.py that had its own fallback logic. Updated all imports to use single bus singleton from bus.py. Refactored all test files to use bus singleton instead of direct MockBus instantiation. Status: Partial - some components still expect streaming-level methods that were removed.
- **August 10, 2025**: Added lightweight vector memory system with semantic search capabilities. Features OpenAI embeddings for high-quality similarity search, TF-IDF fallback when embeddings unavailable, and context handle system to store references instead of full text content.
- **August 10, 2025**: Enhanced FastAPI backend with health check and development testing endpoints: GET /health returns event bus and database status, POST /simulate_task creates mock tasks for development testing.
- **August 10, 2025**: Implemented strict configuration system with fail-fast validation and production Redis Streams bus. Created bus.py with RedisStreamsBus and MockBus classes, settings.py with strict validation, and constants.py with topic definitions. System fails immediately if misconfigured.

## System Architecture

### Frontend Architecture
- **Streamlit Web Application**: Single-page application serving as the main user interface.
- **Session State Management**: Handles agent instances, project memory, chat history, and context.
- **Real-time Interface**: Interactive chat with agent status monitoring and file download capabilities.

### Agent Architecture
- **Base Agent Pattern**: Abstract base class for common behaviors and API integration.
- **Specialized Agent Classes**: Five distinct agents (ProjectManager, CodeGenerator, UIDesigner, TestWriter, Debugger) with specific roles and AI model assignments (Claude Sonnet, GPT-4o, Gemini Flash).
- **Agent Communication**: Message-based system with handoff mechanisms.
- **Context Awareness**: Agents maintain conversation history and project context.
- **Sequential Execution**: Fixed workflow orchestrator ensures proper handoffs.
- **Manual Controls**: Buttons for manual progression of the orchestra.

### Core System Components
- **Enterprise Configuration System**: Pydantic BaseSettings-based configuration with fail-fast validation, centralized settings, and comprehensive startup logging.
- **Production Redis Streams Bus**: Enterprise-grade event bus abstraction with RedisStreamsBus for production and MockBus for development, featuring consumer groups, async processing, and error handling.
- **Event-Sourced Orchestrator v2**: Manages workflows, multi-agent coordination, task assignment, artifact publishing, and progress tracking with audit trails using the production bus.
- **FastAPI Backend**: Provides WebSocket endpoints for real-time UI updates and REST APIs for artifact operations and health monitoring.
- **Data-Driven Model Router**: Capability vector-based routing with multi-objective optimization (quality, cost, latency) and Thompson Sampling for adaptive model selection. Includes cost governance and performance tracking.
- **Artifact Handler**: Type-safe artifact validation, serialization, and dependency tracking with quality scoring.
- **Schema System**: JSON Schema framework with Pydantic validation for artifacts, ledgers, routing decisions, and agent contracts.
- **Live Orchestration Dashboard**: Real-time agent activity monitoring, collaboration feeds, progress tracking, and visual workflow management.
- **Event Replay System**: Time-travel debugging with correlation-based filtering.
- **LiveCollaborationEngine**: Real-time collaboration tracking and UI updates.
- **LiveProgressTracker**: System health monitoring and workflow status management.
- **ParallelExecutionEngine**: Concurrent agent execution with dependency management.
- **Project Memory**: SQLite-based persistent storage for project context and interactions.
- **Communication Protocol**: Structured message system with priority levels and correlation IDs.
- **WebSocket Integration**: Real-time bidirectional communication between frontend and backend.

### Stability and Safety Systems
- **Error Handler**: Comprehensive error handling with exponential backoff, circuit breakers, and API timeouts.
- **Session Manager**: Advanced session state management with validation, reset, and automatic cleanup.
- **Stability Monitor**: Real-time health monitoring and automated recovery suggestions.
- **Emergency Controls**: User-accessible safety controls (stop, memory cleanup, system reset).
- **Input Validation**: Security-focused input sanitization.
- **Memory Management**: Automatic cleanup of conversation history and objects.

### Data Storage Solutions
- **SQLite Database Infrastructure**: Comprehensive persistence layer for artifacts, timeline events, project sessions, agent performance, bandit learning data, quality metrics, and router performance. Includes DatabaseManager for CRUD operations.
- **Vector Memory System**: Lightweight local vector storage with semantic search capabilities using OpenAI embeddings (with TF-IDF fallback). Stores context handles instead of raw text to prevent memory bloat, enabling intelligent retrieval of agent interactions and artifacts.
- **Session State**: In-memory storage for current project context.
- **File System**: Local file operations for generated code and downloadable artifacts.
- **Database Dashboard**: Interactive interface for status monitoring, testing, and analytics.

### Code Generation and Templates
- **Template System**: Predefined project structures (web applications, API services, data pipelines).
- **Dynamic Code Generation**: Real-time code file creation.
- **Multi-language Support**: Python, JavaScript, HTML/CSS code generation.

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4o model integration.
- **Claude API**: For ProjectManager and Debugger agents.
- **Gemini API**: For UIDesigner agent.

### Python Libraries
- **Streamlit**: Web application framework.
- **OpenAI Python Client**: For LLM interactions.
- **SQLite3**: Built-in Python database.
- **asyncio**: Asynchronous programming support.
- **Pydantic**: For configuration and schema validation.
- **redis-py**: For Redis Streams integration.
- **FastAPI**: For backend API and WebSockets.

### Development Tools
- **UUID Generation**: For unique identifiers.
- **JSON Handling**: For data serialization.
- **File Operations**: Python's `pathlib` and `os` modules.
- **Regular Expressions**: For pattern matching.