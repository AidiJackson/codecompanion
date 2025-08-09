# CodeCompanion - Multi-Agent AI Development System

## Overview

CodeCompanion is a multi-agent AI development system that leverages specialized AI agents to collaborate on software development projects. The system consists of five specialized agents working together: Project Manager (orchestration and planning), Code Generator (backend development), UI Designer (frontend development), Test Writer (quality assurance), and Debugger (code analysis and bug fixing). Built with Streamlit for the user interface, the system provides an interactive platform where agents can hand off tasks to each other, maintain project memory, and generate complete software solutions through collaborative AI workflows.

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
  - ProjectManagerAgent: Central orchestrator for project planning and coordination
  - CodeGeneratorAgent: Backend development and algorithm implementation
  - UIDesignerAgent: Frontend development and user experience design
  - TestWriterAgent: Test case generation and quality assurance
  - DebuggerAgent: Code analysis, bug detection, and optimization
- **Agent Communication**: Message-based system with handoff mechanisms between agents
- **Context Awareness**: Agents maintain conversation history and project context

### Core System Components
- **Agent Orchestrator**: Central coordination system managing multi-agent workflows with task assignment and dependency tracking
- **Project Memory**: SQLite-based persistent storage for project context, agent interactions, and conversation history
- **Communication Protocol**: Structured message system with priority levels, correlation IDs, and response requirements
- **File Management**: Comprehensive file operations including project structure creation, code generation, and file packaging

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