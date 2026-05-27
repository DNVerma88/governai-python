"""Tests for the governai.core package import.

Verifies that the package is importable and exposes its public API.
"""

from __future__ import annotations

import unittest


class TestCoreImport(unittest.TestCase):
    """Tests that governai.core imports cleanly."""

    def test_core_package_is_importable(self) -> None:
        """governai.core must be importable without errors."""
        import governai.core  # noqa: F401

    def test_core_has_all_attribute(self) -> None:
        """governai.core must define __all__."""
        import governai.core

        self.assertTrue(hasattr(governai.core, "__all__"))


if __name__ == "__main__":
    unittest.main()
