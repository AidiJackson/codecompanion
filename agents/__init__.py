"""
Multi-Agent AI Development System

This package contains specialized AI agents for collaborative software development:
- ProjectManagerAgent: Central orchestrator and project planning
- CodeGeneratorAgent: Backend and algorithm development
- UIDesignerAgent: Frontend and user experience design
- TestWriterAgent: Test case generation and quality assurance
- DebuggerAgent: Code analysis and bug fixing
"""

from .base_agent import BaseAgent
from .project_manager import ProjectManagerAgent
from .code_generator import CodeGeneratorAgent
from .ui_designer import UIDesignerAgent
from .test_writer import TestWriterAgent
from .debugger import DebuggerAgent

__all__ = [
    'BaseAgent',
    'ProjectManagerAgent',
    'CodeGeneratorAgent',
    'UIDesignerAgent',
    'TestWriterAgent',
    'DebuggerAgent'
]
