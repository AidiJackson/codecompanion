from __future__ import annotations
from typing import Dict, Any, Optional
from .base import BaseSpecialist, SpecialistResult


class FrontendSpecialist(BaseSpecialist):
    """
    Frontend Specialist Agent (skeleton).

    Focuses on client-side features:
      - UI/UX design and implementation
      - component architecture
      - user interaction and state management
    """

    def run_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> SpecialistResult:
        description = (
            "Frontend specialist stub. Prepares a Claude Code (web) prompt to implement "
            "or modify frontend UI/UX according to the requested task."
        )
        prompt = (
            "You are Claude Code working on the frontend of this project.\n\n"
            f"GOAL\n{task}\n\n"
            "CONTEXT\n"
            "- Only modify frontend-related files (e.g., src/pages, src/components, UI assets).\n"
            "- Follow existing component patterns and design systems.\n"
            "- Ensure responsive and accessible UI.\n\n"
            "TASK\n"
            "- Implement or update the frontend feature described in GOAL.\n"
            "- Keep changes focused and well-documented.\n"
        )
        notes = [
            "This is a skeleton frontend specialist; real implementations will inspect the repo and suggest concrete files.",
        ]
        return SpecialistResult(description=description, prompts=[prompt], notes=notes)
