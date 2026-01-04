"""Integration tests for the __main__ module."""

import importlib
import sys
from pathlib import Path

import pytest


def run_main_module(file_path: Path) -> int:
    """Run __main__ with given file and return exit code."""
    orig_argv = sys.argv
    sys.argv = ["prog", "--tools", "pylint", str(file_path)]
    try:
        with pytest.raises(SystemExit) as exc_info:
            if "assert_no_inline_directives.__main__" in sys.modules:
                importlib.reload(sys.modules["assert_no_inline_directives.__main__"])
            else:
                importlib.import_module("assert_no_inline_directives.__main__")
        return exc_info.value.code if isinstance(exc_info.value.code, int) else 1
    finally:
        sys.argv = orig_argv


@pytest.mark.integration
class TestMainModule:
    """Tests for the __main__ module."""

    def test_main_module_calls_main_clean(self, tmp_path: Path) -> None:
        """Importing __main__ calls main and exits 0 for clean file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        assert run_main_module(test_file) == 0

    def test_main_module_exits_with_findings(self, tmp_path: Path) -> None:
        """__main__ exits 1 when findings exist."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        assert run_main_module(test_file) == 1
