"""GovernAI protocol definitions.

This module defines the structural subtyping extension points for the
GovernAI SDK using ``typing.Protocol``. All protocols are marked
``@runtime_checkable`` to support ``isinstance`` checks in tests.

Implementing any of these protocols does not require inheriting from a
base class — structural duck-typing is sufficient. This approach keeps
implementations independent and testable in isolation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from governai.abstractions.models import GovernAIContext, GovernAIEvent, GovernAIPolicyDecision


@runtime_checkable
class GovernAIExporter(Protocol):
    """Protocol for GovernAI event exporters.

    Exporters receive governance audit events and forward them to a
    destination (console, file, in-memory store, HTTP collector, etc.).

    Implementations must be safe to call from async contexts and must
    not raise exceptions that propagate to the caller by default.
    """

    async def export_async(self, event: GovernAIEvent) -> None:
        """Export a GovernAI governance event to the configured destination.

        Args:
            event: The governance audit event to export.
        """
        ...


@runtime_checkable
class GovernAIPolicyEvaluator(Protocol):
    """Protocol for GovernAI policy evaluators.

    Policy evaluators inspect an AI operation context and return a
    governance decision indicating whether the operation should be
    allowed, reviewed, or denied.
    """

    async def evaluate_async(self, context: GovernAIContext) -> GovernAIPolicyDecision:
        """Evaluate the governance policy for an AI operation context.

        Args:
            context: The AI operation context describing the operation to evaluate.

        Returns:
            A ``GovernAIPolicyDecision`` indicating Allow, Review, or Deny.
        """
        ...


@runtime_checkable
class GovernAIRedactor(Protocol):
    """Protocol for GovernAI data redactors.

    Redactors scan text for sensitive data patterns and replace matched
    values with safe placeholders before hashing or logging.
    """

    def redact(self, input: str | None) -> str:
        """Redact sensitive data from the provided input string.

        Args:
            input: The text to scan and redact. Returns empty string if ``None``.

        Returns:
            The redacted text with sensitive values replaced by placeholders.
        """
        ...


@runtime_checkable
class GovernAITenantResolver(Protocol):
    """Protocol for GovernAI tenant resolvers.

    Tenant resolvers extract the tenant identifier from the current
    execution context (e.g., from an HTTP request header or JWT claim).
    Implementations typically read from a WSGI environ, JWT claim, or
    similar request-scoped source.
    """

    async def resolve_tenant_id_async(self, context: object) -> str | None:
        """Resolve the tenant ID for the current request context.

        Args:
            context: Optional operation context (``GovernAIContext`` or
                ``None``). Implementations may ignore this and read from
                a context variable (e.g., WSGI environ via ``ContextVar``).

        Returns:
            The tenant ID string, or ``None`` if the tenant cannot be resolved.
        """
        ...


@runtime_checkable
class GovernAIUserResolver(Protocol):
    """Protocol for GovernAI user resolvers.

    User resolvers extract the user identifier from the current
    execution context (e.g., from an HTTP request header or JWT claim).
    Implementations typically read from a WSGI environ, JWT claim, or
    similar request-scoped source.
    """

    async def resolve_user_id_async(self, context: object) -> str | None:
        """Resolve the user ID for the current request context.

        Args:
            context: Optional operation context (``GovernAIContext`` or
                ``None``). Implementations may ignore this and read from
                a context variable (e.g., WSGI environ via ``ContextVar``).

        Returns:
            The user ID string, or ``None`` if the user cannot be resolved.
        """
        ...


@runtime_checkable
class GovernAIClock(Protocol):
    """Protocol for GovernAI clock providers.

    Clock providers supply the current UTC time. Injecting a clock
    implementation via this protocol enables deterministic time control
    in unit tests.
    """

    @property
    def utc_now(self) -> datetime:
        """Get the current time in UTC.

        Returns:
            The current UTC datetime, preferably timezone-aware.
        """
        ...
