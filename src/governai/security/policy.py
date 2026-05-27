"""GovernAI default local policy evaluator.

Provides ``DefaultLocalPolicyEvaluator``, which combines prompt injection
and sensitive data scanning to make local Allow / Review / Deny decisions.
"""

from __future__ import annotations

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel
from governai.abstractions.models import GovernAIContext, GovernAIPolicyDecision, GovernAIRiskResult
from governai.security.risk import RiskScoreCalculator
from governai.security.scanning import PromptInjectionHeuristicScanner, SensitiveDataScanner

# Policy decision table:
#   NONE / LOW / MEDIUM  →  ALLOW
#   HIGH                 →  REVIEW
#   CRITICAL             →  DENY
_LEVEL_TO_DECISION: dict[GovernAIRiskLevel, GovernAIPolicyDecisionType] = {
    GovernAIRiskLevel.NONE: GovernAIPolicyDecisionType.ALLOW,
    GovernAIRiskLevel.LOW: GovernAIPolicyDecisionType.ALLOW,
    GovernAIRiskLevel.MEDIUM: GovernAIPolicyDecisionType.ALLOW,
    GovernAIRiskLevel.HIGH: GovernAIPolicyDecisionType.REVIEW,
    GovernAIRiskLevel.CRITICAL: GovernAIPolicyDecisionType.DENY,
}


class DefaultLocalPolicyEvaluator:
    """Local policy evaluator using heuristic risk scanning.

    Combines prompt injection detection and sensitive data scanning to
    produce a risk score. Maps the aggregate risk level to a policy
    decision using the standard GovernAI policy table:

    +----------+----------+
    | Level    | Decision |
    +==========+==========+
    | NONE     | ALLOW    |
    +----------+----------+
    | LOW      | ALLOW    |
    +----------+----------+
    | MEDIUM   | ALLOW    |
    +----------+----------+
    | HIGH     | REVIEW   |
    +----------+----------+
    | CRITICAL | DENY     |
    +----------+----------+

    All components are injected via the constructor for testability.
    Pass ``None`` to use sensible default instances.

    .. warning::
        This evaluator is heuristic-based. It does not provide complete
        protection against prompt injection or data leakage. It is intended
        as a governance assistance tool only.
    """

    def __init__(
        self,
        injection_scanner: PromptInjectionHeuristicScanner | None = None,
        sensitive_scanner: SensitiveDataScanner | None = None,
        calculator: RiskScoreCalculator | None = None,
    ) -> None:
        """Initialise the policy evaluator.

        Args:
            injection_scanner: Scanner for prompt injection patterns.
                Defaults to a new ``PromptInjectionHeuristicScanner``.
            sensitive_scanner: Scanner for sensitive data patterns.
                Defaults to a new ``SensitiveDataScanner``.
            calculator: Aggregates scanner results into a single score.
                Defaults to a new ``RiskScoreCalculator``.
        """
        self._injection_scanner = injection_scanner or PromptInjectionHeuristicScanner()
        self._sensitive_scanner = sensitive_scanner or SensitiveDataScanner()
        self._calculator = calculator or RiskScoreCalculator()

    async def evaluate_async(self, context: GovernAIContext) -> GovernAIPolicyDecision:
        """Evaluate the governance policy for an AI operation context.

        Scans the prompt (if present) for injection and sensitive data
        patterns, aggregates the results, and maps the risk level to a
        policy decision.

        Args:
            context: The AI operation context to evaluate.

        Returns:
            A ``GovernAIPolicyDecision`` with Allow, Review, or Deny.
        """
        results: list[GovernAIRiskResult] = []

        if context.prompt:
            results.append(self._injection_scanner.scan(context.prompt))
            results.append(self._sensitive_scanner.scan(context.prompt))

        combined = self._calculator.calculate(results)
        decision = _LEVEL_TO_DECISION.get(combined.risk_level, GovernAIPolicyDecisionType.DENY)

        return GovernAIPolicyDecision(
            decision=decision,
            reason=combined.reason or "Local policy evaluation completed.",
            risk_score=combined.risk_score,
            risk_level=combined.risk_level,
            risk_category=combined.risk_category,
        )
