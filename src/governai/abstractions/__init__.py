"""GovernAI abstractions package.

This package contains the protocols, models, and enumerations that
form the shared public contracts of the GovernAI SDK.

Packages that depend on GovernAI contracts should import only from
``governai.abstractions`` to remain decoupled from runtime implementations.

Exported symbols:
    Enums:
        GovernAIPolicyDecisionType: Allow / Review / Deny decision values.
        GovernAIRiskLevel: None / Low / Medium / High / Critical risk levels.

    Models:
        GovernAIContext: Input context for a tracked AI operation.
        GovernAIEvent: Governance audit event produced by the runtime.
        GovernAIPolicyDecision: Result of a policy evaluation.
        GovernAIRiskResult: Result of a risk assessment.

    Protocols:
        GovernAIClock: Provides the current UTC time.
        GovernAIExporter: Exports governance events to a destination.
        GovernAIPolicyEvaluator: Evaluates governance policy for an operation.
        GovernAIRedactor: Redacts sensitive data from text.
        GovernAITenantResolver: Resolves the tenant ID from request context.
        GovernAIUserResolver: Resolves the user ID from request context.
"""

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel
from governai.abstractions.models import (
    GovernAIContext,
    GovernAIEvent,
    GovernAIPolicyDecision,
    GovernAIRiskResult,
)
from governai.abstractions.protocols import (
    GovernAIClock,
    GovernAIExporter,
    GovernAIPolicyEvaluator,
    GovernAIRedactor,
    GovernAITenantResolver,
    GovernAIUserResolver,
)

__all__ = [
    # Enums
    "GovernAIPolicyDecisionType",
    "GovernAIRiskLevel",
    # Models
    "GovernAIContext",
    "GovernAIEvent",
    "GovernAIPolicyDecision",
    "GovernAIRiskResult",
    # Protocols
    "GovernAIClock",
    "GovernAIExporter",
    "GovernAIPolicyEvaluator",
    "GovernAIRedactor",
    "GovernAITenantResolver",
    "GovernAIUserResolver",
]
