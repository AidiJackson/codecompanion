"""
Orchestrator - Manages CodeCompanion agents and workflow state.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

from .architect import Architect


class Orchestrator:
    """
    Orchestrator manages the execution of CodeCompanion agents and maintains
    workflow state across runs.
    """

    def __init__(self, project_root: str = "."):
        """
        Initialize the Orchestrator.

        Args:
            project_root: Root directory of the project (default: current directory)
        """
        self.project_root = Path(project_root).resolve()
        self.cc_dir = self.project_root / ".cc"
        self.state_file = self.cc_dir / "state.json"

        # Initialize agents
        self.settings = self._load_settings()
        self.architect = Architect(self.settings)

    def _load_settings(self) -> Dict[str, Any]:
        """
        Load settings from .cc directory.

        Returns:
            Dictionary containing settings
        """
        # For now, return empty settings
        # In the future, this could load from .cc/settings.json
        return {}

    def _load_state(self) -> Dict[str, Any]:
        """
        Load current workflow state from state file.

        Returns:
            Dictionary containing current state
        """
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Initialize default state
            return {
                "architecture_version": 0,
                "last_agent": None,
                "last_run": None,
            }

    def _save_state(self, state: Dict[str, Any]) -> None:
        """
        Save workflow state to state file.

        Args:
            state: State dictionary to save
        """
        # Ensure .cc directory exists
        self.cc_dir.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def run_architect(self) -> Dict[str, Any]:
        """
        Execute the Architect agent to generate architecture documentation.

        This method:
        1. Loads current state
        2. Loads settings
        3. Creates a merged plan (stub for now)
        4. Generates ARCHITECTURE.md and PHASES.md
        5. Updates and saves state
        6. Returns execution results

        Returns:
            Dictionary with:
                - architecture_file: Path to ARCHITECTURE.md
                - phases_file: Path to PHASES.md
                - version: Updated architecture version number
        """
        # Load current state
        state = self._load_state()

        # Create a simple stub merged_plan
        merged_plan = {
            "phases": ["Setup", "Core Implementation", "Testing"],
            "notes": []
        }

        # Generate architecture and phases content
        content_arch = self.architect.generate_architecture_overview(merged_plan)
        content_phases = self.architect.generate_phases_outline(merged_plan)

        # Ensure directories exist
        docs_dir = self.project_root / "docs"
        ops_dir = self.project_root / "ops"
        docs_dir.mkdir(parents=True, exist_ok=True)
        ops_dir.mkdir(parents=True, exist_ok=True)

        # Write files
        arch_file = docs_dir / "ARCHITECTURE.md"
        phases_file = ops_dir / "PHASES.md"

        with open(arch_file, "w", encoding="utf-8") as f:
            f.write(content_arch)

        with open(phases_file, "w", encoding="utf-8") as f:
            f.write(content_phases)

        # Increment architecture version
        state["architecture_version"] += 1
        state["last_agent"] = "architect"

        # Add timestamp
        from datetime import datetime
        state["last_run"] = datetime.now().isoformat()

        # Save updated state
        self._save_state(state)

        # Return results
        return {
            "architecture_file": str(arch_file.relative_to(self.project_root)),
            "phases_file": str(phases_file.relative_to(self.project_root)),
            "version": state["architecture_version"],
        }

    def get_state(self) -> Dict[str, Any]:
        """
        Get current workflow state.

        Returns:
            Dictionary containing current state
        """
        return self._load_state()
