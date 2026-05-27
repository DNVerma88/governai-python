"""GovernAI event exporters.

Provides concrete exporter implementations:
- ``NoOpExporter``: Discards all events.
- ``CompositeExporter``: Fans out to multiple exporters.
- ``InMemoryExporter``: Stores events in a bounded in-memory buffer.
- ``ConsoleExporter``: Writes events as JSON to stdout.
- ``FileExporter``: Writes events as JSON Lines to a file.
"""

from __future__ import annotations

import asyncio
import collections
import dataclasses
import json
import logging
import os
import threading
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any

from governai.abstractions.models import GovernAIEvent
from governai.abstractions.protocols import GovernAIExporter

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _serialize_value(obj: Any) -> Any:
    """Recursively convert non-JSON-serialisable values to serialisable form."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_value(i) for i in obj]
    return obj


def _event_to_json_str(event: GovernAIEvent) -> str:
    """Serialise a ``GovernAIEvent`` to a JSON string.

    Args:
        event: The event to serialise.

    Returns:
        A compact JSON string representation of the event.
    """
    raw: dict[str, Any] = dataclasses.asdict(event)
    return json.dumps(_serialize_value(raw), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------


class NoOpExporter:
    """Exporter that silently discards all events.

    Used as the default when no exporter is configured or when event
    collection is explicitly disabled.
    """

    async def export_async(self, event: GovernAIEvent) -> None:
        """Discard the event without any action.

        Args:
            event: The governance event (ignored).
        """


class CompositeExporter:
    """Exporter that fans out to multiple child exporters.

    Iterates over all configured exporters in order. If a child exporter
    raises an exception and ``fail_on_error`` is ``False`` (default), the
    exception is logged and the remaining exporters are still called.
    When ``fail_on_error`` is ``True``, the first exception is re-raised
    immediately.

    Attributes:
        exporters: Ordered sequence of child exporters to fan out to.
        fail_on_error: When ``True``, re-raise the first exporter exception.
    """

    def __init__(
        self,
        exporters: list[GovernAIExporter],
        fail_on_error: bool = False,
    ) -> None:
        """Initialise the composite exporter.

        Args:
            exporters: Child exporters to call for each event.
            fail_on_error: Re-raise on first child exporter failure.
        """
        self._exporters: list[GovernAIExporter] = list(exporters)
        self._fail_on_error = fail_on_error

    async def export_async(self, event: GovernAIEvent) -> None:
        """Export the event to all configured child exporters.

        Args:
            event: The governance event to export.

        Raises:
            Exception: Re-raises the first child exception when
                ``fail_on_error`` is ``True``.
        """
        for exporter in self._exporters:
            try:
                await exporter.export_async(event)
            except Exception as exc:
                if self._fail_on_error:
                    raise
                _logger.warning("GovernAI child exporter failed: %s", exc)


class InMemoryExporter:
    """Exporter that stores events in a bounded in-memory ring buffer.

    Thread-safe. Older events are automatically discarded when the buffer
    reaches ``capacity``. Suitable for testing and local development.

    Attributes:
        capacity: Maximum number of events held before old ones are discarded.
    """

    def __init__(self, capacity: int = 1000) -> None:
        """Initialise the in-memory exporter.

        Args:
            capacity: Maximum number of events to retain. Defaults to 1000.
        """
        self._events: deque[GovernAIEvent] = collections.deque(maxlen=capacity)
        self._lock = threading.Lock()

    async def export_async(self, event: GovernAIEvent) -> None:
        """Append the event to the in-memory buffer.

        Args:
            event: The governance event to store.
        """
        with self._lock:
            self._events.append(event)

    def get_events(self) -> list[GovernAIEvent]:
        """Return a snapshot of all currently stored events.

        Returns:
            A list of stored ``GovernAIEvent`` instances, oldest first.
        """
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        """Remove all stored events from the buffer."""
        with self._lock:
            self._events.clear()


class ConsoleExporter:
    """Exporter that writes events as JSON to standard output.

    Each event is printed as a single-line compact JSON string.
    Intended for local development and debugging.
    """

    async def export_async(self, event: GovernAIEvent) -> None:
        """Write the event as JSON to stdout.

        Args:
            event: The governance event to print.
        """
        print(_event_to_json_str(event))


class FileExporter:
    """Exporter that appends events as JSON Lines to a file.

    Each event is written as one JSON object per line (JSONL format).
    File I/O is offloaded to a thread via ``asyncio.to_thread`` to avoid
    blocking the event loop. Concurrent writes are serialised with an
    ``asyncio.Lock``.

    Attributes:
        file_path: Absolute or relative path to the output file.
    """

    def __init__(self, file_path: str) -> None:
        """Initialise the file exporter.

        Args:
            file_path: Path to the JSONL output file. Created if absent;
                events are appended if the file already exists. The path
                is resolved to an absolute path at construction time.
        """
        self._file_path = os.path.abspath(file_path)
        self._lock = asyncio.Lock()

    async def export_async(self, event: GovernAIEvent) -> None:
        """Append the event as a JSON line to the configured file.

        Args:
            event: The governance event to write.
        """
        line = _event_to_json_str(event) + "\n"
        async with self._lock:
            await asyncio.to_thread(self._append_line, line)

    def _append_line(self, line: str) -> None:
        """Write a single line to the output file (blocking).

        Args:
            line: The JSON line (including trailing newline) to append.
        """
        with open(self._file_path, "a", encoding="utf-8") as f:
            f.write(line)
