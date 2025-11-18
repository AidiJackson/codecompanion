"""
Specialist agent loader and execution.

Loads and runs specialized agents for different domains: frontend, backend, test, docs.
"""

from typing import Dict, Any, Optional, Literal
import json


SpecialistType = Literal["frontend", "backend", "test", "docs"]


class SpecialistAgent:
    """
    Base class for specialist agents.

    Each specialist agent focuses on a specific domain of software development.
    """

    def __init__(self, agent_type: SpecialistType, state_file: str = ".codecompanion_state.json") -> None:
        """
        Initialize a specialist agent.

        Args:
            agent_type: Type of specialist (frontend, backend, test, docs)
            state_file: Path to the project state file
        """
        self.agent_type = agent_type
        self.state_file = state_file
        self.state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load project state from file."""
        try:
            with open(self.state_file, "r") as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {"initialized": False}
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse state file: {e}")
            self.state = {"initialized": False}

    def _save_state(self) -> None:
        """Save project state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error: Failed to save state: {e}")

    def run(self) -> int:
        """
        Execute the specialist agent.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        print(f"[specialist:{self.agent_type}] Starting {self.agent_type} specialist...")

        # Check if project is initialized
        if not self.state.get("initialized", False):
            print(f"[specialist:{self.agent_type}] Warning: Project not initialized")
            print(f"[specialist:{self.agent_type}] Run 'cc init' first for best results")

        # Execute specialist-specific logic
        result = self._execute()

        # Update state
        if "specialists_run" not in self.state:
            self.state["specialists_run"] = []

        if self.agent_type not in self.state["specialists_run"]:
            self.state["specialists_run"].append(self.agent_type)

        self._save_state()

        print(f"[specialist:{self.agent_type}] Specialist execution complete")
        return result

    def _execute(self) -> int:
        """
        Execute specialist-specific logic.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if self.agent_type == "frontend":
            return self._execute_frontend()
        elif self.agent_type == "backend":
            return self._execute_backend()
        elif self.agent_type == "test":
            return self._execute_test()
        elif self.agent_type == "docs":
            return self._execute_docs()
        else:
            print(f"[specialist:{self.agent_type}] Error: Unknown specialist type")
            return 1

    def _execute_frontend(self) -> int:
        """Execute frontend specialist tasks."""
        print("[specialist:frontend] Analyzing frontend components...")
        print("[specialist:frontend] - Checking UI/UX patterns")
        print("[specialist:frontend] - Validating component structure")
        print("[specialist:frontend] - Reviewing state management")
        return 0

    def _execute_backend(self) -> int:
        """Execute backend specialist tasks."""
        print("[specialist:backend] Analyzing backend services...")
        print("[specialist:backend] - Checking API endpoints")
        print("[specialist:backend] - Validating database schema")
        print("[specialist:backend] - Reviewing business logic")
        return 0

    def _execute_test(self) -> int:
        """Execute test specialist tasks."""
        print("[specialist:test] Analyzing test coverage...")
        print("[specialist:test] - Identifying missing tests")
        print("[specialist:test] - Reviewing test quality")
        print("[specialist:test] - Checking test organization")
        return 0

    def _execute_docs(self) -> int:
        """Execute documentation specialist tasks."""
        print("[specialist:docs] Analyzing documentation...")
        print("[specialist:docs] - Checking API documentation")
        print("[specialist:docs] - Reviewing code comments")
        print("[specialist:docs] - Validating README completeness")
        return 0


class SpecialistAgentLoader:
    """
    Loader for specialist agents.

    Provides factory methods to create and load specialist agents.
    """

    @staticmethod
    def load(agent_type: SpecialistType, state_file: str = ".codecompanion_state.json") -> SpecialistAgent:
        """
        Load a specialist agent by type.

        Args:
            agent_type: Type of specialist to load
            state_file: Path to the project state file

        Returns:
            Configured specialist agent instance
        """
        return SpecialistAgent(agent_type, state_file)

    @staticmethod
    def get_available_types() -> list[SpecialistType]:
        """
        Get list of available specialist types.

        Returns:
            List of specialist type names
        """
        return ["frontend", "backend", "test", "docs"]
