from __future__ import annotations
from typing import Dict, Any, Optional
from .base import BaseSpecialist, SpecialistResult


class DocsSpecialist(BaseSpecialist):
    """
    Documentation Specialist Agent (skeleton).

    Focuses on documentation updates:
      - README files
      - API documentation
      - internal developer documentation (docs/*.md)
    """

    def run_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> SpecialistResult:
        description = (
            "Docs specialist stub. Prepares a Claude Code (web) prompt to update "
            "documentation according to the requested task."
        )
        prompt = (
            "You are Claude Code working on documentation for this project.\n\n"
            f"GOAL\n{task}\n\n"
            "CONTEXT\n"
            "- Only modify documentation files (e.g., README.md, docs/*.md, API docs).\n"
            "- Do NOT change runtime code unless absolutely necessary for doc examples.\n"
            "- Follow existing documentation style and structure.\n\n"
            "TASK\n"
            "- Update documentation as described in GOAL.\n"
            "- Ensure clarity, accuracy, and completeness.\n"
            "- Keep changes focused on documentation improvements.\n"
        )
        notes = [
            "This is a skeleton docs specialist; real implementations will inspect the repo and suggest concrete documentation files.",
        ]
        return SpecialistResult(description=description, prompts=[prompt], notes=notes)
