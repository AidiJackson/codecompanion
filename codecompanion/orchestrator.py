"""
Orchestrator - Multi-Agent Workflow Coordination

This module coordinates the execution of different agent roles,
using the model policy engine to select appropriate LLMs for each task.
"""

from typing import Optional
from .llm import complete
from .model_policy import TaskContext
from .settings import Settings, load_settings


# Role definitions for the agent workflow
AGENT_ROLES = {
    "Installer": None,  # No LLM needed - pure tooling
    "EnvDoctor": "recovery",  # Diagnostic and repair
    "Analyzer": "architect",  # Code analysis and architecture
    "DepAuditor": "specialist_backend",  # Dependency optimization
    "BugTriage": "quality",  # Bug identification and triage
    "Fixer": "specialist_backend",  # Code generation and patches
    "TestRunner": None,  # No LLM needed - pure execution
    "WebDoctor": "specialist_frontend",  # Web app configuration
    "PRPreparer": "specialist_docs",  # Documentation and commits
}


class Orchestrator:
    """
    Coordinates multi-agent workflows with policy-based model selection.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the orchestrator.

        Args:
            settings: Project settings (loaded from default location if None)
        """
        self.settings = settings or load_settings()

    def call_llm_for_agent(
        self,
        agent_name: str,
        system: str,
        messages: list,
        **kwargs
    ) -> dict:
        """
        Call LLM for a specific agent using policy-based model selection.

        Args:
            agent_name: Name of the agent (e.g., "Analyzer", "Fixer")
            system: System prompt
            messages: List of message dicts
            **kwargs: Additional LLM parameters

        Returns:
            Response dict with 'content' key
        """
        # Determine role for this agent
        role = AGENT_ROLES.get(agent_name, "generic")

        if role is None:
            raise ValueError(
                f"Agent '{agent_name}' does not use LLM. "
                "This agent should not call the LLM."
            )

        # Create task context
        task_context = TaskContext(
            role=role,
            purpose=f"Agent: {agent_name}",
            project_name=self.settings.project_name
        )

        # Call LLM with policy-based model selection
        return complete(
            system=system,
            messages=messages,
            task_context=task_context,
            mode=self.settings.model_policy_mode,
            **kwargs
        )

    def call_planner(self, system: str, messages: list, **kwargs) -> dict:
        """Call LLM with planner role."""
        task_context = TaskContext(role="planner", purpose="Planning")
        return complete(
            system=system,
            messages=messages,
            task_context=task_context,
            mode=self.settings.model_policy_mode,
            **kwargs
        )

    def call_architect(self, system: str, messages: list, **kwargs) -> dict:
        """Call LLM with architect role."""
        task_context = TaskContext(role="architect", purpose="Architecture design")
        return complete(
            system=system,
            messages=messages,
            task_context=task_context,
            mode=self.settings.model_policy_mode,
            **kwargs
        )

    def call_specialist(
        self,
        specialist_type: str,
        system: str,
        messages: list,
        **kwargs
    ) -> dict:
        """
        Call LLM with specialist role.

        Args:
            specialist_type: Type of specialist (frontend, backend, docs, test)
            system: System prompt
            messages: List of message dicts
            **kwargs: Additional LLM parameters

        Returns:
            Response dict
        """
        role = f"specialist_{specialist_type}"
        task_context = TaskContext(
            role=role,
            purpose=f"Specialist: {specialist_type}"
        )
        return complete(
            system=system,
            messages=messages,
            task_context=task_context,
            mode=self.settings.model_policy_mode,
            **kwargs
        )

    def call_quality(self, system: str, messages: list, **kwargs) -> dict:
        """Call LLM with quality role."""
        task_context = TaskContext(role="quality", purpose="Quality assurance")
        return complete(
            system=system,
            messages=messages,
            task_context=task_context,
            mode=self.settings.model_policy_mode,
            **kwargs
        )

    def call_recovery(self, system: str, messages: list, **kwargs) -> dict:
        """Call LLM with recovery role."""
        task_context = TaskContext(role="recovery", purpose="Error recovery")
        return complete(
            system=system,
            messages=messages,
            task_context=task_context,
            mode=self.settings.model_policy_mode,
            **kwargs
        )
