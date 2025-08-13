"""
Multi-agent system with structured I/O contracts and specialized AI model agents.

Provides base agent architecture and specialized agents for different AI models
with standardized input/output contracts and artifact-based communication.
"""

# Base agent classes and types
from .base_agent import (
    BaseAgent,
    AgentInput,
    AgentOutput,
    AgentCapability,
    AgentType,
    ProcessingResult,
)

# Specialized agent implementations
from .claude_agent import ClaudeAgent
from .gpt4_agent import GPT4Agent
from .gemini_agent import GeminiAgent

__version__ = "1.0.0"
__all__ = [
    # Base agent
    "BaseAgent",
    "AgentInput",
    "AgentOutput",
    "AgentCapability",
    # Specialized agents
    "ClaudeAgent",
    "GPT4Agent",
    "GeminiAgent",
    # Agent types
    "AgentType",
    "ProcessingResult",
]
