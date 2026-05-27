"""Tests for GovernAI enumeration types.

Covers:
    - All enum values exist with correct string values.
    - All expected members are present and no extras.
    - Enum identity comparison works correctly.
    - Enum lookup by value works correctly.
"""

from __future__ import annotations

import unittest

from governai.abstractions.enums import GovernAIPolicyDecisionType, GovernAIRiskLevel


class TestGovernAIPolicyDecisionType(unittest.TestCase):
    """Tests for the GovernAIPolicyDecisionType enum."""

    def test_allow_value(self) -> None:
        """ALLOW member must have string value 'ALLOW'."""
        self.assertEqual(GovernAIPolicyDecisionType.ALLOW.value, "ALLOW")

    def test_review_value(self) -> None:
        """REVIEW member must have string value 'REVIEW'."""
        self.assertEqual(GovernAIPolicyDecisionType.REVIEW.value, "REVIEW")

    def test_deny_value(self) -> None:
        """DENY member must have string value 'DENY'."""
        self.assertEqual(GovernAIPolicyDecisionType.DENY.value, "DENY")

    def test_all_three_members_present(self) -> None:
        """Exactly three policy decision members must be present."""
        values = {e.value for e in GovernAIPolicyDecisionType}
        self.assertEqual(values, {"ALLOW", "REVIEW", "DENY"})

    def test_lookup_by_value(self) -> None:
        """Enum members must be retrievable by string value."""
        self.assertIs(GovernAIPolicyDecisionType("ALLOW"), GovernAIPolicyDecisionType.ALLOW)
        self.assertIs(GovernAIPolicyDecisionType("REVIEW"), GovernAIPolicyDecisionType.REVIEW)
        self.assertIs(GovernAIPolicyDecisionType("DENY"), GovernAIPolicyDecisionType.DENY)

    def test_identity_comparison(self) -> None:
        """Enum member identity must be stable (singleton per member)."""
        self.assertIs(GovernAIPolicyDecisionType.ALLOW, GovernAIPolicyDecisionType.ALLOW)
        self.assertIsNot(GovernAIPolicyDecisionType.ALLOW, GovernAIPolicyDecisionType.DENY)
        self.assertIsNot(GovernAIPolicyDecisionType.REVIEW, GovernAIPolicyDecisionType.DENY)

    def test_invalid_value_raises(self) -> None:
        """Constructing from an unknown value must raise ValueError."""
        with self.assertRaises(ValueError):
            GovernAIPolicyDecisionType("UNKNOWN")


class TestGovernAIRiskLevel(unittest.TestCase):
    """Tests for the GovernAIRiskLevel enum."""

    def test_none_value(self) -> None:
        """NONE member must have string value 'NONE'."""
        self.assertEqual(GovernAIRiskLevel.NONE.value, "NONE")

    def test_low_value(self) -> None:
        """LOW member must have string value 'LOW'."""
        self.assertEqual(GovernAIRiskLevel.LOW.value, "LOW")

    def test_medium_value(self) -> None:
        """MEDIUM member must have string value 'MEDIUM'."""
        self.assertEqual(GovernAIRiskLevel.MEDIUM.value, "MEDIUM")

    def test_high_value(self) -> None:
        """HIGH member must have string value 'HIGH'."""
        self.assertEqual(GovernAIRiskLevel.HIGH.value, "HIGH")

    def test_critical_value(self) -> None:
        """CRITICAL member must have string value 'CRITICAL'."""
        self.assertEqual(GovernAIRiskLevel.CRITICAL.value, "CRITICAL")

    def test_all_five_members_present(self) -> None:
        """Exactly five risk level members must be present."""
        values = {e.value for e in GovernAIRiskLevel}
        self.assertEqual(values, {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"})

    def test_lookup_by_value(self) -> None:
        """Enum members must be retrievable by string value."""
        self.assertIs(GovernAIRiskLevel("NONE"), GovernAIRiskLevel.NONE)
        self.assertIs(GovernAIRiskLevel("CRITICAL"), GovernAIRiskLevel.CRITICAL)

    def test_identity_comparison(self) -> None:
        """Enum member identity must be stable (singleton per member)."""
        self.assertIs(GovernAIRiskLevel.NONE, GovernAIRiskLevel.NONE)
        self.assertIsNot(GovernAIRiskLevel.NONE, GovernAIRiskLevel.CRITICAL)
        self.assertIsNot(GovernAIRiskLevel.LOW, GovernAIRiskLevel.HIGH)

    def test_invalid_value_raises(self) -> None:
        """Constructing from an unknown value must raise ValueError."""
        with self.assertRaises(ValueError):
            GovernAIRiskLevel("EXTREME")


if __name__ == "__main__":
    unittest.main()
