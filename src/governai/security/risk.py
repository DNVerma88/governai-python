"""GovernAI risk score calculation.

Provides ``RiskScoreCalculator`` which combines multiple ``GovernAIRiskResult``
instances into a single consolidated risk assessment.
"""

from __future__ import annotations

from governai.abstractions.enums import GovernAIRiskLevel
from governai.abstractions.models import GovernAIRiskResult


class RiskScoreCalculator:
    """Combines multiple risk scanner results into one aggregate result.

    Takes the maximum risk score across all provided results.
    Risk level is derived from the aggregate score using the standard
    GovernAI score-to-level mapping:

    +---------+----------+
    | Score   | Level    |
    +=========+==========+
    | 0       | NONE     |
    +---------+----------+
    | 1–30    | LOW      |
    +---------+----------+
    | 31–60   | MEDIUM   |
    +---------+----------+
    | 61–85   | HIGH     |
    +---------+----------+
    | 86–100  | CRITICAL |
    +---------+----------+
    """

    def calculate(self, results: list[GovernAIRiskResult]) -> GovernAIRiskResult:
        """Combine a list of risk results into a single aggregate result.

        Args:
            results: Individual risk results from one or more scanners.
                An empty list returns a zero-risk result.

        Returns:
            A ``GovernAIRiskResult`` with the maximum score across all
            inputs, a derived risk level, and merged matched pattern names.
        """
        if not results:
            return GovernAIRiskResult()

        non_zero = [r for r in results if r.risk_score > 0]
        if not non_zero:
            return GovernAIRiskResult()

        dominant = max(non_zero, key=lambda r: r.risk_score)
        max_score = dominant.risk_score
        all_patterns = tuple(p for r in non_zero for p in r.matched_patterns)
        all_reasons = [r.reason for r in non_zero if r.reason]
        combined_reason = "; ".join(all_reasons) if all_reasons else ""

        return GovernAIRiskResult(
            risk_score=max_score,
            risk_level=self._score_to_level(max_score),
            risk_category=dominant.risk_category,
            reason=combined_reason,
            matched_patterns=all_patterns,
        )

    @staticmethod
    def _score_to_level(score: float) -> GovernAIRiskLevel:
        """Map a numeric score to a ``GovernAIRiskLevel``.

        Args:
            score: Risk score in the range 0–100.

        Returns:
            The corresponding ``GovernAIRiskLevel``.
        """
        if score <= 0:
            return GovernAIRiskLevel.NONE
        if score <= 30:
            return GovernAIRiskLevel.LOW
        if score <= 60:
            return GovernAIRiskLevel.MEDIUM
        if score <= 85:
            return GovernAIRiskLevel.HIGH
        return GovernAIRiskLevel.CRITICAL
