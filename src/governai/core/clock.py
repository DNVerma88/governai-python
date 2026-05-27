"""GovernAI system clock implementation.

Provides the ``SystemClock`` concrete implementation of ``GovernAIClock``
that returns the real current UTC time.
"""

from __future__ import annotations

from datetime import datetime, timezone


class SystemClock:
    """Real-time UTC clock.

    Returns the current system time in UTC. Inject a test double
    implementing ``GovernAIClock`` to control time in unit tests.
    """

    @property
    def utc_now(self) -> datetime:
        """Return the current UTC time as a timezone-aware datetime.

        Returns:
            Current UTC time with ``timezone.utc`` tzinfo.
        """
        return datetime.now(timezone.utc)
