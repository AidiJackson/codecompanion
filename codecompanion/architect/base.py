from __future__ import annotations
from typing import Dict, Any


class BaseArchitect:
    """
    Base interface for Architect implementations.
    The Architect transforms a merged_plan into:
      - An architecture overview (Markdown)
      - A phases outline (Markdown)
    """

    def generate_architecture_overview(self, merged_plan: Dict[str, Any]) -> str:
        raise NotImplementedError()

    def generate_phases_outline(self, merged_plan: Dict[str, Any]) -> str:
        raise NotImplementedError()
