"""
Base planner interface for CodeCompanion's multi-model planning system.
"""

from __future__ import annotations
from typing import Dict, List, Any


class BasePlanner:
    """
    Base interface for planner agents.

    Each planner receives a goal_spec string and returns a dict with:
      {
        "phases": List[str],
        "tasks": List[Dict[str, Any]],
        "risks": List[str],
        "notes": List[str]
      }

    All planners must return valid structures even if stubbed.
    """

    def plan(self, goal_spec: str) -> Dict[str, Any]:
        """
        Generate a plan based on the given goal specification.

        Args:
            goal_spec: Description of the goal or feature to plan

        Returns:
            Dict containing phases, tasks, risks, and notes

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Planner must implement plan().")
