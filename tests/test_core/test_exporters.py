"""Tests for GovernAI exporters.

Covers:
    - NoOpExporter: does nothing.
    - InMemoryExporter: stores, bounds, clears.
    - CompositeExporter: fan-out, error continuation, error re-raise.
    - ConsoleExporter: produces output.
    - FileExporter: writes JSON lines to file.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import unittest

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel
from governai.abstractions.models import GovernAIEvent
from governai.core.exporters import (
    CompositeExporter,
    ConsoleExporter,
    FileExporter,
    InMemoryExporter,
    NoOpExporter,
    _event_to_json_str,
)


def _make_event(event_id: str = "test-event") -> GovernAIEvent:
    return GovernAIEvent(event_id=event_id, application_name="TestApp")


class TestNoOpExporter(unittest.TestCase):
    """Tests for NoOpExporter."""

    def test_export_does_nothing(self) -> None:
        """NoOpExporter must complete without error."""
        exporter = NoOpExporter()
        asyncio.run(exporter.export_async(_make_event()))


class TestEventToJsonStr(unittest.TestCase):
    """Tests for the _event_to_json_str serialisation helper."""

    def test_produces_valid_json(self) -> None:
        """Serialised event must be valid JSON."""
        event = _make_event("json-test")
        result = _event_to_json_str(event)
        parsed = json.loads(result)
        self.assertEqual(parsed["event_id"], "json-test")

    def test_enum_values_serialised_as_strings(self) -> None:
        """Enum fields must be serialised to their string values."""
        event = GovernAIEvent(
            risk_level=GovernAIRiskLevel.HIGH,
            policy_decision=GovernAIPolicyDecisionType.DENY,
        )
        parsed = json.loads(_event_to_json_str(event))
        self.assertEqual(parsed["risk_level"], "HIGH")
        self.assertEqual(parsed["policy_decision"], "DENY")

    def test_timestamp_serialised_as_iso_string(self) -> None:
        """timestamp_utc must be serialised as an ISO 8601 string."""
        event = _make_event()
        parsed = json.loads(_event_to_json_str(event))
        self.assertIsInstance(parsed["timestamp_utc"], str)
        self.assertIn("T", parsed["timestamp_utc"])


class TestInMemoryExporter(unittest.TestCase):
    """Tests for InMemoryExporter."""

    def test_stores_exported_events(self) -> None:
        """Exported events must be retrievable via get_events."""
        exporter = InMemoryExporter()
        asyncio.run(exporter.export_async(_make_event("e1")))
        asyncio.run(exporter.export_async(_make_event("e2")))
        events = exporter.get_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_id, "e1")
        self.assertEqual(events[1].event_id, "e2")

    def test_respects_capacity_limit(self) -> None:
        """InMemoryExporter must discard oldest events when at capacity."""
        exporter = InMemoryExporter(capacity=3)
        for i in range(5):
            asyncio.run(exporter.export_async(_make_event(f"e{i}")))
        events = exporter.get_events()
        self.assertEqual(len(events), 3)
        # Oldest (e0, e1) should have been discarded
        ids = [e.event_id for e in events]
        self.assertNotIn("e0", ids)
        self.assertNotIn("e1", ids)
        self.assertIn("e4", ids)

    def test_clear_removes_all_events(self) -> None:
        """clear() must remove all stored events."""
        exporter = InMemoryExporter()
        asyncio.run(exporter.export_async(_make_event()))
        exporter.clear()
        self.assertEqual(len(exporter.get_events()), 0)

    def test_get_events_returns_snapshot(self) -> None:
        """get_events must return a list (snapshot), not the internal deque."""
        exporter = InMemoryExporter()
        asyncio.run(exporter.export_async(_make_event()))
        result = exporter.get_events()
        self.assertIsInstance(result, list)

    def test_concurrent_exports_are_safe(self) -> None:
        """Concurrent async exports must not lose events."""

        async def _run() -> None:
            exporter = InMemoryExporter(capacity=100)
            await asyncio.gather(*(exporter.export_async(_make_event(f"e{i}")) for i in range(50)))
            self.assertEqual(len(exporter.get_events()), 50)

        asyncio.run(_run())


class TestCompositeExporter(unittest.TestCase):
    """Tests for CompositeExporter."""

    def test_fans_out_to_all_exporters(self) -> None:
        """Event must be exported to all child exporters."""
        a = InMemoryExporter()
        b = InMemoryExporter()
        composite = CompositeExporter([a, b])
        asyncio.run(composite.export_async(_make_event("shared")))
        self.assertEqual(len(a.get_events()), 1)
        self.assertEqual(len(b.get_events()), 1)

    def test_continues_after_child_failure_when_not_fail_on_error(self) -> None:
        """When fail_on_error=False, failures in one exporter must not block others."""

        class _BrokenExporter:
            async def export_async(self, event: GovernAIEvent) -> None:
                raise RuntimeError("Simulated exporter failure")

        good = InMemoryExporter()
        composite = CompositeExporter([_BrokenExporter(), good], fail_on_error=False)  # type: ignore[list-item]
        asyncio.run(composite.export_async(_make_event()))
        # Good exporter must still have received the event
        self.assertEqual(len(good.get_events()), 1)

    def test_raises_on_child_failure_when_fail_on_error(self) -> None:
        """When fail_on_error=True, the first child exception must propagate."""

        class _BrokenExporter:
            async def export_async(self, event: GovernAIEvent) -> None:
                raise RuntimeError("Deliberate failure")

        composite = CompositeExporter([_BrokenExporter()], fail_on_error=True)  # type: ignore[list-item]
        with self.assertRaises(RuntimeError):
            asyncio.run(composite.export_async(_make_event()))

    def test_empty_exporters_list(self) -> None:
        """CompositeExporter with no children must complete without error."""
        composite = CompositeExporter([])
        asyncio.run(composite.export_async(_make_event()))


class TestConsoleExporter(unittest.TestCase):
    """Tests for ConsoleExporter."""

    def test_export_completes_without_error(self) -> None:
        """ConsoleExporter must complete without raising exceptions."""
        exporter = ConsoleExporter()
        asyncio.run(exporter.export_async(_make_event()))


class TestFileExporter(unittest.TestCase):
    """Tests for FileExporter."""

    def test_writes_json_line_to_file(self) -> None:
        """FileExporter must write a single JSON line per event."""
        with tempfile.NamedTemporaryFile(mode="r", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            exporter = FileExporter(path)
            asyncio.run(exporter.export_async(_make_event("file-test")))
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 1)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["event_id"], "file-test")
        finally:
            os.unlink(path)

    def test_appends_multiple_events(self) -> None:
        """FileExporter must append a new line for each event."""
        with tempfile.NamedTemporaryFile(mode="r", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            exporter = FileExporter(path)
            for i in range(3):
                asyncio.run(exporter.export_async(_make_event(f"e{i}")))
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 3)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
