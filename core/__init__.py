"""
Core orchestration system for multi-agent AI development.

Provides event-sourced orchestration, data-driven model routing, and structured
artifact handling for coordinated multi-agent workflows.
"""

from .orchestrator import *
from .router import *
from .artifacts import *

__version__ = "1.0.0"
__all__ = [
    # Orchestrator
    "EventSourcedOrchestrator", "WorkflowEvent", "EventType", "OrchestratorState",
    
    # Router
    "DataDrivenRouter", "RoutingContext", "ModelSelection",
    
    # Artifacts
    "ArtifactValidator", "ArtifactHandler", "ValidationResult"
]