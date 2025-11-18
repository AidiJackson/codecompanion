"""
Orchestrator - Manages the execution of various agents and tools.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from .file_orchestrator import FileOrchestrator


class Orchestrator:
    """Orchestrates the execution of agents and manages state."""

    def __init__(self, project_path: str = "."):
        """
        Initialize the Orchestrator.

        Args:
            project_path: Root path of the project
        """
        self.project_path = Path(project_path)
        self.state_dir = self.project_path / ".cc"
        self.state_file = self.state_dir / "state.json"

        # Ensure .cc directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict:
        """Load state from .cc/state.json."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {}

    def save_state(self, state: Dict) -> None:
        """Save state to .cc/state.json."""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def run_file_orchestrator(self) -> Dict:
        """
        Run the File Orchestrator to collect all agent outputs.

        Returns:
            Dictionary with status, output_dir, generated, and missing files
        """
        # Load current state
        state = self.load_state()

        # Run the file orchestrator
        file_orch = FileOrchestrator(self.project_path)
        result = file_orch.collect_all()

        # Update state with timestamp
        timestamp = datetime.now().isoformat()
        state["last_file_orchestrator_run"] = timestamp

        # Save updated state
        self.save_state(state)

        return result
