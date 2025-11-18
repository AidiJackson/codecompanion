"""
Orchestrator for Specialist Agents in CodeCompanion.

This module provides a simple orchestrator that dispatches tasks to
specialized agents (Backend, Frontend, Test, Docs) and coordinates
their work.
"""

from typing import Dict, Any, Optional

from codecompanion.specialists.base import SpecialistResult
from codecompanion.specialists.backend import BackendSpecialist
from codecompanion.specialists.frontend import FrontendSpecialist
from codecompanion.specialists.test import TestSpecialist
from codecompanion.specialists.docs import DocsSpecialist


class Orchestrator:
    """
    Orchestrator for managing and dispatching to Specialist Agents.

    The orchestrator maintains instances of all specialist agents and
    provides a unified interface for dispatching tasks to them.
    """

    def __init__(self):
        """Initialize orchestrator with all specialist agents."""
        self.backend_specialist = BackendSpecialist()
        self.frontend_specialist = FrontendSpecialist()
        self.test_specialist = TestSpecialist()
        self.docs_specialist = DocsSpecialist()

    def run_specialist(
        self, specialist_name: str, task: str, context: Optional[Dict[str, Any]] = None
    ) -> SpecialistResult:
        """
        Dispatch a task to a named Specialist Agent.

        Supported specialist_name values (for now):
          - 'backend'
          - 'frontend'
          - 'test'
          - 'docs'

        Returns a SpecialistResult describing proposed prompts or steps.

        NOTE:
        - This does not yet modify any files.
        - In the future, this may:
          • execute changes directly
          • run quality gates automatically
        """
        name = specialist_name.lower()
        if name == "backend":
            specialist = self.backend_specialist
        elif name == "frontend":
            specialist = self.frontend_specialist
        elif name == "test":
            specialist = self.test_specialist
        elif name == "docs":
            specialist = self.docs_specialist
        else:
            raise ValueError(f"Unknown specialist: {specialist_name!r}")

        result = specialist.run_task(task, context=context)
        # Future: integrate quality gate or logging here.
        return result
