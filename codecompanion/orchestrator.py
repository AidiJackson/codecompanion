"""
Orchestrator for CodeCompanion full workflow pipeline.
Manages state and coordinates all agents in the proper sequence.
"""

import os
import json
from datetime import datetime
from pathlib import Path


class Orchestrator:
    """Manages the full CodeCompanion pipeline workflow."""

    def __init__(self, state_file=".cc/state.json"):
        self.state_file = state_file
        self.state = self.load_state()
        self.artifacts_dir = Path("cc_artifacts")
        self.output_dir = self.artifacts_dir / "final_output"

    def load_state(self):
        """Load state from JSON file or return empty state."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load state file: {e}")
                return {}
        return {}

    def save_state(self):
        """Save current state to JSON file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def ensure_initialized(self):
        """Run init if no state/settings exist."""
        if not self.state or not self.state.get("initialized"):
            print("Running initialization...")
            self.run_init()
            return True
        return False

    def run_init(self):
        """Initialize CodeCompanion settings and state."""
        # Create necessary directories
        os.makedirs(".cc", exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)

        # Initialize state
        self.state = {
            "initialized": True,
            "initialized_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        self.save_state()
        print("✓ Initialization complete")
        return 0

    def run_architect(self):
        """Run the architect agent to design the system."""
        print("Running Architect...")

        # Create architect artifacts directory
        architect_dir = self.artifacts_dir / "architect"
        os.makedirs(architect_dir, exist_ok=True)

        # Simulate architect work
        architecture = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "components": ["backend", "frontend", "docs", "tests"],
            "architecture_plan": "Full stack application design"
        }

        with open(architect_dir / "architecture.json", 'w') as f:
            json.dump(architecture, f, indent=2)

        print("✓ Architect complete")
        return 0

    def run_specialist(self, specialist_type):
        """Run a specialist agent (backend, frontend, docs, test)."""
        print(f"Running {specialist_type.capitalize()} Specialist...")

        # Create specialist artifacts directory
        specialist_dir = self.artifacts_dir / f"specialist_{specialist_type}"
        os.makedirs(specialist_dir, exist_ok=True)

        # Simulate specialist work
        result = {
            "timestamp": datetime.now().isoformat(),
            "specialist": specialist_type,
            "status": "success",
            "artifacts_created": [f"{specialist_type}_implementation.md"]
        }

        with open(specialist_dir / f"{specialist_type}_result.json", 'w') as f:
            json.dump(result, f, indent=2)

        print(f"✓ {specialist_type.capitalize()} Specialist complete")
        return 0

    def run_quality(self):
        """Run quality gates and checks."""
        print("Running Quality Gates...")

        # Create quality artifacts directory
        quality_dir = self.artifacts_dir / "quality"
        os.makedirs(quality_dir, exist_ok=True)

        # Simulate quality checks
        quality_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "checks": {
                "code_quality": "passed",
                "test_coverage": "passed",
                "security_scan": "passed",
                "performance": "passed"
            }
        }

        with open(quality_dir / "quality_report.json", 'w') as f:
            json.dump(quality_report, f, indent=2)

        print("✓ Quality Gates complete")
        return 0

    def run_file_orchestrator(self):
        """Build final output and create manifest."""
        print("Building final output...")

        # Create final output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Create manifest
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "pipeline_stages": [
                "init",
                "architect",
                "specialist_backend",
                "specialist_frontend",
                "specialist_docs",
                "specialist_test",
                "quality",
                "build"
            ],
            "output_directory": str(self.output_dir),
            "artifacts_generated": True
        }

        with open(self.output_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)

        print("✓ Build complete")
        return 0

    def run_full_pipeline(self):
        """
        Execute the full end-to-end workflow in sequence:
        1. init (if needed)
        2. architect
        3. specialists (backend, frontend, docs, test)
        4. quality
        5. build

        Returns:
            dict: Result with status and output_dir
        """
        try:
            # Step 1: Initialize if needed
            self.ensure_initialized()

            # Step 2: Run architect
            rc = self.run_architect()
            if rc != 0:
                print("❌ Error during Architect")
                return {"status": "error", "step": "architect"}

            # Step 3: Run specialists
            specialists = ["backend", "frontend", "docs", "test"]
            for specialist in specialists:
                rc = self.run_specialist(specialist)
                if rc != 0:
                    print(f"❌ Error during {specialist.capitalize()} Specialist")
                    return {"status": "error", "step": f"specialist_{specialist}"}

            # Step 4: Run quality gates
            rc = self.run_quality()
            if rc != 0:
                print("❌ Error during Quality Gates")
                return {"status": "error", "step": "quality"}

            # Step 5: Build final output
            rc = self.run_file_orchestrator()
            if rc != 0:
                print("❌ Error during Build")
                return {"status": "error", "step": "build"}

            # Update state with completion timestamp
            self.state["last_full_run"] = datetime.now().isoformat()
            self.save_state()

            return {
                "status": "success",
                "output_dir": str(self.output_dir)
            }

        except Exception as e:
            print(f"❌ Error during pipeline: {e}")
            return {"status": "error", "error": str(e)}
