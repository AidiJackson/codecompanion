from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import json
from codecompanion.architect.architect_agent import ArchitectAgent


class OrchestratorState:
    """
    Simple state management for the Orchestrator.
    Tracks the architecture version and other metadata.
    """

    def __init__(self) -> None:
        self.architecture_version: int = 0
        self.state_file = Path(".codecompanion_state.json")

    def load(self) -> None:
        """Load state from disk if it exists."""
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            self.architecture_version = data.get("architecture_version", 0)

    def save(self) -> None:
        """Save state to disk."""
        data = {
            "architecture_version": self.architecture_version,
        }
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


class Orchestrator:
    """
    Main orchestrator for CodeCompanion's multi-model dev OS.

    Coordinates between different agents and manages the overall workflow.
    """

    def __init__(self) -> None:
        # Initialize state
        self.state = OrchestratorState()
        self.state.load()

        # Initialize architect agent
        self.architect = ArchitectAgent()

    def save_state(self) -> None:
        """Save orchestrator state to disk."""
        self.state.save()

    def run_architect(self, merged_plan: Dict[str, Any] | None = None) -> None:
        """
        Run the Architect Agent to generate docs/ARCHITECTURE.md and ops/PHASES.md.

        For now, a merged_plan must be passed explicitly.
        In a later phase, this will automatically use the latest Planner Council output.

        Steps:
        1. Use ArchitectAgent to build and write documents.
        2. Increment architecture_version.
        3. save_state().
        """
        if merged_plan is None:
            raise NotImplementedError(
                "run_architect() requires a merged_plan for now; "
                "future versions will auto-fetch from Planner Council."
            )

        self.architect.write_documents(merged_plan)
        self.state.architecture_version += 1
        self.save_state()
