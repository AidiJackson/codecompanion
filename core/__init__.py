"""
Core system components for the multi-agent AI development system

This package contains the core orchestration, communication, and memory
management components that enable collaboration between AI agents.
"""

from .orchestrator import AgentOrchestrator
from .communication import AgentCommunication
from .memory import ProjectMemory

__all__ = [
    'AgentOrchestrator',
    'AgentCommunication', 
    'ProjectMemory'
]
