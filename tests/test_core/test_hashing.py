"""Tests for GovernAI hashing utilities.

Covers:
    - SHA-256 prompt hashing produces correct output.
    - SHA-256 response hashing produces correct output.
    - None/empty inputs return empty string.
    - Different inputs produce different hashes.
    - Same input always produces same hash (deterministic).
"""

from __future__ import annotations

import hashlib
import unittest

from governai.core.hashing import PromptHasher, ResponseHasher


class TestPromptHasher(unittest.TestCase):
    """Tests for PromptHasher."""

    def setUp(self) -> None:
        self.hasher = PromptHasher()

    def test_non_empty_prompt_returns_hex_string(self) -> None:
        """Non-empty prompt must produce a non-empty hash string."""
        result = self.hasher.hash("Hello world")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_produces_sha256_digest(self) -> None:
        """Hash must match the expected SHA-256 hex digest."""
        text = "Test prompt"
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(self.hasher.hash(text), expected)

    def test_none_returns_empty_string(self) -> None:
        """None input must return an empty string."""
        self.assertEqual(self.hasher.hash(None), "")

    def test_empty_string_returns_empty_string(self) -> None:
        """Empty string must return an empty string."""
        self.assertEqual(self.hasher.hash(""), "")

    def test_different_inputs_produce_different_hashes(self) -> None:
        """Two different prompts must produce different hashes."""
        self.assertNotEqual(self.hasher.hash("prompt A"), self.hasher.hash("prompt B"))

    def test_same_input_is_deterministic(self) -> None:
        """Same input must always produce the same hash."""
        text = "Deterministic prompt"
        self.assertEqual(self.hasher.hash(text), self.hasher.hash(text))

    def test_hash_is_lowercase_hex(self) -> None:
        """Hash output must be lowercase hexadecimal."""
        result = self.hasher.hash("some prompt")
        self.assertEqual(result, result.lower())
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_hash_length_is_64_chars(self) -> None:
        """SHA-256 digest must be exactly 64 hex characters."""
        self.assertEqual(len(self.hasher.hash("any prompt")), 64)


class TestResponseHasher(unittest.TestCase):
    """Tests for ResponseHasher."""

    def setUp(self) -> None:
        self.hasher = ResponseHasher()

    def test_non_empty_response_returns_hash(self) -> None:
        """Non-empty response must produce a non-empty hash string."""
        result = self.hasher.hash("AI response text")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_produces_sha256_digest(self) -> None:
        """Hash must match the expected SHA-256 hex digest."""
        text = "AI says hello"
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(self.hasher.hash(text), expected)

    def test_none_returns_empty_string(self) -> None:
        """None input must return an empty string."""
        self.assertEqual(self.hasher.hash(None), "")

    def test_empty_string_returns_empty_string(self) -> None:
        """Empty string must return an empty string."""
        self.assertEqual(self.hasher.hash(""), "")

    def test_hash_length_is_64_chars(self) -> None:
        """SHA-256 digest must be exactly 64 hex characters."""
        self.assertEqual(len(self.hasher.hash("response")), 64)

    def test_unicode_input_is_handled(self) -> None:
        """Unicode prompt text must be hashed correctly."""
        result = self.hasher.hash("Ünïcödé rësponse 🤖")
        self.assertEqual(len(result), 64)


if __name__ == "__main__":
    unittest.main()
