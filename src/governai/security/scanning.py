"""GovernAI security scanners.

Provides two heuristic scanners:
- ``SensitiveDataScanner``: detects sensitive data (PII, tokens, credentials).
- ``PromptInjectionHeuristicScanner``: detects prompt injection patterns.

Both scanners return a ``GovernAIRiskResult`` with a numeric score,
a risk level, and the matched pattern names.
"""

from __future__ import annotations

import re

from governai.abstractions.enums import GovernAIRiskLevel
from governai.abstractions.models import GovernAIRiskResult

# ---------------------------------------------------------------------------
# Sensitive data detection patterns
# ---------------------------------------------------------------------------

_SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], float, GovernAIRiskLevel, str, str]] = [
    # (pattern, score, level, category, pattern_name)
    (
        re.compile(r"DefaultEndpointsProtocol=[^;]+(?:;[^;=]+=?[^;]*)+", re.IGNORECASE),
        90.0, GovernAIRiskLevel.CRITICAL, "SensitiveData", "azure_connection_string",
    ),
    (
        re.compile(
            r"(?i)(?:server|data\s+source|user\s+id|uid|password|pwd|initial\s+catalog|database)"
            r"\s*=\s*[^;\"'\s]{1,200}"
        ),
        90.0, GovernAIRiskLevel.CRITICAL, "SensitiveData", "sql_connection_string",
    ),
    (
        re.compile(
            r"(?i)(?:password|passwd|pwd|secret|client[_\-]?secret)\s*[=:]\s*[\"']?[^\s\"']{4,}[\"']?"
        ),
        90.0, GovernAIRiskLevel.CRITICAL, "SensitiveData", "password_value",
    ),
    (
        re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        70.0, GovernAIRiskLevel.HIGH, "SensitiveData", "bearer_token",
    ),
    (
        re.compile(
            r"\b[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_\+/=]{10,}\b"
        ),
        70.0, GovernAIRiskLevel.HIGH, "SensitiveData", "jwt_token",
    ),
    (
        re.compile(
            r"(?i)(?:api[_\-]?key|x-api-key|apikey)\s*[=:]\s*[\"']?[A-Za-z0-9\-_]{16,}[\"']?"
        ),
        70.0, GovernAIRiskLevel.HIGH, "SensitiveData", "api_key",
    ),
    (
        re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"),
        70.0, GovernAIRiskLevel.HIGH, "SensitiveData", "credit_card",
    ),
    (
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        20.0, GovernAIRiskLevel.LOW, "SensitiveData", "email_address",
    ),
    (
        re.compile(r"\b(\+?1[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b"),
        20.0, GovernAIRiskLevel.LOW, "SensitiveData", "phone_number",
    ),
]

# ---------------------------------------------------------------------------
# Prompt injection detection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[re.Pattern[str], float, GovernAIRiskLevel, str]] = [
    # (pattern, score, level, pattern_name)
    (
        re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
        75.0, GovernAIRiskLevel.HIGH, "ignore_previous_instructions",
    ),
    (
        re.compile(r"override\s+(?:all\s+)?instructions", re.IGNORECASE),
        75.0, GovernAIRiskLevel.HIGH, "override_instructions",
    ),
    (
        re.compile(r"(?:reveal|show|print|output|display)\s+(?:the\s+)?system\s+prompt", re.IGNORECASE),
        75.0, GovernAIRiskLevel.HIGH, "system_prompt_extraction",
    ),
    (
        re.compile(r"(?:print|show|output|reveal|expose|leak)\s+(?:all\s+)?secrets?", re.IGNORECASE),
        90.0, GovernAIRiskLevel.CRITICAL, "secret_extraction",
    ),
    (
        re.compile(r"exfiltrate\s+data", re.IGNORECASE),
        90.0, GovernAIRiskLevel.CRITICAL, "data_exfiltration",
    ),
    (
        re.compile(r"(?:bypass|circumvent|evade)\s+(?:security|guardrails?|policy|filter)", re.IGNORECASE),
        70.0, GovernAIRiskLevel.HIGH, "bypass_security",
    ),
    (
        re.compile(r"disable\s+(?:policy|guardrails?|filter|safety)", re.IGNORECASE),
        70.0, GovernAIRiskLevel.HIGH, "disable_policy",
    ),
    (
        re.compile(r"act\s+as\s+(?:an?\s+)?(?:unrestricted|uncensored|unfiltered|jailbroken)", re.IGNORECASE),
        70.0, GovernAIRiskLevel.HIGH, "act_as_unrestricted",
    ),
    (
        re.compile(r"\bjailbreak\b", re.IGNORECASE),
        70.0, GovernAIRiskLevel.HIGH, "jailbreak",
    ),
    (
        re.compile(r"(?:developer|system)\s+message\b", re.IGNORECASE),
        40.0, GovernAIRiskLevel.MEDIUM, "developer_system_message",
    ),
    (
        re.compile(r"hidden\s+(?:prompt|instruction)", re.IGNORECASE),
        40.0, GovernAIRiskLevel.MEDIUM, "hidden_prompt",
    ),
]


class SensitiveDataScanner:
    """Heuristic scanner for sensitive data in text.

    Detects patterns such as email addresses, phone numbers, bearer tokens,
    API keys, JWT-like tokens, credit card numbers, and connection strings.
    Returns a ``GovernAIRiskResult`` with a risk score proportional to the
    sensitivity of detected data.

    .. warning::
        This implementation is heuristic-based. It does not guarantee
        detection of all sensitive data.
    """

    def scan(self, text: str | None) -> GovernAIRiskResult:
        """Scan the input text for sensitive data patterns.

        Args:
            text: The text to scan. Returns a zero-risk result for
                ``None`` or empty input.

        Returns:
            A ``GovernAIRiskResult`` reflecting the highest-severity
            sensitive data pattern found, plus all matched pattern names.
        """
        if not text:
            return GovernAIRiskResult()

        max_score = 0.0
        max_level = GovernAIRiskLevel.NONE
        max_category = ""
        matched: list[str] = []

        for pattern, score, level, category, name in _SENSITIVE_PATTERNS:
            if pattern.search(text):
                matched.append(name)
                if score > max_score:
                    max_score = score
                    max_level = level
                    max_category = category

        if not matched:
            return GovernAIRiskResult()

        return GovernAIRiskResult(
            risk_score=max_score,
            risk_level=max_level,
            risk_category=max_category,
            reason=f"Sensitive data detected: {', '.join(matched)}",
            matched_patterns=tuple(matched),
        )


class PromptInjectionHeuristicScanner:
    """Heuristic scanner for prompt injection patterns.

    Detects phrases commonly associated with prompt injection attacks,
    such as instructions to ignore previous guidance, extract system
    prompts, reveal secrets, bypass security controls, or jailbreak the
    model.

    Returns a ``GovernAIRiskResult`` reflecting the severity of detected
    patterns.

    .. warning::
        This implementation is heuristic-based. It cannot detect all prompt
        injection attempts and should not be relied upon as the sole defence
        against adversarial prompts.
    """

    def scan(self, text: str | None) -> GovernAIRiskResult:
        """Scan the input text for prompt injection patterns.

        Args:
            text: The text to scan. Returns a zero-risk result for
                ``None`` or empty input.

        Returns:
            A ``GovernAIRiskResult`` reflecting the highest-severity
            injection pattern found, plus all matched pattern names.
        """
        if not text:
            return GovernAIRiskResult()

        max_score = 0.0
        max_level = GovernAIRiskLevel.NONE
        matched: list[str] = []

        for pattern, score, level, name in _INJECTION_PATTERNS:
            if pattern.search(text):
                matched.append(name)
                if score > max_score:
                    max_score = score
                    max_level = level

        if not matched:
            return GovernAIRiskResult()

        return GovernAIRiskResult(
            risk_score=max_score,
            risk_level=max_level,
            risk_category="PromptInjection",
            reason=f"Prompt injection pattern detected: {', '.join(matched)}",
            matched_patterns=tuple(matched),
        )
