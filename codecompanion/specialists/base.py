from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class SpecialistResult:
    """
    Structured result from a Specialist Agent.

    For now this is focused on producing:
      - A natural-language description
      - One or more prompts or steps the user can apply
      - Optional notes (e.g., risks, assumptions)

    In the future this may include:
      - Direct patch suggestions
      - File-level instructions
      - Links to quality reports
    """
    description: str
    prompts: List[str]
    notes: List[str]


class BaseSpecialist:
    """
    Base interface for all Specialist Agents.

    Each specialist receives:
      - task: a short human-readable task description
      - context: an optional dict of extra metadata

    It returns a SpecialistResult describing:
      - what should be done
      - suggested prompts/steps
      - any important notes or caveats
    """

    def run_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> SpecialistResult:
        raise NotImplementedError()
