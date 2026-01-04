"""Integration tests for the CLI module."""

from pathlib import Path
from typing import Any

import pytest

from ..conftest import run_main_with_args


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

    def test_findings_across_files(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Findings from multiple files are all reported."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("# pylint: disable=foo\n")
        run_main_with_args(["--tools", "pylint,mypy", str(file1), str(file2)])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2
        assert "a.py" in lines[0]
        assert "b.py" in lines[1]


@pytest.mark.integration
class TestCliToolFiltering:
    """Tests for --tools flag."""

    def test_single_tool(self, tmp_path: Path, capsys: Any) -> None:
        """Only specified tool is checked."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "mypy" in captured.out
        assert "pylint" not in captured.out

    def test_multiple_tools(self, tmp_path: Path, capsys: Any) -> None:
        """Multiple specified tools are checked."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        run_main_with_args(["--tools", "pylint,mypy", str(test_file)])
        captured = capsys.readouterr()
        assert "pylint" in captured.out
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

    def test_exclude_multiple_patterns(self, tmp_path: Path, capsys: Any) -> None:
        """Multiple exclude patterns work together."""
        file1 = tmp_path / "test.py"
        file2 = tmp_path / "vendor.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("y = 2  # type: ignore\n")
        run_main_with_args([
            "--tools", "mypy",
            "--exclude", "*vendor*",
            str(file1),
            str(file2),
        ])
        captured = capsys.readouterr()
        assert "test.py" in captured.out
        assert "vendor.py" not in captured.out


@pytest.mark.integration
class TestCliQuiet:
    """Tests for --quiet flag."""

    def test_quiet_no_output(self, tmp_path: Path, capsys: Any) -> None:
        """Quiet mode produces no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "mypy",
            "--quiet",
            str(test_file),
        ])
        assert exit_code == 1
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

    def test_fail_fast_exits_on_first(self, tmp_path: Path, capsys: Any) -> None:
        """Fail-fast exits on first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        exit_code = run_main_with_args([
            "--tools", "pylint,mypy",
            "--fail-fast",
            str(test_file),
        ])
        assert exit_code == 1
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

    def test_allow_multiple_patterns(self, tmp_path: Path, capsys: Any) -> None:
        """Multiple allow patterns work together."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=too-many-arguments\n"
            "x = 1  # type: ignore[import]\n"
            "y = 2  # type: ignore\n"
        )
        run_main_with_args([
            "--tools", "pylint,mypy",
            "--allow", "type: ignore[import],too-many-arguments",
            str(test_file),
        ])
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) == 1
        assert "type: ignore" in lines[0]
        assert "[import]" not in lines[0]


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

    def test_pylint_only_scans_py(self, tmp_path: Path, capsys: Any) -> None:
        """Pylint linter only scans .py files."""
        py_file = tmp_path / "test.py"
        yaml_file = tmp_path / "test.yaml"
        py_file.write_text("# pylint: disable=foo\n")
        yaml_file.write_text("# pylint: disable=foo\n")
        run_main_with_args([
            "--tools", "pylint",
            str(py_file),
            str(yaml_file),
        ])
        captured = capsys.readouterr()
        assert "test.py" in captured.out
        assert "test.yaml" not in captured.out

    def test_yamllint_only_scans_yaml_yml(self, tmp_path: Path, capsys: Any) -> None:
        """Yamllint linter only scans .yaml and .yml files."""
        yaml_file = tmp_path / "test.yaml"
        yml_file = tmp_path / "test.yml"
        py_file = tmp_path / "test.py"
        yaml_file.write_text("# yamllint disable\n")
        yml_file.write_text("# yamllint disable\n")
        py_file.write_text("# yamllint disable\n")
        run_main_with_args([
            "--tools", "yamllint",
            str(yaml_file),
            str(yml_file),
            str(py_file),
        ])
        captured = capsys.readouterr()
        assert "test.yaml" in captured.out
        assert "test.yml" in captured.out
        assert "test.py" not in captured.out

    def test_combined_linters_scan_all_relevant(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Combined linters scan all relevant file types."""
        py_file = tmp_path / "test.py"
        yaml_file = tmp_path / "test.yaml"
        txt_file = tmp_path / "test.txt"
        py_file.write_text("# pylint: disable=foo\n")
        yaml_file.write_text("# yamllint disable\n")
        txt_file.write_text("# pylint: disable=foo\n")
        run_main_with_args([
            "--tools", "pylint,yamllint",
            str(py_file),
            str(yaml_file),
            str(txt_file),
        ])
        captured = capsys.readouterr()
        assert "test.py" in captured.out
        assert "test.yaml" in captured.out
        assert "test.txt" not in captured.out

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

    def test_verbose_full_workflow(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose shows complete workflow: tools, scans, findings, summary."""
        # Create various files to test verbose output
        py_file = tmp_path / "code.py"
        py_file.write_text("x = 1  # type: ignore\n")
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("not scanned\n")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        excluded = tmp_path / "generated.py"
        excluded.write_text("# pylint: disable=foo\n")
        run_main_with_args([
            "--tools", "pylint,mypy",
            "--verbose",
            "--exclude", "*generated.py",
            str(py_file), str(txt_file), str(subdir), str(excluded),
        ])
        out = capsys.readouterr().out
        assert "Checking for:" in out
        assert "Scanning:" in out
        # Skipping messages are not shown (files are silently skipped)
        assert "Skipping" not in out
        assert "type: ignore" in out
        assert "Scanned 1 file(s), found 1 finding(s)" in out

    def test_verbose_fail_fast_stops_early(self, tmp_path: Path, capsys: Any) -> None:
        """Verbose with fail-fast stops after first finding and shows summary."""
        file1 = tmp_path / "first.py"
        file1.write_text("# pylint: disable=one\n")
        file2 = tmp_path / "second.py"
        file2.write_text("# pylint: disable=two\n")
        run_main_with_args([
            "--tools", "pylint", "--verbose", "--fail-fast",
            str(file1), str(file2),
        ])
        out = capsys.readouterr().out
        assert "first.py" in out
        assert "pylint: disable" in out
        assert "second.py" not in out
        assert "found 1 finding" in out


@pytest.mark.integration
class TestCliStringLiteralHandling:
    """Tests for string literal handling through the CLI."""

    def test_single_quoted_string_not_detected(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in single-quoted strings are not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text("s = 'type: ignore'\n")
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_double_quoted_string_not_detected(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in double-quoted strings are not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "type: ignore"\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_triple_quoted_string_not_detected(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in triple-quoted strings are not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = """type: ignore"""\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_triple_single_quoted_string_not_detected(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in triple single-quoted strings are not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text("s = '''type: ignore'''\n")
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_multiline_triple_quoted_string_not_detected(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in multiline triple-quoted strings are not detected."""
        test_file = tmp_path / "test.py"
        content = '''s = """
type: ignore
pylint: disable
"""
'''
        test_file.write_text(content)
        exit_code = run_main_with_args(["--tools", "mypy,pylint", str(test_file)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_comment_after_string_detected(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directives in comments after strings are detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "hello"  # type: ignore\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "type: ignore" in captured.out

    def test_escaped_quote_in_string(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Escaped quotes in strings don't break parsing."""
        test_file = tmp_path / "test.py"
        test_file.write_text(r's = "escaped \" quote"  # type: ignore' + '\n')
        exit_code = run_main_with_args(["--tools", "mypy", str(test_file)])
        assert exit_code == 1
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

    def test_directories_do_not_cause_errors(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Directories do not produce error messages."""
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
        assert "Is a directory" not in captured.err

    def test_unreadable_file_in_directory(
        self,
        tmp_path: Path,
        capsys: Any,
    ) -> None:
        """Unreadable file in directory causes error but continues."""
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
            captured = capsys.readouterr()
            assert "Error reading" in captured.err
            assert "type: ignore" in captured.out
        finally:
            unreadable.chmod(0o644)


@pytest.mark.integration
class TestCliGlobPatterns:
    """Integration tests for glob pattern expansion.

    Unit tests cover all glob pattern types exhaustively with mocking.
    These integration tests verify the full pipeline works with real files.
    """

    def test_glob_expands_and_scans_multiple_files(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Glob pattern expands to multiple files and scans all of them."""
        (tmp_path / "alpha.py").write_text("a = 1  # type: ignore\n")
        (tmp_path / "beta.py").write_text("b = 2  # type: ignore\n")
        (tmp_path / "gamma.py").write_text("clean code\n")
        exit_code = run_main_with_args([
            "--tools", "mypy", str(tmp_path / "*.py")
        ])
        assert exit_code == 1
        output = capsys.readouterr().out
        # Verify multiple files were scanned and findings reported
        assert "alpha.py" in output
        assert "beta.py" in output
        assert "gamma.py" not in output  # No finding in clean file

    def test_glob_matching_directory_expands_contents(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Glob matching a directory name expands to scan files inside."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "module.py").write_text("# pylint: disable=all\n")
        # Glob matches directory name, should expand and scan contents
        exit_code = run_main_with_args([
            "--tools", "pylint", str(tmp_path / "s*")
        ])
        assert exit_code == 1
        assert "module.py" in capsys.readouterr().out

    def test_recursive_glob_finds_deeply_nested_files(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Recursive ** glob finds files in nested directories."""
        nested = tmp_path / "src" / "pkg" / "subpkg"
        nested.mkdir(parents=True)
        (nested / "module.py").write_text("# pylint: disable=all\n")
        (tmp_path / "root.py").write_text("# pylint: disable=all\n")
        exit_code = run_main_with_args([
            "--tools", "pylint", str(tmp_path / "**" / "*.py")
        ])
        assert exit_code == 1
        output = capsys.readouterr().out
        # Both root and deeply nested files found
        assert "root.py" in output
        assert "module.py" in output

    def test_nonexistent_glob_pattern_reports_error(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Glob pattern matching nothing reports error with pattern name."""
        exit_code = run_main_with_args([
            "--tools", "mypy", str(tmp_path / "no_match_*.py")
        ])
        assert exit_code == 2
        assert "no_match_*.py" in capsys.readouterr().err
