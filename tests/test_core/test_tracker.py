"""Tests for GovernAITracker and GovernAIRuntime.

Covers:
    - Successful operation: event exported, response returned.
    - Failed operation: failure event exported, exception re-raised.
    - Policy DENY: operation skipped, denial event exported, None returned.
    - Policy REVIEW: operation still executes.
    - Prompt hashing is applied.
    - Response hashing is applied.
    - Total tokens calculated when both input/output provided.
    - Duration is captured (> 0 for real operations).
    - Exporter failure is suppressed when fail_on_exporter_error=False.
    - Exporter failure is raised when fail_on_exporter_error=True.
    - Raw prompts/responses are never stored in events.
"""

from __future__ import annotations

import asyncio
import hashlib
import unittest
from datetime import datetime, timezone

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel
from governai.abstractions.models import GovernAIContext, GovernAIEvent, GovernAIPolicyDecision
from governai.core.exporters import InMemoryExporter, NoOpExporter
from governai.core.hashing import PromptHasher, ResponseHasher
from governai.core.options import GovernAIOptions
from governai.core.policy import NoOpPolicyEvaluator
from governai.core.runtime import GovernAIRuntime
from governai.core.tracker import GovernAITracker


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _FixedClock:
    _TIME = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    @property
    def utc_now(self) -> datetime:
        return self._TIME


class _DenyAllEvaluator:
    async def evaluate_async(self, context: GovernAIContext) -> GovernAIPolicyDecision:
        return GovernAIPolicyDecision(
            decision=GovernAIPolicyDecisionType.DENY,
            reason="Always denied.",
            risk_level=GovernAIRiskLevel.CRITICAL,
            risk_score=100.0,
        )


class _ReviewAllEvaluator:
    async def evaluate_async(self, context: GovernAIContext) -> GovernAIPolicyDecision:
        return GovernAIPolicyDecision(
            decision=GovernAIPolicyDecisionType.REVIEW,
            reason="Always review.",
            risk_level=GovernAIRiskLevel.HIGH,
            risk_score=70.0,
        )


class _BrokenExporter:
    async def export_async(self, event: GovernAIEvent) -> None:
        raise RuntimeError("Exporter is broken")


def _make_tracker(
    exporter: InMemoryExporter | None = None,
    policy: object | None = None,
    options: GovernAIOptions | None = None,
) -> tuple[GovernAITracker, InMemoryExporter]:
    mem = exporter or InMemoryExporter()
    opts = options or GovernAIOptions(application_name="TestApp")
    tracker = GovernAITracker(
        options=opts,
        exporter=mem,
        policy_evaluator=policy or NoOpPolicyEvaluator(),  # type: ignore[arg-type]
        clock=_FixedClock(),  # type: ignore[arg-type]
        prompt_hasher=PromptHasher(),
        response_hasher=ResponseHasher(),
    )
    return tracker, mem


def _ctx(**kwargs: object) -> GovernAIContext:
    return GovernAIContext(application_name="TestApp", **kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# GovernAITracker tests
# ---------------------------------------------------------------------------


class TestGovernAITrackerSuccess(unittest.TestCase):
    """Tests for successful AI operation tracking."""

    def test_successful_operation_returns_response(self) -> None:
        """track_async must return the AI response on success."""

        async def _op() -> str:
            return "AI says hello"

        async def _run() -> None:
            tracker, _ = _make_tracker()
            result = await tracker.track_async(context=_ctx(prompt="Hello"), operation=_op)
            self.assertEqual(result, "AI says hello")

        asyncio.run(_run())

    def test_successful_operation_exports_event(self) -> None:
        """track_async must export exactly one event on success."""

        async def _op() -> str:
            return "response"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            await tracker.track_async(context=_ctx(), operation=_op)
            self.assertEqual(len(mem.get_events()), 1)

        asyncio.run(_run())

    def test_success_event_has_correct_fields(self) -> None:
        """Exported event on success must have success=True and ALLOW decision."""

        async def _op() -> str:
            return "response"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            await tracker.track_async(
                context=_ctx(
                    prompt="Hello AI",
                    tenant_id="tenant-1",
                    user_id="user-1",
                    input_tokens=10,
                    output_tokens=20,
                ),
                operation=_op,
            )
            event = mem.get_events()[0]
            self.assertTrue(event.success)
            self.assertEqual(event.policy_decision, GovernAIPolicyDecisionType.ALLOW)
            self.assertEqual(event.tenant_id, "tenant-1")
            self.assertEqual(event.user_id, "user-1")

        asyncio.run(_run())

    def test_event_id_is_populated(self) -> None:
        """Exported event must have a non-empty event_id."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            await tracker.track_async(context=_ctx(), operation=_op)
            self.assertTrue(len(mem.get_events()[0].event_id) > 0)

        asyncio.run(_run())

    def test_total_tokens_calculated(self) -> None:
        """total_tokens must equal input_tokens + output_tokens."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            await tracker.track_async(
                context=_ctx(input_tokens=15, output_tokens=25),
                operation=_op,
            )
            self.assertEqual(mem.get_events()[0].total_tokens, 40)

        asyncio.run(_run())

    def test_total_tokens_none_when_partial(self) -> None:
        """total_tokens must be None when only one token count is provided."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            await tracker.track_async(
                context=_ctx(input_tokens=10, output_tokens=None),
                operation=_op,
            )
            self.assertIsNone(mem.get_events()[0].total_tokens)

        asyncio.run(_run())


class TestGovernAITrackerHashing(unittest.TestCase):
    """Tests for prompt and response hashing behaviour."""

    def test_prompt_is_hashed(self) -> None:
        """Exported event must contain the SHA-256 hash of the prompt."""

        async def _op() -> str:
            return "response"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            prompt = "Hash me"
            expected_hash = hashlib.sha256(prompt.encode()).hexdigest()
            await tracker.track_async(context=_ctx(prompt=prompt), operation=_op)
            self.assertEqual(mem.get_events()[0].prompt_hash, expected_hash)

        asyncio.run(_run())

    def test_response_is_hashed(self) -> None:
        """Exported event must contain the SHA-256 hash of the response."""

        async def _op() -> str:
            return "Hash me too"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            expected_hash = hashlib.sha256("Hash me too".encode()).hexdigest()
            await tracker.track_async(context=_ctx(), operation=_op)
            self.assertEqual(mem.get_events()[0].response_hash, expected_hash)

        asyncio.run(_run())

    def test_raw_prompt_not_in_event(self) -> None:
        """GovernAIEvent must never contain raw prompt text."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            tracker, mem = _make_tracker()
            await tracker.track_async(context=_ctx(prompt="secret prompt"), operation=_op)
            event = mem.get_events()[0]
            self.assertFalse(hasattr(event, "prompt"))

        asyncio.run(_run())

    def test_hashing_disabled_leaves_hash_empty(self) -> None:
        """When hashing is disabled, prompt_hash and response_hash must be empty."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            opts = GovernAIOptions(
                enable_prompt_hashing=False,
                enable_response_hashing=False,
            )
            tracker, mem = _make_tracker(options=opts)
            await tracker.track_async(context=_ctx(prompt="test"), operation=_op)
            event = mem.get_events()[0]
            self.assertEqual(event.prompt_hash, "")
            self.assertEqual(event.response_hash, "")

        asyncio.run(_run())


class TestGovernAITrackerFailure(unittest.TestCase):
    """Tests for failed AI operation handling."""

    def test_failed_operation_re_raises(self) -> None:
        """track_async must re-raise the operation exception."""

        async def _failing_op() -> str:
            raise ValueError("AI service unavailable")

        async def _run() -> None:
            tracker, _ = _make_tracker()
            with self.assertRaises(ValueError):
                await tracker.track_async(context=_ctx(), operation=_failing_op)

        asyncio.run(_run())

    def test_failed_operation_still_exports_event(self) -> None:
        """A failure event must be exported even when the operation raises."""

        async def _failing_op() -> str:
            raise RuntimeError("Boom")

        async def _run() -> None:
            tracker, mem = _make_tracker()
            try:
                await tracker.track_async(context=_ctx(), operation=_failing_op)
            except RuntimeError:
                pass
            events = mem.get_events()
            self.assertEqual(len(events), 1)
            self.assertFalse(events[0].success)
            self.assertEqual(events[0].error_code, "RuntimeError")

        asyncio.run(_run())

    def test_duration_captured_on_failure(self) -> None:
        """Duration must be captured even when the operation fails."""

        async def _failing_op() -> str:
            raise RuntimeError("fail")

        async def _run() -> None:
            tracker, mem = _make_tracker()
            try:
                await tracker.track_async(context=_ctx(), operation=_failing_op)
            except RuntimeError:
                pass
            self.assertGreaterEqual(mem.get_events()[0].duration_ms, 0.0)

        asyncio.run(_run())


class TestGovernAITrackerPolicy(unittest.TestCase):
    """Tests for policy evaluation integration."""

    def test_deny_skips_operation(self) -> None:
        """When policy is DENY, the operation callable must not be invoked."""
        called = []

        async def _op() -> str:
            called.append(True)
            return "should not execute"

        async def _run() -> None:
            tracker, mem = _make_tracker(policy=_DenyAllEvaluator())
            result = await tracker.track_async(context=_ctx(), operation=_op)
            self.assertIsNone(result)
            self.assertEqual(len(called), 0)

        asyncio.run(_run())

    def test_deny_exports_denial_event(self) -> None:
        """Policy DENY must export an event with DENY decision."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            tracker, mem = _make_tracker(policy=_DenyAllEvaluator())
            await tracker.track_async(context=_ctx(), operation=_op)
            event = mem.get_events()[0]
            self.assertEqual(event.policy_decision, GovernAIPolicyDecisionType.DENY)
            self.assertTrue(event.success)  # denial is not a failure

        asyncio.run(_run())

    def test_review_still_executes_operation(self) -> None:
        """Policy REVIEW must still execute the operation."""
        called = []

        async def _op() -> str:
            called.append(True)
            return "reviewed response"

        async def _run() -> None:
            tracker, mem = _make_tracker(policy=_ReviewAllEvaluator())
            result = await tracker.track_async(context=_ctx(), operation=_op)
            self.assertEqual(result, "reviewed response")
            self.assertEqual(len(called), 1)
            self.assertEqual(mem.get_events()[0].policy_decision, GovernAIPolicyDecisionType.REVIEW)

        asyncio.run(_run())


class TestGovernAITrackerExporterErrors(unittest.TestCase):
    """Tests for exporter error handling in GovernAITracker."""

    def test_exporter_error_suppressed_by_default(self) -> None:
        """Exporter exceptions must not propagate when fail_on_exporter_error=False."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            opts = GovernAIOptions(fail_on_exporter_error=False)
            tracker = GovernAITracker(
                options=opts,
                exporter=_BrokenExporter(),  # type: ignore[arg-type]
                policy_evaluator=NoOpPolicyEvaluator(),
                clock=_FixedClock(),  # type: ignore[arg-type]
                prompt_hasher=PromptHasher(),
                response_hasher=ResponseHasher(),
            )
            # Must not raise
            result = await tracker.track_async(context=_ctx(), operation=_op)
            self.assertEqual(result, "r")

        asyncio.run(_run())

    def test_exporter_error_raised_when_configured(self) -> None:
        """Exporter exceptions must propagate when fail_on_exporter_error=True."""

        async def _op() -> str:
            return "r"

        async def _run() -> None:
            opts = GovernAIOptions(fail_on_exporter_error=True)
            tracker = GovernAITracker(
                options=opts,
                exporter=_BrokenExporter(),  # type: ignore[arg-type]
                policy_evaluator=NoOpPolicyEvaluator(),
                clock=_FixedClock(),  # type: ignore[arg-type]
                prompt_hasher=PromptHasher(),
                response_hasher=ResponseHasher(),
            )
            with self.assertRaises(RuntimeError):
                await tracker.track_async(context=_ctx(), operation=_op)

        asyncio.run(_run())


class TestGovernAIRuntime(unittest.TestCase):
    """Tests for GovernAIRuntime facade."""

    def test_runtime_delegates_to_tracker(self) -> None:
        """GovernAIRuntime.track_async must return the operation result."""

        async def _op() -> str:
            return "runtime response"

        async def _run() -> None:
            mem = InMemoryExporter()
            runtime = GovernAIRuntime(
                options=GovernAIOptions(application_name="TestApp"),
                exporter=mem,
            )
            result = await runtime.track_async(
                context=GovernAIContext(application_name="TestApp"),
                operation=_op,
            )
            self.assertEqual(result, "runtime response")
            self.assertEqual(len(mem.get_events()), 1)

        asyncio.run(_run())

    def test_runtime_options_accessible(self) -> None:
        """GovernAIRuntime.options must return the configured options."""
        opts = GovernAIOptions(application_name="MyApp")
        runtime = GovernAIRuntime(options=opts)
        self.assertIs(runtime.options, opts)


if __name__ == "__main__":
    unittest.main()
