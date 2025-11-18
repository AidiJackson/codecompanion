from __future__ import annotations
from typing import Dict, Any, Optional
from .base import BaseSpecialist, SpecialistResult


class TestSpecialist(BaseSpecialist):
    """
    Test Specialist Agent (skeleton).

    Focuses on test coverage and quality:
      - generating or improving test cases
      - running pytest or relevant test commands
      - regression protection and edge case coverage
    """

    def run_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> SpecialistResult:
        description = (
            "Test specialist stub. Prepares a Claude Code (web) prompt to add or improve "
            "tests according to the requested task."
        )
        prompt = (
            "You are Claude Code working on tests for this project.\n\n"
            f"GOAL\n{task}\n\n"
            "CONTEXT\n"
            "- Only modify test-related files (e.g., tests/, test_*.py, *_test.py).\n"
            "- Follow existing test patterns and frameworks (pytest, unittest, etc.).\n"
            "- Ensure comprehensive coverage and regression protection.\n\n"
            "TASK\n"
            "- Implement or update tests as described in GOAL.\n"
            "- Run tests to verify they pass: pytest or similar.\n"
            "- Keep test code clean and maintainable.\n"
        )
        notes = [
            "This is a skeleton test specialist; real implementations will inspect the repo and suggest concrete test files.",
        ]
        return SpecialistResult(description=description, prompts=[prompt], notes=notes)
