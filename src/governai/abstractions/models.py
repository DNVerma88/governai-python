"""GovernAI core data models.

This module defines immutable frozen dataclass models that serve as the
public contracts for all GovernAI SDK packages. All models use
``@dataclasses.dataclass(frozen=True)`` to ensure thread-safety and
prevent accidental mutation.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Any

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel


def _empty_tuple() -> tuple[str, ...]:
    """Return an empty tuple of strings. Used as a dataclass default factory."""
    return ()


def _utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


@dataclasses.dataclass(frozen=True)
class GovernAIContext:
    """Context describing an AI operation being tracked by GovernAI.

    Carries all inputs required by the runtime to evaluate policy,
    hash content, and build a governance audit event. This object is
    constructed by the caller before invoking the GovernAI runtime.

    Privacy note:
        ``prompt`` and ``response`` are present for in-process hashing
        and risk scanning only. They must not be stored or exported by
        default. Set them to ``None`` when raw text is unavailable.

    Attributes:
        trace_id: Distributed trace ID for correlation with application telemetry.
        correlation_id: Request-level correlation ID. Generated if not provided.
        application_name: Name of the application using GovernAI.
        environment_name: Runtime environment (e.g., Production, Development).
        tenant_id: Tenant identifier for multi-tenant applications.
        user_id: User identifier, resolved from claims where available.
        agent_name: Logical AI agent or workflow name.
        operation_name: Name of the AI operation being performed.
        model_provider: Name of the AI model provider.
        model_name: Name of the AI model.
        prompt: Raw prompt text. Not stored or exported by default.
        response: Raw response text. Not stored or exported by default.
        input_tokens: Input token count if provided by the application.
        output_tokens: Output token count if provided by the application.
        metadata: Additional key-value metadata for the operation.
    """

    trace_id: str | None = None
    correlation_id: str | None = None
    application_name: str = ""
    environment_name: str = ""
    tenant_id: str | None = None
    user_id: str | None = None
    agent_name: str = ""
    operation_name: str = ""
    model_provider: str = ""
    model_name: str = ""
    prompt: str | None = None
    response: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    metadata: dict[str, Any] | None = None


@dataclasses.dataclass(frozen=True)
class GovernAIRiskResult:
    """Result of a risk assessment for a GovernAI operation.

    Produced by risk scanner implementations and consumed by policy
    evaluators to make governance decisions.

    Attributes:
        risk_score: Numeric risk score in the range 0–100. Higher is riskier.
        risk_level: Categorized risk severity level.
        risk_category: Human-readable description of the primary risk category.
        reason: Human-readable explanation for the risk assessment outcome.
        matched_patterns: Names of patterns that contributed to the risk score.
    """

    risk_score: float = 0.0
    risk_level: GovernAIRiskLevel = GovernAIRiskLevel.NONE
    risk_category: str = ""
    reason: str = ""
    matched_patterns: tuple[str, ...] = dataclasses.field(default_factory=_empty_tuple)


@dataclasses.dataclass(frozen=True)
class GovernAIPolicyDecision:
    """Result of a policy evaluation.

    Produced by policy evaluator implementations. The ``decision`` field
    indicates whether the AI operation should be allowed, reviewed, or denied.

    Attributes:
        decision: The policy decision outcome (Allow, Review, or Deny).
        reason: Human-readable reason for the decision.
        risk_score: Numeric risk score that informed the decision.
        risk_level: Risk severity level that informed the decision.
        risk_category: Risk category that informed the decision.
        metadata: Additional key-value metadata for the decision.
    """

    decision: GovernAIPolicyDecisionType = GovernAIPolicyDecisionType.ALLOW
    reason: str = ""
    risk_score: float = 0.0
    risk_level: GovernAIRiskLevel = GovernAIRiskLevel.NONE
    risk_category: str = ""
    metadata: dict[str, Any] | None = None


@dataclasses.dataclass(frozen=True)
class GovernAIEvent:
    """Governance audit event produced by the GovernAI runtime.

    This is the primary contract for all GovernAI exporters. Each event
    represents a single tracked AI operation with its full governance
    context, hashes, risk assessment, and policy decision.

    Privacy note:
        Raw prompt and response text are never stored in this event.
        Only SHA-256 hashes are included.

    Attributes:
        event_id: Unique identifier for this event (UUID without hyphens).
        trace_id: Distributed trace ID if available.
        correlation_id: Request or operation-level correlation ID.
        application_name: Name of the application using GovernAI.
        environment_name: Runtime environment name.
        tenant_id: Tenant identifier.
        user_id: User identifier.
        agent_name: Logical AI agent or workflow name.
        operation_name: Name of the AI operation.
        model_provider: Name of the AI model provider.
        model_name: Name of the AI model.
        prompt_hash: SHA-256 hash of the prompt. Empty if no prompt provided.
        response_hash: SHA-256 hash of the response. Empty if no response provided.
        input_tokens: Input token count if available.
        output_tokens: Output token count if available.
        total_tokens: Total token count (input + output) if available.
        risk_score: Numeric risk score 0–100.
        risk_level: Risk severity level.
        risk_category: Human-readable risk category.
        policy_decision: Policy decision outcome.
        policy_reason: Human-readable reason for the policy decision.
        duration_ms: Duration of the AI operation in milliseconds.
        success: Whether the AI operation completed successfully.
        error_code: Error code if the operation failed.
        error_message: Error message if the operation failed.
        timestamp_utc: UTC timestamp when the event was created.
        metadata: Additional key-value metadata for the event.
    """

    event_id: str = ""
    trace_id: str | None = None
    correlation_id: str | None = None
    application_name: str = ""
    environment_name: str = ""
    tenant_id: str | None = None
    user_id: str | None = None
    agent_name: str = ""
    operation_name: str = ""
    model_provider: str = ""
    model_name: str = ""
    prompt_hash: str = ""
    response_hash: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    risk_score: float = 0.0
    risk_level: GovernAIRiskLevel = GovernAIRiskLevel.NONE
    risk_category: str = ""
    policy_decision: GovernAIPolicyDecisionType = GovernAIPolicyDecisionType.ALLOW
    policy_reason: str = ""
    duration_ms: float = 0.0
    success: bool = True
    error_code: str | None = None
    error_message: str | None = None
    timestamp_utc: datetime = dataclasses.field(default_factory=_utc_now)
    metadata: dict[str, Any] | None = None
