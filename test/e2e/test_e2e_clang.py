"""End-to-end tests for clang tool support."""

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


# --- clang-tidy e2e tests ---


@pytest.mark.e2e
class TestCliClangTidy:
    """E2E tests for clang-tidy directive detection."""

    def test_nolint_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for NOLINT."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; // NOLINT\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_nolint_output(self, tmp_path: Path) -> None:
        """Output contains NOLINT directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; // NOLINT\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert "clang-tidy:NOLINT" in result.stdout

    def test_nolint_with_check_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for NOLINT with check name."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; // NOLINT(bugprone-*)\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_nolintnextline_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for NOLINTNEXTLINE."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTNEXTLINE\nint x = 1;\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_nolintnextline_output(self, tmp_path: Path) -> None:
        """Output contains NOLINTNEXTLINE directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTNEXTLINE\nint x = 1;\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert "clang-tidy:NOLINTNEXTLINE" in result.stdout

    def test_nolintbegin_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for NOLINTBEGIN."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTBEGIN\nint x = 1;\n// NOLINTEND\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_nolintbegin_output(self, tmp_path: Path) -> None:
        """Output contains NOLINTBEGIN directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTBEGIN\nint x = 1;\n// NOLINTEND\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert "clang-tidy:NOLINTBEGIN" in result.stdout

    def test_nolint_in_c_file(self, tmp_path: Path) -> None:
        """NOLINT detected in .c file."""
        test_file = tmp_path / "test.c"
        test_file.write_text("int x = 1; // NOLINT\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_nolint_in_header_file(self, tmp_path: Path) -> None:
        """NOLINT detected in .h file."""
        test_file = tmp_path / "test.h"
        test_file.write_text("int x = 1; // NOLINT\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_clean_cpp_file(self, tmp_path: Path) -> None:
        """Clean C++ file exits 0."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int main() {\n    return 0;\n}\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 0


# --- clang-format e2e tests ---


@pytest.mark.e2e
class TestCliClangFormat:
    """E2E tests for clang-format directive detection."""

    def test_clang_format_off_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for clang-format off."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format off\nint x=1;\n")
        result = run_cli("--tools", "clang-format", str(test_file))
        assert result.returncode == 1

    def test_clang_format_off_output(self, tmp_path: Path) -> None:
        """Output contains clang-format off directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format off\nint x=1;\n")
        result = run_cli("--tools", "clang-format", str(test_file))
        assert "clang-format:clang-format off" in result.stdout

    def test_clang_format_on_not_detected(self, tmp_path: Path) -> None:
        """clang-format on is not detected (enable directive)."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format on\n")
        result = run_cli("--tools", "clang-format", str(test_file))
        assert result.returncode == 0


# --- clang-diagnostic e2e tests ---


@pytest.mark.e2e
class TestCliClangDiagnostic:
    """E2E tests for clang-diagnostic directive detection."""

    def test_pragma_ignored_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for #pragma clang diagnostic ignored."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            '#pragma clang diagnostic ignored "-Wunused"\nint x = 1;\n'
        )
        result = run_cli("--tools", "clang-diagnostic", str(test_file))
        assert result.returncode == 1

    def test_pragma_ignored_output(self, tmp_path: Path) -> None:
        """Output contains #pragma directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            '#pragma clang diagnostic ignored "-Wunused"\nint x = 1;\n'
        )
        result = run_cli("--tools", "clang-diagnostic", str(test_file))
        assert "clang-diagnostic:#pragma clang diagnostic ignored" in result.stdout

    def test_pragma_push_not_detected(self, tmp_path: Path) -> None:
        """#pragma clang diagnostic push is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("#pragma clang diagnostic push\n")
        result = run_cli("--tools", "clang-diagnostic", str(test_file))
        assert result.returncode == 0

    def test_pragma_pop_not_detected(self, tmp_path: Path) -> None:
        """#pragma clang diagnostic pop is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("#pragma clang diagnostic pop\n")
        result = run_cli("--tools", "clang-diagnostic", str(test_file))
        assert result.returncode == 0


# --- clang enable directives e2e ---


@pytest.mark.e2e
class TestCliClangEnableNotDetected:
    """E2E tests verifying clang enable directives are NOT detected."""

    def test_nolintend_not_detected_returncode(self, tmp_path: Path) -> None:
        """NOLINTEND exits 0."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTEND\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 0

    def test_nolintend_not_detected_no_output(self, tmp_path: Path) -> None:
        """NOLINTEND produces no output."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTEND\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.stdout == ""

    def test_clang_format_on_not_detected_returncode(
        self, tmp_path: Path
    ) -> None:
        """clang-format on exits 0."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format on\n")
        result = run_cli("--tools", "clang-format", str(test_file))
        assert result.returncode == 0

    def test_clang_format_on_not_detected_no_output(
        self, tmp_path: Path
    ) -> None:
        """clang-format on produces no output."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format on\n")
        result = run_cli("--tools", "clang-format", str(test_file))
        assert result.stdout == ""


# --- clang extension filtering e2e ---


@pytest.mark.e2e
class TestCliClangExtensionFiltering:
    """E2E tests for clang tool file extension filtering."""

    def test_clang_tidy_only_scans_cpp_returncode(
        self, tmp_path: Path
    ) -> None:
        """clang-tidy with .cpp file exits 1."""
        cpp_file = tmp_path / "test.cpp"
        py_file = tmp_path / "test.py"
        cpp_file.write_text("int x = 1; // NOLINT\n")
        py_file.write_text("int x = 1; // NOLINT\n")
        result = run_cli(
            "--tools", "clang-tidy", str(cpp_file), str(py_file)
        )
        assert result.returncode == 1

    def test_clang_tidy_only_scans_cpp_includes(
        self, tmp_path: Path
    ) -> None:
        """clang-tidy includes .cpp file in output."""
        cpp_file = tmp_path / "test.cpp"
        py_file = tmp_path / "test.py"
        cpp_file.write_text("int x = 1; // NOLINT\n")
        py_file.write_text("int x = 1; // NOLINT\n")
        result = run_cli(
            "--tools", "clang-tidy", str(cpp_file), str(py_file)
        )
        assert "test.cpp" in result.stdout

    def test_clang_tidy_only_scans_cpp_excludes_py(
        self, tmp_path: Path
    ) -> None:
        """clang-tidy excludes .py file from output."""
        cpp_file = tmp_path / "test.cpp"
        py_file = tmp_path / "test.py"
        cpp_file.write_text("int x = 1; // NOLINT\n")
        py_file.write_text("int x = 1; // NOLINT\n")
        result = run_cli(
            "--tools", "clang-tidy", str(cpp_file), str(py_file)
        )
        assert "test.py" not in result.stdout

    def test_all_tools_scan_both_cpp_and_py(self, tmp_path: Path) -> None:
        """All tools together scan both C++ and Python files."""
        cpp_file = tmp_path / "test.cpp"
        py_file = tmp_path / "test.py"
        cpp_file.write_text("int x = 1; // NOLINT\n")
        py_file.write_text("x = 1  # type: ignore\n")
        result = run_cli(
            "--tools", "clang-tidy,mypy", str(cpp_file), str(py_file)
        )
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2


# --- clang string literal handling e2e ---


@pytest.mark.e2e
class TestCliClangStringLiteralHandling:
    """E2E tests for C/C++ string literal false positive prevention."""

    def test_nolint_in_string_not_detected(self, tmp_path: Path) -> None:
        """NOLINT in string literal is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text('const char* s = "NOLINT";\n')
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 0

    def test_nolint_in_comment_after_string_detected(
        self, tmp_path: Path
    ) -> None:
        """NOLINT in comment after string is detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text('const char* s = "text"; // NOLINT\n')
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1


# --- clang block comment handling e2e ---


@pytest.mark.e2e
class TestCliClangBlockCommentHandling:
    """E2E tests for C/C++ block comment handling."""

    def test_nolint_in_block_comment_detected(self, tmp_path: Path) -> None:
        """NOLINT in block comment is detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; /* NOLINT */\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_nolint_in_multiline_block_comment_detected(
        self, tmp_path: Path
    ) -> None:
        """NOLINT in multiline block comment is detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("/*\n * NOLINT\n */\n")
        result = run_cli("--tools", "clang-tidy", str(test_file))
        assert result.returncode == 1

    def test_pragma_in_block_comment_not_detected(
        self, tmp_path: Path
    ) -> None:
        """#pragma inside block comment is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "/*\n"
            '#pragma clang diagnostic ignored "-Wfoo"\n'
            "*/\n"
        )
        result = run_cli("--tools", "clang-diagnostic", str(test_file))
        assert result.returncode == 0
