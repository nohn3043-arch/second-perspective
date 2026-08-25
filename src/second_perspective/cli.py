from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from .decision.engine import IntelligentDecisionEngine
from .models.schemas import DecisionRequest
from .report import export_expert_report
from .service import DecisionService
from .version import VERSION

logger = logging.getLogger(__name__)


def _example_path() -> Path:
    example = (
        Path(__file__).resolve().parents[2]
        / "examples"
        / "market_entry.json"
    )
    if not example.exists():
        raise SystemExit(
            "Example not found. Run from a source checkout or call the Python API directly."
        )
    return example


def _run_demo() -> None:
    data = json.loads(_example_path().read_text(encoding="utf-8"))
    request = DecisionRequest.model_validate(data)
    result = IntelligentDecisionEngine().evaluate(request)
    print(result.model_dump_json(indent=2))


def _run_report(args: list[str]) -> None:
    decision_file = _example_path()
    out_dir = Path("reports")
    out_file: Path | None = None
    it = iter(args)
    for arg in it:
        if arg == "--decision":
            decision_file = Path(next(it))
        elif arg == "--out":
            out_file = Path(next(it))
        elif arg == "--version":
            print(VERSION)
            return
        else:
            raise SystemExit(f"Unknown argument: {arg}")

    data = json.loads(decision_file.read_text(encoding="utf-8"))
    request = DecisionRequest.model_validate(data)
    record = DecisionService().evaluate(request)
    written = export_expert_report(
        records=[record],
        out_path=out_file,
        out_dir=out_dir,
    )
    logger.info("expert review report written to %s", written)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        _run_report(sys.argv[2:])
        return
    _run_demo()


if __name__ == "__main__":
    main()