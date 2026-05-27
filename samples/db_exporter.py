"""GovernAI SQLite exporter — saves every GovernAIEvent to a local SQLite DB.

Usage::

    from governai.core.options import GovernAIOptions
    from governai.core.runtime import GovernAIRuntime
    from samples.db_exporter import SqliteExporter

    db = SqliteExporter("governai_events.db")
    runtime = GovernAIRuntime(
        options=GovernAIOptions(application_name="MyApp"),
        exporter=db,
    )

Query saved events::

    import sqlite3
    con = sqlite3.connect("governai_events.db")
    for row in con.execute("SELECT * FROM governai_events ORDER BY timestamp_utc DESC LIMIT 20"):
        print(row)
"""

from __future__ import annotations

import asyncio
import sqlite3

from governai.abstractions.models import GovernAIEvent

# DDL — created once on first use
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS governai_events (
    event_id           TEXT PRIMARY KEY,
    timestamp_utc      TEXT NOT NULL,
    application_name   TEXT,
    environment_name   TEXT,
    tenant_id          TEXT,
    user_id            TEXT,
    operation_name     TEXT,
    agent_name         TEXT,
    model_provider     TEXT,
    model_name         TEXT,
    correlation_id     TEXT,
    trace_id           TEXT,
    prompt_hash        TEXT,
    response_hash      TEXT,
    input_tokens       INTEGER,
    output_tokens      INTEGER,
    total_tokens       INTEGER,
    risk_score         REAL,
    risk_level         TEXT,
    risk_category      TEXT,
    policy_decision    TEXT,
    policy_reason      TEXT,
    duration_ms        REAL,
    success            INTEGER,
    error_code         TEXT,
    error_message      TEXT
)
"""

_INSERT = """
INSERT OR IGNORE INTO governai_events (
    event_id, timestamp_utc, application_name, environment_name,
    tenant_id, user_id, operation_name, agent_name,
    model_provider, model_name, correlation_id, trace_id,
    prompt_hash, response_hash, input_tokens, output_tokens, total_tokens,
    risk_score, risk_level, risk_category,
    policy_decision, policy_reason,
    duration_ms, success, error_code, error_message
) VALUES (
    ?,?,?,?,  ?,?,?,?,  ?,?,?,?,  ?,?,?,?,?,  ?,?,?,  ?,?,  ?,?,?,?
)
"""


class SqliteExporter:
    """GovernAI exporter that persists events to a SQLite database.

    Implements the GovernAIExporter protocol — no base class required.
    File I/O is offloaded to a thread so it does not block the event loop.

    Args:
        db_path: Path to the SQLite file. Created if it does not exist.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        # Create table synchronously at startup (one-time cost)
        with sqlite3.connect(self._db_path) as con:
            con.execute(_CREATE_TABLE)
            con.commit()

    async def export_async(self, event: GovernAIEvent) -> None:
        """Persist the event to SQLite (non-blocking)."""
        await asyncio.to_thread(self._insert, event)

    def _insert(self, event: GovernAIEvent) -> None:
        row = (
            event.event_id,
            event.timestamp_utc.isoformat(),
            event.application_name,
            event.environment_name,
            event.tenant_id,
            event.user_id,
            event.operation_name,
            event.agent_name,
            event.model_provider,
            event.model_name,
            event.correlation_id,
            event.trace_id,
            event.prompt_hash,
            event.response_hash,
            event.input_tokens,
            event.output_tokens,
            event.total_tokens,
            event.risk_score,
            event.risk_level.value,       # enum → string
            event.risk_category,
            event.policy_decision.value,  # enum → string
            event.policy_reason,
            event.duration_ms,
            int(event.success),
            event.error_code,
            event.error_message,
        )
        with sqlite3.connect(self._db_path) as con:
            con.execute(_INSERT, row)
            con.commit()
