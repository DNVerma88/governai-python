"""Tests for governai.security.risk.RiskScoreCalculator."""

import unittest

from governai.abstractions.enums import GovernAIRiskLevel
from governai.abstractions.models import GovernAIRiskResult
from governai.security.risk import RiskScoreCalculator


def _make_result(
    score: float,
    level: GovernAIRiskLevel,
    category: str = "Test",
    reason: str = "",
    patterns: tuple[str, ...] = (),
) -> GovernAIRiskResult:
    return GovernAIRiskResult(
        risk_score=score,
        risk_level=level,
        risk_category=category,
        reason=reason,
        matched_patterns=patterns,
    )


class TestRiskScoreCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = RiskScoreCalculator()

    # ------------------------------------------------------------------
    # Empty input
    # ------------------------------------------------------------------

    def test_empty_list_returns_zero_risk(self) -> None:
        result = self.calculator.calculate([])
        self.assertEqual(result.risk_score, 0.0)
        self.assertEqual(result.risk_level, GovernAIRiskLevel.NONE)

    def test_all_zero_scores_returns_zero_risk(self) -> None:
        results = [GovernAIRiskResult(), GovernAIRiskResult()]
        result = self.calculator.calculate(results)
        self.assertEqual(result.risk_level, GovernAIRiskLevel.NONE)

    # ------------------------------------------------------------------
    # Single result passthrough
    # ------------------------------------------------------------------

    def test_single_result_score_preserved(self) -> None:
        r = _make_result(25.0, GovernAIRiskLevel.LOW, patterns=("email_address",))
        result = self.calculator.calculate([r])
        self.assertEqual(result.risk_score, 25.0)

    def test_single_result_pattern_preserved(self) -> None:
        r = _make_result(25.0, GovernAIRiskLevel.LOW, patterns=("email_address",))
        result = self.calculator.calculate([r])
        self.assertIn("email_address", result.matched_patterns)

    # ------------------------------------------------------------------
    # Score-to-level mapping
    # ------------------------------------------------------------------

    def test_score_0_is_none(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(0), GovernAIRiskLevel.NONE)

    def test_score_1_is_low(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(1), GovernAIRiskLevel.LOW)

    def test_score_30_is_low(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(30), GovernAIRiskLevel.LOW)

    def test_score_31_is_medium(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(31), GovernAIRiskLevel.MEDIUM)

    def test_score_60_is_medium(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(60), GovernAIRiskLevel.MEDIUM)

    def test_score_61_is_high(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(61), GovernAIRiskLevel.HIGH)

    def test_score_85_is_high(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(85), GovernAIRiskLevel.HIGH)

    def test_score_86_is_critical(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(86), GovernAIRiskLevel.CRITICAL)

    def test_score_100_is_critical(self) -> None:
        self.assertEqual(RiskScoreCalculator._score_to_level(100), GovernAIRiskLevel.CRITICAL)

    # ------------------------------------------------------------------
    # Combining multiple results: max score wins
    # ------------------------------------------------------------------

    def test_max_score_wins(self) -> None:
        results = [
            _make_result(20.0, GovernAIRiskLevel.LOW, patterns=("email_address",)),
            _make_result(75.0, GovernAIRiskLevel.HIGH, patterns=("bearer_token",)),
        ]
        result = self.calculator.calculate(results)
        self.assertEqual(result.risk_score, 75.0)
        self.assertEqual(result.risk_level, GovernAIRiskLevel.HIGH)

    def test_patterns_merged(self) -> None:
        results = [
            _make_result(20.0, GovernAIRiskLevel.LOW, patterns=("email_address",)),
            _make_result(75.0, GovernAIRiskLevel.HIGH, patterns=("bearer_token",)),
        ]
        result = self.calculator.calculate(results)
        self.assertIn("email_address", result.matched_patterns)
        self.assertIn("bearer_token", result.matched_patterns)

    def test_reasons_combined(self) -> None:
        results = [
            _make_result(20.0, GovernAIRiskLevel.LOW, reason="Email found"),
            _make_result(75.0, GovernAIRiskLevel.HIGH, reason="Bearer token found"),
        ]
        result = self.calculator.calculate(results)
        self.assertIn("Email found", result.reason)
        self.assertIn("Bearer token found", result.reason)

    def test_critical_overrides_high(self) -> None:
        results = [
            _make_result(75.0, GovernAIRiskLevel.HIGH),
            _make_result(90.0, GovernAIRiskLevel.CRITICAL),
        ]
        result = self.calculator.calculate(results)
        self.assertEqual(result.risk_level, GovernAIRiskLevel.CRITICAL)
        self.assertEqual(result.risk_score, 90.0)

    # ------------------------------------------------------------------
    # Zero-score results are excluded from combination
    # ------------------------------------------------------------------

    def test_zero_score_results_excluded(self) -> None:
        results = [
            GovernAIRiskResult(),  # score=0
            _make_result(20.0, GovernAIRiskLevel.LOW, patterns=("email_address",)),
        ]
        result = self.calculator.calculate(results)
        self.assertEqual(result.risk_score, 20.0)


if __name__ == "__main__":
    unittest.main()
