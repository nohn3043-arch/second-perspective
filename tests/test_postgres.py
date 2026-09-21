"""Postgres repositories coverage with a faked psycopg2 layer.

The repositories are exercised against an in-memory fake connection/cursor
that routes on SQL text; integrity primitives (seal/verify) run for real.
"""

import sys
import types

import pytest

# ── fake psycopg2 modules (must exist before importing the persistence package)


class FakeSQL:
    def __init__(self, template):
        self.template = template

    def format(self, parts):
        return self.template


class FakeCursor:
    def __init__(self, config):
        self.config = config
        self.executed = []
        self._last = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        s = str(sql)
        self.executed.append((s, params))
        if "CREATE TABLE" in s or "CREATE INDEX" in s:
            self._last = []
        elif "SELECT revision FROM nomos_decisions" in s:
            row = self.config.get("latest_revision_row")
            self._last = [row] if row else []
        elif "SELECT record_hash FROM nomos_decisions" in s:
            row = self.config.get("parent_hash_row")
            self._last = [row] if row else []
        elif "SELECT body FROM nomos_decisions" in s:
            self._last = self.config.get("decision_bodies", [])
        elif "SELECT 1 FROM nomos_hub_reports" in s:
            self._last = self.config.get("hub_exists_row", [])
        elif "SELECT body FROM nomos_hub_reports" in s:
            self._last = self.config.get("hub_bodies", [])
        elif "SELECT 1 FROM nomos_sessions" in s:
            self._last = self.config.get("session_exists_row", [])
        elif "SELECT body FROM nomos_sessions" in s:
            self._last = self.config.get("session_bodies", [])
        else:
            self._last = []

    def fetchone(self):
        rows = self._last or []
        return rows[0] if rows else None

    def fetchall(self):
        return list(self._last or [])


class FakeConn:
    def __init__(self, config):
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def cursor(self):
        return FakeCursor(self.config)

    def commit(self):
        return None


CURRENT_CONFIG = {}


def _fake_connect(dsn, cursor_factory=None):
    return FakeConn(CURRENT_CONFIG)


@pytest.fixture(scope="module", autouse=True)
def _install_fake_psycopg2():
    fake = types.ModuleType("psycopg2")
    fake.connect = _fake_connect
    fake.extras = types.ModuleType("psycopg2.extras")
    fake.extras.RealDictCursor = dict
    fake.extras.register_uuid = lambda: None
    fake.sql = types.ModuleType("psycopg2.sql")
    fake.sql.SQL = FakeSQL
    sys.modules["psycopg2"] = fake
    sys.modules["psycopg2.extras"] = fake.extras
    sys.modules["psycopg2.sql"] = fake.sql
    yield
    sys.modules.pop("psycopg2", None)
    sys.modules.pop("psycopg2.extras", None)
    sys.modules.pop("psycopg2.sql", None)


@pytest.fixture(autouse=True)
def _reset_config():
    CURRENT_CONFIG.clear()
    CURRENT_CONFIG.update(
        latest_revision_row=None,
        parent_hash_row=None,
        decision_bodies=[],
        hub_exists_row=[],
        hub_bodies=[],
        session_exists_row=[],
        session_bodies=[],
    )
    yield


def _sealed(record):
    from second_perspective.decision.integrity import seal_record

    return seal_record(record)


def _sealed_hub_report(record):
    from second_perspective.decision.integrity import seal_record
    from second_perspective.hub.integrity import seal_hub_report
    from second_perspective.hub.policy import HubPolicy
    from second_perspective.models.hub import HubReport

    report = HubReport(
        hub_run_id="HUB-PG-TEST-0001",
        hub_version="0.3.0",
        decision_record=seal_record(record),
        hub_policy=HubPolicy().snapshot(),
        algorithm_audit_verified=True,
    )
    return seal_hub_report(report)


def _make_session(make_request):
    from second_perspective.models.schemas import ReconstructionSession

    return ReconstructionSession(
        session_id="SESS-PG-TEST-0001",
        request=make_request(),
    )


# ── PostgresDecisionRepository ─────────────────────────────────────────


def test_decision_put_inserts_sealed(make_record):
    from second_perspective.persistence.postgres import PostgresDecisionRepository

    repo = PostgresDecisionRepository("dbname=test")
    repo.put(_sealed(make_record()))  # must not raise


def test_decision_put_rejects_unsealed(make_record):
    from second_perspective.persistence.postgres import PostgresDecisionRepository

    repo = PostgresDecisionRepository("dbname=test")
    with pytest.raises(ValueError, match="record_hash"):
        repo.put(make_record())


def test_decision_put_enforces_revision_sequence(make_record):
    from second_perspective.persistence.postgres import PostgresDecisionRepository

    CURRENT_CONFIG["latest_revision_row"] = {"revision": 3}
    repo = PostgresDecisionRepository("dbname=test")
    with pytest.raises(ValueError, match="revision must be 4"):
        repo.put(_sealed(make_record()))


def test_decision_put_rejects_wrong_parent_hash(make_record):
    from second_perspective.decision.integrity import seal_record
    from second_perspective.persistence.postgres import PostgresDecisionRepository

    CURRENT_CONFIG["latest_revision_row"] = {"revision": 1}
    CURRENT_CONFIG["parent_hash_row"] = {"record_hash": "f" * 64}
    prev = seal_record(make_record(revision=1))
    # rebuild revision=2 with a bogus parent hash
    cur = make_record(revision=2, parent_record_hash="0" * 64)
    cur.result = prev.result
    record = seal_record(cur)
    repo = PostgresDecisionRepository("dbname=test")
    with pytest.raises(ValueError, match="parent_record_hash"):
        repo.put(record)


def test_decision_put_accepts_correct_parent_hash(make_record):
    from second_perspective.decision.integrity import seal_record
    from second_perspective.persistence.postgres import PostgresDecisionRepository

    CURRENT_CONFIG["latest_revision_row"] = {"revision": 1}
    prev = seal_record(make_record(revision=1))
    CURRENT_CONFIG["parent_hash_row"] = {"record_hash": prev.record_hash}
    cur = make_record(revision=2, parent_record_hash=prev.record_hash)
    cur.result = prev.result
    record = seal_record(cur)
    repo = PostgresDecisionRepository("dbname=test")
    repo.put(record)  # must not raise


def test_decision_get_returns_latest(make_record):
    import json

    from second_perspective.persistence.postgres import PostgresDecisionRepository

    record = _sealed(make_record())
    CURRENT_CONFIG["decision_bodies"] = [{"body": record.model_dump_json()}]
    repo = PostgresDecisionRepository("dbname=test")
    got = repo.get("DEC-TEST-0001")
    assert got is not None
    assert got.result.decision_id == "DEC-TEST-0001"
    assert got.revision == 1


def test_decision_get_none_when_missing():
    from second_perspective.persistence.postgres import PostgresDecisionRepository

    repo = PostgresDecisionRepository("dbname=test")
    assert repo.get("DEC-MISSING") is None


def test_decision_history_returns_ordered_records(make_record):
    import json

    from second_perspective.persistence.postgres import PostgresDecisionRepository

    records = [_sealed(make_record(revision=1))]
    CURRENT_CONFIG["decision_bodies"] = [{"body": r.model_dump_json()} for r in records]
    repo = PostgresDecisionRepository("dbname=test")
    hist = repo.history("DEC-TEST-0001")
    assert len(hist) == 1
    assert hist[0].revision == 1


def test_decision_history_tampered_chain_raises(make_record):
    import json

    from second_perspective.decision.integrity import verify_chain
    from second_perspective.persistence.postgres import PostgresDecisionRepository

    r1 = _sealed(make_record(revision=1))
    r2 = _sealed(make_record(revision=2, parent_record_hash=r1.record_hash))
    # Corrupt r2's body so the chain no longer verifies
    r2.result = r1.result
    payload = r2.model_dump_json()
    CURRENT_CONFIG["decision_bodies"] = [
        {"body": r1.model_dump_json()},
        {"body": payload},
    ]
    repo = PostgresDecisionRepository("dbname=test")
    with pytest.raises(ValueError, match="integrity verification"):
        repo.history("DEC-TEST-0001")


# ── PostgresHubReportRepository ────────────────────────────────────────


def test_hub_put_rejects_unsealed(make_record):
    from second_perspective.hub.policy import HubPolicy
    from second_perspective.models.hub import HubReport
    from second_perspective.persistence.postgres import PostgresHubReportRepository

    report = HubReport(
        hub_run_id="HUB-PG-TEST-0002",
        hub_version="0.3.0",
        decision_record=_sealed(make_record()),
        hub_policy=HubPolicy().snapshot(),
        algorithm_audit_verified=True,
    )
    repo = PostgresHubReportRepository("dbname=test")
    with pytest.raises(ValueError, match="integrity"):
        repo.put(report)


def test_hub_put_inserts_sealed(make_record):
    from second_perspective.persistence.postgres import PostgresHubReportRepository

    repo = PostgresHubReportRepository("dbname=test")
    repo.put(_sealed_hub_report(make_record()))  # must not raise


def test_hub_put_rejects_duplicate(make_record):
    from second_perspective.persistence.postgres import PostgresHubReportRepository

    CURRENT_CONFIG["hub_exists_row"] = [{"1": 1}]
    repo = PostgresHubReportRepository("dbname=test")
    with pytest.raises(ValueError, match="already exists"):
        repo.put(_sealed_hub_report(make_record()))


def test_hub_get_returns_report(make_record):
    import json

    from second_perspective.persistence.postgres import PostgresHubReportRepository

    report = _sealed_hub_report(make_record())
    CURRENT_CONFIG["hub_bodies"] = [{"body": report.model_dump_json()}]
    repo = PostgresHubReportRepository("dbname=test")
    got = repo.get("HUB-PG-TEST-0001")
    assert got is not None
    assert got.hub_run_id == "HUB-PG-TEST-0001"


def test_hub_get_none_when_missing():
    from second_perspective.persistence.postgres import PostgresHubReportRepository

    repo = PostgresHubReportRepository("dbname=test")
    assert repo.get("HUB-MISSING") is None


def test_hub_get_rejects_tampered(make_record):
    import json

    from second_perspective.persistence.postgres import PostgresHubReportRepository

    report = _sealed_hub_report(make_record())
    report.hub_version = "9.9.9"
    CURRENT_CONFIG["hub_bodies"] = [{"body": report.model_dump_json()}]
    repo = PostgresHubReportRepository("dbname=test")
    with pytest.raises(ValueError, match="integrity"):
        repo.get("HUB-PG-TEST-0001")


# ── PostgresSessionRepository ──────────────────────────────────────────


def test_session_put_and_get_roundtrip(make_request):
    import json

    from second_perspective.models.enums import SessionStatus
    from second_perspective.persistence.postgres import PostgresSessionRepository

    session = _make_session(make_request)
    repo = PostgresSessionRepository("dbname=test")
    repo.put(session)

    CURRENT_CONFIG["session_bodies"] = [{"body": session.model_dump_json()}]
    got = repo.get("SESS-PG-TEST-0001")
    assert got is not None
    assert got.session_id == "SESS-PG-TEST-0001"
    assert got.status == SessionStatus.ACTIVE


def test_session_put_rejects_duplicate(make_request):
    from second_perspective.persistence.postgres import PostgresSessionRepository

    CURRENT_CONFIG["session_exists_row"] = [{"1": 1}]
    repo = PostgresSessionRepository("dbname=test")
    with pytest.raises(ValueError, match="already exists"):
        repo.put(_make_session(make_request))


def test_session_update_requires_existing(make_request):
    from second_perspective.persistence.postgres import PostgresSessionRepository

    repo = PostgresSessionRepository("dbname=test")
    with pytest.raises(ValueError, match="does not exist"):
        repo.update(_make_session(make_request))


def test_session_update_persists(make_request):
    from second_perspective.models.enums import SessionStatus
    from second_perspective.persistence.postgres import PostgresSessionRepository

    CURRENT_CONFIG["session_exists_row"] = [{"1": 1}]
    repo = PostgresSessionRepository("dbname=test")
    session = _make_session(make_request)
    session.status = SessionStatus.SEALED
    repo.update(session)  # must not raise


def test_session_get_none_when_missing():
    from second_perspective.persistence.postgres import PostgresSessionRepository

    repo = PostgresSessionRepository("dbname=test")
    assert repo.get("SESS-MISSING") is None
