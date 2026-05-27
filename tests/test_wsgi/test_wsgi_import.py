"""Tests for the governai.wsgi package import.

Verifies that the package is importable and exposes its public API.
"""

from __future__ import annotations

import unittest


class TestWsgiImport(unittest.TestCase):
    """Tests that governai.wsgi imports cleanly."""

    def test_wsgi_package_is_importable(self) -> None:
        """governai.wsgi must be importable without errors."""
        import governai.wsgi  # noqa: F401

    def test_wsgi_has_all_attribute(self) -> None:
        """governai.wsgi must define __all__."""
        import governai.wsgi

        self.assertTrue(hasattr(governai.wsgi, "__all__"))


if __name__ == "__main__":
    unittest.main()
