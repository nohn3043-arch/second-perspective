from __future__ import annotations

import json
from pathlib import Path

from .decision.engine import IntelligentDecisionEngine
from .models.schemas import DecisionRequest


def main() -> None:
    example = (
        Path(__file__).resolve().parents[2]
        / "examples"
        / "market_entry.json"
    )
    if not example.exists():
        raise SystemExit(
            "Example not found. Run from a source checkout or call the Python API directly."
        )

    data = json.loads(example.read_text(encoding="utf-8"))
    request = DecisionRequest.model_validate(data)
    result = IntelligentDecisionEngine().evaluate(request)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
