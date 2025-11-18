"""
Architect Agent - Generates architecture documentation and phase outlines.
"""
from typing import Dict, List, Any


class Architect:
    """
    Architect agent responsible for generating architecture documentation
    and phase outlines based on project plans.
    """

    def __init__(self, settings: Dict[str, Any] = None):
        """
        Initialize the Architect agent.

        Args:
            settings: Optional configuration settings for the architect
        """
        self.settings = settings or {}

    def generate_architecture_overview(self, merged_plan: Dict[str, Any]) -> str:
        """
        Generate ARCHITECTURE.md content based on the merged plan.

        Args:
            merged_plan: Dictionary containing phases and notes for the project

        Returns:
            Formatted markdown content for ARCHITECTURE.md
        """
        phases = merged_plan.get("phases", [])
        notes = merged_plan.get("notes", [])

        content = "# Architecture Overview\n\n"
        content += "## Project Structure\n\n"
        content += "This document provides a high-level overview of the project architecture.\n\n"

        content += "## Planned Phases\n\n"
        if phases:
            for i, phase in enumerate(phases, 1):
                content += f"{i}. {phase}\n"
        else:
            content += "No phases defined yet.\n"

        content += "\n## Architecture Notes\n\n"
        if notes:
            for note in notes:
                content += f"- {note}\n"
        else:
            content += "No additional notes.\n"

        content += "\n## Components\n\n"
        content += "### Core Components\n\n"
        content += "- **Orchestrator**: Manages agent workflow and state\n"
        content += "- **Architect**: Generates architecture documentation\n"
        content += "- **CLI**: Command-line interface for CodeCompanion\n\n"

        content += "### Data Flow\n\n"
        content += "1. User initiates command via CLI\n"
        content += "2. Orchestrator loads current state\n"
        content += "3. Architect generates documentation\n"
        content += "4. State is updated and persisted\n"
        content += "5. Results returned to user\n\n"

        return content

    def generate_phases_outline(self, merged_plan: Dict[str, Any]) -> str:
        """
        Generate PHASES.md content based on the merged plan.

        Args:
            merged_plan: Dictionary containing phases and notes for the project

        Returns:
            Formatted markdown content for PHASES.md
        """
        phases = merged_plan.get("phases", [])
        notes = merged_plan.get("notes", [])

        content = "# Project Phases\n\n"
        content += "This document outlines the project implementation phases.\n\n"

        if phases:
            for i, phase in enumerate(phases, 1):
                content += f"## Phase {i}: {phase}\n\n"
                content += f"### Objectives\n\n"
                content += f"- Complete {phase.lower()} activities\n"
                content += f"- Ensure quality and test coverage\n"
                content += f"- Document progress and learnings\n\n"

                content += f"### Tasks\n\n"
                content += f"- [ ] Define scope for {phase}\n"
                content += f"- [ ] Implement required functionality\n"
                content += f"- [ ] Write tests\n"
                content += f"- [ ] Update documentation\n\n"

                content += f"### Success Criteria\n\n"
                content += f"- All tasks completed\n"
                content += f"- Tests passing\n"
                content += f"- Documentation up to date\n\n"
        else:
            content += "No phases defined yet.\n\n"

        if notes:
            content += "## Additional Notes\n\n"
            for note in notes:
                content += f"- {note}\n"

        return content
