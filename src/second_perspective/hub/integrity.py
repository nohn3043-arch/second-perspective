from __future__ import annotations

import hashlib
import hmac

from ..canonical import canonical_json
from ..models.hub import HubReport


def hub_report_digest(report: HubReport) -> str:
    payload = report.model_dump(mode="json", exclude={"report_hash"})
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def seal_hub_report(report: HubReport) -> HubReport:
    return report.model_copy(update={"report_hash": hub_report_digest(report)})


def verify_hub_report(report: HubReport) -> bool:
    return hmac.compare_digest(report.report_hash, hub_report_digest(report))
