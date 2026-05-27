"""Tests for the governai.security package import.

Verifies that the package is importable and exposes its public API.
"""

from __future__ import annotations

import unittest


class TestSecurityImport(unittest.TestCase):
    """Tests that governai.security imports cleanly."""

    def test_security_package_is_importable(self) -> None:
        """governai.security must be importable without errors."""
        import governai.security  # noqa: F401

    def test_security_has_all_attribute(self) -> None:
        """governai.security must define __all__."""
        import governai.security

        self.assertTrue(hasattr(governai.security, "__all__"))


if __name__ == "__main__":
    unittest.main()
