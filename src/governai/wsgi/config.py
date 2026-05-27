"""GovernAI WSGI configuration.

Provides ``GovernAIConfig``, the configuration dataclass for
``GovernAIMiddleware``. All fields default to safe no-op implementations
from the ``governai.core`` package so that users only need to specify
the fields they want to customise.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from governai.abstractions.protocols import (
    GovernAIClock,
    GovernAIExporter,
    GovernAIPolicyEvaluator,
    GovernAIRedactor,
    GovernAITenantResolver,
    GovernAIUserResolver,
)
from governai.core.clock import SystemClock
from governai.core.exporters import NoOpExporter
from governai.core.options import GovernAIOptions
from governai.core.policy import NoOpPolicyEvaluator
from governai.core.runtime import GovernAIRuntime


@dataclasses.dataclass
class GovernAIConfig:
    """Configuration for ``GovernAIMiddleware``.

    All fields that accept a governance component default to a safe
    no-op implementation. Only ``application_name`` and
    ``environment_name`` need to be provided for basic usage.

    Attributes:
        application_name: Logical name of the application.
            Propagated to ``GovernAIOptions``.
        environment_name: Deployment environment name (e.g. ``"production"``).
            Propagated to ``GovernAIOptions``.
        options: Runtime options. Created from ``application_name`` and
            ``environment_name`` when ``None``.
        exporter: Event exporter. Defaults to ``NoOpExporter``.
        policy_evaluator: Policy evaluator. Defaults to
            ``NoOpPolicyEvaluator``.
        clock: Clock implementation. Defaults to ``SystemClock``.
        redactor: PII / sensitive data redactor.  ``None`` means no
            redaction is performed.
        tenant_resolver: Resolves the tenant identifier from a request.
            ``None`` falls back to the ``X-Tenant-Id`` header.
        user_resolver: Resolves the user identifier from a request.
            ``None`` falls back to the ``X-User-Id`` header or
            ``governai.user_id`` environ key.
        runtime: Pre-built ``GovernAIRuntime`` instance. When ``None``
            the middleware constructs one from the other fields.
    """

    application_name: str = ""
    environment_name: str = ""
    options: GovernAIOptions | None = None
    exporter: GovernAIExporter | None = None
    policy_evaluator: GovernAIPolicyEvaluator | None = None
    clock: GovernAIClock | None = None
    redactor: GovernAIRedactor | None = None
    tenant_resolver: GovernAITenantResolver | None = None
    user_resolver: GovernAIUserResolver | None = None
    runtime: GovernAIRuntime | None = None

    def build_runtime(self) -> GovernAIRuntime:
        """Construct a ``GovernAIRuntime`` from this configuration.

        Returns the ``runtime`` field if it is already populated.
        Otherwise, assembles a runtime from the individual component
        fields, filling in no-op defaults for any ``None`` values.

        Returns:
            A ready-to-use ``GovernAIRuntime`` instance.
        """
        if self.runtime is not None:
            return self.runtime

        options = self.options or GovernAIOptions(
            application_name=self.application_name,
            environment_name=self.environment_name,
        )
        return GovernAIRuntime(
            options=options,
            exporter=self.exporter or NoOpExporter(),
            policy_evaluator=self.policy_evaluator or NoOpPolicyEvaluator(),
            clock=self.clock or SystemClock(),
            redactor=self.redactor,
        )
