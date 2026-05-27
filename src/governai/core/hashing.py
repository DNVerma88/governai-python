"""GovernAI prompt and response hashing.

Provides SHA-256 based hashing for prompts and responses.
Raw text is never stored; only the hash is retained in audit events.
"""

from __future__ import annotations

import hashlib


class PromptHasher:
    """Computes SHA-256 hashes of AI prompt text.

    Raw prompts are never stored or exported. Only the lowercase hex
    digest is included in ``GovernAIEvent.prompt_hash``.
    """

    def hash(self, prompt: str | None) -> str:
        """Compute the SHA-256 hash of the given prompt.

        Args:
            prompt: Raw prompt text. Returns empty string for ``None`` or
                empty input.

        Returns:
            Lowercase hexadecimal SHA-256 digest, or ``""`` if input is empty.
        """
        if not prompt:
            return ""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class ResponseHasher:
    """Computes SHA-256 hashes of AI response text.

    Raw responses are never stored or exported. Only the lowercase hex
    digest is included in ``GovernAIEvent.response_hash``.
    """

    def hash(self, response: str | None) -> str:
        """Compute the SHA-256 hash of the given response.

        Args:
            response: Raw response text. Returns empty string for ``None`` or
                empty input.

        Returns:
            Lowercase hexadecimal SHA-256 digest, or ``""`` if input is empty.
        """
        if not response:
            return ""
        return hashlib.sha256(response.encode("utf-8")).hexdigest()
