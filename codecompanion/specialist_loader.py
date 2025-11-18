"""
Specialist Loader - Dynamically load specialist agents by type.
"""
from typing import Type
from .specialists.base import SpecialistBase
from .specialists.backend import BackendSpecialist
from .specialists.frontend import FrontendSpecialist
from .specialists.docs import DocsSpecialist
from .specialists.test import TestSpecialist


# Mapping of specialist type names to their classes
SPECIALIST_MAP = {
    "backend": BackendSpecialist,
    "frontend": FrontendSpecialist,
    "docs": DocsSpecialist,
    "test": TestSpecialist,
}


def load_specialist(type_name: str) -> SpecialistBase:
    """
    Load a specialist agent by type name.

    Args:
        type_name: The type of specialist to load
                   (backend, frontend, docs, test)

    Returns:
        An instance of the requested specialist

    Raises:
        ValueError: If the specialist type is unknown
    """
    type_name = type_name.lower()

    if type_name not in SPECIALIST_MAP:
        valid_types = ", ".join(SPECIALIST_MAP.keys())
        raise ValueError(
            f"Unknown specialist type: '{type_name}'. "
            f"Valid types are: {valid_types}"
        )

    specialist_class = SPECIALIST_MAP[type_name]
    return specialist_class()


def get_available_specialists() -> list[str]:
    """
    Get list of available specialist types.

    Returns:
        List of specialist type names
    """
    return list(SPECIALIST_MAP.keys())
