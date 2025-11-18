"""
Main Orchestrator for CodeCompanion's multi-model dev OS.

Coordinates high-level workflow including planner council and architect agent.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from codecompanion.architect.architect_agent import ArchitectAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator for CodeCompanion's multi-model development OS.

    Coordinates the workflow across:
    - Planner Council (future)
    - Architect Agent
    - Implementation Agents (future)
    - Review Agents (future)
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the Orchestrator.

        Args:
            project_root: Root directory of the project (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.state_file = self.project_root / ".codecompanion" / "orchestrator_state.json"

        # Initialize the Architect Agent
        self.architect = ArchitectAgent()

        # Initialize planner council (future implementation)
        self.planner_council = None  # Will be initialized when planner is implemented

        # Load or initialize state
        self.state = self._load_state()

        logger.info(f"Orchestrator initialized for project: {self.project_root}")

    def _load_state(self) -> Dict[str, Any]:
        """
        Load orchestrator state from disk.

        Returns:
            Dict[str, Any]: Current orchestrator state
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"Loaded orchestrator state from {self.state_file}")
                return state
            except Exception as e:
                logger.warning(f"Failed to load state file: {e}. Initializing new state.")

        # Initialize new state
        return {
            "architecture_version": 0,
            "phases_version": 0,
            "last_updated": None,
            "workflow_history": []
        }

    def save_state(self) -> None:
        """
        Save orchestrator state to disk.
        """
        # Ensure .codecompanion directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        self.state["last_updated"] = datetime.now().isoformat()

        # Write state to file
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

        logger.info(f"Saved orchestrator state to {self.state_file}")

    def run_architect(self, goal_spec: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Run the Architect Agent using the merged plan from Planner Council.

        This method will:
        1. Call self.planner_council.run(goal_spec) if needed (future implementation)
        2. Generate architecture + phases documents (currently stub implementation)
        3. Write docs/ARCHITECTURE.md and ops/PHASES.md
        4. Update project state: increment architecture_version
        5. save_state()

        Args:
            goal_spec: Optional goal specification for the planner council

        Returns:
            Dict[str, str]: Dictionary with 'architecture_md' and 'phases_md' keys

        Raises:
            NotImplementedError: This method is not fully implemented until the
                                planner council is integrated. The architect agent
                                infrastructure is in place but awaits planner integration.

        Example future implementation (commented):
            # Step 1: Get merged plan from Planner Council
            # if self.planner_council is None:
            #     raise RuntimeError("Planner council not initialized")
            #
            # merged_plan = self.planner_council.run(goal_spec)
            #
            # # Step 2: Generate architecture documents using Architect Agent
            # documents = self.architect.build_documents(merged_plan)
            #
            # # Step 3: Write documents to disk
            # self.architect.write_documents(merged_plan)
            #
            # # Step 4: Update state
            # self.state["architecture_version"] += 1
            # self.state["phases_version"] += 1
            # self.state["workflow_history"].append({
            #     "timestamp": datetime.now().isoformat(),
            #     "action": "architect_run",
            #     "architecture_version": self.state["architecture_version"],
            #     "phases_version": self.state["phases_version"]
            # })
            #
            # # Step 5: Save state
            # self.save_state()
            #
            # return documents
        """
        raise NotImplementedError(
            "run_architect() is not fully implemented yet. "
            "This method requires the Planner Council integration to be completed first. "
            "The Architect Agent infrastructure is in place and ready to generate "
            "architecture documents once the planner provides the merged plan. "
            "\n\n"
            "Current status:\n"
            "✓ Architect Agent structure created\n"
            "✓ Document generation methods implemented (stub logic)\n"
            "✓ State management infrastructure ready\n"
            "✗ Planner Council integration pending\n"
            "\n"
            "See commented code in this method for the planned implementation flow."
        )

    def get_architecture_version(self) -> int:
        """
        Get current architecture version.

        Returns:
            int: Current architecture version number
        """
        return self.state.get("architecture_version", 0)

    def get_phases_version(self) -> int:
        """
        Get current phases version.

        Returns:
            int: Current phases version number
        """
        return self.state.get("phases_version", 0)

    def get_workflow_history(self) -> list:
        """
        Get workflow history.

        Returns:
            list: List of workflow history entries
        """
        return self.state.get("workflow_history", [])
