"""
Comprehensive JSON Schema system for multi-agent AI development.

This module provides structured artifact types, ledger systems, and model capability definitions
for coordinating multi-agent workflows with type safety and validation.
"""

from .artifacts import *
# from .ledgers import *  # Commented out due to import issues
from .routing import *

__version__ = "1.0.0"
__all__ = [
    # Artifacts
    "SpecDoc", "DesignDoc", "CodePatch", "TestPlan", "EvalReport", "Runbook",
    "ArtifactBase", "ArtifactType",
    
    # Ledgers  
    "TaskLedger", "ProgressLedger", "MemoryIndex",
    "TaskStatus", "WorkItem", "ContextHandle",
    
    # Routing
    "ModelCapability", "TaskComplexity", "RoutingDecision",
    "ModelType", "CapabilityVector"
]