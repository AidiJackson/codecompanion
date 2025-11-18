"""
Specialist Agents for CodeCompanion.

This module provides specialized agents for different aspects of software development:
- BackendSpecialist: Server-side features, APIs, data models
- FrontendSpecialist: UI/UX, components, client-side logic
- TestSpecialist: Test coverage, regression protection
- DocsSpecialist: Documentation updates and maintenance

Each specialist implements a common interface (BaseSpecialist) and returns
structured results (SpecialistResult) containing descriptions, prompts, and notes.
"""

from codecompanion.specialists.base import BaseSpecialist, SpecialistResult
from codecompanion.specialists.backend import BackendSpecialist
from codecompanion.specialists.frontend import FrontendSpecialist
from codecompanion.specialists.test import TestSpecialist
from codecompanion.specialists.docs import DocsSpecialist

__all__ = [
    "BaseSpecialist",
    "SpecialistResult",
    "BackendSpecialist",
    "FrontendSpecialist",
    "TestSpecialist",
    "DocsSpecialist",
]
