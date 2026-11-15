"""Integration tests for the CLI module."""

from pathlib import Path
from typing import Any

import pytest
from _pytest.capture import CaptureResult
from test_run_main import run_main_with_args


@pytest.mark.integration
class TestCliExitCodes:
    """Tests for CLI exit codes."""

    def test_exit_0_no_findings(self, tmp_path: Path) -> None:
        """Exit code 0 when no findings."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        exit_code = run_main_with_args(["--tools", "pylint,mypy", str(test_file)])
        assert exit_code == 0

    def test_exit_1_with_findings(self, tmp_path: Path) -> None:
        """Exit code 1 when findings exist."""
        test_file = tmp_path / "dirty.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 1

    def test_exit_2_file_not_found(self) -> None:
        """Exit code 2 when file does not exist."""
        exit_code = run_main_with_args([
            "--tools", "pylint",
            "/nonexistent/path/file.py",
        ])
        assert exit_code == 2

    def test_exit_2_invalid_tool(self, tmp_path: Path) -> None:
        """Exit code 2 when tool is invalid."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--tools", "eslint", str(test_file)])
        assert exit_code == 2

    def test_exit_2_empty_tools(self, tmp_path: Path) -> None:
        """Exit code 2 when tools string is empty."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args(["--tools", "", str(test_file)])
        assert exit_code == 2

    def test_exit_1_overrides_exit_2(self, tmp_path: Path) -> None:
        """If findings exist, exit 1 even if some files have errors."""
        good_file = tmp_path / "good.py"
        good_file.write_text("x = 1\n")
        dirty_file = tmp_path / "dirty.py"
        dirty_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            str(good_file),
            "/nonexistent/file.py",
            str(dirty_file),
        ])
        assert exit_code == 1


@pytest.mark.integration
class TestCliOutput:
    """Tests for CLI output formatting."""

    def test_output_format(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Output format is path:line:tool:directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert f"{test_file}:1:mypy:type: ignore" in captured.out

    def test_multiple_findings_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Multiple findings are output on separate lines."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=foo\n"
            "x = 1  # type: ignore\n"
        )
        run_main_with_args(["--tools", "pylint,mypy", str(test_file)])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2

    def test_no_output_when_clean(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """No stdout when no findings."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        run_main_with_args(["--tools", "pylint,mypy", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""


@pytest.mark.integration
class TestCliMultipleFiles:
    """Tests for scanning multiple files."""

    def test_multiple_clean_files(self, tmp_path: Path) -> None:
        """Exit 0 when all files are clean."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.py"
        file1.write_text("x = 1\n")
        file2.write_text("y = 2\n")
        exit_code = run_main_with_args([
            "--tools", "pylint,mypy",
            str(file1),
            str(file2),
        ])
        assert exit_code == 0

    def test_findings_across_files_count(
        self, two_file_finding_lines: list[str]
    ) -> None:
        """Findings from multiple files are all reported."""
        assert len(two_file_finding_lines) == 2

    def test_findings_across_files_first_file(
        self, two_file_finding_lines: list[str]
    ) -> None:
        """First file finding is reported first."""
        assert "a.py" in two_file_finding_lines[0]

    def test_findings_across_files_second_file(
        self, two_file_finding_lines: list[str]
    ) -> None:
        """Second file finding is reported second."""
        assert "b.py" in two_file_finding_lines[1]


@pytest.mark.integration
class TestCliToolFiltering:
    """Tests for --tools flag."""

    def test_single_tool_exit_code(self, tmp_path: Path) -> None:
        """Single tool exits 1 when finding present."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 1

    def test_single_tool_includes_matching(self, tmp_path: Path, capsys: Any) -> None:
        """Single tool includes matching tool in output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "mypy" in captured.out

    def test_single_tool_excludes_other(self, tmp_path: Path, capsys: Any) -> None:
        """Single tool excludes other tools from output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "pylint" not in captured.out

    def test_multiple_tools_includes_pylint(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Multiple tools include pylint in output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--tools", "pylint,mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "pylint" in captured.out

    def test_multiple_tools_includes_mypy(self, tmp_path: Path, capsys: Any) -> None:
        """Multiple tools include mypy in output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--tools", "pylint,mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "mypy" in captured.out


@pytest.mark.integration
class TestCliExclude:
    """Tests for --exclude flag."""

    def test_exclude_single_pattern(self, tmp_path: Path) -> None:
        """Excluded files are skipped."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            "--exclude", "*.py",
            str(test_file),
        ])
        assert exit_code == 0

    def test_exclude_multiple_patterns_includes_test(
        self, exclude_vendor_output: str
    ) -> None:
        """Multiple exclude patterns include non-excluded file."""
        assert "test.py" in exclude_vendor_output

    def test_exclude_multiple_patterns_excludes_vendor(
        self, exclude_vendor_output: str
    ) -> None:
        """Multiple exclude patterns exclude vendor file."""
        assert "vendor.py" not in exclude_vendor_output


@pytest.mark.integration
class TestCliQuiet:
    """Tests for --quiet flag."""

    def test_quiet_exit_code(self, tmp_path: Path) -> None:
        """Quiet mode exits 1 with findings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            "--quiet",
            str(test_file),
        ])
        assert exit_code == 1

    def test_quiet_no_output(self, tmp_path: Path, capsys: Any) -> None:
        """Quiet mode produces no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args([
            "--tools", "mypy",
            "--quiet",
            str(test_file),
        ])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_still_returns_exit_code(self, tmp_path: Path) -> None:
        """Quiet mode still returns correct exit code."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            "--quiet",
            str(test_file),
        ])
        assert exit_code == 0


@pytest.mark.integration
class TestCliCount:
    """Tests for --count flag."""

    def test_count_output(self, tmp_path: Path, capsys: Any) -> None:
        """Count mode outputs only the count."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--tools", "pylint,mypy", "--count", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out.strip() == "2"

    def test_count_zero(self, tmp_path: Path, capsys: Any) -> None:
        """Count mode outputs 0 for clean files."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        run_main_with_args(["--tools", "mypy", "--count", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out.strip() == "0"


@pytest.mark.integration
class TestCliBehaviorFlags:
    """Tests for --fail-fast and --warn-only flags."""

    def test_fail_fast_exit_code(self, tmp_path: Path) -> None:
        """Fail-fast exits 1 on first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "pylint,mypy",
            "--fail-fast",
            str(test_file),
        ])
        assert exit_code == 1

    def test_fail_fast_single_output(self, tmp_path: Path, capsys: Any) -> None:
        """Fail-fast outputs only first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args([
            "--tools", "pylint,mypy",
            "--fail-fast",
            str(test_file),
        ])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """Warn-only always exits 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            "--warn-only",
            str(test_file),
        ])
        assert exit_code == 0

    def test_warn_only_still_outputs(self, tmp_path: Path, capsys: Any) -> None:
        """Warn-only still outputs findings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args(["--tools", "mypy", "--warn-only", str(test_file)])
        captured = capsys.readouterr()
        assert "mypy" in captured.out


@pytest.mark.integration
class TestCliAllow:
    """Tests for --allow flag."""

    def test_allow_skips_matching(self, tmp_path: Path) -> None:
        """Allowed patterns are skipped."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore[import]\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            "--allow", "type: ignore[import]",
            str(test_file),
        ])
        assert exit_code == 0

    def test_allow_multiple_patterns_count(
        self, allow_multiple_lines: list[str]
    ) -> None:
        """Multiple allow patterns - only non-allowed finding reported."""
        assert len(allow_multiple_lines) == 1

    def test_allow_multiple_patterns_content(
        self, allow_multiple_lines: list[str]
    ) -> None:
        """Multiple allow patterns - correct finding is reported."""
        assert "type: ignore" in allow_multiple_lines[0]

    def test_allow_multiple_patterns_excludes_import(
        self, allow_multiple_lines: list[str]
    ) -> None:
        """Multiple allow patterns - import variant not in output."""
        assert "[import]" not in allow_multiple_lines[0]


@pytest.mark.integration
class TestCliExtensionFiltering:
    """Tests for automatic file extension filtering based on linters."""

    def test_skips_irrelevant_extensions(self, tmp_path: Path) -> None:
        """Files with irrelevant extensions are skipped."""
        py_file = tmp_path / "test.py"
        txt_file = tmp_path / "test.txt"
        py_file.write_text("x = 1  # type: ignore\n")
        txt_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            str(py_file),
            str(txt_file),
        ])
        assert exit_code == 1  # Only py_file should be scanned

    def test_pylint_only_scans_py_includes(self, pylint_py_yaml_output: str) -> None:
        """Pylint linter includes .py files."""
        assert "test.py" in pylint_py_yaml_output

    def test_pylint_only_scans_py_excludes_yaml(
        self, pylint_py_yaml_output: str
    ) -> None:
        """Pylint linter excludes yaml files."""
        assert "test.yaml" not in pylint_py_yaml_output

    def test_yamllint_only_scans_yaml(self, yamllint_output: str) -> None:
        """Yamllint linter scans .yaml files."""
        assert "test.yaml" in yamllint_output

    def test_yamllint_only_scans_yml(self, yamllint_output: str) -> None:
        """Yamllint linter scans .yml files."""
        assert "test.yml" in yamllint_output

    def test_yamllint_excludes_py(self, yamllint_output: str) -> None:
        """Yamllint linter excludes .py files."""
        assert "test.py" not in yamllint_output

    def test_combined_linters_scan_py(self, combined_linters_output: str) -> None:
        """Combined linters scan .py files."""
        assert "test.py" in combined_linters_output

    def test_combined_linters_scan_yaml(self, combined_linters_output: str) -> None:
        """Combined linters scan .yaml files."""
        assert "test.yaml" in combined_linters_output

    def test_combined_linters_exclude_txt(self, combined_linters_output: str) -> None:
        """Combined linters exclude .txt files."""
        assert "test.txt" not in combined_linters_output

    def test_case_insensitive_extension(self, tmp_path: Path, capsys: Any) -> None:
        """Extension matching is case-insensitive."""
        py_file = tmp_path / "test.PY"
        py_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args(["--tools", "mypy", str(py_file)])
        captured = capsys.readouterr()
        assert "test.PY" in captured.out


@pytest.mark.integration
class TestCliVerbose:
    """Tests for --verbose flag integration scenarios."""

    def test_verbose_shows_checking_for(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows 'Checking for' header."""
        py_file = tmp_path / "code.py"
        py_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args([
            "--tools", "pylint,mypy",
            "--verbose",
            str(py_file),
        ])
        out = capsys.readouterr().out
        assert "Checking for:" in out

    def test_verbose_shows_scanning(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows 'Scanning' messages."""
        py_file = tmp_path / "code.py"
        py_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args([
            "--tools", "pylint,mypy",
            "--verbose",
            str(py_file),
        ])
        out = capsys.readouterr().out
        assert "Scanning:" in out

    def test_verbose_no_skipping_messages(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose does not show skipping messages."""
        py_file = tmp_path / "code.py"
        py_file.write_text("x = 1  # type: ignore\n")
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("not scanned\n")
        run_main_with_args([
            "--tools", "pylint,mypy",
            "--verbose",
            str(py_file), str(txt_file),
        ])
        out = capsys.readouterr().out
        assert "Skipping" not in out

    def test_verbose_shows_findings(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows findings."""
        py_file = tmp_path / "code.py"
        py_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args([
            "--tools", "mypy",
            "--verbose",
            str(py_file),
        ])
        out = capsys.readouterr().out
        assert "type: ignore" in out

    def test_verbose_shows_summary(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows summary."""
        py_file = tmp_path / "code.py"
        py_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args([
            "--tools", "mypy",
            "--verbose",
            str(py_file),
        ])
        out = capsys.readouterr().out
        assert "Scanned 1 file(s), found 1 finding(s)" in out

    def test_verbose_fail_fast_shows_first_file(
        self, verbose_fail_fast_output: str
    ) -> None:
        """Verbose with fail-fast shows first file."""
        assert "first.py" in verbose_fail_fast_output

    def test_verbose_fail_fast_shows_finding(
        self, verbose_fail_fast_output: str
    ) -> None:
        """Verbose with fail-fast shows finding."""
        assert "pylint: disable" in verbose_fail_fast_output

    def test_verbose_fail_fast_excludes_second_file(
        self, verbose_fail_fast_output: str
    ) -> None:
        """Verbose with fail-fast excludes second file."""
        assert "second.py" not in verbose_fail_fast_output

    def test_verbose_fail_fast_shows_one_finding_summary(
        self, verbose_fail_fast_output: str
    ) -> None:
        """Verbose with fail-fast shows one finding in summary."""
        assert "found 1 finding" in verbose_fail_fast_output


@pytest.mark.integration
class TestCliStringLiteralHandling:
    """Tests for string literal handling through the CLI."""

    def test_single_quoted_string_not_detected_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Directives in single-quoted strings - exit 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("s = 'type: ignore'\n")
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0

    def test_single_quoted_string_not_detected_no_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in single-quoted strings - no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("s = 'type: ignore'\n")
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_double_quoted_string_not_detected_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Directives in double-quoted strings - exit 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "type: ignore"\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0

    def test_double_quoted_string_not_detected_no_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in double-quoted strings - no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "type: ignore"\n')
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_triple_quoted_string_not_detected_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Directives in triple-quoted strings - exit 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = """type: ignore"""\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0

    def test_triple_quoted_string_not_detected_no_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in triple-quoted strings - no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = """type: ignore"""\n')
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_triple_single_quoted_string_not_detected_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Directives in triple single-quoted strings - exit 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("s = '''type: ignore'''\n")
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0

    def test_triple_single_quoted_string_not_detected_no_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in triple single-quoted strings - no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("s = '''type: ignore'''\n")
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_multiline_triple_quoted_string_not_detected_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Directives in multiline triple-quoted strings - exit 0."""
        test_file = tmp_path / "test.py"
        content = '''s = """
type: ignore
pylint: disable
"""
'''
        test_file.write_text(content)
        exit_code = run_main_with_args(["--tools", "mypy,pylint", str(test_file)])
        assert exit_code == 0

    def test_multiline_triple_quoted_string_not_detected_no_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in multiline triple-quoted strings - no output."""
        test_file = tmp_path / "test.py"
        content = '''s = """
type: ignore
pylint: disable
"""
'''
        test_file.write_text(content)
        run_main_with_args(["--tools", "mypy,pylint", str(test_file)])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_comment_after_string_detected_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Directives in comments after strings - exit 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "hello"  # type: ignore\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 1

    def test_comment_after_string_detected_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in comments after strings are detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "hello"  # type: ignore\n')
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "type: ignore" in captured.out

    def test_escaped_quote_in_string_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Escaped quotes in strings - exit 1 when comment present."""
        test_file = tmp_path / "test.py"
        test_file.write_text(r's = "escaped \" quote"  # type: ignore' + '\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 1

    def test_escaped_quote_in_string_output(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Escaped quotes in strings don't break parsing."""
        test_file = tmp_path / "test.py"
        test_file.write_text(r's = "escaped \" quote"  # type: ignore' + '\n')
        run_main_with_args(["--tools", "mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "type: ignore" in captured.out


@pytest.mark.integration
class TestCliDirectoryHandling:
    """Tests for directory handling."""

    def test_scans_directories_recursively(self, tmp_path: Path) -> None:
        """Directories are scanned recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        nested_file = subdir / "test.py"
        nested_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            str(subdir),
        ])
        assert exit_code == 1  # Finding detected in nested file

    def test_directories_do_not_cause_error_in_err(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directories do not produce 'Error' messages."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        run_main_with_args([
            "--tools", "mypy",
            str(subdir),
            str(test_file),
        ])
        captured = capsys.readouterr()
        assert "Error" not in captured.err

    def test_directories_do_not_cause_is_a_directory_message(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directories do not produce 'Is a directory' messages."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        run_main_with_args([
            "--tools", "mypy",
            str(subdir),
            str(test_file),
        ])
        captured = capsys.readouterr()
        assert "Is a directory" not in captured.err

    def test_unreadable_file_in_directory_exit_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Unreadable file in directory - exit 1 for readable finding."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        unreadable = subdir / "unreadable.py"
        unreadable.write_text("content\n")
        unreadable.chmod(0o000)
        readable = subdir / "readable.py"
        readable.write_text("x = 1  # type: ignore\n")
        try:
            exit_code = run_main_with_args([
                "--tools", "mypy", str(subdir)
            ])
            assert exit_code == 1  # Finding in readable file
        finally:
            unreadable.chmod(0o644)

    def test_unreadable_file_in_directory_error_message(
        self, unreadable_in_directory: CaptureResult[str]
    ) -> None:
        """Unreadable file in directory shows error message."""
        assert "Error reading" in unreadable_in_directory.err

    def test_unreadable_file_in_directory_continues_scanning(
        self, unreadable_in_directory: CaptureResult[str]
    ) -> None:
        """Unreadable file in directory continues scanning other files."""
        assert "type: ignore" in unreadable_in_directory.out


@pytest.mark.integration
class TestCliGlobPatterns:
    """Integration tests for glob pattern expansion.

    Unit tests cover all glob pattern types exhaustively with mocking.
    These integration tests verify the full pipeline works with real files.
    """

    def test_glob_expands_and_scans_multiple_files_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Glob pattern expands to multiple files - exit 1."""
        (tmp_path / "alpha.py").write_text("a = 1  # type: ignore\n")
        (tmp_path / "beta.py").write_text("b = 2  # type: ignore\n")
        (tmp_path / "gamma.py").write_text("clean code\n")
        exit_code = run_main_with_args([
            "--tools", "mypy", str(tmp_path / "*.py")
        ])
        assert exit_code == 1

    def test_glob_expands_and_scans_multiple_files_includes_alpha(
        self, glob_three_files_output: str
    ) -> None:
        """Glob pattern includes alpha.py."""
        assert "alpha.py" in glob_three_files_output

    def test_glob_expands_and_scans_multiple_files_includes_beta(
        self, glob_three_files_output: str
    ) -> None:
        """Glob pattern includes beta.py."""
        assert "beta.py" in glob_three_files_output

    def test_glob_expands_and_scans_multiple_files_excludes_clean(
        self, glob_three_files_output: str
    ) -> None:
        """Glob pattern excludes gamma.py (no finding)."""
        assert "gamma.py" not in glob_three_files_output

    def test_glob_matching_directory_expands_contents_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Glob matching a directory name - exit 1."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "module.py").write_text("# pylint: disable=all\n")
        exit_code = run_main_with_args([
            "--tools", "pylint", str(tmp_path / "s*")
        ])
        assert exit_code == 1

    def test_glob_matching_directory_expands_contents_output(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Glob matching a directory name expands to scan files inside."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "module.py").write_text("# pylint: disable=all\n")
        run_main_with_args([
            "--tools", "pylint", str(tmp_path / "s*")
        ])
        assert "module.py" in capsys.readouterr().out

    def test_recursive_glob_finds_deeply_nested_files_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Recursive ** glob - exit 1."""
        nested = tmp_path / "src" / "pkg" / "subpkg"
        nested.mkdir(parents=True)
        (nested / "module.py").write_text("# pylint: disable=all\n")
        (tmp_path / "root.py").write_text("# pylint: disable=all\n")
        exit_code = run_main_with_args([
            "--tools", "pylint", str(tmp_path / "**" / "*.py")
        ])
        assert exit_code == 1

    def test_recursive_glob_finds_root_file(self, recursive_glob_output: str) -> None:
        """Recursive ** glob finds root file."""
        assert "root.py" in recursive_glob_output

    def test_recursive_glob_finds_nested_file(self, recursive_glob_output: str) -> None:
        """Recursive ** glob finds nested file."""
        assert "module.py" in recursive_glob_output

    def test_nonexistent_glob_pattern_reports_error_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Glob pattern matching nothing - exit 2."""
        exit_code = run_main_with_args([
            "--tools", "mypy", str(tmp_path / "no_match_*.py")
        ])
        assert exit_code == 2

    def test_nonexistent_glob_pattern_reports_error_message(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Glob pattern matching nothing reports error with pattern name."""
        run_main_with_args([
            "--tools", "mypy", str(tmp_path / "no_match_*.py")
        ])
        assert "no_match_*.py" in capsys.readouterr().err
