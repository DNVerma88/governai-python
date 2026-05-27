"""GovernAI no-op policy evaluator.

Provides a pass-through policy evaluator for use when no policy
enforcement is required or configured.
"""

from __future__ import annotations

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel
from governai.abstractions.models import GovernAIContext, GovernAIPolicyDecision


class NoOpPolicyEvaluator:
    """Policy evaluator that always returns ALLOW with zero risk.

    Used as the default when no policy evaluator is configured.
    Suitable for development environments or applications that rely
    on application-level guards rather than GovernAI policy enforcement.
    """

    async def evaluate_async(self, context: GovernAIContext) -> GovernAIPolicyDecision:
        """Always allow the operation with zero risk score.

        Args:
            context: The AI operation context (unused by this implementation).

        Returns:
            A ``GovernAIPolicyDecision`` with ``ALLOW`` decision and zero risk.
        """
        return GovernAIPolicyDecision(
            decision=GovernAIPolicyDecisionType.ALLOW,
            reason="No policy evaluator configured.",
            risk_score=0.0,
            risk_level=GovernAIRiskLevel.NONE,
            risk_category="",
        )
