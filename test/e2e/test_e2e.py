"""End-to-end tests for the CLI tool."""

import subprocess
from pathlib import Path

import pytest


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess."""
    return subprocess.run(
        ["assert-no-inline-lint-disables", *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.e2e
class TestCliExitCodes:
    """E2E tests for CLI exit codes."""

    def test_exit_0_clean_file(self, tmp_path: Path) -> None:
        """Exit code 0 for a clean file."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_exit_1_with_pylint_disable(self, tmp_path: Path) -> None:
        """Exit code 1 for file with pylint: disable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=missing-docstring\nx = 1\n")
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 1
        assert "pylint" in result.stdout

    def test_exit_1_with_mypy_ignore(self, tmp_path: Path) -> None:
        """Exit code 1 for file with type: ignore."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1
        assert "mypy" in result.stdout

    def test_exit_1_with_yamllint_disable(self, tmp_path: Path) -> None:
        """Exit code 1 for file with yamllint disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli("--linters", "yamllint", str(test_file))
        assert result.returncode == 1
        assert "yamllint" in result.stdout

    def test_exit_2_missing_file(self) -> None:
        """Exit code 2 for missing file."""
        result = run_cli("--linters", "pylint", "/nonexistent/path/file.py")
        assert result.returncode == 2

    def test_exit_2_missing_linters_flag(self, tmp_path: Path) -> None:
        """Exit code 2 when --linters flag is missing."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli(str(test_file))
        assert result.returncode == 2

    def test_exit_2_empty_linters(self, tmp_path: Path) -> None:
        """Exit code 2 for empty linters string."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--linters", "", str(test_file))
        assert result.returncode == 2
        assert "At least one linter" in result.stderr

    def test_exit_2_invalid_linter(self, tmp_path: Path) -> None:
        """Exit code 2 for invalid linter name."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--linters", "eslint", str(test_file))
        assert result.returncode == 2


@pytest.mark.e2e
class TestOutputFormat:
    """E2E tests for output format."""

    def test_output_format_path_line_linter_directive(
        self,
        tmp_path: Path,
    ) -> None:
        """Output format is path:line:linter:directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1
        expected = f"{test_file}:1:mypy:type: ignore\n"
        assert result.stdout == expected

    def test_line_number_is_1_based(self, tmp_path: Path) -> None:
        """Line numbers are 1-based."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\ny = 2\nz = foo()  # type: ignore\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert ":3:" in result.stdout


@pytest.mark.e2e
class TestAllDirectiveTypes:
    """E2E tests verifying all directive types are detected."""

    def test_yamllint_disable(self, tmp_path: Path) -> None:
        """Detects yamllint disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable\nkey: value\n")
        result = run_cli("--linters", "yamllint", str(test_file))
        assert result.returncode == 1
        assert "yamllint:yamllint disable" in result.stdout

    def test_yamllint_disable_line(self, tmp_path: Path) -> None:
        """Detects yamllint disable-line."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli("--linters", "yamllint", str(test_file))
        assert result.returncode == 1
        assert "yamllint:yamllint disable-line" in result.stdout

    def test_yamllint_disable_file(self, tmp_path: Path) -> None:
        """Detects yamllint disable-file."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable-file\nkey: value\n")
        result = run_cli("--linters", "yamllint", str(test_file))
        assert result.returncode == 1
        assert "yamllint:yamllint disable-file" in result.stdout

    def test_pylint_disable(self, tmp_path: Path) -> None:
        """Detects pylint: disable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 1
        assert "pylint:pylint: disable" in result.stdout

    def test_pylint_disable_next(self, tmp_path: Path) -> None:
        """Detects pylint: disable-next."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable-next=foo\nx = 1\n")
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 1
        assert "pylint:pylint: disable-next" in result.stdout

    def test_pylint_skip_file(self, tmp_path: Path) -> None:
        """Detects pylint: skip-file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: skip-file\nx = 1\n")
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 1
        assert "pylint:pylint: skip-file" in result.stdout

    def test_mypy_type_ignore(self, tmp_path: Path) -> None:
        """Detects type: ignore."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1
        assert "mypy:type: ignore" in result.stdout

    def test_mypy_type_ignore_bracketed(self, tmp_path: Path) -> None:
        """Detects type: ignore[error-code]."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore[attr-defined]\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1
        assert "mypy:type: ignore" in result.stdout

    def test_mypy_ignore_errors(self, tmp_path: Path) -> None:
        """Detects mypy: ignore-errors."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# mypy: ignore-errors\nx = 1\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1
        assert "mypy:mypy: ignore-errors" in result.stdout


@pytest.mark.e2e
class TestEnableDirectivesNotDetected:
    """E2E tests verifying enable directives are NOT detected."""

    def test_yamllint_enable_not_detected(self, tmp_path: Path) -> None:
        """Yamllint enable is not detected."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint enable\nkey: value\n")
        result = run_cli("--linters", "yamllint", str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_pylint_enable_not_detected(self, tmp_path: Path) -> None:
        """Pylint enable is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: enable=foo\n")
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""


@pytest.mark.e2e
class TestLinterFiltering:
    """E2E tests for --linters flag."""

    def test_single_linter_filters(self, tmp_path: Path) -> None:
        """Single linter only detects that linter."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1
        assert "mypy" in result.stdout
        assert "pylint" not in result.stdout

    def test_multiple_linters(self, tmp_path: Path) -> None:
        """Multiple linters detect all specified."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 1
        assert "pylint" in result.stdout
        assert "mypy" in result.stdout

    def test_all_linters(self, tmp_path: Path) -> None:
        """All three linters can be specified."""
        py_file = tmp_path / "test.py"
        py_file.write_text(
            "# pylint: disable=foo\n"
            "x = 1  # type: ignore\n"
        )
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(
            "--linters", "yamllint,pylint,mypy",
            str(py_file), str(yaml_file),
        )
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_linters_filtered_by_extension(self, tmp_path: Path) -> None:
        """Linters only check files with matching extensions."""
        py_file = tmp_path / "test.py"
        py_file.write_text("# yamllint disable\n")  # Should NOT match
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("# pylint: disable=foo\n")  # Should NOT match
        result = run_cli(
            "--linters", "yamllint,pylint",
            str(py_file), str(yaml_file),
        )
        assert result.returncode == 0
        assert result.stdout == ""


@pytest.mark.e2e
class TestExcludeFlag:
    """E2E tests for --exclude flag."""

    def test_exclude_pattern(self, tmp_path: Path) -> None:
        """Excluded files are skipped."""
        test_file = tmp_path / "vendor_code.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--linters", "mypy", "--exclude", "*vendor*", str(test_file))
        assert result.returncode == 0

    def test_exclude_multiple_patterns(self, tmp_path: Path) -> None:
        """Multiple exclude patterns work."""
        file1 = tmp_path / "test.py"
        file2 = tmp_path / "vendor.py"
        file3 = tmp_path / "generated.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("y = 2  # type: ignore\n")
        file3.write_text("z = 3  # type: ignore\n")
        result = run_cli(
            "--linters", "mypy",
            "--exclude", "*vendor*,*generated*",
            str(file1), str(file2), str(file3),
        )
        assert result.returncode == 1
        assert "test.py" in result.stdout
        assert "vendor.py" not in result.stdout
        assert "generated.py" not in result.stdout


@pytest.mark.e2e
class TestQuietFlag:
    """E2E tests for --quiet flag."""

    def test_quiet_no_output(self, tmp_path: Path) -> None:
        """Quiet mode produces no stdout."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--linters", "mypy", "--quiet", str(test_file))
        assert result.returncode == 1
        assert result.stdout == ""

    def test_quiet_clean_file(self, tmp_path: Path) -> None:
        """Quiet mode with clean file exits 0."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--linters", "mypy", "--quiet", str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestCountFlag:
    """E2E tests for --count flag."""

    def test_count_output(self, tmp_path: Path) -> None:
        """Count mode outputs only count."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--linters", "pylint,mypy", "--count", str(test_file))
        assert result.returncode == 1
        assert result.stdout.strip() == "2"

    def test_count_zero(self, tmp_path: Path) -> None:
        """Count mode outputs 0 for clean files."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--linters", "mypy", "--count", str(test_file))
        assert result.returncode == 0
        assert result.stdout.strip() == "0"


@pytest.mark.e2e
class TestFailFastFlag:
    """E2E tests for --fail-fast flag."""

    def test_fail_fast_single_finding(self, tmp_path: Path) -> None:
        """Fail-fast outputs only first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--linters", "pylint,mypy", "--fail-fast", str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_fail_fast_with_quiet(self, tmp_path: Path) -> None:
        """Fail-fast with quiet produces no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli(
            "--linters", "pylint,mypy",
            "--fail-fast", "--quiet",
            str(test_file),
        )
        assert result.returncode == 1
        assert result.stdout == ""


@pytest.mark.e2e
class TestVerboseFlag:
    """E2E tests for --verbose flag."""

    def test_verbose_shows_linters(self, tmp_path: Path) -> None:
        """Verbose shows linters being checked."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--linters", "pylint,mypy", "--verbose", str(test_file))
        assert result.returncode == 0
        assert "Checking for:" in result.stdout
        assert "mypy" in result.stdout
        assert "pylint" in result.stdout

    def test_verbose_shows_scanning(self, tmp_path: Path) -> None:
        """Verbose shows files being scanned."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--linters", "pylint", "--verbose", str(test_file))
        assert result.returncode == 0
        assert "Scanning:" in result.stdout

    def test_verbose_silently_skips_irrelevant_files(self, tmp_path: Path) -> None:
        """Verbose silently skips files with irrelevant extensions."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("x = 1\n")
        result = run_cli("--linters", "pylint", "--verbose", str(txt_file))
        assert result.returncode == 0
        assert "Skipping" not in result.stdout
        assert "Scanned 0 file(s)" in result.stdout

    def test_verbose_shows_findings(self, tmp_path: Path) -> None:
        """Verbose shows findings inline."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--linters", "pylint", "--verbose", str(test_file))
        assert result.returncode == 1
        assert "pylint: disable" in result.stdout

    def test_verbose_shows_summary(self, tmp_path: Path) -> None:
        """Verbose shows summary at end."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--linters", "pylint", "--verbose", str(test_file))
        assert result.returncode == 1
        assert "Scanned 1 file(s)" in result.stdout
        assert "found 1 finding(s)" in result.stdout

    def test_verbose_with_fail_fast(self, tmp_path: Path) -> None:
        """Verbose with fail-fast shows one finding and exits."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=a\n# pylint: disable=b\n")
        result = run_cli(
            "--linters", "pylint", "--verbose", "--fail-fast", str(test_file)
        )
        assert result.returncode == 1
        assert "found 1 finding" in result.stdout

    def test_verbose_mutually_exclusive_with_quiet(self, tmp_path: Path) -> None:
        """Verbose and quiet are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli(
            "--linters", "pylint", "--verbose", "--quiet", str(test_file)
        )
        assert result.returncode == 2

    def test_verbose_mutually_exclusive_with_count(self, tmp_path: Path) -> None:
        """Verbose and count are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli(
            "--linters", "pylint", "--verbose", "--count", str(test_file)
        )
        assert result.returncode == 2


@pytest.mark.e2e
class TestWarnOnlyFlag:
    """E2E tests for --warn-only flag."""

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """Warn-only always exits 0 even with findings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--linters", "mypy", "--warn-only", str(test_file))
        assert result.returncode == 0
        assert "mypy" in result.stdout

    def test_warn_only_clean_file(self, tmp_path: Path) -> None:
        """Warn-only with clean file exits 0."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--linters", "mypy", "--warn-only", str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestAllowFlag:
    """E2E tests for --allow flag."""

    def test_allow_specific_directive(self, tmp_path: Path) -> None:
        """Allowed directive is not reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore[import]\n")
        result = run_cli(
            "--linters", "mypy",
            "--allow", "type: ignore[import]",
            str(test_file),
        )
        assert result.returncode == 0

    def test_allow_partial_match(self, tmp_path: Path) -> None:
        """Allow pattern matches substring."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=too-many-arguments\n")
        result = run_cli(
            "--linters", "pylint",
            "--allow", "too-many-arguments",
            str(test_file),
        )
        assert result.returncode == 0

    def test_allow_multiple_patterns(self, tmp_path: Path) -> None:
        """Multiple allow patterns work together."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=too-many-arguments\n"
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        result = run_cli(
            "--linters", "pylint,mypy",
            "--allow", "too-many-arguments,type: ignore[import]",
            str(test_file),
        )
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1
        assert "type: ignore" in lines[0]


@pytest.mark.e2e
class TestCaseInsensitivity:
    """E2E tests for case-insensitive matching."""

    def test_uppercase_pylint(self, tmp_path: Path) -> None:
        """Detects uppercase PYLINT: DISABLE."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# PYLINT: DISABLE=foo\n")
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 1

    def test_uppercase_mypy(self, tmp_path: Path) -> None:
        """Detects uppercase TYPE: IGNORE."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # TYPE: IGNORE\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1

    def test_mixed_case_yamllint(self, tmp_path: Path) -> None:
        """Detects mixed case YamlLint Disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# YamlLint Disable\nkey: value\n")
        result = run_cli("--linters", "yamllint", str(test_file))
        assert result.returncode == 1


@pytest.mark.e2e
class TestWhitespaceTolerance:
    """E2E tests for whitespace tolerance."""

    def test_extra_whitespace_pylint(self, tmp_path: Path) -> None:
        """Tolerates extra whitespace in pylint directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint:    disable=foo\n")
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 1

    def test_extra_whitespace_mypy(self, tmp_path: Path) -> None:
        """Tolerates extra whitespace in mypy directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type:    ignore\n")
        result = run_cli("--linters", "mypy", str(test_file))
        assert result.returncode == 1


@pytest.mark.e2e
class TestMultipleFindings:
    """E2E tests for multiple findings."""

    def test_multiple_findings_single_file(self, tmp_path: Path) -> None:
        """Multiple findings in single file are all reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=foo\n"
            "x = bar()  # type: ignore\n"
            "# pylint: skip-file\n"
        )
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_multiple_findings_multiple_files(self, tmp_path: Path) -> None:
        """Findings across multiple files are all reported."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.yaml"
        file1.write_text("x = foo()  # type: ignore\n")
        file2.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(
            "--linters", "yamllint,mypy",
            str(file1), str(file2),
        )
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_multiple_directives_same_line(self, tmp_path: Path) -> None:
        """Multiple directives on same line are all reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # pylint: disable=bar  # type: ignore\n")
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2


@pytest.mark.e2e
class TestDirectoryHandling:
    """E2E tests for directory handling."""

    def test_scans_directories_recursively(self, tmp_path: Path) -> None:
        """Directories passed as arguments are scanned recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        nested_file = subdir / "test.py"
        nested_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--linters", "mypy", str(subdir))
        assert result.returncode == 1  # Finding detected in nested file

    def test_empty_directory_exits_0(self, tmp_path: Path) -> None:
        """Passing an empty directory exits 0 (nothing to scan)."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = run_cli("--linters", "mypy", str(subdir))
        assert result.returncode == 0

    def test_unreadable_file_in_directory_exits_1(self, tmp_path: Path) -> None:
        """Unreadable file in directory causes error but continues scanning."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        unreadable = subdir / "unreadable.py"
        unreadable.write_text("clean\n")
        unreadable.chmod(0o000)
        readable = subdir / "readable.py"
        readable.write_text("# pylint: disable=foo\n")
        try:
            result = run_cli("--linters", "pylint", str(subdir))
            assert result.returncode == 1
            assert "Error reading" in result.stderr
            assert "pylint: disable" in result.stdout
        finally:
            unreadable.chmod(0o644)


@pytest.mark.e2e
class TestExtensionFiltering:
    """E2E tests for file extension filtering."""

    def test_skips_irrelevant_extensions(self, tmp_path: Path) -> None:
        """Files with irrelevant extensions are silently skipped."""
        py_file = tmp_path / "test.py"
        txt_file = tmp_path / "test.txt"
        py_file.write_text("x = 1  # type: ignore\n")
        txt_file.write_text("x = 1  # type: ignore\n")
        result = run_cli(
            "--linters", "mypy",
            str(py_file),
            str(txt_file),
        )
        assert result.returncode == 1
        assert "test.py" in result.stdout
        assert "test.txt" not in result.stdout

    def test_yamllint_skips_py_files(self, tmp_path: Path) -> None:
        """Yamllint only scans yaml/yml files."""
        yaml_file = tmp_path / "test.yaml"
        py_file = tmp_path / "test.py"
        yaml_file.write_text("# yamllint disable\n")
        py_file.write_text("# yamllint disable\n")
        result = run_cli(
            "--linters", "yamllint",
            str(yaml_file),
            str(py_file),
        )
        assert result.returncode == 1
        assert "test.yaml" in result.stdout
        assert "test.py" not in result.stdout


@pytest.mark.e2e
class TestRealisticScenarios:
    """E2E tests with realistic file content."""

    def test_python_file_with_mixed_content(self, tmp_path: Path) -> None:
        """Realistic Python file with some suppressions."""
        test_file = tmp_path / "example.py"
        test_file.write_text('''"""Module docstring."""

import os
import sys  # type: ignore[import]

# pylint: disable=too-many-arguments
def complex_function(a, b, c, d, e, f):
    """Do something complex."""
    result = a + b + c + d + e + f
    return result  # type: ignore


class MyClass:
    """A class."""

    def method(self):
        """A method."""
        pass  # pylint: disable=unnecessary-pass
''')
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 4

    def test_yaml_file_with_mixed_content(self, tmp_path: Path) -> None:
        """Realistic YAML file with some suppressions."""
        test_file = tmp_path / "config.yaml"
        test_file.write_text('''---
# yamllint disable-file
name: example
settings:
  debug: true
  log_level: info  # yamllint disable-line rule:truthy
  max_connections: 100
''')
        result = run_cli("--linters", "yamllint", str(test_file))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_clean_python_file(self, tmp_path: Path) -> None:
        """Clean Python file without any suppressions."""
        test_file = tmp_path / "clean.py"
        test_file.write_text('''"""Clean module."""

from typing import List


def add_numbers(numbers: List[int]) -> int:
    """Add all numbers in the list."""
    return sum(numbers)


def main() -> None:
    """Main entry point."""
    result = add_numbers([1, 2, 3, 4, 5])
    print(f"Sum: {result}")


if __name__ == "__main__":
    main()
''')
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 0
        assert result.stdout == ""


@pytest.mark.e2e
class TestStringLiteralHandling:
    """E2E tests for string literal false positive prevention."""

    def test_string_literal_not_detected(self, tmp_path: Path) -> None:
        """Directive in string literal is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "# pylint: disable=foo"\n')
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 0

    def test_multiline_string_not_detected(self, tmp_path: Path) -> None:
        """Directive in multiline string is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('''s = """
# pylint: disable=foo
# type: ignore
"""
''')
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 0

    def test_comment_after_string_detected(self, tmp_path: Path) -> None:
        """Comment after string literal is detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "text"  # pylint: disable=foo\n')
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 1
        assert "pylint: disable" in result.stdout

    def test_regex_pattern_not_detected(self, tmp_path: Path) -> None:
        """Regex pattern containing directive is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('pattern = re.compile(r"pylint:\\s*disable")\n')
        result = run_cli("--linters", "pylint", str(test_file))
        assert result.returncode == 0

    def test_test_file_with_directive_strings(self, tmp_path: Path) -> None:
        """Test file containing directive patterns as test data is clean."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text('''"""Tests for linting."""

def test_detects_pylint_disable():
    """Test that pylint disable is detected."""
    content = "# pylint: disable=foo"
    assert "pylint" in content

def test_detects_type_ignore():
    """Test that type ignore is detected."""
    line = "x = 1  # type: ignore"
    assert "ignore" in line
''')
        result = run_cli("--linters", "pylint,mypy", str(test_file))
        assert result.returncode == 0
