"""Integration tests for clang tool CLI handling."""

from pathlib import Path
from typing import Any

import pytest
from test_run_main import run_main_with_args


@pytest.mark.integration
class TestCliClangTidyIntegration:
    """Integration tests for clang-tidy tool via CLI."""

    def test_exit_1_with_nolint(self, tmp_path: Path) -> None:
        """Exit code 1 for file with NOLINT."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; // NOLINT\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 1

    def test_output_contains_nolint(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Output contains NOLINT directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; // NOLINT\n")
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out

    def test_exit_0_clean_cpp_file(self, tmp_path: Path) -> None:
        """Exit code 0 for clean C++ file."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int main() {\n    return 0;\n}\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_nolintnextline_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """NOLINTNEXTLINE is detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTNEXTLINE\nint x = 1;\n")
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINTNEXTLINE" in captured.out

    def test_nolintbegin_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """NOLINTBEGIN is detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTBEGIN\nint x = 1;\n// NOLINTEND\n")
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINTBEGIN" in captured.out

    def test_nolintend_not_detected(self, tmp_path: Path) -> None:
        """NOLINTEND is not detected (enable directive)."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// NOLINTEND\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0


@pytest.mark.integration
class TestCliClangFormatIntegration:
    """Integration tests for clang-format tool via CLI."""

    def test_exit_1_with_clang_format_off(self, tmp_path: Path) -> None:
        """Exit code 1 for file with clang-format off."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format off\nint x=1;\n")
        exit_code = run_main_with_args([
            "--tools", "clang-format", str(test_file)
        ])
        assert exit_code == 1

    def test_output_contains_clang_format_off(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Output contains clang-format off directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format off\nint x=1;\n")
        run_main_with_args(["--tools", "clang-format", str(test_file)])
        captured = capsys.readouterr()
        assert "clang-format off" in captured.out

    def test_clang_format_on_not_detected(self, tmp_path: Path) -> None:
        """clang-format on is not detected (enable directive)."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("// clang-format on\n")
        exit_code = run_main_with_args([
            "--tools", "clang-format", str(test_file)
        ])
        assert exit_code == 0


@pytest.mark.integration
class TestCliClangDiagnosticIntegration:
    """Integration tests for clang-diagnostic tool via CLI."""

    def test_exit_1_with_pragma_ignored(self, tmp_path: Path) -> None:
        """Exit code 1 for file with #pragma clang diagnostic ignored."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            '#pragma clang diagnostic ignored "-Wfoo"\nint x = 1;\n'
        )
        exit_code = run_main_with_args([
            "--tools", "clang-diagnostic", str(test_file)
        ])
        assert exit_code == 1

    def test_output_contains_pragma(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Output contains #pragma directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            '#pragma clang diagnostic ignored "-Wfoo"\nint x = 1;\n'
        )
        run_main_with_args(["--tools", "clang-diagnostic", str(test_file)])
        captured = capsys.readouterr()
        assert "#pragma clang diagnostic ignored" in captured.out

    def test_pragma_push_not_detected(self, tmp_path: Path) -> None:
        """#pragma clang diagnostic push is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("#pragma clang diagnostic push\n")
        exit_code = run_main_with_args([
            "--tools", "clang-diagnostic", str(test_file)
        ])
        assert exit_code == 0


@pytest.mark.integration
class TestCliClangExtensionFiltering:
    """Integration tests for clang tool file extension filtering."""

    def test_clang_tidy_only_scans_cpp_includes(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """clang-tidy scans .cpp files."""
        cpp_file = tmp_path / "test.cpp"
        py_file = tmp_path / "test.py"
        cpp_file.write_text("int x = 1; // NOLINT\n")
        py_file.write_text("int x = 1; // NOLINT\n")  # wrong extension
        run_main_with_args([
            "--tools", "clang-tidy",
            str(cpp_file),
            str(py_file),
        ])
        captured = capsys.readouterr()
        assert "test.cpp" in captured.out

    def test_clang_tidy_skips_py_files(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """clang-tidy skips .py files."""
        cpp_file = tmp_path / "test.cpp"
        py_file = tmp_path / "test.py"
        cpp_file.write_text("int x = 1; // NOLINT\n")
        py_file.write_text("int x = 1; // NOLINT\n")
        run_main_with_args([
            "--tools", "clang-tidy",
            str(cpp_file),
            str(py_file),
        ])
        captured = capsys.readouterr()
        assert "test.py" not in captured.out

    def test_clang_tidy_scans_c_file(self, tmp_path: Path) -> None:
        """clang-tidy scans .c files."""
        c_file = tmp_path / "test.c"
        c_file.write_text("int x = 1; // NOLINT\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(c_file)
        ])
        assert exit_code == 1

    def test_clang_tidy_scans_h_file(self, tmp_path: Path) -> None:
        """clang-tidy scans .h files."""
        h_file = tmp_path / "test.h"
        h_file.write_text("int x = 1; // NOLINT\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(h_file)
        ])
        assert exit_code == 1

    def test_combined_clang_and_python_tools(
        self, clang_tidy_and_mypy_output: str
    ) -> None:
        """Combined clang and Python tools scan appropriate files."""
        assert "NOLINT" in clang_tidy_and_mypy_output

    def test_combined_clang_and_python_tools_mypy(
        self, clang_tidy_and_mypy_output: str
    ) -> None:
        """Combined clang and Python tools detect mypy in .py files."""
        assert "type: ignore" in clang_tidy_and_mypy_output


@pytest.mark.integration
class TestCliClangBlockCommentIntegration:
    """Integration tests for C/C++ block comment handling via CLI."""

    def test_nolint_in_inline_block_comment_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Exit code 1 for NOLINT in inline block comment."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; /* NOLINT */\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 1

    def test_nolint_in_inline_block_comment_output(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Output contains NOLINT from inline block comment."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; /* NOLINT */\n")
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out

    def test_multiline_block_comment_continuation_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Exit code 1 for NOLINT in multiline block comment."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("/*\n * NOLINT\n */\nint x = 1;\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 1

    def test_multiline_block_comment_continuation_output(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Output contains NOLINT from multiline block comment."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("/*\n * NOLINT\n */\nint x = 1;\n")
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out

    def test_block_comment_entire_line_inside_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Exit code 1 for NOLINT on line inside block comment."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "/* start\n"
            "NOLINT\n"
            "end */\n"
        )
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 1

    def test_block_comment_entire_line_inside_output(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Output contains NOLINT from line entirely inside block."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "/* start\n"
            "NOLINT\n"
            "end */\n"
        )
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out

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
        exit_code = run_main_with_args([
            "--tools", "clang-diagnostic", str(test_file)
        ])
        assert exit_code == 0

    def test_block_comment_closes_then_code_continues(
        self, tmp_path: Path
    ) -> None:
        """Block comment closes mid-line, code continues clean."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "/* comment */ int x = 1;\n"
        )
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_block_comment_then_line_comment_with_nolint(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Block comment then line comment with NOLINT on same line."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "/* comment */ int x = 1; // NOLINT\n"
        )
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out


@pytest.mark.integration
class TestCliClangStringLiteralIntegration:
    """Integration tests for C/C++ string literal handling via CLI."""

    def test_nolint_in_string_literal_not_detected(
        self, tmp_path: Path
    ) -> None:
        """NOLINT in C string literal is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text('const char* s = "NOLINT";\n')
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_nolint_in_comment_after_string_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """NOLINT in comment after string literal is detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text('const char* s = "text"; // NOLINT\n')
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out

    def test_string_with_escaped_quote_not_detected(
        self, tmp_path: Path
    ) -> None:
        """NOLINT in string with escaped quotes is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            r'const char* s = "escaped \" NOLINT";' + "\n"
        )
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_string_with_escaped_backslash_not_detected(
        self, tmp_path: Path
    ) -> None:
        """NOLINT in string with escaped backslash is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            r'const char* s = "path\\NOLINT";' + "\n"
        )
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_char_literal_not_detected(
        self, tmp_path: Path
    ) -> None:
        """Directive-like content in char literal is not detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("char c = 'N';\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_char_literal_with_escape_not_detected(
        self, tmp_path: Path
    ) -> None:
        """Char literal with escape sequence is handled correctly."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("char c = '\\'';\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_comment_after_char_literal_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """NOLINT in comment after char literal is detected."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("char c = 'x'; // NOLINT\n")
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out


@pytest.mark.integration
class TestCliClangAllowIntegration:
    """Integration tests for --allow flag with clang tools."""

    def test_allow_nolint_specific_check(self, tmp_path: Path) -> None:
        """Allowed NOLINT pattern is skipped."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; // NOLINT(bugprone-*)\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy",
            "--allow", "NOLINT(bugprone-*)",
            str(test_file),
        ])
        assert exit_code == 0

    def test_allow_does_not_skip_other_nolint(
        self, tmp_path: Path
    ) -> None:
        """Allow pattern does not skip non-matching NOLINT."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int x = 1; // NOLINT\n")
        exit_code = run_main_with_args([
            "--tools", "clang-tidy",
            "--allow", "NOLINT(bugprone-*)",
            str(test_file),
        ])
        assert exit_code == 1


@pytest.mark.integration
class TestCliClangCommentPartsJoining:
    """Integration tests for multiple comment segments on one line."""

    def test_block_then_line_comment_both_joined(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Multiple comment parts on one line are joined for matching."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "int x = 1; /* safe */ int y = 2; // NOLINT\n"
        )
        run_main_with_args(["--tools", "clang-tidy", str(test_file)])
        captured = capsys.readouterr()
        assert "NOLINT" in captured.out

    def test_multiple_block_comments_joined(
        self, tmp_path: Path
    ) -> None:
        """Multiple block comments on one line with no directive."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "int /* a */ x /* b */ = 1;\n"
        )
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_block_comment_continuation_then_closes_with_code(
        self, tmp_path: Path
    ) -> None:
        """Block comment from previous line closes then clean code."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "/* start\n"
            "end */ int x = 1;\n"
        )
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 0

    def test_unclosed_block_comment_start(
        self, tmp_path: Path
    ) -> None:
        """Unclosed block comment at end of line."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text(
            "int x = 1; /* NOLINT\n"
            "end of comment */\n"
        )
        exit_code = run_main_with_args([
            "--tools", "clang-tidy", str(test_file)
        ])
        assert exit_code == 1
