from __future__ import annotations

from typing import Any, Protocol


class RedesignAdvisor(Protocol):
    def explain(self, analysis: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]: ...


class RuleAdvisor:
    """Transparent provider-free advisor. It explains; it never selects."""

    def explain(self, analysis: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
        highest = analysis["step_diagnostics"][0]
        candidate = comparison["top_scoring_candidate"]
        projection = next(item for item in comparison["projections"] if item["option_id"] == candidate)
        return {
            "candidate": candidate,
            "reasoning_summary": [
                f"The largest measured queue is {highest['step_id']} at {highest['average_wait_minutes_per_case']} average minutes per case.",
                f"{candidate} has the highest weighted trade-off score under the supplied weights.",
                "Every modeled option preserves all five mandatory controls before it is eligible for ranking.",
            ],
            "important_caveat": projection["assumption_notice"],
            "authority": "ADVISORY_ONLY",
        }
