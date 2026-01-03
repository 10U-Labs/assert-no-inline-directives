"""Unit tests for the __main__ module."""

from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestMainModule:
    """Tests for __main__.py module."""

    def test_main_module_runs(self) -> None:
        """__main__ module executes main()."""
        with patch("assert_no_inline_lint_disables.cli.main") as mock_main:
            mock_main.return_value = 0
            # Import triggers execution
            import importlib
            import assert_no_inline_lint_disables.__main__  # noqa: F401
            importlib.reload(assert_no_inline_lint_disables.__main__)
            mock_main.assert_called()
