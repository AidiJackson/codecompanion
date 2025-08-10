# CodeCompanion Orchestra - Multi-Agent AI Development System

## Overview

CodeCompanion Orchestra is an advanced multi-agent AI development system featuring intelligent orchestration between specialized AI agents powered by Claude, GPT-4, and Gemini. The system provides a comprehensive project initiation interface where users describe their project requirements and watch as AI agents collaborate in real-time to deliver complete software solutions. The core orchestration engine analyzes project complexity, assigns optimal AI models to each agent specialty, and coordinates intelligent handoffs between agents with live status monitoring and visual collaboration feeds.

**RECENT MAJOR UPDATE (August 2025):** Comprehensive crash prevention and stability measures have been implemented to ensure production-level resilience and user-friendly error handling. The system now includes robust error boundaries, automatic session recovery, memory management, API safety measures, and emergency controls.

**LATEST UPDATE (August 10, 2025):** Fixed critical agent orchestration flow to ensure proper sequential execution after dependencies complete. Added manual control buttons for orchestra management and resolved function naming conflicts that were causing application crashes.

**COMPREHENSIVE SCHEMA SYSTEM (August 10, 2025):** Built complete JSON Schema-based multi-agent system with artifact-driven communication, event-sourced orchestration, and data-driven model routing. Implemented structured schemas for artifacts, ledgers, routing decisions, and agent I/O contracts with full Pydantic validation.

**REAL-TIME EVENT STREAMING INTEGRATION (August 10, 2025):** Enhanced system with production-grade Redis Streams event-sourced orchestration. Added FastAPI backend with WebSocket endpoints, real-time artifact creation/validation, event replay capability, and live collaboration feeds. System now supports both mock mode (without Redis) and full production mode with persistent event streaming.

**REAL MULTI-AGENT EXECUTION IMPLEMENTATION (August 10, 2025):** Implemented actual AI agent collaboration with real API calls to Claude, GPT-4, and Gemini. Added comprehensive AI client system with structured prompts, real-time agent execution workflow, and live monitoring interface displaying actual agent results. Users can now launch real AI projects where agents collaborate through actual API calls and produce real artifacts.

**INTELLIGENT MODEL ROUTER WITH LEARNING (August 10, 2025):** Implemented advanced Thompson Sampling bandit learning system for adaptive model selection. Added comprehensive cost governance, performance tracking with trend analysis, and outcome-based learning optimization. The system now learns from task outcomes and continuously improves routing decisions using Bayesian learning algorithms.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Streamlit Web Application**: Single-page application serving as the main user interface
- **Session State Management**: Streamlit session state handles agent instances, project memory, chat history, and current project context
- **Real-time Interface**: Interactive chat interface with agent status monitoring and file download capabilities

### Agent Architecture
- **Base Agent Pattern**: Abstract base class defining common agent behaviors and OpenAI API integration
- **Specialized Agent Classes**: Five distinct agents each with specific roles and capabilities
  - ProjectManagerAgent: Central orchestrator for project planning and coordination (Claude Sonnet)
  - CodeGeneratorAgent: Backend development and algorithm implementation (GPT-4)
  - UIDesignerAgent: Frontend development and user experience design (Gemini Flash)
  - TestWriterAgent: Test case generation and quality assurance (GPT-4)
  - DebuggerAgent: Code analysis, bug detection, and optimization (Claude Sonnet)
- **Agent Communication**: Message-based system with handoff mechanisms between agents
- **Context Awareness**: Agents maintain conversation history and project context
- **Sequential Execution**: Fixed workflow orchestrator ensures proper agent handoffs after dependency completion
- **Manual Controls**: Added "Continue Orchestra", "Execute All Agents", and "Next Agent" buttons for manual progression

### Core System Components
- **Real-Time Event Bus (Redis Streams)**: Production-grade event streaming with consumer groups, automatic retries, and stream monitoring
- **Event-Sourced Orchestrator**: Immutable event stream managing workflow state with full auditability, replay capability, and time-travel debugging
- **FastAPI Backend**: WebSocket endpoints for real-time UI updates, REST APIs for artifact operations, agent registration, and health monitoring
- **Data-Driven Model Router**: Capability vector-based routing with multi-objective optimization (quality, cost, latency) and load balancing
- **Intelligent Model Router**: Thompson Sampling bandit learning system with adaptive model selection, cost governance, and performance tracking
- **Cost Governor**: Budget management system with project complexity-based limits, spending optimization, and cost violation detection
- **Performance Tracker**: Real-time outcome tracking with trend analysis, quality metrics, and optimization opportunity identification
- **Thompson Sampling Bandit**: Bayesian learning algorithm for balancing exploration vs exploitation in model selection
- **Artifact Handler**: Type-safe artifact validation, serialization, and dependency tracking with comprehensive quality scoring
- **Schema System**: Complete JSON Schema framework with Pydantic validation for artifacts, ledgers, routing decisions, and agent contracts
- **Stream Consumers**: Specialized consumers for orchestration, metrics collection, UI updates, and conflict detection
- **Live Orchestration Dashboard**: Real-time agent activity monitoring, collaboration feeds, progress tracking, and visual workflow management
- **Event Replay System**: Time-travel debugging with correlation-based filtering and chronological event reconstruction
- **Project Memory**: SQLite-based persistent storage for project context, agent interactions, and conversation history
- **Communication Protocol**: Structured message system with priority levels, correlation IDs, and response requirements
- **WebSocket Integration**: Real-time bidirectional communication between Streamlit frontend and FastAPI backend

### Stability and Safety Systems
- **Error Handler**: Comprehensive error handling with exponential backoff, circuit breakers, API timeouts, and user-friendly error messages
- **Session Manager**: Advanced session state management with validation, emergency reset, partial reset, and automatic cleanup
- **Stability Monitor**: Real-time health monitoring with system diagnostics, performance metrics, and automated recovery suggestions
- **Emergency Controls**: User-accessible safety controls including emergency stop, memory cleanup, and system reset functionality
- **Input Validation**: Security-focused input sanitization with length limits, content filtering, and injection prevention
- **Memory Management**: Automatic cleanup of conversation history, project files, and large objects to prevent memory issues

### Data Storage Solutions
- **SQLite Database**: Local storage for project memory, agent interactions, and conversation history
- **Session State**: In-memory storage for current project context and agent instances
- **File System**: Local file operations for generated code, project templates, and downloadable artifacts

### Code Generation and Templates
- **Template System**: Predefined project structures for web applications, API services, and data pipelines
- **Dynamic Code Generation**: Real-time code file creation based on user requests and project context
- **Multi-language Support**: Python, JavaScript, HTML/CSS code generation with framework-specific templates

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4o model integration for all agent reasoning and code generation
- **API Key Management**: Environment variable configuration for OpenAI authentication

### Python Libraries
- **Streamlit**: Web application framework for the user interface
- **OpenAI Python Client**: Official OpenAI API client for LLM interactions
- **SQLite3**: Built-in Python database for persistent storage
- **asyncio**: Asynchronous programming support for agent orchestration

### Development Tools
- **UUID Generation**: Unique identifier creation for agents, messages, and projects
- **JSON Handling**: Data serialization for agent communication and project persistence
- **File Operations**: Built-in Python file management with pathlib and os modules
- **Regular Expressions**: Pattern matching for code analysis and validation

### Optional Integrations
- **Email Validation**: Pattern-based email address validation
- **File Compression**: ZIP file creation for project downloads
- **Logging System**: Python logging for debugging and monitoring agent activities