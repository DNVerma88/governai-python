"""Tests for GovernAI protocol definitions.

Covers:
    - Concrete classes satisfying each protocol via isinstance checks.
    - Protocol methods callable and returning correct types.
    - Edge cases: None inputs for redactor.
    - Async protocol methods work correctly with asyncio.run.
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timezone

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel
from governai.abstractions.models import (
    GovernAIContext,
    GovernAIEvent,
    GovernAIPolicyDecision,
)
from governai.abstractions.protocols import (
    GovernAIClock,
    GovernAIExporter,
    GovernAIPolicyEvaluator,
    GovernAIRedactor,
    GovernAITenantResolver,
    GovernAIUserResolver,
)

# ---------------------------------------------------------------------------
# Concrete test implementations
# ---------------------------------------------------------------------------


class _RecordingExporter:
    """Minimal GovernAIExporter implementation that records exported events."""

    def __init__(self) -> None:
        self.events: list[GovernAIEvent] = []

    async def export_async(self, event: GovernAIEvent) -> None:
        self.events.append(event)


class _AllowAllPolicyEvaluator:
    """Minimal GovernAIPolicyEvaluator that always returns ALLOW."""

    async def evaluate_async(self, context: GovernAIContext) -> GovernAIPolicyDecision:
        return GovernAIPolicyDecision(decision=GovernAIPolicyDecisionType.ALLOW)


class _DenyAllPolicyEvaluator:
    """Minimal GovernAIPolicyEvaluator that always returns DENY."""

    async def evaluate_async(self, context: GovernAIContext) -> GovernAIPolicyDecision:
        return GovernAIPolicyDecision(
            decision=GovernAIPolicyDecisionType.DENY,
            reason="Always denied.",
            risk_level=GovernAIRiskLevel.CRITICAL,
        )


class _PassThroughRedactor:
    """Minimal GovernAIRedactor that returns input unchanged."""

    def redact(self, input: str | None) -> str:
        return input if input is not None else ""


class _FixedTenantResolver:
    """Minimal GovernAITenantResolver that returns a fixed tenant ID."""

    async def resolve_tenant_id_async(self, context: object) -> str | None:
        return "tenant-fixed"


class _NullTenantResolver:
    """Minimal GovernAITenantResolver that returns None."""

    async def resolve_tenant_id_async(self, context: object) -> str | None:
        return None


class _FixedUserResolver:
    """Minimal GovernAIUserResolver that returns a fixed user ID."""

    async def resolve_user_id_async(self, context: object) -> str | None:
        return "user-fixed"


class _NullUserResolver:
    """Minimal GovernAIUserResolver that returns None."""

    async def resolve_user_id_async(self, context: object) -> str | None:
        return None


class _FixedClock:
    """Minimal GovernAIClock that returns a fixed UTC datetime."""

    _FIXED_TIME = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    @property
    def utc_now(self) -> datetime:
        return self._FIXED_TIME


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGovernAIExporterProtocol(unittest.TestCase):
    """Tests for the GovernAIExporter protocol."""

    def test_concrete_class_is_instance(self) -> None:
        """_RecordingExporter must satisfy isinstance check for GovernAIExporter."""
        exporter = _RecordingExporter()
        self.assertIsInstance(exporter, GovernAIExporter)

    def test_export_async_called_once(self) -> None:
        """export_async must be called and the event must be recorded."""
        exporter = _RecordingExporter()
        event = GovernAIEvent(event_id="evt-001", application_name="TestApp")
        asyncio.run(exporter.export_async(event))
        self.assertEqual(len(exporter.events), 1)
        self.assertEqual(exporter.events[0].event_id, "evt-001")

    def test_export_async_called_multiple_times(self) -> None:
        """export_async must accumulate all exported events."""
        exporter = _RecordingExporter()
        for i in range(5):
            asyncio.run(exporter.export_async(GovernAIEvent(event_id=f"evt-{i}")))
        self.assertEqual(len(exporter.events), 5)

    def test_non_conforming_class_not_instance(self) -> None:
        """An object without export_async must not satisfy GovernAIExporter."""

        class _NoMethods:
            pass

        self.assertNotIsInstance(_NoMethods(), GovernAIExporter)


class TestGovernAIPolicyEvaluatorProtocol(unittest.TestCase):
    """Tests for the GovernAIPolicyEvaluator protocol."""

    def test_allow_evaluator_is_instance(self) -> None:
        """_AllowAllPolicyEvaluator must satisfy isinstance check."""
        evaluator = _AllowAllPolicyEvaluator()
        self.assertIsInstance(evaluator, GovernAIPolicyEvaluator)

    def test_deny_evaluator_is_instance(self) -> None:
        """_DenyAllPolicyEvaluator must satisfy isinstance check."""
        evaluator = _DenyAllPolicyEvaluator()
        self.assertIsInstance(evaluator, GovernAIPolicyEvaluator)

    def test_allow_evaluator_returns_allow(self) -> None:
        """evaluate_async must return ALLOW for the allow-all evaluator."""
        evaluator = _AllowAllPolicyEvaluator()
        ctx = GovernAIContext(application_name="TestApp", operation_name="GenerateSummary")
        decision = asyncio.run(evaluator.evaluate_async(ctx))
        self.assertIsInstance(decision, GovernAIPolicyDecision)
        self.assertEqual(decision.decision, GovernAIPolicyDecisionType.ALLOW)

    def test_deny_evaluator_returns_deny(self) -> None:
        """evaluate_async must return DENY for the deny-all evaluator."""
        evaluator = _DenyAllPolicyEvaluator()
        ctx = GovernAIContext()
        decision = asyncio.run(evaluator.evaluate_async(ctx))
        self.assertEqual(decision.decision, GovernAIPolicyDecisionType.DENY)
        self.assertEqual(decision.risk_level, GovernAIRiskLevel.CRITICAL)

    def test_non_conforming_class_not_instance(self) -> None:
        """An object without evaluate_async must not satisfy GovernAIPolicyEvaluator."""

        class _NoMethods:
            pass

        self.assertNotIsInstance(_NoMethods(), GovernAIPolicyEvaluator)


class TestGovernAIRedactorProtocol(unittest.TestCase):
    """Tests for the GovernAIRedactor protocol."""

    def test_concrete_class_is_instance(self) -> None:
        """_PassThroughRedactor must satisfy isinstance check for GovernAIRedactor."""
        redactor = _PassThroughRedactor()
        self.assertIsInstance(redactor, GovernAIRedactor)

    def test_redact_returns_string_for_text_input(self) -> None:
        """redact must return a string when given a non-None input."""
        redactor = _PassThroughRedactor()
        result = redactor.redact("Hello world")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "Hello world")

    def test_redact_returns_empty_string_for_none(self) -> None:
        """redact must return an empty string when given None input."""
        redactor = _PassThroughRedactor()
        result = redactor.redact(None)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "")

    def test_redact_handles_empty_string(self) -> None:
        """redact must handle an empty string input correctly."""
        redactor = _PassThroughRedactor()
        result = redactor.redact("")
        self.assertEqual(result, "")

    def test_non_conforming_class_not_instance(self) -> None:
        """An object without redact must not satisfy GovernAIRedactor."""

        class _NoMethods:
            pass

        self.assertNotIsInstance(_NoMethods(), GovernAIRedactor)


class TestGovernAITenantResolverProtocol(unittest.TestCase):
    """Tests for the GovernAITenantResolver protocol."""

    def test_fixed_resolver_is_instance(self) -> None:
        """_FixedTenantResolver must satisfy isinstance check."""
        resolver = _FixedTenantResolver()
        self.assertIsInstance(resolver, GovernAITenantResolver)

    def test_null_resolver_is_instance(self) -> None:
        """_NullTenantResolver must satisfy isinstance check."""
        resolver = _NullTenantResolver()
        self.assertIsInstance(resolver, GovernAITenantResolver)

    def test_fixed_resolver_returns_tenant_id(self) -> None:
        """resolve_tenant_id_async must return the configured tenant ID."""
        resolver = _FixedTenantResolver()
        result = asyncio.run(resolver.resolve_tenant_id_async(None))
        self.assertEqual(result, "tenant-fixed")

    def test_null_resolver_returns_none(self) -> None:
        """resolve_tenant_id_async must return None when tenant is unavailable."""
        resolver = _NullTenantResolver()
        result = asyncio.run(resolver.resolve_tenant_id_async(None))
        self.assertIsNone(result)

    def test_non_conforming_class_not_instance(self) -> None:
        """An object without resolve_tenant_id_async must not satisfy GovernAITenantResolver."""

        class _NoMethods:
            pass

        self.assertNotIsInstance(_NoMethods(), GovernAITenantResolver)


class TestGovernAIUserResolverProtocol(unittest.TestCase):
    """Tests for the GovernAIUserResolver protocol."""

    def test_fixed_resolver_is_instance(self) -> None:
        """_FixedUserResolver must satisfy isinstance check."""
        resolver = _FixedUserResolver()
        self.assertIsInstance(resolver, GovernAIUserResolver)

    def test_null_resolver_is_instance(self) -> None:
        """_NullUserResolver must satisfy isinstance check."""
        resolver = _NullUserResolver()
        self.assertIsInstance(resolver, GovernAIUserResolver)

    def test_fixed_resolver_returns_user_id(self) -> None:
        """resolve_user_id_async must return the configured user ID."""
        resolver = _FixedUserResolver()
        result = asyncio.run(resolver.resolve_user_id_async(None))
        self.assertEqual(result, "user-fixed")

    def test_null_resolver_returns_none(self) -> None:
        """resolve_user_id_async must return None when user is unavailable."""
        resolver = _NullUserResolver()
        result = asyncio.run(resolver.resolve_user_id_async(None))
        self.assertIsNone(result)

    def test_non_conforming_class_not_instance(self) -> None:
        """An object without resolve_user_id_async must not satisfy GovernAIUserResolver."""

        class _NoMethods:
            pass

        self.assertNotIsInstance(_NoMethods(), GovernAIUserResolver)


class TestGovernAIClockProtocol(unittest.TestCase):
    """Tests for the GovernAIClock protocol."""

    def test_concrete_class_is_instance(self) -> None:
        """_FixedClock must satisfy isinstance check for GovernAIClock."""
        clock = _FixedClock()
        self.assertIsInstance(clock, GovernAIClock)

    def test_utc_now_returns_datetime(self) -> None:
        """utc_now must return a datetime instance."""
        clock = _FixedClock()
        self.assertIsInstance(clock.utc_now, datetime)

    def test_utc_now_returns_expected_fixed_value(self) -> None:
        """utc_now must return the exact fixed time from _FixedClock."""
        clock = _FixedClock()
        expected = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(clock.utc_now, expected)

    def test_utc_now_is_timezone_aware(self) -> None:
        """utc_now from _FixedClock must include timezone info."""
        clock = _FixedClock()
        self.assertIsNotNone(clock.utc_now.tzinfo)

    def test_non_conforming_class_not_instance(self) -> None:
        """An object without utc_now property must not satisfy GovernAIClock."""

        class _NoProperties:
            pass

        self.assertNotIsInstance(_NoProperties(), GovernAIClock)


if __name__ == "__main__":
    unittest.main()
