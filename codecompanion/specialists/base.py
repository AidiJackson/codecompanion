"""
Base class for all Specialist Agents.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class SpecialistBase(ABC):
    """
    Abstract base class for specialist agents.

    Each specialist agent handles a specific aspect of the project
    (backend, frontend, documentation, testing).
    """

    def __init__(self, specialist_type: str):
        """
        Initialize the specialist agent.

        Args:
            specialist_type: The type of specialist (backend, frontend, docs, test)
        """
        self.type = specialist_type

    @abstractmethod
    def generate_output(self) -> str:
        """
        Generate the specialist's output content.

        Each specialist must implement this method to produce
        their specific output/report.

        Returns:
            String content for the specialist's output file
        """
        pass

    def run(self, project_path: Path) -> Dict[str, Any]:
        """
        Execute the specialist agent.

        This method orchestrates the specialist's work:
        1. Generates output content
        2. Returns execution results

        Args:
            project_path: Path to the project root directory

        Returns:
            Dictionary containing:
                - result: Description of what was executed
                - details: Additional execution details (timestamp, etc.)
                - content: Generated output content
        """
        # Generate the specialist's output
        content = self.generate_output()

        # Create result dictionary
        result = {
            "result": f"{self.type} specialist executed",
            "details": {
                "timestamp": datetime.now().isoformat(),
                "specialist_type": self.type,
            },
            "content": content,
        }

        return result
