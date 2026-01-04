"""Unit tests for the __main__ module."""

import importlib
import sys
from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestMainModule:
    """Tests for __main__.py module."""

    def test_main_module_runs(self) -> None:
        """__main__ module executes main()."""
        with patch("assert_no_inline_directives.cli.main") as mock_main:
            mock_main.return_value = 0
            if "assert_no_inline_directives.__main__" in sys.modules:
                importlib.reload(sys.modules["assert_no_inline_directives.__main__"])
            else:
                importlib.import_module("assert_no_inline_directives.__main__")
            assert mock_main.called

    def test_main_module_can_be_imported(self) -> None:
        """__main__ module exists and can be imported."""
        with patch("assert_no_inline_directives.cli.main"):
            module = importlib.import_module("assert_no_inline_directives.__main__")
            assert module is not None
