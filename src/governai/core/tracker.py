"""GovernAI core tracker.

The ``GovernAITracker`` is the central engine that orchestrates policy
evaluation, AI operation execution, event creation, and exporting.
"""

from __future__ import annotations

import dataclasses
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from governai.abstractions.enums import GovernAIPolicyDecisionType
from governai.abstractions.models import GovernAIContext, GovernAIEvent, GovernAIPolicyDecision
from governai.abstractions.protocols import GovernAIClock, GovernAIExporter, GovernAIPolicyEvaluator, GovernAIRedactor
from governai.core.hashing import PromptHasher, ResponseHasher
from governai.core.options import GovernAIOptions

_logger = logging.getLogger(__name__)

# Maximum characters retained in sanitised error messages.
_MAX_ERROR_MESSAGE_LEN = 500


class GovernAITracker:
    """Core AI operation tracker.

    Orchestrates the full governance lifecycle for each tracked operation:

    1. Evaluate policy via the configured ``GovernAIPolicyEvaluator``.
    2. Skip execution if the decision is ``DENY``.
    3. Execute the operation and measure wall-clock duration.
    4. Hash prompt and response (raw values are never stored).
    5. Build and export a ``GovernAIEvent``.
    6. Re-raise operation exceptions after the event is exported.

    Dependencies are injected via the constructor to support unit testing.
    """

    def __init__(
        self,
        options: GovernAIOptions,
        exporter: GovernAIExporter,
        policy_evaluator: GovernAIPolicyEvaluator,
        clock: GovernAIClock,
        prompt_hasher: PromptHasher,
        response_hasher: ResponseHasher,
        redactor: GovernAIRedactor | None = None,
    ) -> None:
        """Initialise the tracker with its dependencies.

        Args:
            options: Runtime configuration controlling hashing, capture, and
                error handling behaviour.
            exporter: Destination for governance audit events.
            policy_evaluator: Evaluates whether operations should be
                allowed, reviewed, or denied.
            clock: Provides the current UTC time for event timestamps.
            prompt_hasher: Hashes raw prompt text.
            response_hasher: Hashes raw response text.
        """
        self._options = options
        self._exporter = exporter
        self._policy_evaluator = policy_evaluator
        self._clock = clock
        self._prompt_hasher = prompt_hasher
        self._response_hasher = response_hasher
        self._redactor = redactor

    async def track_async(
        self,
        context: GovernAIContext,
        operation: Callable[[], Awaitable[str | None]],
    ) -> str | None:
        """Track an AI operation through the full governance lifecycle.

        Evaluates policy, executes the operation (unless denied), hashes
        prompt and response, builds a ``GovernAIEvent``, and exports it.

        Args:
            context: Describes the AI operation including prompt, model,
                tenant, and correlation metadata.
            operation: Zero-argument async callable that performs the AI call.
                Must return the response text, or ``None``.

        Returns:
            The AI response string, or ``None`` if the operation was denied
            or the operation itself returned ``None``.

        Raises:
            Exception: Re-raises any exception thrown by ``operation`` after
                the failure event has been exported.
        """
        # Truncate the prompt before policy scanning to prevent CPU exhaustion
        # from adversarially large inputs.  Hashing always uses the full prompt.
        max_len = self._options.max_prompt_scan_len
        scan_context = context
        if max_len > 0 and context.prompt and len(context.prompt) > max_len:
            scan_context = dataclasses.replace(context, prompt=context.prompt[:max_len])
            _logger.warning(
                "GovernAI: prompt truncated from %d to %d chars for policy scan",
                len(context.prompt),
                max_len,
            )

        decision = await self._policy_evaluator.evaluate_async(scan_context)

        if decision.decision == GovernAIPolicyDecisionType.DENY:
            event = self._build_event(
                context=context,
                decision=decision,
                response=None,
                duration_ms=0.0,
                success=True,
                error_code=None,
                error_message=None,
            )
            await self._safe_export(event)
            return None

        start_mono = time.monotonic()
        response: str | None = None
        success = True
        error_code: str | None = None
        error_message: str | None = None
        caught_exc: BaseException | None = None

        try:
            response = await operation()
        except Exception as exc:
            success = False
            error_code = type(exc).__name__
            raw_error = str(exc)[:_MAX_ERROR_MESSAGE_LEN]
            # Redact the error message in case the AI provider has embedded
            # secrets (API keys, bearer tokens) in the exception text.
            error_message = self._redactor.redact(raw_error) if self._redactor is not None else raw_error
            caught_exc = exc

        duration_ms = (time.monotonic() - start_mono) * 1000.0

        event = self._build_event(
            context=context,
            decision=decision,
            response=response,
            duration_ms=duration_ms,
            success=success,
            error_code=error_code,
            error_message=error_message,
        )
        await self._safe_export(event)

        if caught_exc is not None:
            raise caught_exc

        return response

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_event(
        self,
        context: GovernAIContext,
        decision: GovernAIPolicyDecision,
        response: str | None,
        duration_ms: float,
        success: bool,
        error_code: str | None,
        error_message: str | None,
    ) -> GovernAIEvent:
        """Construct a ``GovernAIEvent`` from tracking data.

        Args:
            context: Original operation context.
            decision: Policy evaluation result.
            response: AI response text (used for hashing only).
            duration_ms: Measured duration of the AI call.
            success: Whether the operation completed without exception.
            error_code: Exception class name on failure.
            error_message: Sanitised exception message on failure.

        Returns:
            A fully populated ``GovernAIEvent``.
        """
        prompt_hash = ""
        if self._options.enable_prompt_hashing:
            prompt_hash = self._prompt_hasher.hash(context.prompt)

        response_hash = ""
        if self._options.enable_response_hashing:
            response_hash = self._response_hasher.hash(response)

        total_tokens: int | None = None
        if context.input_tokens is not None and context.output_tokens is not None:
            total_tokens = context.input_tokens + context.output_tokens

        app_name = context.application_name or self._options.application_name
        env_name = context.environment_name or self._options.environment_name

        return GovernAIEvent(
            event_id=uuid.uuid4().hex,
            trace_id=context.trace_id,
            correlation_id=context.correlation_id,
            application_name=app_name,
            environment_name=env_name,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            agent_name=context.agent_name,
            operation_name=context.operation_name,
            model_provider=context.model_provider,
            model_name=context.model_name,
            prompt_hash=prompt_hash,
            response_hash=response_hash,
            input_tokens=context.input_tokens,
            output_tokens=context.output_tokens,
            total_tokens=total_tokens,
            risk_score=decision.risk_score,
            risk_level=decision.risk_level,
            risk_category=decision.risk_category,
            policy_decision=decision.decision,
            policy_reason=decision.reason,
            duration_ms=duration_ms,
            success=success,
            error_code=error_code,
            error_message=error_message,
            timestamp_utc=self._clock.utc_now,
            metadata=context.metadata,
        )

    async def _safe_export(self, event: GovernAIEvent) -> None:
        """Export an event, suppressing errors when configured to do so.

        Args:
            event: The governance event to export.

        Raises:
            Exception: Re-raises exporter exceptions when
                ``options.fail_on_exporter_error`` is ``True``.
        """
        try:
            await self._exporter.export_async(event)
        except Exception as exc:
            if self._options.fail_on_exporter_error:
                raise
            _logger.warning("GovernAI exporter error (suppressed): %s", exc)
