from __future__ import annotations

import json
from pathlib import Path

from .hub import SuperDecisionHub
from .models.hub import HubAnalysisRequest


def main() -> None:
    example = Path(__file__).resolve().parents[2] / "examples" / "market_entry.json"
    if not example.exists():
        raise SystemExit(
            "Example not found. Run from a source checkout or call SuperDecisionHub directly."
        )

    decision = json.loads(example.read_text(encoding="utf-8"))
    request = HubAnalysisRequest.model_validate(
        {
            "decision": decision,
            "scenarios": [
                {
                    "id": "SC1",
                    "name": "Critical partner assumption fails",
                    "failed_assumption_ids": ["A1"],
                },
                {
                    "id": "SC2",
                    "name": "Partner capital requirement exceeds budget",
                    "metric_overrides": {"S2": {"capital_required": 6000000}},
                },
            ],
        }
    )
    report = SuperDecisionHub().analyze(request)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
