"""
Orchestrator - Manages CodeCompanion agents and workflow state.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

from .architect import Architect
from .specialist_loader import load_specialist
from . import quality_gates


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
                "last_specialist": None,
                "specialists_run": [],
                "last_quality_run": None,
                "quality_reports": [],
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

    def run_specialist(self, specialist_type: str) -> Dict[str, Any]:
        """
        Execute a specialist agent to generate specialized analysis.

        This method:
        1. Loads current state
        2. Loads the requested specialist
        3. Runs the specialist
        4. Writes output to cc_artifacts/
        5. Updates and saves state
        6. Returns execution results

        Args:
            specialist_type: Type of specialist to run (backend, frontend, docs, test)

        Returns:
            Dictionary with:
                - specialist_type: Type of specialist executed
                - output_file: Path to generated report file
                - timestamp: Execution timestamp

        Raises:
            ValueError: If specialist_type is unknown
        """
        # Load current state
        state = self._load_state()

        # Ensure specialists_run exists in state (for backward compatibility)
        if "specialists_run" not in state:
            state["specialists_run"] = []

        # Load and run specialist
        specialist = load_specialist(specialist_type)
        result = specialist.run(self.project_root)

        # Ensure cc_artifacts directory exists
        artifacts_dir = self.project_root / "cc_artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Write output file
        output_file = artifacts_dir / f"{specialist_type}_report.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["content"])

        # Update state
        state["last_specialist"] = specialist_type

        # Add to specialists run history
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        state["specialists_run"].append({
            "type": specialist_type,
            "file": str(output_file.relative_to(self.project_root)),
            "timestamp": timestamp,
        })

        # Save updated state
        self._save_state(state)

        # Return results
        return {
            "specialist_type": specialist_type,
            "output_file": str(output_file.relative_to(self.project_root)),
            "timestamp": timestamp,
        }

    def run_quality(self) -> Dict[str, Any]:
        """
        Execute quality gate checks on the project.

        This method:
        1. Loads current state
        2. Runs quality checks via quality_gates module
        3. Updates state with quality run information
        4. Saves updated state
        5. Returns execution results

        Returns:
            Dictionary with:
                - status: "success" or "failure"
                - report_file: Path to generated report file
                - timestamp: Execution timestamp
        """
        # Load current state
        state = self._load_state()

        # Ensure quality_reports exists in state (for backward compatibility)
        if "quality_reports" not in state:
            state["quality_reports"] = []

        # Run quality gates
        result = quality_gates.run_quality_gates(self.project_root)

        # Update state
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        state["last_quality_run"] = timestamp

        # Add to quality reports history
        state["quality_reports"].append({
            "file": result["file"],
            "timestamp": timestamp,
        })

        # Save updated state
        self._save_state(state)

        # Return results
        return {
            "status": result["status"],
            "report_file": result["file"],
            "timestamp": timestamp,
        }

    def get_state(self) -> Dict[str, Any]:
        """
        Get current workflow state.

        Returns:
            Dictionary containing current state
        """
        return self._load_state()
