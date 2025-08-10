"""
Multi-agent system with structured I/O contracts and specialized AI model agents.

Provides base agent architecture and specialized agents for different AI models
with standardized input/output contracts and artifact-based communication.
"""

from .base_agent import *
from .claude_agent import *
from .gpt4_agent import *
from .gemini_agent import *

__version__ = "1.0.0"
__all__ = [
    # Base agent
    "BaseAgent", "AgentInput", "AgentOutput", "AgentCapability",
    
    # Specialized agents
    "ClaudeAgent", "GPT4Agent", "GeminiAgent",
    
    # Agent types
    "AgentType", "ProcessingResult"
]