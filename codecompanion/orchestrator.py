"""
Orchestrator core for CodeCompanion's multi-model dev OS.

This module provides the central orchestration layer that manages project state,
coordinates multi-model planning councils, and tracks development checkpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import datetime as _dt

# TODO: Future imports for multi-model components
# from codecompanion.planning import PlannerCouncil
# from codecompanion.architecture import ArchitectAgent
# from codecompanion.specialists import BackendSpecialist, FrontendSpecialist
# from codecompanion.specialists import TestSpecialist, DocsSpecialist


@dataclass
class ProjectState:
    """
    Represents the current state of a CodeCompanion project.

    This dataclass mirrors the structure of ops/PROJECT_STATE.json and provides
    serialization/deserialization methods for state persistence.
    """

    project_name: Optional[str] = None
    project_description: Optional[str] = None
    active_phase: Optional[str] = None
    plan_version: int = 1
    architecture_version: int = 1
    recent_checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    todo: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ProjectState to a dictionary for JSON serialization.

        Returns:
            Dict representation of the project state
        """
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "active_phase": self.active_phase,
            "plan_version": self.plan_version,
            "architecture_version": self.architecture_version,
            "recent_checkpoints": self.recent_checkpoints,
            "open_questions": self.open_questions,
            "todo": self.todo,
            "last_updated": self.last_updated,
            "settings": self.settings,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ProjectState":
        """
        Create a ProjectState from a dictionary loaded from JSON.

        This method is tolerant of missing keys and will use defaults
        that match the ops/PROJECT_STATE.json schema.

        Args:
            data: Dictionary containing project state data

        Returns:
            ProjectState instance populated with data
        """
        # Provide default settings structure if not present
        default_settings = {
            "workflow": {
                "prefer_claude_web_for_scaffolding": True,
                "prefer_claude_shell_for_small_fixes": True,
                "require_checkpoint_before_major_changes": True
            },
            "models": {
                "planner_gpt": True,
                "planner_claude": True,
                "planner_gemini": True,
                "architect_model": "claude"
            }
        }

        return ProjectState(
            project_name=data.get("project_name"),
            project_description=data.get("project_description"),
            active_phase=data.get("active_phase"),
            plan_version=data.get("plan_version", 1),
            architecture_version=data.get("architecture_version", 1),
            recent_checkpoints=data.get("recent_checkpoints", []),
            open_questions=data.get("open_questions", []),
            todo=data.get("todo", []),
            last_updated=data.get("last_updated"),
            settings=data.get("settings", default_settings),
        )


class Orchestrator:
    """
    Central orchestration layer for CodeCompanion projects.

    The Orchestrator manages project state, coordinates multi-model planning
    councils (GPT, Claude, Gemini), delegates to architecture and specialist
    agents, and tracks development checkpoints.

    Attributes:
        state_path: Path to the PROJECT_STATE.json file
        state: Current project state
    """

    def __init__(self, state_path: Path | str = Path("ops/PROJECT_STATE.json")):
        """
        Initialize the Orchestrator and load project state.

        Args:
            state_path: Path to the project state JSON file (default: ops/PROJECT_STATE.json)
        """
        self.state_path = Path(state_path)
        self.state: ProjectState = self.load_state()

    def load_state(self) -> ProjectState:
        """
        Load project state from disk or create default state.

        If the state file exists, it will be loaded and parsed into a ProjectState.
        If it does not exist, a new default state will be created matching the
        ops/PROJECT_STATE.json schema.

        Returns:
            ProjectState instance loaded from file or created with defaults
        """
        if self.state_path.exists():
            # Load existing state
            with open(self.state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectState.from_dict(data)
        else:
            # Create default state matching ops/PROJECT_STATE.json structure
            default_data = {
                "project_name": None,
                "project_description": None,
                "active_phase": None,
                "plan_version": 1,
                "architecture_version": 1,
                "recent_checkpoints": [],
                "open_questions": [],
                "todo": [],
                "last_updated": None,
                "settings": {
                    "workflow": {
                        "prefer_claude_web_for_scaffolding": True,
                        "prefer_claude_shell_for_small_fixes": True,
                        "require_checkpoint_before_major_changes": True
                    },
                    "models": {
                        "planner_gpt": True,
                        "planner_claude": True,
                        "planner_gemini": True,
                        "architect_model": "claude"
                    }
                }
            }
            return ProjectState.from_dict(default_data)

    def save_state(self) -> None:
        """
        Save the current project state to disk.

        Updates the last_updated timestamp and writes the state to the
        configured state_path with pretty-printed JSON formatting.
        """
        # Update timestamp to current UTC time
        self.state.last_updated = _dt.datetime.now(_dt.timezone.utc).isoformat()

        # Ensure parent directory exists
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        # Write state to file
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(self.state.to_dict(), f, indent=2, sort_keys=False)

    def kickoff_project(self, name: str, description: str) -> None:
        """
        Initialize a brand-new project with the Orchestrator.

        This is the entry point for starting a new CodeCompanion project.
        It sets up the initial project metadata, places the project in the
        "planning" phase, and saves the state.

        Args:
            name: Name of the project
            description: Brief description of the project goals
        """
        self.state.project_name = name
        self.state.project_description = description
        self.state.active_phase = "planning"

        # Initialize versions if not already set
        if self.state.plan_version == 0:
            self.state.plan_version = 1
        if self.state.architecture_version == 0:
            self.state.architecture_version = 1

        self.save_state()

    def create_checkpoint(self, label: str) -> None:
        """
        Create a development checkpoint for tracking progress.

        Checkpoints are logical markers that track significant project milestones.
        This method records the checkpoint in the project state but does not
        create git tags or commits - that should be handled by separate tooling.

        The checkpoint list is automatically trimmed to the most recent 20 entries
        to prevent unbounded growth.

        Args:
            label: Human-readable label for the checkpoint (e.g., "Initial scaffolding complete")
        """
        checkpoint = {
            "label": label,
            "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "active_phase": self.state.active_phase
        }

        self.state.recent_checkpoints.append(checkpoint)

        # Trim to most recent 20 checkpoints
        if len(self.state.recent_checkpoints) > 20:
            self.state.recent_checkpoints = self.state.recent_checkpoints[-20:]

        self.save_state()

    def get_current_state(self) -> ProjectState:
        """
        Get the current project state.

        Returns:
            The current ProjectState instance
        """
        return self.state

    # =========================================================================
    # Stubbed methods for upcoming multi-model components
    # =========================================================================

    def run_planner_council(self, goal_spec: str) -> None:
        """
        Call the multi-model Planner Council (GPT, Claude, Gemini) to update PLAN.md and TODO.json.

        The Planner Council orchestrates multiple LLMs to collaboratively create
        and refine project plans, ensuring diverse perspectives and robust planning.

        This will be implemented in a later phase.

        Args:
            goal_spec: Specification of the goal or feature to plan

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Planner Council integration not implemented yet.")

    def run_architect(self) -> None:
        """
        Call the Architect Agent to update docs/ARCHITECTURE.md and ops/PHASES.md.

        The Architect Agent is responsible for maintaining high-level architecture
        documentation and defining development phases based on the current plan.

        This will be implemented in a later phase.

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Architect integration not implemented yet.")

    def run_specialist(self, specialist_name: str, task: str) -> None:
        """
        Call a named Specialist Agent (backend, frontend, test, docs) to generate prompts or changes.

        Specialist agents are domain-focused agents that handle specific aspects
        of the codebase (backend logic, frontend UI, testing, documentation).

        This will be implemented in a later phase.

        Args:
            specialist_name: Name of the specialist to invoke
                           (e.g., "backend", "frontend", "test", "docs")
            task: Task specification for the specialist to complete

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Specialist integration not implemented yet.")


# =============================================================================
# Self-check for manual debugging
# =============================================================================

if __name__ == "__main__":
    orch = Orchestrator()
    print("Loaded project state for:", orch.state.project_name)
    print(f"Active phase: {orch.state.active_phase}")
    print(f"Plan version: {orch.state.plan_version}")
    print(f"Architecture version: {orch.state.architecture_version}")
    print(f"Number of checkpoints: {len(orch.state.recent_checkpoints)}")
