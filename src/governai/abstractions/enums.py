"""GovernAI enumeration types.

This module defines the core enumerations used across the GovernAI SDK
as shared contracts between all packages.
"""

from __future__ import annotations

from enum import Enum


class GovernAIPolicyDecisionType(Enum):
    """Enumeration of possible policy decision outcomes.

    Used by policy evaluators and stored in GovernAIEvent to record the
    governance decision made for each AI operation.

    Values:
        ALLOW: The operation is permitted to proceed.
        REVIEW: The operation requires human review but may proceed.
        DENY: The operation is not permitted and must be blocked.
    """

    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    DENY = "DENY"


class GovernAIRiskLevel(Enum):
    """Enumeration of risk severity levels.

    Used by risk scanners and stored in GovernAIEvent to record the
    assessed risk level for each AI operation.

    Values:
        NONE: No detected risk. Safe to proceed.
        LOW: Low risk. Generally safe to proceed.
        MEDIUM: Moderate risk. May warrant attention.
        HIGH: High risk. Human review recommended.
        CRITICAL: Critical risk. Denial recommended.
    """

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
