"""End-to-end tests for the CLI tool."""

import subprocess
from pathlib import Path

import pytest


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess."""
    return subprocess.run(
        ["assert-no-inline-directives", *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.e2e
class TestCliExitCodes:
    """E2E tests for CLI exit codes."""

    def test_exit_0_clean_file_returncode(self, tmp_path: Path) -> None:
        """Exit code 0 for a clean file."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 0

    def test_exit_0_clean_file_no_output(self, tmp_path: Path) -> None:
        """No output for a clean file."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def foo():\n    return 42\n")
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.stdout == ""

    def test_exit_1_with_pylint_disable_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for file with pylint: disable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=missing-docstring\nx = 1\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 1

    def test_exit_1_with_pylint_disable_output(self, tmp_path: Path) -> None:
        """Output contains pylint for file with pylint: disable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=missing-docstring\nx = 1\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert "pylint" in result.stdout

    def test_exit_1_with_mypy_ignore_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for file with type: ignore."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1

    def test_exit_1_with_mypy_ignore_output(self, tmp_path: Path) -> None:
        """Output contains mypy for file with type: ignore."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert "mypy" in result.stdout

    def test_exit_1_with_yamllint_disable_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for file with yamllint disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.returncode == 1

    def test_exit_1_with_yamllint_disable_output(self, tmp_path: Path) -> None:
        """Output contains yamllint for file with yamllint disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert "yamllint" in result.stdout

    def test_exit_2_missing_file(self) -> None:
        """Exit code 2 for missing file."""
        result = run_cli("--tools", "pylint", "/nonexistent/path/file.py")
        assert result.returncode == 2

    def test_exit_2_missing_tools_flag(self, tmp_path: Path) -> None:
        """Exit code 2 when --tools flag is missing."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli(str(test_file))
        assert result.returncode == 2

    def test_exit_2_empty_tools_returncode(self, tmp_path: Path) -> None:
        """Exit code 2 for empty tools string."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "", str(test_file))
        assert result.returncode == 2

    def test_exit_2_empty_tools_message(self, tmp_path: Path) -> None:
        """Error message for empty tools string."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "", str(test_file))
        assert "At least one tool" in result.stderr

    def test_exit_2_invalid_tool(self, tmp_path: Path) -> None:
        """Exit code 2 for invalid tool name."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "eslint", str(test_file))
        assert result.returncode == 2


@pytest.mark.e2e
class TestOutputFormat:
    """E2E tests for output format."""

    def test_output_format_path_line_tool_directive_returncode(
        self,
        tmp_path: Path,
    ) -> None:
        """Exit code 1 for file with directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1

    def test_output_format_path_line_tool_directive_format(
        self,
        tmp_path: Path,
    ) -> None:
        """Output format is path:line:tool:directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        expected = f"{test_file}:1:mypy:type: ignore\n"
        assert result.stdout == expected

    def test_line_number_is_1_based(self, tmp_path: Path) -> None:
        """Line numbers are 1-based."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\ny = 2\nz = foo()  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert ":3:" in result.stdout


@pytest.mark.e2e
class TestAllDirectiveTypes:
    """E2E tests verifying all directive types are detected."""

    def test_yamllint_disable_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for yamllint disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable\nkey: value\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.returncode == 1

    def test_yamllint_disable_output(self, tmp_path: Path) -> None:
        """Output contains yamllint disable directive."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable\nkey: value\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert "yamllint:yamllint disable" in result.stdout

    def test_yamllint_disable_line_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for yamllint disable-line."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.returncode == 1

    def test_yamllint_disable_line_output(self, tmp_path: Path) -> None:
        """Output contains yamllint disable-line directive."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value  # yamllint disable-line\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert "yamllint:yamllint disable-line" in result.stdout

    def test_yamllint_disable_file_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for yamllint disable-file."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable-file\nkey: value\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.returncode == 1

    def test_yamllint_disable_file_output(self, tmp_path: Path) -> None:
        """Output contains yamllint disable-file directive."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint disable-file\nkey: value\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert "yamllint:yamllint disable-file" in result.stdout

    def test_pylint_disable_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for pylint: disable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 1

    def test_pylint_disable_output(self, tmp_path: Path) -> None:
        """Output contains pylint: disable directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert "pylint:pylint: disable" in result.stdout

    def test_pylint_disable_next_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for pylint: disable-next."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable-next=foo\nx = 1\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 1

    def test_pylint_disable_next_output(self, tmp_path: Path) -> None:
        """Output contains pylint: disable-next directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable-next=foo\nx = 1\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert "pylint:pylint: disable-next" in result.stdout

    def test_pylint_skip_file_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for pylint: skip-file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: skip-file\nx = 1\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 1

    def test_pylint_skip_file_output(self, tmp_path: Path) -> None:
        """Output contains pylint: skip-file directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: skip-file\nx = 1\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert "pylint:pylint: skip-file" in result.stdout

    def test_mypy_type_ignore_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for type: ignore."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1

    def test_mypy_type_ignore_output(self, tmp_path: Path) -> None:
        """Output contains type: ignore directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert "mypy:type: ignore" in result.stdout

    def test_mypy_type_ignore_bracketed_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for type: ignore[error-code]."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore[attr-defined]\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1

    def test_mypy_type_ignore_bracketed_output(self, tmp_path: Path) -> None:
        """Output contains type: ignore for bracketed directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore[attr-defined]\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert "mypy:type: ignore" in result.stdout

    def test_mypy_ignore_errors_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for mypy: ignore-errors."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# mypy: ignore-errors\nx = 1\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1

    def test_mypy_ignore_errors_output(self, tmp_path: Path) -> None:
        """Output contains mypy: ignore-errors directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# mypy: ignore-errors\nx = 1\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert "mypy:mypy: ignore-errors" in result.stdout


@pytest.mark.e2e
class TestEnableDirectivesNotDetected:
    """E2E tests verifying enable directives are NOT detected."""

    def test_yamllint_enable_not_detected_returncode(self, tmp_path: Path) -> None:
        """Yamllint enable exits 0."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint enable\nkey: value\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.returncode == 0

    def test_yamllint_enable_not_detected_no_output(self, tmp_path: Path) -> None:
        """Yamllint enable produces no output."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# yamllint enable\nkey: value\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.stdout == ""

    def test_pylint_enable_not_detected_returncode(self, tmp_path: Path) -> None:
        """Pylint enable exits 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: enable=foo\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 0

    def test_pylint_enable_not_detected_no_output(self, tmp_path: Path) -> None:
        """Pylint enable produces no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: enable=foo\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.stdout == ""


@pytest.mark.e2e
class TestToolFiltering:
    """E2E tests for --tools flag."""

    def test_single_tool_filters_returncode(self, tmp_path: Path) -> None:
        """Single tool exits 1 when finding present."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1

    def test_single_tool_filters_includes_tool(self, tmp_path: Path) -> None:
        """Single tool includes matching tool in output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert "mypy" in result.stdout

    def test_single_tool_filters_excludes_other(self, tmp_path: Path) -> None:
        """Single tool excludes other tools from output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert "pylint" not in result.stdout

    def test_multiple_tools_returncode(self, tmp_path: Path) -> None:
        """Multiple tools exit 1 when findings present."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 1

    def test_multiple_tools_includes_pylint(self, tmp_path: Path) -> None:
        """Multiple tools includes pylint in output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert "pylint" in result.stdout

    def test_multiple_tools_includes_mypy(self, tmp_path: Path) -> None:
        """Multiple tools includes mypy in output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert "mypy" in result.stdout

    def test_all_tools_returncode(self, tmp_path: Path) -> None:
        """All tools exit 1 when findings present."""
        py_file = tmp_path / "test.py"
        py_file.write_text(
            "# pylint: disable=foo\n"
            "x = 1  # type: ignore\n"
        )
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(
            "--tools", "yamllint,pylint,mypy",
            str(py_file), str(yaml_file),
        )
        assert result.returncode == 1

    def test_all_tools_finding_count(self, tmp_path: Path) -> None:
        """All tools report all findings."""
        py_file = tmp_path / "test.py"
        py_file.write_text(
            "# pylint: disable=foo\n"
            "x = 1  # type: ignore\n"
        )
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(
            "--tools", "yamllint,pylint,mypy",
            str(py_file), str(yaml_file),
        )
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_tools_filtered_by_extension_returncode(self, tmp_path: Path) -> None:
        """Tools only check files with matching extensions - exits 0."""
        py_file = tmp_path / "test.py"
        py_file.write_text("# yamllint disable\n")  # Should NOT match
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("# pylint: disable=foo\n")  # Should NOT match
        result = run_cli(
            "--tools", "yamllint,pylint",
            str(py_file), str(yaml_file),
        )
        assert result.returncode == 0

    def test_tools_filtered_by_extension_no_output(self, tmp_path: Path) -> None:
        """Tools only check files with matching extensions - no output."""
        py_file = tmp_path / "test.py"
        py_file.write_text("# yamllint disable\n")  # Should NOT match
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("# pylint: disable=foo\n")  # Should NOT match
        result = run_cli(
            "--tools", "yamllint,pylint",
            str(py_file), str(yaml_file),
        )
        assert result.stdout == ""


@pytest.mark.e2e
class TestExcludeFlag:
    """E2E tests for --exclude flag."""

    def test_exclude_pattern(self, tmp_path: Path) -> None:
        """Excluded files are skipped."""
        test_file = tmp_path / "vendor_code.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", "--exclude", "*vendor*", str(test_file))
        assert result.returncode == 0

    def test_exclude_multiple_patterns_returncode(self, tmp_path: Path) -> None:
        """Multiple exclude patterns - exits 1 for non-excluded."""
        file1 = tmp_path / "test.py"
        file2 = tmp_path / "vendor.py"
        file3 = tmp_path / "generated.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("y = 2  # type: ignore\n")
        file3.write_text("z = 3  # type: ignore\n")
        result = run_cli(
            "--tools", "mypy",
            "--exclude", "*vendor*,*generated*",
            str(file1), str(file2), str(file3),
        )
        assert result.returncode == 1

    def test_exclude_multiple_patterns_includes_test(self, tmp_path: Path) -> None:
        """Multiple exclude patterns includes non-excluded file."""
        file1 = tmp_path / "test.py"
        file2 = tmp_path / "vendor.py"
        file3 = tmp_path / "generated.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("y = 2  # type: ignore\n")
        file3.write_text("z = 3  # type: ignore\n")
        result = run_cli(
            "--tools", "mypy",
            "--exclude", "*vendor*,*generated*",
            str(file1), str(file2), str(file3),
        )
        assert "test.py" in result.stdout

    def test_exclude_multiple_patterns_excludes_vendor(self, tmp_path: Path) -> None:
        """Multiple exclude patterns excludes vendor file."""
        file1 = tmp_path / "test.py"
        file2 = tmp_path / "vendor.py"
        file3 = tmp_path / "generated.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("y = 2  # type: ignore\n")
        file3.write_text("z = 3  # type: ignore\n")
        result = run_cli(
            "--tools", "mypy",
            "--exclude", "*vendor*,*generated*",
            str(file1), str(file2), str(file3),
        )
        assert "vendor.py" not in result.stdout

    def test_exclude_multiple_patterns_excludes_generated(
        self, tmp_path: Path
    ) -> None:
        """Multiple exclude patterns excludes generated file."""
        file1 = tmp_path / "test.py"
        file2 = tmp_path / "vendor.py"
        file3 = tmp_path / "generated.py"
        file1.write_text("x = 1  # type: ignore\n")
        file2.write_text("y = 2  # type: ignore\n")
        file3.write_text("z = 3  # type: ignore\n")
        result = run_cli(
            "--tools", "mypy",
            "--exclude", "*vendor*,*generated*",
            str(file1), str(file2), str(file3),
        )
        assert "generated.py" not in result.stdout


@pytest.mark.e2e
class TestQuietFlag:
    """E2E tests for --quiet flag."""

    def test_quiet_no_output_returncode(self, tmp_path: Path) -> None:
        """Quiet mode exits 1 with findings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", "--quiet", str(test_file))
        assert result.returncode == 1

    def test_quiet_no_output_stdout(self, tmp_path: Path) -> None:
        """Quiet mode produces no stdout."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", "--quiet", str(test_file))
        assert result.stdout == ""

    def test_quiet_clean_file(self, tmp_path: Path) -> None:
        """Quiet mode with clean file exits 0."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "mypy", "--quiet", str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestCountFlag:
    """E2E tests for --count flag."""

    def test_count_output_returncode(self, tmp_path: Path) -> None:
        """Count mode exits 1 with findings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", "--count", str(test_file))
        assert result.returncode == 1

    def test_count_output_value(self, tmp_path: Path) -> None:
        """Count mode outputs only count."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", "--count", str(test_file))
        assert result.stdout.strip() == "2"

    def test_count_zero_returncode(self, tmp_path: Path) -> None:
        """Count mode exits 0 for clean files."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "mypy", "--count", str(test_file))
        assert result.returncode == 0

    def test_count_zero_value(self, tmp_path: Path) -> None:
        """Count mode outputs 0 for clean files."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "mypy", "--count", str(test_file))
        assert result.stdout.strip() == "0"


@pytest.mark.e2e
class TestFailFastFlag:
    """E2E tests for --fail-fast flag."""

    def test_fail_fast_single_finding_returncode(self, tmp_path: Path) -> None:
        """Fail-fast exits 1 on first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", "--fail-fast", str(test_file))
        assert result.returncode == 1

    def test_fail_fast_single_finding_output_count(self, tmp_path: Path) -> None:
        """Fail-fast outputs only first finding."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", "--fail-fast", str(test_file))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_fail_fast_with_quiet_returncode(self, tmp_path: Path) -> None:
        """Fail-fast with quiet exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli(
            "--tools", "pylint,mypy",
            "--fail-fast", "--quiet",
            str(test_file),
        )
        assert result.returncode == 1

    def test_fail_fast_with_quiet_no_output(self, tmp_path: Path) -> None:
        """Fail-fast with quiet produces no output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\nx = 1  # type: ignore\n")
        result = run_cli(
            "--tools", "pylint,mypy",
            "--fail-fast", "--quiet",
            str(test_file),
        )
        assert result.stdout == ""


@pytest.mark.e2e
class TestVerboseFlag:
    """E2E tests for --verbose flag."""

    def test_verbose_shows_tools_returncode(self, tmp_path: Path) -> None:
        """Verbose exits 0 for clean file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint,mypy", "--verbose", str(test_file))
        assert result.returncode == 0

    def test_verbose_shows_tools_header(self, tmp_path: Path) -> None:
        """Verbose shows 'Checking for' header."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint,mypy", "--verbose", str(test_file))
        assert "Checking for:" in result.stdout

    def test_verbose_shows_tools_mypy(self, tmp_path: Path) -> None:
        """Verbose shows mypy in tools list."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint,mypy", "--verbose", str(test_file))
        assert "mypy" in result.stdout

    def test_verbose_shows_tools_pylint(self, tmp_path: Path) -> None:
        """Verbose shows pylint in tools list."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint,mypy", "--verbose", str(test_file))
        assert "pylint" in result.stdout

    def test_verbose_shows_scanning_returncode(self, tmp_path: Path) -> None:
        """Verbose with clean file exits 0."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint", "--verbose", str(test_file))
        assert result.returncode == 0

    def test_verbose_shows_scanning_message(self, tmp_path: Path) -> None:
        """Verbose shows files being scanned."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint", "--verbose", str(test_file))
        assert "Scanning:" in result.stdout

    def test_verbose_silently_skips_irrelevant_files_returncode(
        self, tmp_path: Path
    ) -> None:
        """Verbose with irrelevant file exits 0."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint", "--verbose", str(txt_file))
        assert result.returncode == 0

    def test_verbose_silently_skips_irrelevant_files_no_skipping(
        self, tmp_path: Path
    ) -> None:
        """Verbose silently skips files with irrelevant extensions."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint", "--verbose", str(txt_file))
        assert "Skipping" not in result.stdout

    def test_verbose_silently_skips_irrelevant_files_zero_scanned(
        self, tmp_path: Path
    ) -> None:
        """Verbose shows 0 files scanned for irrelevant file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("x = 1\n")
        result = run_cli("--tools", "pylint", "--verbose", str(txt_file))
        assert "Scanned 0 file(s)" in result.stdout

    def test_verbose_shows_findings_returncode(self, tmp_path: Path) -> None:
        """Verbose with findings exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", "--verbose", str(test_file))
        assert result.returncode == 1

    def test_verbose_shows_findings_content(self, tmp_path: Path) -> None:
        """Verbose shows findings inline."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", "--verbose", str(test_file))
        assert "pylint: disable" in result.stdout

    def test_verbose_shows_summary_returncode(self, tmp_path: Path) -> None:
        """Verbose with findings exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", "--verbose", str(test_file))
        assert result.returncode == 1

    def test_verbose_shows_summary_files_scanned(self, tmp_path: Path) -> None:
        """Verbose shows files scanned in summary."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", "--verbose", str(test_file))
        assert "Scanned 1 file(s)" in result.stdout

    def test_verbose_shows_summary_findings_count(self, tmp_path: Path) -> None:
        """Verbose shows findings count in summary."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", "--verbose", str(test_file))
        assert "found 1 finding(s)" in result.stdout

    def test_verbose_with_fail_fast_returncode(self, tmp_path: Path) -> None:
        """Verbose with fail-fast exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=a\n# pylint: disable=b\n")
        result = run_cli(
            "--tools", "pylint", "--verbose", "--fail-fast", str(test_file)
        )
        assert result.returncode == 1

    def test_verbose_with_fail_fast_one_finding(self, tmp_path: Path) -> None:
        """Verbose with fail-fast shows one finding and exits."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=a\n# pylint: disable=b\n")
        result = run_cli(
            "--tools", "pylint", "--verbose", "--fail-fast", str(test_file)
        )
        assert "found 1 finding" in result.stdout

    def test_verbose_mutually_exclusive_with_quiet(self, tmp_path: Path) -> None:
        """Verbose and quiet are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli(
            "--tools", "pylint", "--verbose", "--quiet", str(test_file)
        )
        assert result.returncode == 2

    def test_verbose_mutually_exclusive_with_count(self, tmp_path: Path) -> None:
        """Verbose and count are mutually exclusive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        result = run_cli(
            "--tools", "pylint", "--verbose", "--count", str(test_file)
        )
        assert result.returncode == 2


@pytest.mark.e2e
class TestWarnOnlyFlag:
    """E2E tests for --warn-only flag."""

    def test_warn_only_exits_0_returncode(self, tmp_path: Path) -> None:
        """Warn-only always exits 0 even with findings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", "--warn-only", str(test_file))
        assert result.returncode == 0

    def test_warn_only_exits_0_has_output(self, tmp_path: Path) -> None:
        """Warn-only still shows findings in output."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", "--warn-only", str(test_file))
        assert "mypy" in result.stdout

    def test_warn_only_clean_file(self, tmp_path: Path) -> None:
        """Warn-only with clean file exits 0."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")
        result = run_cli("--tools", "mypy", "--warn-only", str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestAllowFlag:
    """E2E tests for --allow flag."""

    def test_allow_specific_directive(self, tmp_path: Path) -> None:
        """Allowed directive is not reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type: ignore[import]\n")
        result = run_cli(
            "--tools", "mypy",
            "--allow", "type: ignore[import]",
            str(test_file),
        )
        assert result.returncode == 0

    def test_allow_partial_match(self, tmp_path: Path) -> None:
        """Allow pattern matches substring."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint: disable=too-many-arguments\n")
        result = run_cli(
            "--tools", "pylint",
            "--allow", "too-many-arguments",
            str(test_file),
        )
        assert result.returncode == 0

    def test_allow_multiple_patterns_returncode(self, tmp_path: Path) -> None:
        """Multiple allow patterns - exits 1 for non-allowed."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=too-many-arguments\n"
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        result = run_cli(
            "--tools", "pylint,mypy",
            "--allow", "too-many-arguments,type: ignore[import]",
            str(test_file),
        )
        assert result.returncode == 1

    def test_allow_multiple_patterns_one_finding(self, tmp_path: Path) -> None:
        """Multiple allow patterns - only non-allowed finding reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=too-many-arguments\n"
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        result = run_cli(
            "--tools", "pylint,mypy",
            "--allow", "too-many-arguments,type: ignore[import]",
            str(test_file),
        )
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_allow_multiple_patterns_correct_finding(self, tmp_path: Path) -> None:
        """Multiple allow patterns - correct finding is reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=too-many-arguments\n"
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        result = run_cli(
            "--tools", "pylint,mypy",
            "--allow", "too-many-arguments,type: ignore[import]",
            str(test_file),
        )
        lines = result.stdout.strip().split("\n")
        assert "type: ignore" in lines[0]


@pytest.mark.e2e
class TestCaseInsensitivity:
    """E2E tests for case-insensitive matching."""

    def test_uppercase_pylint(self, tmp_path: Path) -> None:
        """Detects uppercase PYLINT: DISABLE."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# PYLINT: DISABLE=foo\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 1

    def test_uppercase_mypy(self, tmp_path: Path) -> None:
        """Detects uppercase TYPE: IGNORE."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # TYPE: IGNORE\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1

    def test_mixed_case_yamllint(self, tmp_path: Path) -> None:
        """Detects mixed case YamlLint Disable."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("# YamlLint Disable\nkey: value\n")
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.returncode == 1


@pytest.mark.e2e
class TestWhitespaceTolerance:
    """E2E tests for whitespace tolerance."""

    def test_extra_whitespace_pylint(self, tmp_path: Path) -> None:
        """Tolerates extra whitespace in pylint directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# pylint:    disable=foo\n")
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 1

    def test_extra_whitespace_mypy(self, tmp_path: Path) -> None:
        """Tolerates extra whitespace in mypy directive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # type:    ignore\n")
        result = run_cli("--tools", "mypy", str(test_file))
        assert result.returncode == 1


@pytest.mark.e2e
class TestMultipleFindings:
    """E2E tests for multiple findings."""

    def test_multiple_findings_single_file_returncode(self, tmp_path: Path) -> None:
        """Multiple findings in single file exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=foo\n"
            "x = bar()  # type: ignore\n"
            "# pylint: skip-file\n"
        )
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 1

    def test_multiple_findings_single_file_count(self, tmp_path: Path) -> None:
        """Multiple findings in single file are all reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "# pylint: disable=foo\n"
            "x = bar()  # type: ignore\n"
            "# pylint: skip-file\n"
        )
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_multiple_findings_multiple_files_returncode(self, tmp_path: Path) -> None:
        """Findings across multiple files exits 1."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.yaml"
        file1.write_text("x = foo()  # type: ignore\n")
        file2.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(
            "--tools", "yamllint,mypy",
            str(file1), str(file2),
        )
        assert result.returncode == 1

    def test_multiple_findings_multiple_files_count(self, tmp_path: Path) -> None:
        """Findings across multiple files are all reported."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.yaml"
        file1.write_text("x = foo()  # type: ignore\n")
        file2.write_text("# yamllint disable\nkey: value\n")
        result = run_cli(
            "--tools", "yamllint,mypy",
            str(file1), str(file2),
        )
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_multiple_directives_same_line_returncode(self, tmp_path: Path) -> None:
        """Multiple directives on same line exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # pylint: disable=bar  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 1

    def test_multiple_directives_same_line_count(self, tmp_path: Path) -> None:
        """Multiple directives on same line are all reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = foo()  # pylint: disable=bar  # type: ignore\n")
        result = run_cli("--tools", "pylint,mypy", str(test_file))
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
        result = run_cli("--tools", "mypy", str(subdir))
        assert result.returncode == 1  # Finding detected in nested file

    def test_empty_directory_exits_0(self, tmp_path: Path) -> None:
        """Passing an empty directory exits 0 (nothing to scan)."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = run_cli("--tools", "mypy", str(subdir))
        assert result.returncode == 0

    def test_unreadable_file_in_directory_returncode(self, tmp_path: Path) -> None:
        """Unreadable file in directory causes findings to still report."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        unreadable = subdir / "unreadable.py"
        unreadable.write_text("clean\n")
        unreadable.chmod(0o000)
        readable = subdir / "readable.py"
        readable.write_text("# pylint: disable=foo\n")
        try:
            result = run_cli("--tools", "pylint", str(subdir))
            assert result.returncode == 1
        finally:
            unreadable.chmod(0o644)

    def test_unreadable_file_in_directory_error_message(self, tmp_path: Path) -> None:
        """Unreadable file in directory shows error message."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        unreadable = subdir / "unreadable.py"
        unreadable.write_text("clean\n")
        unreadable.chmod(0o000)
        readable = subdir / "readable.py"
        readable.write_text("# pylint: disable=foo\n")
        try:
            result = run_cli("--tools", "pylint", str(subdir))
            assert "Error reading" in result.stderr
        finally:
            unreadable.chmod(0o644)

    def test_unreadable_file_in_directory_continues_scanning(
        self, tmp_path: Path
    ) -> None:
        """Unreadable file in directory continues scanning other files."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        unreadable = subdir / "unreadable.py"
        unreadable.write_text("clean\n")
        unreadable.chmod(0o000)
        readable = subdir / "readable.py"
        readable.write_text("# pylint: disable=foo\n")
        try:
            result = run_cli("--tools", "pylint", str(subdir))
            assert "pylint: disable" in result.stdout
        finally:
            unreadable.chmod(0o644)


@pytest.mark.e2e
class TestExtensionFiltering:
    """E2E tests for file extension filtering."""

    def test_skips_irrelevant_extensions_returncode(self, tmp_path: Path) -> None:
        """Files with irrelevant extensions - exits 1 for relevant."""
        py_file = tmp_path / "test.py"
        txt_file = tmp_path / "test.txt"
        py_file.write_text("x = 1  # type: ignore\n")
        txt_file.write_text("x = 1  # type: ignore\n")
        result = run_cli(
            "--tools", "mypy",
            str(py_file),
            str(txt_file),
        )
        assert result.returncode == 1

    def test_skips_irrelevant_extensions_includes_py(self, tmp_path: Path) -> None:
        """Files with irrelevant extensions - includes .py file."""
        py_file = tmp_path / "test.py"
        txt_file = tmp_path / "test.txt"
        py_file.write_text("x = 1  # type: ignore\n")
        txt_file.write_text("x = 1  # type: ignore\n")
        result = run_cli(
            "--tools", "mypy",
            str(py_file),
            str(txt_file),
        )
        assert "test.py" in result.stdout

    def test_skips_irrelevant_extensions_excludes_txt(self, tmp_path: Path) -> None:
        """Files with irrelevant extensions are silently skipped."""
        py_file = tmp_path / "test.py"
        txt_file = tmp_path / "test.txt"
        py_file.write_text("x = 1  # type: ignore\n")
        txt_file.write_text("x = 1  # type: ignore\n")
        result = run_cli(
            "--tools", "mypy",
            str(py_file),
            str(txt_file),
        )
        assert "test.txt" not in result.stdout

    def test_yamllint_skips_py_files_returncode(self, tmp_path: Path) -> None:
        """Yamllint only scans yaml/yml files - exits 1."""
        yaml_file = tmp_path / "test.yaml"
        py_file = tmp_path / "test.py"
        yaml_file.write_text("# yamllint disable\n")
        py_file.write_text("# yamllint disable\n")
        result = run_cli(
            "--tools", "yamllint",
            str(yaml_file),
            str(py_file),
        )
        assert result.returncode == 1

    def test_yamllint_skips_py_files_includes_yaml(self, tmp_path: Path) -> None:
        """Yamllint includes yaml files."""
        yaml_file = tmp_path / "test.yaml"
        py_file = tmp_path / "test.py"
        yaml_file.write_text("# yamllint disable\n")
        py_file.write_text("# yamllint disable\n")
        result = run_cli(
            "--tools", "yamllint",
            str(yaml_file),
            str(py_file),
        )
        assert "test.yaml" in result.stdout

    def test_yamllint_skips_py_files_excludes_py(self, tmp_path: Path) -> None:
        """Yamllint skips py files."""
        yaml_file = tmp_path / "test.yaml"
        py_file = tmp_path / "test.py"
        yaml_file.write_text("# yamllint disable\n")
        py_file.write_text("# yamllint disable\n")
        result = run_cli(
            "--tools", "yamllint",
            str(yaml_file),
            str(py_file),
        )
        assert "test.py" not in result.stdout


@pytest.mark.e2e
class TestRealisticScenarios:
    """E2E tests with realistic file content."""

    def test_python_file_with_mixed_content_returncode(self, tmp_path: Path) -> None:
        """Realistic Python file with some suppressions exits 1."""
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
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 1

    def test_python_file_with_mixed_content_count(self, tmp_path: Path) -> None:
        """Realistic Python file reports all findings."""
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
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 4

    def test_yaml_file_with_mixed_content_returncode(self, tmp_path: Path) -> None:
        """Realistic YAML file with some suppressions exits 1."""
        test_file = tmp_path / "config.yaml"
        test_file.write_text('''---
# yamllint disable-file
name: example
settings:
  debug: true
  log_level: info  # yamllint disable-line rule:truthy
  max_connections: 100
''')
        result = run_cli("--tools", "yamllint", str(test_file))
        assert result.returncode == 1

    def test_yaml_file_with_mixed_content_count(self, tmp_path: Path) -> None:
        """Realistic YAML file reports all findings."""
        test_file = tmp_path / "config.yaml"
        test_file.write_text('''---
# yamllint disable-file
name: example
settings:
  debug: true
  log_level: info  # yamllint disable-line rule:truthy
  max_connections: 100
''')
        result = run_cli("--tools", "yamllint", str(test_file))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_clean_python_file_returncode(self, tmp_path: Path) -> None:
        """Clean Python file without any suppressions exits 0."""
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
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 0

    def test_clean_python_file_no_output(self, tmp_path: Path) -> None:
        """Clean Python file produces no output."""
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
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.stdout == ""


@pytest.mark.e2e
class TestStringLiteralHandling:
    """E2E tests for string literal false positive prevention."""

    def test_string_literal_not_detected(self, tmp_path: Path) -> None:
        """Directive in string literal is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "# pylint: disable=foo"\n')
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 0

    def test_multiline_string_not_detected(self, tmp_path: Path) -> None:
        """Directive in multiline string is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('''s = """
# pylint: disable=foo
# type: ignore
"""
''')
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 0

    def test_comment_after_string_detected_returncode(self, tmp_path: Path) -> None:
        """Comment after string literal exits 1."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "text"  # pylint: disable=foo\n')
        result = run_cli("--tools", "pylint", str(test_file))
        assert result.returncode == 1

    def test_comment_after_string_detected_output(self, tmp_path: Path) -> None:
        """Comment after string literal is detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('s = "text"  # pylint: disable=foo\n')
        result = run_cli("--tools", "pylint", str(test_file))
        assert "pylint: disable" in result.stdout

    def test_regex_pattern_not_detected(self, tmp_path: Path) -> None:
        """Regex pattern containing directive is not detected."""
        test_file = tmp_path / "test.py"
        test_file.write_text('pattern = re.compile(r"pylint:\\s*disable")\n')
        result = run_cli("--tools", "pylint", str(test_file))
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
        result = run_cli("--tools", "pylint,mypy", str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestAlphabeticalSorting:
    """Tests for alphabetical file ordering."""

    def test_files_scanned_alphabetically_returncode(self, tmp_path: Path) -> None:
        """Files scanned alphabetically exits 1."""
        (tmp_path / "z_file.py").write_text("# pylint: disable=a\n")
        (tmp_path / "a_file.py").write_text("# pylint: disable=b\n")
        (tmp_path / "m_file.py").write_text("# pylint: disable=c\n")
        result = run_cli("--tools", "pylint", "--verbose", str(tmp_path))
        assert result.returncode == 1

    def test_files_scanned_alphabetically_first(self, tmp_path: Path) -> None:
        """First file scanned is alphabetically first."""
        (tmp_path / "z_file.py").write_text("# pylint: disable=a\n")
        (tmp_path / "a_file.py").write_text("# pylint: disable=b\n")
        (tmp_path / "m_file.py").write_text("# pylint: disable=c\n")
        result = run_cli("--tools", "pylint", "--verbose", str(tmp_path))
        lines = result.stdout.splitlines()
        scan_lines = [line for line in lines if line.startswith("Scanning:")]
        assert "a_file.py" in scan_lines[0]

    def test_files_scanned_alphabetically_order(self, tmp_path: Path) -> None:
        """Files are scanned in alphabetical order."""
        (tmp_path / "z_file.py").write_text("# pylint: disable=a\n")
        (tmp_path / "a_file.py").write_text("# pylint: disable=b\n")
        (tmp_path / "m_file.py").write_text("# pylint: disable=c\n")
        result = run_cli("--tools", "pylint", "--verbose", str(tmp_path))
        lines = result.stdout.splitlines()
        scan_lines = [line for line in lines if line.startswith("Scanning:")]
        assert "m_file.py" in scan_lines[1]

    def test_findings_output_alphabetically_returncode(self, tmp_path: Path) -> None:
        """Findings output alphabetically exits 1."""
        (tmp_path / "z.py").write_text("# pylint: disable=a\n")
        (tmp_path / "a.py").write_text("# pylint: disable=b\n")
        result = run_cli("--tools", "pylint", str(tmp_path))
        assert result.returncode == 1

    def test_findings_output_alphabetically_order(self, tmp_path: Path) -> None:
        """Findings are output in alphabetical file order."""
        (tmp_path / "z.py").write_text("# pylint: disable=a\n")
        (tmp_path / "a.py").write_text("# pylint: disable=b\n")
        result = run_cli("--tools", "pylint", str(tmp_path))
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        assert "a.py" in lines[0]


@pytest.mark.e2e
class TestGlobPatterns:
    """Tests for glob pattern support."""

    def test_glob_pattern_matches_files(self, tmp_path: Path) -> None:
        """Glob patterns match files."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "test.py").write_text("# pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", str(tmp_path / "**" / "*.py"))
        assert result.returncode == 1

    def test_glob_pattern_no_match_exits_2(self, tmp_path: Path) -> None:
        """Glob pattern with no matches exits 2."""
        result = run_cli("--tools", "pylint", str(tmp_path / "**" / "*.xyz"))
        assert result.returncode == 2

    def test_hidden_directory_matched_returncode(self, tmp_path: Path) -> None:
        """Hidden directories are matched by glob - exits 1."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "config.yml").write_text("# yamllint disable\n")
        result = run_cli("--tools", "yamllint", str(tmp_path / "**" / "*.yml"))
        assert result.returncode == 1

    def test_hidden_directory_matched_output(self, tmp_path: Path) -> None:
        """Hidden directories are matched by glob."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "config.yml").write_text("# yamllint disable\n")
        result = run_cli("--tools", "yamllint", str(tmp_path / "**" / "*.yml"))
        assert ".hidden" in result.stdout

    def test_double_star_glob_deduplicates_files_returncode(
        self, tmp_path: Path
    ) -> None:
        """Glob pattern **/* exits 0 for clean file."""
        subdir = tmp_path / "sub1" / "sub2"
        subdir.mkdir(parents=True)
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")

        result = run_cli(
            "--tools", "pylint", "--verbose", str(tmp_path / "**" / "*")
        )
        assert result.returncode == 0

    def test_double_star_glob_deduplicates_files_count(self, tmp_path: Path) -> None:
        """Glob pattern **/* does not scan files multiple times."""
        subdir = tmp_path / "sub1" / "sub2"
        subdir.mkdir(parents=True)
        py_file = subdir / "test.py"
        py_file.write_text("x = 1\n")

        result = run_cli(
            "--tools", "pylint", "--verbose", str(tmp_path / "**" / "*")
        )
        scan_count = result.stdout.count(f"Scanning: {py_file}")
        assert scan_count == 1


@pytest.mark.e2e
class TestTomlSupport:
    """Tests for .toml file support."""

    def test_toml_scanned_for_pylint_returncode(self, tmp_path: Path) -> None:
        """TOML files are scanned for pylint directives - exits 1."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text("[tool.black]\nline-length = 88  # pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", str(toml_file))
        assert result.returncode == 1

    def test_toml_scanned_for_pylint_output(self, tmp_path: Path) -> None:
        """TOML files are scanned for pylint directives."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text("[tool.black]\nline-length = 88  # pylint: disable=foo\n")
        result = run_cli("--tools", "pylint", str(toml_file))
        assert "pylint: disable" in result.stdout

    def test_toml_scanned_for_mypy_returncode(self, tmp_path: Path) -> None:
        """TOML files are scanned for mypy directives - exits 1."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text("value = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(toml_file))
        assert result.returncode == 1

    def test_toml_scanned_for_mypy_output(self, tmp_path: Path) -> None:
        """TOML files are scanned for mypy directives."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text("value = 1  # type: ignore\n")
        result = run_cli("--tools", "mypy", str(toml_file))
        assert "type: ignore" in result.stdout

    def test_toml_scanned_for_yamllint_returncode(self, tmp_path: Path) -> None:
        """TOML files are scanned for yamllint directives - exits 1."""
        toml_file = tmp_path / "settings.toml"
        toml_file.write_text("key = 'value'  # yamllint disable\n")
        result = run_cli("--tools", "yamllint", str(toml_file))
        assert result.returncode == 1

    def test_toml_scanned_for_yamllint_output(self, tmp_path: Path) -> None:
        """TOML files are scanned for yamllint directives."""
        toml_file = tmp_path / "settings.toml"
        toml_file.write_text("key = 'value'  # yamllint disable\n")
        result = run_cli("--tools", "yamllint", str(toml_file))
        assert "yamllint disable" in result.stdout

    def test_clean_toml_exits_0(self, tmp_path: Path) -> None:
        """Clean TOML file exits 0."""
        toml_file = tmp_path / "clean.toml"
        toml_file.write_text("[section]\nkey = 'value'\n")
        result = run_cli("--tools", "pylint,mypy,yamllint", str(toml_file))
        assert result.returncode == 0
