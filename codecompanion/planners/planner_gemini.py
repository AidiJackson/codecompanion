"""
Gemini-based planner implementation (stubbed for now).
"""

from __future__ import annotations
from typing import Dict, Any

from codecompanion.planners.base import BasePlanner


class GeminiPlanner(BasePlanner):
    """
    Gemini-based planner that will use Google's Gemini models for planning.

    Currently returns stubbed responses. Will be replaced with actual
    Gemini API calls in a future implementation phase.
    """

    def plan(self, goal_spec: str) -> Dict[str, Any]:
        """
        Generate a plan using Gemini (stubbed).

        Args:
            goal_spec: Description of the goal or feature to plan

        Returns:
            Dict containing phases, tasks, risks, and notes
        """
        # TODO: Replace with actual Gemini API call
        return {
            "phases": [
                "requirements-analysis",
                "prototyping",
                "implementation",
                "testing",
            ],
            "tasks": [
                {
                    "id": "gemini-task-1",
                    "description": "Analyze requirements and constraints",
                    "phase": "requirements-analysis",
                },
                {
                    "id": "gemini-task-2",
                    "description": "Create rapid prototype",
                    "phase": "prototyping",
                },
                {
                    "id": "gemini-task-3",
                    "description": "Implement core functionality",
                    "phase": "implementation",
                },
                {
                    "id": "gemini-task-4",
                    "description": "Perform integration testing",
                    "phase": "testing",
                },
            ],
            "risks": [
                "Insufficient prototyping may lead to rework",
                "Performance issues if not considered early",
            ],
            "notes": [
                "Gemini planner stub output",
                f"Planning for goal: {goal_spec[:50]}...",
                "Gemini emphasizes rapid prototyping approach",
            ],
        }
