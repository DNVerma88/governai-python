"""GovernAI PII and sensitive data redaction.

Provides ``BasicPiiRedactor``, a heuristic regex-based implementation of
the ``GovernAIRedactor`` protocol that detects and replaces common
sensitive data patterns before text is hashed or logged.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Compiled redaction patterns — ordered from most-specific to least-specific
# to minimise false-positive conflicts.
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Azure Storage connection strings  (most specific — match first)
    (
        re.compile(
            r"DefaultEndpointsProtocol=[^;]+(?:;[^;=]+=?[^;]*)+",
            re.IGNORECASE,
        ),
        "[REDACTED_CONNECTION_STRING]",
    ),
    # SQL / ODBC / ADO.NET connection strings
    # password/pwd keywords are handled separately by the password pattern below.
    (
        re.compile(
            r"(?i)(?:server|data\s+source|user\s+id|uid|initial\s+catalog|database)"
            r"\s*=\s*[^;\"'\s]{1,200}",
        ),
        "[REDACTED_CONNECTION_STRING]",
    ),
    # Bearer tokens  (Authorization: Bearer <token>)
    (
        re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        "Bearer [REDACTED_TOKEN]",
    ),
    # JWT-like tokens  (three base64url segments separated by dots)
    (
        re.compile(
            r"\b[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_\+/=]{10,}\b"
        ),
        "[REDACTED_TOKEN]",
    ),
    # API key key=value patterns  (api_key=..., apikey=..., x-api-key=...)
    (
        re.compile(
            r"(?i)(?:api[_\-]?key|x-api-key|apikey)\s*[=:]\s*[\"']?[A-Za-z0-9\-_]{16,}[\"']?"
        ),
        "[REDACTED_API_KEY]",
    ),
    # Password / secret key=value patterns
    (
        re.compile(
            r"(?i)(?:password|passwd|pwd|secret|client[_\-]?secret)\s*[=:]\s*[\"']?[^\s\"']{4,}[\"']?"
        ),
        "[REDACTED_SECRET]",
    ),
    # Email addresses
    (
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    # Credit-card-like numbers  (16 digits, optionally spaced or dashed)
    (
        re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"),
        "[REDACTED_CARD]",
    ),
    # Phone numbers  (E.164, US/international formats)
    (
        re.compile(
            r"\b(\+?1[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b"
        ),
        "[REDACTED_PHONE]",
    ),
]


class BasicPiiRedactor:
    """Heuristic regex-based PII and sensitive data redactor.

    Implements the ``GovernAIRedactor`` protocol. Applies a sequence of
    compiled regular expression patterns to replace sensitive values with
    safe placeholder tokens.

    Patterns covered:

    - Email addresses → ``[REDACTED_EMAIL]``
    - Phone numbers → ``[REDACTED_PHONE]``
    - Credit card-like numbers → ``[REDACTED_CARD]``
    - Bearer tokens → ``Bearer [REDACTED_TOKEN]``
    - JWT-like tokens → ``[REDACTED_TOKEN]``
    - API key patterns → ``[REDACTED_API_KEY]``
    - Password / secret patterns → ``[REDACTED_SECRET]``
    - SQL / ODBC connection strings → ``[REDACTED_CONNECTION_STRING]``
    - Azure Storage connection strings → ``[REDACTED_CONNECTION_STRING]``

    .. warning::
        This implementation is heuristic-based. It does not guarantee
        complete redaction of all sensitive data. It is intended to reduce
        accidental exposure, not to serve as a complete data-loss-prevention
        system.
    """

    def redact(self, input: str | None) -> str:
        """Redact sensitive data from the input string.

        Args:
            input: The text to scan and redact. Returns an empty string
                if ``None`` is provided.

        Returns:
            The input text with detected sensitive values replaced by
            safe placeholder tokens.
        """
        if not input:
            return input if input is not None else ""
        result = input
        for pattern, replacement in _PATTERNS:
            result = pattern.sub(replacement, result)
        return result
