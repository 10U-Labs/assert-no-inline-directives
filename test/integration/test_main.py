"""Integration tests for the __main__ module."""

import importlib
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
class TestMainModule:
    """Tests for the __main__ module."""

    def test_main_module_calls_main_clean(self, tmp_path: Path) -> None:
        """Importing __main__ calls main and exits 0 for clean file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        orig_argv = sys.argv
        sys.argv = ["prog", "--linters", "pylint", str(test_file)]
        try:
            with pytest.raises(SystemExit) as exc_info:
                if "assert_no_inline_lint_disables.__main__" in sys.modules:
                    importlib.reload(sys.modules["assert_no_inline_lint_disables.__main__"])
                else:
                    importlib.import_module("assert_no_inline_lint_disables.__main__")
            assert exc_info.value.code == 0
        finally:
            sys.argv = orig_argv

    def test_main_module_exits_with_findings(self, tmp_path: Path) -> None:
        """__main__ exits 1 when findings exist."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")

        orig_argv = sys.argv
        sys.argv = ["prog", "--linters", "pylint", str(test_file)]
        try:
            with pytest.raises(SystemExit) as exc_info:
                if "assert_no_inline_lint_disables.__main__" in sys.modules:
                    importlib.reload(sys.modules["assert_no_inline_lint_disables.__main__"])
                else:
                    importlib.import_module("assert_no_inline_lint_disables.__main__")
            assert exc_info.value.code == 1
        finally:
            sys.argv = orig_argv
