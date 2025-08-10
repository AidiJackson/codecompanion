# CodeCompanion Orchestra - Multi-Agent AI Development System

## Overview

CodeCompanion Orchestra is an advanced multi-agent AI development system featuring intelligent orchestration between specialized AI agents powered by Claude, GPT-4, and Gemini. The system provides a comprehensive project initiation interface where users describe their project requirements and watch as AI agents collaborate in real-time to deliver complete software solutions. The core orchestration engine analyzes project complexity, assigns optimal AI models to each agent specialty, and coordinates intelligent handoffs between agents with live status monitoring and visual collaboration feeds.

**RECENT MAJOR UPDATE (August 2025):** Comprehensive crash prevention and stability measures have been implemented to ensure production-level resilience and user-friendly error handling. The system now includes robust error boundaries, automatic session recovery, memory management, API safety measures, and emergency controls.

**LATEST UPDATE (August 10, 2025):** Fixed critical agent orchestration flow to ensure proper sequential execution after dependencies complete. Added manual control buttons for orchestra management and resolved function naming conflicts that were causing application crashes.

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
- **Workflow Orchestrator**: Advanced orchestration engine analyzing project requirements, determining agent assignments, coordinating intelligent handoffs, and providing real-time collaboration monitoring
- **Project Initiation Panel**: Comprehensive interface for project description, type selection, complexity levels, and agent preview with estimated completion times
- **Live Orchestration Dashboard**: Real-time agent activity monitoring, collaboration feeds, progress tracking, and visual workflow management
- **Agent Orchestrator**: Central coordination system managing multi-agent workflows with task assignment and dependency tracking
- **Project Memory**: SQLite-based persistent storage for project context, agent interactions, and conversation history
- **Communication Protocol**: Structured message system with priority levels, correlation IDs, and response requirements
- **File Management**: Comprehensive file operations including project structure creation, code generation, and file packaging

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