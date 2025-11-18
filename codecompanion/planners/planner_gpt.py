"""
GPT-based planner implementation (stubbed for now).
"""

from __future__ import annotations
from typing import Dict, Any

from codecompanion.planners.base import BasePlanner


class GPTPlanner(BasePlanner):
    """
    GPT-based planner that will use OpenAI's GPT models for planning.

    Currently returns stubbed responses. Will be replaced with actual
    GPT API calls in a future implementation phase.
    """

    def plan(self, goal_spec: str) -> Dict[str, Any]:
        """
        Generate a plan using GPT (stubbed).

        Args:
            goal_spec: Description of the goal or feature to plan

        Returns:
            Dict containing phases, tasks, risks, and notes
        """
        # TODO: Replace with actual GPT API call
        return {
            "phases": [
                "requirements-analysis",
                "design",
                "implementation",
                "testing",
            ],
            "tasks": [
                {
                    "id": "gpt-task-1",
                    "description": "Analyze requirements and constraints",
                    "phase": "requirements-analysis",
                },
                {
                    "id": "gpt-task-2",
                    "description": "Design system architecture",
                    "phase": "design",
                },
                {
                    "id": "gpt-task-3",
                    "description": "Implement core functionality",
                    "phase": "implementation",
                },
            ],
            "risks": [
                "Scope creep during requirements phase",
                "Technical debt if architecture is not well-designed",
            ],
            "notes": [
                "GPT planner stub output",
                f"Planning for goal: {goal_spec[:50]}...",
            ],
        }
