from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any
import json


@dataclass
class ModelPolicy:
    """Configuration for multi-LLM routing and model selection.

    Attributes:
        mode: Operating mode (e.g., "orchestrated", "single_model")
        defaults: Default model assignments for different roles
        routing_rules: Task-specific model routing rules
    """
    mode: str
    defaults: Dict[str, str]
    routing_rules: Dict[str, str]

    @staticmethod
    def load(path: str | Path = "ops/MODEL_POLICY.json") -> "ModelPolicy":
        """Load model policy from a JSON configuration file.

        Args:
            path: Path to the model policy JSON file

        Returns:
            ModelPolicy instance with loaded configuration

        Note:
            If the file doesn't exist, returns a minimal default policy
        """
        p = Path(path)
        if not p.exists():
            # Fallback minimal default
            return ModelPolicy(
                mode="orchestrated",
                defaults={},
                routing_rules={},
            )
        data = json.loads(p.read_text())
        return ModelPolicy(
            mode=data.get("mode", "orchestrated"),
            defaults=data.get("defaults", {}),
            routing_rules=data.get("routing_rules", {}),
        )
