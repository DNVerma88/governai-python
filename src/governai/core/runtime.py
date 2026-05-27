"""GovernAI core runtime.

Provides ``GovernAIRuntime``, the public-facing facade that assembles
a ``GovernAITracker`` from configuration and exposes ``track_async``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from governai.abstractions.protocols import GovernAIClock, GovernAIExporter, GovernAIPolicyEvaluator, GovernAIRedactor
from governai.core.clock import SystemClock
from governai.core.exporters import CompositeExporter, FileExporter, NoOpExporter
from governai.core.hashing import PromptHasher, ResponseHasher
from governai.core.options import GovernAIOptions
from governai.core.policy import NoOpPolicyEvaluator
from governai.core.tracker import GovernAITracker
from governai.abstractions.models import GovernAIContext


class GovernAIRuntime:
    """Public façade for the GovernAI tracking engine.

    Assembles a ``GovernAITracker`` from the provided options and optional
    dependency overrides. Callers interact only with this class; internal
    details are hidden behind the tracker.

    Example usage::

        runtime = GovernAIRuntime(
            options=GovernAIOptions(application_name="MyApp"),
            exporter=ConsoleExporter(),
        )

        response = await runtime.track_async(
            context=context,
            operation=lambda: call_ai_async(prompt),
        )
    """

    def __init__(
        self,
        options: GovernAIOptions,
        exporter: GovernAIExporter | None = None,
        policy_evaluator: GovernAIPolicyEvaluator | None = None,
        clock: GovernAIClock | None = None,
        redactor: GovernAIRedactor | None = None,
    ) -> None:
        """Initialise the runtime.

        Args:
            options: Configuration controlling hashing, capture, and
                error handling.
            exporter: Event exporter. Defaults to ``NoOpExporter``.
            policy_evaluator: Policy evaluator. Defaults to
                ``NoOpPolicyEvaluator`` (always ALLOW).
            clock: Clock provider. Defaults to ``SystemClock``.
        """
        self._options = options

        # If file_exporter_path is set, compose FileExporter with the provided exporter.
        resolved_exporter: GovernAIExporter
        if options.file_exporter_path:
            file_exp: GovernAIExporter = FileExporter(options.file_exporter_path)
            base_exp = exporter or NoOpExporter()
            resolved_exporter = CompositeExporter([base_exp, file_exp])
        else:
            resolved_exporter = exporter or NoOpExporter()

        self._tracker = GovernAITracker(
            options=options,
            exporter=resolved_exporter,
            policy_evaluator=policy_evaluator or NoOpPolicyEvaluator(),
            clock=clock or SystemClock(),
            prompt_hasher=PromptHasher(),
            response_hasher=ResponseHasher(),
            redactor=redactor,
        )

    @property
    def options(self) -> GovernAIOptions:
        """Return the runtime configuration options.

        Returns:
            The ``GovernAIOptions`` used to initialise this runtime.
        """
        return self._options

    async def track_async(
        self,
        context: GovernAIContext,
        operation: Callable[[], Awaitable[str | None]],
    ) -> str | None:
        """Track an AI operation through the full governance lifecycle.

        Delegates to the internal ``GovernAITracker``. See
        ``GovernAITracker.track_async`` for full behavioural documentation.

        Args:
            context: Describes the AI operation being tracked.
            operation: Zero-argument async callable that performs the AI call.

        Returns:
            The AI response string, or ``None`` if denied or operation
            returned ``None``.

        Raises:
            Exception: Re-raises any exception thrown by ``operation``.
        """
        return await self._tracker.track_async(context, operation)
