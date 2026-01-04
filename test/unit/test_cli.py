"""Unit tests for the cli module.

These tests use mocking to isolate CLI logic from scanner implementation,
following TDD principles where tests can be written before implementation.
"""

import io
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from assert_no_inline_directives.scanner import Finding

from ..conftest import run_main_with_args


def create_mock_finding(path: str, line: int, tool: str, directive: str) -> Finding:
    """Create a Finding object for testing."""
    return Finding(path=path, line_number=line, tool=tool, directive=directive)


def create_two_findings(path: str, tool: str = "pylint") -> list[Finding]:
    """Create two findings for testing multi-finding scenarios."""
    return [
        Finding(path=path, line_number=1, tool=tool, directive=f"{tool}: disable"),
        Finding(path=path, line_number=2, tool=tool, directive=f"{tool}: disable"),
    ]


@contextmanager
def mock_scan_file(
    return_value: list[Finding] | None = None,
) -> Generator[MagicMock, None, None]:
    """Context manager to mock scan_file with a return value."""
    with patch("assert_no_inline_directives.cli.scan_file") as mock:
        mock.return_value = return_value if return_value is not None else []
        yield mock


@contextmanager
def unreadable_and_readable_files(
    tmp_path: Path
) -> Generator[tuple[Path, Path], None, None]:
    """Create unreadable and readable test files, cleanup on exit."""
    unreadable = tmp_path / "unreadable.py"
    unreadable.write_text("x = 1\n")
    unreadable.chmod(0o000)
    readable = tmp_path / "readable.py"
    readable.write_text("x = 1\n")
    try:
        yield unreadable, readable
    finally:
        unreadable.chmod(0o644)


def run_with_unreadable_file_and_finding(tmp_path: Path) -> tuple[str, str]:
    """Run with unreadable + readable files with finding, return (stdout, stderr)."""
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    try:
        with unreadable_and_readable_files(tmp_path) as (unreadable, readable):
            finding = create_mock_finding(str(readable), 1, "pylint", "pylint: disable")
            with mock_scan_file([finding]):
                run_main_with_args(["--tools", "pylint", str(unreadable), str(readable)])
        return sys.stdout.getvalue(), sys.stderr.getvalue()
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def run_verbose_with_finding(tmp_path: Path) -> str:
    """Run verbose mode with a single finding and return stdout."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1\n")
    finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    try:
        with mock_scan_file([finding]):
            run_main_with_args(["--tools", "pylint", "--verbose", str(test_file)])
        return sys.stdout.getvalue()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


@pytest.mark.unit
class TestMainFunction:
    """Tests for the main function argument handling."""

    def test_no_files_exits_2(self) -> None:
        """No files argument exits 2 (argparse error)."""
        exit_code = run_main_with_args(["--tools", "pylint"])
        assert exit_code == 2

    def test_no_tools_exits_2(self, tmp_path: Path) -> None:
        """No tools argument exits 2 (argparse error)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([str(test_file)])
        assert exit_code == 2


@pytest.mark.unit
class TestMainWithMockedScanner:
    """Tests for main function with mocked scanner."""

    def test_clean_file_exits_0(self, tmp_path: Path) -> None:
        """Clean file (no findings) exits 0."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file([]):
            exit_code = run_main_with_args(["--tools", "pylint", str(test_file)])
        assert exit_code == 0

    def test_file_with_finding_exits_1(self, tmp_path: Path) -> None:
        """File with finding exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with mock_scan_file([finding]):
            exit_code = run_main_with_args(["--tools", "pylint", str(test_file)])
        assert exit_code == 1

    def test_missing_file_exits_2(self) -> None:
        """Missing file exits 2."""
        exit_code = run_main_with_args(
            ["--tools", "pylint", "/nonexistent/file.py"]
        )
        assert exit_code == 2

    def test_invalid_tool_exits_2(self, tmp_path: Path) -> None:
        """Invalid tool exits 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--tools", "invalid", str(test_file)])
        assert exit_code == 2

    def test_commas_only_tools_exits_2(self, tmp_path: Path) -> None:
        """Tools with only commas exits 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--tools", ",,,", str(test_file)])
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
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with mock_scan_file([finding]):
            run_main_with_args(["--tools", "pylint", "--quiet", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_count_output(self, tmp_path: Path, capsys: Any) -> None:
        """Count flag outputs count."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file(create_two_findings(str(test_file))):
            run_main_with_args(["--tools", "pylint", "--count", str(test_file)])
        captured = capsys.readouterr()
        assert "2" in captured.out


@pytest.mark.unit
class TestFlags:
    """Tests for various flags."""

    def test_fail_fast_exits_on_first(self, tmp_path: Path, capsys: Any) -> None:
        """Fail-fast exits on first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file(create_two_findings(str(test_file))):
            run_main_with_args(["--tools", "pylint", "--fail-fast", str(test_file)])
        captured = capsys.readouterr()
        lines = [line for line in captured.out.strip().split("\n") if line]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """Warn-only always exits 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        finding = create_mock_finding(str(test_file), 1, "pylint", "pylint: disable")
        with mock_scan_file([finding]):
            exit_code = run_main_with_args(
                ["--tools", "pylint", "--warn-only", str(test_file)]
            )
        assert exit_code == 0

    def test_allow_passes_to_scan_file(self, tmp_path: Path) -> None:
        """Allow flag is passed to scan_file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file([]) as mock:
            run_main_with_args([
                "--tools", "pylint",
                "--allow", "too-many-args",
                str(test_file),
            ])
        # Verify allow patterns were passed (call_args is guaranteed non-None
        # since mock_scan_file is configured with return value)
        assert "too-many-args" in mock.call_args[0][3]  # allow_patterns is 4th arg

    def test_exclude_skips_matching_files(self, tmp_path: Path) -> None:
        """Exclude flag skips matching files."""
        test_file = tmp_path / "test_generated.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file([]) as mock:
            exit_code = run_main_with_args([
                "--tools", "pylint",
                "--exclude", "*_generated.py",
                str(test_file),
            ])
        assert exit_code == 0
        mock.assert_not_called()  # File was excluded, never scanned


@pytest.mark.unit
class TestDirectoryAndExtensionHandling:
    """Tests for directory and extension handling."""

    def test_scans_directories_recursively(self, tmp_path: Path) -> None:
        """Directories are scanned recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")
        finding = create_mock_finding(str(py_file), 1, "pylint", "pylint: disable")
        with mock_scan_file([finding]) as mock:
            exit_code = run_main_with_args(["--tools", "pylint", str(subdir)])
        assert exit_code == 1
        mock.assert_called_once()

    def test_skips_irrelevant_extensions(self, tmp_path: Path) -> None:
        """Irrelevant extensions are skipped."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("content\n")
        with mock_scan_file([]) as mock:
            exit_code = run_main_with_args(["--tools", "pylint", str(txt_file)])
        assert exit_code == 0
        mock.assert_not_called()  # .txt not scanned for pylint

    def test_scans_relevant_extensions(self, tmp_path: Path) -> None:
        """Relevant extensions are scanned."""
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1\n")
        finding = create_mock_finding(str(py_file), 1, "pylint", "pylint: disable")
        with mock_scan_file([finding]) as mock:
            exit_code = run_main_with_args(["--tools", "pylint", str(py_file)])
        assert exit_code == 1
        mock.assert_called_once()


@pytest.mark.unit
class TestVerboseFlag:
    """Tests for the --verbose flag."""

    def test_verbose_shows_tools(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows tools being checked."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file([]):
            run_main_with_args(
                ["--tools", "pylint,mypy", "--verbose", str(test_file)]
            )
        captured = capsys.readouterr()
        assert "Checking for: mypy, pylint" in captured.out

    def test_verbose_shows_scanning(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows files being scanned."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file([]):
            run_main_with_args(["--tools", "pylint", "--verbose", str(test_file)])
        captured = capsys.readouterr()
        assert f"Scanning: {test_file}" in captured.out

    def test_verbose_silently_skips_directory(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose does not show skipped directories (scans recursively instead)."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        with mock_scan_file([]):
            run_main_with_args(["--tools", "pylint", "--verbose", str(subdir)])
        captured = capsys.readouterr()
        assert "Skipping" not in captured.out

    def test_verbose_silently_skips_extension(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose silently skips irrelevant extensions."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("content\n")
        with mock_scan_file([]):
            run_main_with_args(["--tools", "pylint", "--verbose", str(txt_file)])
        captured = capsys.readouterr()
        assert "Skipping" not in captured.out

    def test_verbose_silently_skips_excluded(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose silently skips excluded files."""
        test_file = tmp_path / "generated.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file([]):
            run_main_with_args([
                "--tools", "pylint",
                "--verbose",
                "--exclude", "*generated.py",
                str(test_file),
            ])
        captured = capsys.readouterr()
        assert "Skipping" not in captured.out

    def test_verbose_shows_findings(self, tmp_path: Path) -> None:
        """Verbose shows findings inline."""
        output = run_verbose_with_finding(tmp_path)
        assert "pylint: disable" in output

    def test_verbose_shows_summary(self, tmp_path: Path) -> None:
        """Verbose shows summary at end."""
        output = run_verbose_with_finding(tmp_path)
        assert "Scanned 1 file(s), found 1 finding(s)" in output

    def test_verbose_short_flag(self, tmp_path: Path, capsys: Any) -> None:
        """Short -v flag works."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file([]):
            run_main_with_args(["--tools", "pylint", "-v", str(test_file)])
        captured = capsys.readouterr()
        assert "Checking for: pylint" in captured.out

    def test_verbose_mutually_exclusive_with_quiet(self, tmp_path: Path) -> None:
        """Verbose and quiet are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([
            "--tools", "pylint", "--verbose", "--quiet", str(test_file)
        ])
        assert exit_code == 2

    def test_verbose_mutually_exclusive_with_count(self, tmp_path: Path) -> None:
        """Verbose and count are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([
            "--tools", "pylint", "--verbose", "--count", str(test_file)
        ])
        assert exit_code == 2

    def test_verbose_with_fail_fast_shows_finding(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose with fail-fast shows finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file(create_two_findings(str(test_file))):
            run_main_with_args([
                "--tools", "pylint", "--verbose", "--fail-fast", str(test_file)
            ])
        captured = capsys.readouterr()
        assert "pylint: disable" in captured.out

    def test_verbose_with_fail_fast_shows_one_finding_summary(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Verbose with fail-fast shows one finding in summary."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with mock_scan_file(create_two_findings(str(test_file))):
            run_main_with_args([
                "--tools", "pylint", "--verbose", "--fail-fast", str(test_file)
            ])
        captured = capsys.readouterr()
        assert "found 1 finding" in captured.out


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling paths."""

    def test_unreadable_file_exits_2(
        self, tmp_path: Path,
    ) -> None:
        """Unreadable file causes exit code 2."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        test_file.chmod(0o000)
        try:
            exit_code = run_main_with_args([
                "--tools", "pylint", str(test_file)
            ])
            assert exit_code == 2
        finally:
            test_file.chmod(0o644)

    def test_unreadable_file_shows_error(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Unreadable file shows error message."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        test_file.chmod(0o000)
        try:
            run_main_with_args([
                "--tools", "pylint", str(test_file)
            ])
            captured = capsys.readouterr()
            assert "Error reading" in captured.err
        finally:
            test_file.chmod(0o644)

    def test_unreadable_file_continues_scanning_exit_code(self, tmp_path: Path) -> None:
        """Unreadable file doesn't stop scanning - exit 1 for finding."""
        with unreadable_and_readable_files(tmp_path) as (unreadable, readable):
            finding = create_mock_finding(str(readable), 1, "pylint", "pylint: disable")
            with mock_scan_file([finding]):
                exit_code = run_main_with_args([
                    "--tools", "pylint", str(unreadable), str(readable)
                ])
            assert exit_code == 1

    def test_unreadable_file_continues_scanning_error_message(self, tmp_path: Path) -> None:
        """Unreadable file shows error but continues scanning."""
        _, stderr = run_with_unreadable_file_and_finding(tmp_path)
        assert "Error reading" in stderr

    def test_unreadable_file_continues_scanning_outputs_finding(self, tmp_path: Path) -> None:
        """Unreadable file continues scanning and outputs finding."""
        stdout, _ = run_with_unreadable_file_and_finding(tmp_path)
        assert "pylint: disable" in stdout


@pytest.mark.unit
class TestGlobPatterns:
    """Tests for glob pattern expansion."""

    def test_glob_pattern_matches_files(self, tmp_path: Path) -> None:
        """Glob pattern matching files expands correctly."""
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1\n")
        pattern = str(tmp_path / "*.py")
        with mock_scan_file([]):
            exit_code = run_main_with_args(["--tools", "pylint", pattern])
        assert exit_code == 0

    def test_glob_pattern_matches_directory(self, tmp_path: Path) -> None:
        """Glob pattern matching directory expands to files inside."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")
        # Pattern matches the directory, which should be expanded
        pattern = str(tmp_path / "sub*")
        finding = create_mock_finding(str(py_file), 1, "pylint", "pylint: disable")
        with mock_scan_file([finding]):
            exit_code = run_main_with_args(["--tools", "pylint", pattern])
        assert exit_code == 1

    def test_glob_pattern_no_match_exits_2(self, tmp_path: Path) -> None:
        """Glob pattern that matches nothing exits 2."""
        pattern = str(tmp_path / "nonexistent*.py")
        exit_code = run_main_with_args(["--tools", "pylint", pattern])
        assert exit_code == 2

    def test_glob_pattern_no_match_shows_error(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Glob pattern that matches nothing shows error message."""
        pattern = str(tmp_path / "nonexistent*.py")
        run_main_with_args(["--tools", "pylint", pattern])
        captured = capsys.readouterr()
        assert "No such file or directory" in captured.err

    def test_recursive_glob_pattern(self, tmp_path: Path) -> None:
        """Recursive glob pattern (**) works correctly."""
        subdir = tmp_path / "deep" / "nested"
        subdir.mkdir(parents=True)
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")
        pattern = str(tmp_path / "**" / "*.py")
        with mock_scan_file([]):
            exit_code = run_main_with_args(["--tools", "pylint", pattern])
        assert exit_code == 0

    def test_question_mark_glob_pattern(self, tmp_path: Path) -> None:
        """Question mark glob pattern works."""
        py_file = tmp_path / "a.py"
        py_file.write_text("x = 1\n")
        pattern = str(tmp_path / "?.py")
        with mock_scan_file([]):
            exit_code = run_main_with_args(["--tools", "pylint", pattern])
        assert exit_code == 0

    def test_bracket_glob_pattern(self, tmp_path: Path) -> None:
        """Bracket glob pattern works."""
        py_file = tmp_path / "a.py"
        py_file.write_text("x = 1\n")
        pattern = str(tmp_path / "[abc].py")
        with mock_scan_file([]):
            exit_code = run_main_with_args(["--tools", "pylint", pattern])
        assert exit_code == 0

    def test_double_star_glob_deduplicates_files_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Glob pattern **/* exits 0 for clean files."""
        subdir = tmp_path / "sub1" / "sub2"
        subdir.mkdir(parents=True)
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")

        pattern = str(tmp_path / "**" / "*")
        with mock_scan_file([]):
            exit_code = run_main_with_args(
                ["--tools", "pylint", "--verbose", pattern]
            )
        assert exit_code == 0

    def test_double_star_glob_deduplicates_files_scan_count(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Glob pattern **/* does not scan files multiple times.

        Regression test: **/* matches both files directly AND directories.
        When a directory is matched, it gets expanded to include its files.
        Without deduplication, files would be scanned once per directory level
        plus once for the direct match.
        """
        subdir = tmp_path / "sub1" / "sub2"
        subdir.mkdir(parents=True)
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")

        pattern = str(tmp_path / "**" / "*")
        with mock_scan_file([]):
            run_main_with_args(
                ["--tools", "pylint", "--verbose", pattern]
            )
        captured = capsys.readouterr()
        scan_count = captured.out.count(f"Scanning: {py_file}")
        assert scan_count == 1
