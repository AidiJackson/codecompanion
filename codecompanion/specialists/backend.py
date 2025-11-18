from __future__ import annotations
from typing import Dict, Any, Optional
from .base import BaseSpecialist, SpecialistResult


class BackendSpecialist(BaseSpecialist):
    """
    Backend Specialist Agent (skeleton).

    Focuses on server-side features:
      - API design and implementation
      - data models and persistence
      - integration with external services
    """

    def run_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> SpecialistResult:
        description = (
            "Backend specialist stub. Prepares a Claude Code (web) prompt to implement "
            "or modify backend logic according to the requested task."
        )
        prompt = (
            "You are Claude Code working on the backend of this project.\n\n"
            f"GOAL\n{task}\n\n"
            "CONTEXT\n"
            "- Only modify backend-related files (e.g., app/api, models, schemas).\n"
            "- Follow existing patterns and coding standards.\n\n"
            "TASK\n"
            "- Implement or update the backend feature described in GOAL.\n"
            "- Keep changes focused and well-documented.\n"
        )
        notes = [
            "This is a skeleton backend specialist; real implementations will inspect the repo and suggest concrete files.",
        ]
        return SpecialistResult(description=description, prompts=[prompt], notes=notes)
