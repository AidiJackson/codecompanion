"""
File Orchestrator - Assembles all agent outputs into a unified export package.
"""
import json
from pathlib import Path
from typing import Dict, List


class FileOrchestrator:
    """Collects all agent outputs and creates a unified export package."""

    FILES_TO_COLLECT = [
        ".cc/state.json",
        ".cc/settings.json",
        "cc_artifacts/backend_report.txt",
        "cc_artifacts/frontend_report.txt",
        "cc_artifacts/docs_report.txt",
        "cc_artifacts/test_report.txt",
        "cc_artifacts/quality_report.json",
        "docs/ARCHITECTURE.md",
        "ops/PHASES.md",
    ]

    def __init__(self, project_path: Path):
        """
        Initialize the File Orchestrator.

        Args:
            project_path: Root path of the project
        """
        self.project_path = Path(project_path)
        self.output_dir = self.project_path / "cc_artifacts" / "final_output"

    def collect_all(self) -> Dict:
        """
        Collect all agent output files and create manifest.

        Returns:
            Dictionary with status, output_dir, generated, and missing files
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        generated = []
        missing = []

        # Check each file
        for file_path in self.FILES_TO_COLLECT:
            full_path = self.project_path / file_path
            if full_path.exists():
                generated.append(file_path)
            else:
                missing.append(file_path)

        # Write manifest
        manifest = {
            "generated": generated,
            "missing": missing,
        }

        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Return result
        return {
            "status": "success",
            "output_dir": str(self.output_dir),
            "generated": generated,
            "missing": missing,
        }
