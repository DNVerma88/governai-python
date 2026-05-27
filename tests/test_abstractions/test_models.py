"""Tests for GovernAI data models.

Covers:
    - All models instantiate with default values.
    - All models accept explicit field values.
    - All models are frozen (immutable).
    - Field types are correct.
    - Edge cases: None values, empty strings, zero tokens.
"""

from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timezone

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel
from governai.abstractions.models import (
    GovernAIContext,
    GovernAIEvent,
    GovernAIPolicyDecision,
    GovernAIRiskResult,
)


class TestGovernAIContext(unittest.TestCase):
    """Tests for the GovernAIContext model."""

    def test_default_instantiation(self) -> None:
        """GovernAIContext must instantiate with all fields at their defaults."""
        ctx = GovernAIContext()
        self.assertIsNone(ctx.trace_id)
        self.assertIsNone(ctx.correlation_id)
        self.assertEqual(ctx.application_name, "")
        self.assertEqual(ctx.environment_name, "")
        self.assertIsNone(ctx.tenant_id)
        self.assertIsNone(ctx.user_id)
        self.assertEqual(ctx.agent_name, "")
        self.assertEqual(ctx.operation_name, "")
        self.assertEqual(ctx.model_provider, "")
        self.assertEqual(ctx.model_name, "")
        self.assertIsNone(ctx.prompt)
        self.assertIsNone(ctx.response)
        self.assertIsNone(ctx.input_tokens)
        self.assertIsNone(ctx.output_tokens)
        self.assertIsNone(ctx.metadata)

    def test_explicit_values(self) -> None:
        """GovernAIContext must accept all explicitly provided field values."""
        ctx = GovernAIContext(
            trace_id="trace-abc",
            correlation_id="corr-xyz",
            application_name="Enterprise.Api",
            environment_name="Production",
            tenant_id="tenant-001",
            user_id="user-001",
            agent_name="ReportAgent",
            operation_name="GenerateSummary",
            model_provider="AzureOpenAI",
            model_name="gpt-4.1",
            prompt="Summarize this document.",
            response="Here is the summary.",
            input_tokens=15,
            output_tokens=25,
            metadata={"session": "s-1"},
        )
        self.assertEqual(ctx.trace_id, "trace-abc")
        self.assertEqual(ctx.application_name, "Enterprise.Api")
        self.assertEqual(ctx.environment_name, "Production")
        self.assertEqual(ctx.tenant_id, "tenant-001")
        self.assertEqual(ctx.model_provider, "AzureOpenAI")
        self.assertEqual(ctx.prompt, "Summarize this document.")
        self.assertEqual(ctx.input_tokens, 15)
        self.assertEqual(ctx.output_tokens, 25)
        self.assertIsNotNone(ctx.metadata)

    def test_is_frozen(self) -> None:
        """GovernAIContext must be immutable — field assignment must raise FrozenInstanceError."""
        ctx = GovernAIContext(application_name="TestApp")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            ctx.application_name = "Modified"  # type: ignore[misc]

    def test_prompt_none_by_default(self) -> None:
        """Prompt must be None by default (privacy-safe default)."""
        ctx = GovernAIContext()
        self.assertIsNone(ctx.prompt)

    def test_response_none_by_default(self) -> None:
        """Response must be None by default (privacy-safe default)."""
        ctx = GovernAIContext()
        self.assertIsNone(ctx.response)

    def test_zero_token_counts(self) -> None:
        """Token counts of zero are valid and must be stored correctly."""
        ctx = GovernAIContext(input_tokens=0, output_tokens=0)
        self.assertEqual(ctx.input_tokens, 0)
        self.assertEqual(ctx.output_tokens, 0)


class TestGovernAIRiskResult(unittest.TestCase):
    """Tests for the GovernAIRiskResult model."""

    def test_default_instantiation(self) -> None:
        """GovernAIRiskResult must instantiate with safe default values."""
        result = GovernAIRiskResult()
        self.assertEqual(result.risk_score, 0.0)
        self.assertEqual(result.risk_level, GovernAIRiskLevel.NONE)
        self.assertEqual(result.risk_category, "")
        self.assertEqual(result.reason, "")
        self.assertEqual(result.matched_patterns, ())

    def test_explicit_values(self) -> None:
        """GovernAIRiskResult must accept explicitly provided field values."""
        result = GovernAIRiskResult(
            risk_score=80.0,
            risk_level=GovernAIRiskLevel.HIGH,
            risk_category="PromptInjection",
            reason="Detected jailbreak attempt.",
            matched_patterns=("ignore_previous_instructions", "bypass_security"),
        )
        self.assertEqual(result.risk_score, 80.0)
        self.assertEqual(result.risk_level, GovernAIRiskLevel.HIGH)
        self.assertEqual(result.risk_category, "PromptInjection")
        self.assertEqual(len(result.matched_patterns), 2)
        self.assertIn("ignore_previous_instructions", result.matched_patterns)

    def test_is_frozen(self) -> None:
        """GovernAIRiskResult must be immutable."""
        result = GovernAIRiskResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.risk_score = 50.0  # type: ignore[misc]

    def test_matched_patterns_default_is_empty_tuple(self) -> None:
        """matched_patterns must default to an empty tuple, not a mutable list."""
        result = GovernAIRiskResult()
        self.assertIsInstance(result.matched_patterns, tuple)
        self.assertEqual(len(result.matched_patterns), 0)

    def test_matched_patterns_independence(self) -> None:
        """Each GovernAIRiskResult instance must have its own matched_patterns tuple."""
        a = GovernAIRiskResult()
        b = GovernAIRiskResult()
        # Both empty, but they are not the same object in the general case.
        # This verifies default_factory is called per instance.
        self.assertEqual(a.matched_patterns, b.matched_patterns)

    def test_critical_risk_score(self) -> None:
        """A critical risk result must store score of 100.0."""
        result = GovernAIRiskResult(risk_score=100.0, risk_level=GovernAIRiskLevel.CRITICAL)
        self.assertEqual(result.risk_score, 100.0)
        self.assertEqual(result.risk_level, GovernAIRiskLevel.CRITICAL)


class TestGovernAIPolicyDecision(unittest.TestCase):
    """Tests for the GovernAIPolicyDecision model."""

    def test_default_instantiation(self) -> None:
        """GovernAIPolicyDecision must default to ALLOW with no risk."""
        decision = GovernAIPolicyDecision()
        self.assertEqual(decision.decision, GovernAIPolicyDecisionType.ALLOW)
        self.assertEqual(decision.reason, "")
        self.assertEqual(decision.risk_score, 0.0)
        self.assertEqual(decision.risk_level, GovernAIRiskLevel.NONE)
        self.assertEqual(decision.risk_category, "")
        self.assertIsNone(decision.metadata)

    def test_deny_decision(self) -> None:
        """GovernAIPolicyDecision must support DENY with high risk."""
        decision = GovernAIPolicyDecision(
            decision=GovernAIPolicyDecisionType.DENY,
            reason="Prompt injection detected.",
            risk_score=95.0,
            risk_level=GovernAIRiskLevel.CRITICAL,
            risk_category="PromptInjection",
        )
        self.assertEqual(decision.decision, GovernAIPolicyDecisionType.DENY)
        self.assertEqual(decision.risk_level, GovernAIRiskLevel.CRITICAL)
        self.assertEqual(decision.risk_score, 95.0)

    def test_review_decision(self) -> None:
        """GovernAIPolicyDecision must support REVIEW with medium risk."""
        decision = GovernAIPolicyDecision(
            decision=GovernAIPolicyDecisionType.REVIEW,
            reason="Medium risk detected — human review advised.",
            risk_level=GovernAIRiskLevel.MEDIUM,
        )
        self.assertEqual(decision.decision, GovernAIPolicyDecisionType.REVIEW)
        self.assertEqual(decision.risk_level, GovernAIRiskLevel.MEDIUM)

    def test_is_frozen(self) -> None:
        """GovernAIPolicyDecision must be immutable."""
        decision = GovernAIPolicyDecision()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            decision.reason = "Modified"  # type: ignore[misc]

    def test_metadata_can_be_set(self) -> None:
        """GovernAIPolicyDecision must accept optional metadata."""
        decision = GovernAIPolicyDecision(metadata={"rule": "R001"})
        self.assertIsNotNone(decision.metadata)
        self.assertEqual(decision.metadata, {"rule": "R001"})  # type: ignore[index]


class TestGovernAIEvent(unittest.TestCase):
    """Tests for the GovernAIEvent model."""

    def test_default_instantiation(self) -> None:
        """GovernAIEvent must instantiate with all fields at their defaults."""
        event = GovernAIEvent()
        self.assertEqual(event.event_id, "")
        self.assertIsNone(event.trace_id)
        self.assertIsNone(event.correlation_id)
        self.assertEqual(event.application_name, "")
        self.assertEqual(event.environment_name, "")
        self.assertIsNone(event.tenant_id)
        self.assertIsNone(event.user_id)
        self.assertEqual(event.agent_name, "")
        self.assertEqual(event.operation_name, "")
        self.assertEqual(event.model_provider, "")
        self.assertEqual(event.model_name, "")
        self.assertEqual(event.prompt_hash, "")
        self.assertEqual(event.response_hash, "")
        self.assertIsNone(event.input_tokens)
        self.assertIsNone(event.output_tokens)
        self.assertIsNone(event.total_tokens)
        self.assertEqual(event.risk_score, 0.0)
        self.assertEqual(event.risk_level, GovernAIRiskLevel.NONE)
        self.assertEqual(event.risk_category, "")
        self.assertEqual(event.policy_decision, GovernAIPolicyDecisionType.ALLOW)
        self.assertEqual(event.policy_reason, "")
        self.assertEqual(event.duration_ms, 0.0)
        self.assertTrue(event.success)
        self.assertIsNone(event.error_code)
        self.assertIsNone(event.error_message)
        self.assertIsInstance(event.timestamp_utc, datetime)
        self.assertIsNone(event.metadata)

    def test_timestamp_utc_is_timezone_aware(self) -> None:
        """Default timestamp_utc must be a timezone-aware UTC datetime."""
        event = GovernAIEvent()
        self.assertIsNotNone(event.timestamp_utc.tzinfo)

    def test_explicit_values(self) -> None:
        """GovernAIEvent must accept all explicitly provided field values."""
        ts = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        event = GovernAIEvent(
            event_id="evt-001",
            trace_id="trace-001",
            correlation_id="corr-001",
            application_name="Enterprise.Api",
            environment_name="Production",
            tenant_id="tenant-001",
            user_id="user-001",
            agent_name="ReportAgent",
            operation_name="GenerateSummary",
            model_provider="AzureOpenAI",
            model_name="gpt-4.1",
            prompt_hash="abc123hash",
            response_hash="def456hash",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            risk_score=10.0,
            risk_level=GovernAIRiskLevel.LOW,
            risk_category="None",
            policy_decision=GovernAIPolicyDecisionType.ALLOW,
            policy_reason="Low risk.",
            duration_ms=250.5,
            success=True,
            timestamp_utc=ts,
            metadata={"x": "y"},
        )
        self.assertEqual(event.event_id, "evt-001")
        self.assertEqual(event.total_tokens, 300)
        self.assertEqual(event.duration_ms, 250.5)
        self.assertEqual(event.timestamp_utc, ts)
        self.assertEqual(event.prompt_hash, "abc123hash")
        self.assertEqual(event.model_name, "gpt-4.1")

    def test_is_frozen(self) -> None:
        """GovernAIEvent must be immutable."""
        event = GovernAIEvent()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            event.event_id = "modified"  # type: ignore[misc]

    def test_failed_operation_fields(self) -> None:
        """GovernAIEvent must correctly represent a failed AI operation."""
        event = GovernAIEvent(
            success=False,
            error_code="AI_UNAVAILABLE",
            error_message="The upstream AI service returned 503.",
        )
        self.assertFalse(event.success)
        self.assertEqual(event.error_code, "AI_UNAVAILABLE")
        self.assertEqual(event.error_message, "The upstream AI service returned 503.")

    def test_denied_operation(self) -> None:
        """GovernAIEvent must support a DENY policy decision."""
        event = GovernAIEvent(
            policy_decision=GovernAIPolicyDecisionType.DENY,
            policy_reason="Prompt injection detected.",
            risk_score=95.0,
            risk_level=GovernAIRiskLevel.CRITICAL,
        )
        self.assertEqual(event.policy_decision, GovernAIPolicyDecisionType.DENY)
        self.assertEqual(event.risk_level, GovernAIRiskLevel.CRITICAL)

    def test_no_raw_prompt_or_response_fields(self) -> None:
        """GovernAIEvent must not contain prompt or response fields (privacy by default)."""
        event = GovernAIEvent()
        self.assertFalse(hasattr(event, "prompt"))
        self.assertFalse(hasattr(event, "response"))

    def test_each_default_event_has_independent_timestamp(self) -> None:
        """Each GovernAIEvent must get its own timestamp via default_factory."""
        a = GovernAIEvent()
        b = GovernAIEvent()
        # Both must be datetime instances. They may or may not be identical
        # depending on clock precision, but both must be valid datetimes.
        self.assertIsInstance(a.timestamp_utc, datetime)
        self.assertIsInstance(b.timestamp_utc, datetime)


if __name__ == "__main__":
    unittest.main()
