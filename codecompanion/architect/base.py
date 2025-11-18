from __future__ import annotations
from typing import Dict, Any


class BaseArchitect:
    """
    Base interface for all Architect implementations.
    The Architect receives a merged_plan dict and produces:
      - architecture_overview: str
      - phases_outline: str
    """

    def generate_architecture_overview(self, merged_plan: Dict[str, Any]) -> str:
        """
        Generate an architecture overview document from the merged plan.

        Args:
            merged_plan: Dictionary containing the merged plan from Planner Council

        Returns:
            str: Architecture overview in markdown format

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError()

    def generate_phases_outline(self, merged_plan: Dict[str, Any]) -> str:
        """
        Generate a phases outline document from the merged plan.

        Args:
            merged_plan: Dictionary containing the merged plan from Planner Council

        Returns:
            str: Phases outline in markdown format

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError()
