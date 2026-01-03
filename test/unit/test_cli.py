"""Unit tests for the cli module."""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from assert_no_inline_lint_disables.cli import main


def run_main_with_args(args: list[str]) -> int:
    """Run main() with given args and return exit code."""
    with patch.object(sys, "argv", ["test"] + args):
        try:
            return main()
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1


@pytest.mark.unit
class TestMainFunction:
    """Tests for the main function."""

    def test_no_files_exits_2(self) -> None:
        """No files argument exits 2 (argparse error)."""
        exit_code = run_main_with_args(["--linters", "pylint"])
        assert exit_code == 2

    def test_clean_file_exits_0(self, tmp_path: Path) -> None:
        """Clean file exits 0."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--linters", "pylint", str(test_file)])
        assert exit_code == 0

    def test_file_with_finding_exits_1(self, tmp_path: Path) -> None:
        """File with finding exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        exit_code = run_main_with_args(["--linters", "pylint", str(test_file)])
        assert exit_code == 1

    def test_missing_file_exits_2(self) -> None:
        """Missing file exits 2."""
        exit_code = run_main_with_args(
            ["--linters", "pylint", "/nonexistent/file.py"]
        )
        assert exit_code == 2

    def test_invalid_linter_exits_2(self, tmp_path: Path) -> None:
        """Invalid linter exits 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--linters", "invalid", str(test_file)])
        assert exit_code == 2

    def test_commas_only_linters_exits_2(self, tmp_path: Path) -> None:
        """Linters with only commas exits 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--linters", ",,,", str(test_file)])
        assert exit_code == 2


@pytest.mark.unit
class TestOutputFormats:
    """Tests for output format options."""

    def test_quiet_suppresses_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Quiet flag suppresses output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        run_main_with_args(["--linters", "pylint", "--quiet", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_count_output(self, tmp_path: Path, capsys: Any) -> None:
        """Count flag outputs count."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n# pylint: disable=bar\n")
        run_main_with_args(["--linters", "pylint", "--count", str(test_file)])
        captured = capsys.readouterr()
        assert "2" in captured.out

    def test_json_output(self, tmp_path: Path, capsys: Any) -> None:
        """JSON flag outputs JSON."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        run_main_with_args(["--linters", "pylint", "--json", str(test_file)])
        captured = capsys.readouterr()
        assert "[" in captured.out
        assert "]" in captured.out


@pytest.mark.unit
class TestFlags:
    """Tests for various flags."""

    def test_fail_fast_exits_on_first(self, tmp_path: Path, capsys: Any) -> None:
        """Fail-fast exits on first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=a\n# pylint: disable=b\n")
        run_main_with_args(
            ["--linters", "pylint", "--fail-fast", str(test_file)]
        )
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """Warn-only always exits 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        exit_code = run_main_with_args(
            ["--linters", "pylint", "--warn-only", str(test_file)]
        )
        assert exit_code == 0

    def test_allow_skips_matching(self, tmp_path: Path) -> None:
        """Allow flag skips matching directives."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=too-many-args\n")
        exit_code = run_main_with_args([
            "--linters", "pylint",
            "--allow", "too-many-args",
            str(test_file),
        ])
        assert exit_code == 0

    def test_exclude_skips_matching_files(self, tmp_path: Path) -> None:
        """Exclude flag skips matching files."""
        test_file = tmp_path / "test_generated.py"
        test_file.write_text("# pylint: disable=foo\n")
        exit_code = run_main_with_args([
            "--linters", "pylint",
            "--exclude", "*_generated.py",
            str(test_file),
        ])
        assert exit_code == 0


@pytest.mark.unit
class TestDirectoryAndExtensionHandling:
    """Tests for directory and extension handling."""

    def test_skips_directories(self, tmp_path: Path) -> None:
        """Directories are skipped silently."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        exit_code = run_main_with_args(["--linters", "pylint", str(subdir)])
        assert exit_code == 0

    def test_skips_irrelevant_extensions(self, tmp_path: Path) -> None:
        """Irrelevant extensions are skipped."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("# pylint: disable=foo\n")
        exit_code = run_main_with_args(["--linters", "pylint", str(txt_file)])
        assert exit_code == 0

    def test_scans_relevant_extensions(self, tmp_path: Path) -> None:
        """Relevant extensions are scanned."""
        py_file = tmp_path / "test.py"
        py_file.write_text("# pylint: disable=foo\n")
        exit_code = run_main_with_args(["--linters", "pylint", str(py_file)])
        assert exit_code == 1
