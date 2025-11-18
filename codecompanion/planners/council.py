"""
Multi-model planner council for generating consensus-based plans.
"""

from __future__ import annotations
from typing import Dict, Any, List

from codecompanion.planners.planner_gpt import GPTPlanner
from codecompanion.planners.planner_claude import ClaudePlanner
from codecompanion.planners.planner_gemini import GeminiPlanner


class PlannerCouncil:
    """
    Multi-model planner council.

    Sends goal_spec to GPT, Claude, and Gemini planners and merges results
    to produce a consensus-based plan. Identifies areas of disagreement as
    "open questions" that require human decision-making.
    """

    def __init__(self):
        """Initialize the planner council with all three planners."""
        self.gpt = GPTPlanner()
        self.claude = ClaudePlanner()
        self.gemini = GeminiPlanner()

    def run(self, goal_spec: str) -> Dict[str, Any]:
        """
        Execute all planners and merge their plans.

        Args:
            goal_spec: Description of the goal or feature to plan

        Returns:
            Dict containing:
              - merged_plan: Consensus plan with phases, tasks, risks, notes
              - open_questions: List of disagreements between planners
              - raw: Raw outputs from each planner
        """
        # Call planners (stubbed for now)
        gpt_plan = self.gpt.plan(goal_spec)
        claude_plan = self.claude.plan(goal_spec)
        gemini_plan = self.gemini.plan(goal_spec)

        # Collect raw outputs
        raw = {
            "gpt": gpt_plan,
            "claude": claude_plan,
            "gemini": gemini_plan,
        }

        # Merge logic (simple consensus)
        merged_phases = self._merge_list_field("phases", raw)
        merged_tasks = self._merge_tasks(raw)
        merged_risks = self._merge_list_field("risks", raw)
        merged_notes = self._merge_list_field("notes", raw)

        open_questions = self._detect_open_questions(raw)

        return {
            "merged_plan": {
                "phases": merged_phases,
                "tasks": merged_tasks,
                "risks": merged_risks,
                "notes": merged_notes,
            },
            "open_questions": open_questions,
            "raw": raw,
        }

    # =========================================================================
    # MERGE HELPERS
    # =========================================================================

    def _merge_list_field(self, field: str, raw: Dict[str, Any]) -> List[Any]:
        """
        Keep unique values that appear in >= 2 planners.

        This implements a simple consensus mechanism: only include items
        that at least 2 out of 3 planners agree on.

        Args:
            field: Name of the field to merge (e.g., "phases", "risks", "notes")
            raw: Dict mapping planner names to their plan outputs

        Returns:
            List of merged values with consensus >= 2
        """
        all_values = {
            "gpt": raw["gpt"].get(field, []),
            "claude": raw["claude"].get(field, []),
            "gemini": raw["gemini"].get(field, []),
        }
        merged = []
        for planner, values in all_values.items():
            for v in values:
                # Count how many planners include this value
                count = sum(v in pv for pv in all_values.values())
                if count >= 2 and v not in merged:
                    merged.append(v)
        return merged

    def _merge_tasks(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Very simple merge: include tasks shared by >= 2 planners (by 'description').

        Tasks are considered the same if they have identical descriptions.
        This is a simple heuristic that will be refined in future versions.

        Args:
            raw: Dict mapping planner names to their plan outputs

        Returns:
            List of merged tasks with consensus >= 2
        """
        task_map = {}  # description -> count & sample

        for planner_key in raw:
            for t in raw[planner_key].get("tasks", []):
                desc = t.get("description")
                if not desc:
                    continue
                if desc not in task_map:
                    task_map[desc] = {"count": 0, "sample": t}
                task_map[desc]["count"] += 1

        merged = [v["sample"] for v in task_map.values() if v["count"] >= 2]
        return merged

    def _detect_open_questions(self, raw: Dict[str, Any]) -> List[str]:
        """
        If planners disagree strongly (e.g., unique tasks/phases), list them as open questions.

        This identifies areas where planners have divergent opinions that may
        require human decision-making or further clarification.

        Args:
            raw: Dict mapping planner names to their plan outputs

        Returns:
            List of open questions describing disagreements
        """
        open_q = []

        # Detect unique tasks across planners
        all_tasks = {
            "gpt": raw["gpt"].get("tasks", []),
            "claude": raw["claude"].get("tasks", []),
            "gemini": raw["gemini"].get("tasks", []),
        }

        descriptions = {}
        for planner, tasks in all_tasks.items():
            descriptions[planner] = [t.get("description") for t in tasks]

        # Find tasks only mentioned by a single planner
        flattened = [
            (planner, desc)
            for planner, descs in descriptions.items()
            for desc in descs
        ]

        for planner, desc in flattened:
            if desc is None:
                continue
            supporters = sum(desc in descriptions[p] for p in descriptions)
            if supporters == 1:
                open_q.append(f"Task '{desc}' only appears in {planner}'s plan.")

        # Detect unique phases
        all_phases = {
            "gpt": raw["gpt"].get("phases", []),
            "claude": raw["claude"].get("phases", []),
            "gemini": raw["gemini"].get("phases", []),
        }

        for planner, phases in all_phases.items():
            for phase in phases:
                supporters = sum(phase in all_phases[p] for p in all_phases)
                if supporters == 1:
                    open_q.append(f"Phase '{phase}' only appears in {planner}'s plan.")

        return open_q
