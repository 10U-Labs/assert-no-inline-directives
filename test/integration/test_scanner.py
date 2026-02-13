"""Integration tests for the scanner module's public API."""

import pytest

from assert_no_inline_directives.scanner import scan_file, scan_line


@pytest.mark.integration
class TestScanLineIntegration:
    """Integration tests for scan_line function."""

    def test_scan_line_no_findings(self) -> None:
        """scan_line returns empty list for clean line."""
        result = scan_line("x = 1", frozenset({"pylint", "mypy"}))
        assert not result

    def test_scan_line_single_finding(self) -> None:
        """scan_line returns finding for directive in comment."""
        result = scan_line("x = 1  # type: ignore", frozenset({"mypy"}))
        assert result == [("mypy", "type: ignore")]

    def test_scan_line_multiple_tools_count(self) -> None:
        """scan_line checks all specified tools - returns correct count."""
        result = scan_line(
            "# pylint: disable=foo  # type: ignore",
            frozenset({"pylint", "mypy"}),
        )
        assert len(result) == 2

    def test_scan_line_multiple_tools_contains_both(self) -> None:
        """scan_line checks all specified tools - contains both tools."""
        result = scan_line(
            "# pylint: disable=foo  # type: ignore",
            frozenset({"pylint", "mypy"}),
        )
        tools = {r[0] for r in result}
        assert tools == {"pylint", "mypy"}

    def test_scan_line_string_literal_not_detected(self) -> None:
        """scan_line ignores directives in string literals."""
        result = scan_line('s = "type: ignore"', frozenset({"mypy"}))
        assert not result

    def test_scan_line_single_quoted_string(self) -> None:
        """scan_line ignores directives in single-quoted strings."""
        result = scan_line("s = 'pylint: disable'", frozenset({"pylint"}))
        assert not result

    def test_scan_line_comment_after_string(self) -> None:
        """scan_line detects directive in comment after string."""
        result = scan_line('s = "hello"  # type: ignore', frozenset({"mypy"}))
        assert result == [("mypy", "type: ignore")]

    def test_scan_line_yamllint(self) -> None:
        """scan_line detects yamllint directives."""
        result = scan_line("# yamllint disable", frozenset({"yamllint"}))
        assert result == [("yamllint", "yamllint disable")]

    def test_scan_line_pylint_disable(self) -> None:
        """scan_line detects pylint: disable."""
        result = scan_line("# pylint: disable=foo", frozenset({"pylint"}))
        assert result == [("pylint", "pylint: disable")]

    def test_scan_line_pylint_disable_next(self) -> None:
        """scan_line detects pylint: disable-next."""
        result = scan_line("# pylint: disable-next=bar", frozenset({"pylint"}))
        assert result == [("pylint", "pylint: disable-next")]

    def test_scan_line_pylint_skip_file(self) -> None:
        """scan_line detects pylint: skip-file."""
        result = scan_line("# pylint: skip-file", frozenset({"pylint"}))
        assert result == [("pylint", "pylint: skip-file")]

    def test_scan_line_unlisted_tool_ignored(self) -> None:
        """scan_line only checks tools in the provided set."""
        result = scan_line("# type: ignore", frozenset({"pylint"}))
        assert not result


@pytest.mark.integration
class TestScanLineClangIntegration:
    """Integration tests for scan_line with C-style comments."""

    def test_scan_line_nolint(self) -> None:
        """scan_line detects NOLINT in C++ comment."""
        result = scan_line(
            "int x = 1; // NOLINT",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_scan_line_nolintnextline(self) -> None:
        """scan_line detects NOLINTNEXTLINE."""
        result = scan_line(
            "// NOLINTNEXTLINE",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINTNEXTLINE")]

    def test_scan_line_clang_format_off(self) -> None:
        """scan_line detects clang-format off."""
        result = scan_line(
            "// clang-format off",
            frozenset({"clang-format"}),
            c_style_comments=True,
        )
        assert result == [("clang-format", "clang-format off")]

    def test_scan_line_pragma_ignored(self) -> None:
        """scan_line detects #pragma clang diagnostic ignored."""
        result = scan_line(
            '#pragma clang diagnostic ignored "-Wfoo"',
            frozenset({"clang-diagnostic"}),
            c_style_comments=True,
        )
        assert result == [
            ("clang-diagnostic", "#pragma clang diagnostic ignored")
        ]

    def test_scan_line_nolint_in_string_not_detected(self) -> None:
        """scan_line ignores NOLINT in C string literals."""
        result = scan_line(
            'const char* s = "NOLINT";',
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert not result

    def test_scan_line_nolintend_not_detected(self) -> None:
        """scan_line does not detect NOLINTEND."""
        result = scan_line(
            "// NOLINTEND",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert not result

    def test_scan_line_clang_format_on_not_detected(self) -> None:
        """scan_line does not detect clang-format on."""
        result = scan_line(
            "// clang-format on",
            frozenset({"clang-format"}),
            c_style_comments=True,
        )
        assert not result

    def test_scan_line_multiple_clang_tools(self) -> None:
        """scan_line checks multiple clang tools."""
        result = scan_line(
            "int x = 1; // NOLINT",
            frozenset({"clang-tidy", "clang-format"}),
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_scan_line_nolint_in_block_comment(self) -> None:
        """scan_line detects NOLINT in inline block comment."""
        result = scan_line(
            "int x = 1; /* NOLINT */",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_scan_line_string_with_escaped_quote(self) -> None:
        """scan_line handles escaped quote in C string."""
        result = scan_line(
            r'const char* s = "escaped \" NOLINT";',
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert not result

    def test_scan_line_char_literal_with_escape(self) -> None:
        """scan_line handles escaped char literal."""
        result = scan_line(
            "char c = '\\''; // NOLINT",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_scan_line_no_comment_no_findings(self) -> None:
        """scan_line returns empty for line with no comment."""
        result = scan_line(
            "int x = 1;",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert not result

    def test_scan_line_block_and_line_comment_joined(self) -> None:
        """scan_line joins block and line comment parts."""
        result = scan_line(
            "int /* a */ x = 1; // NOLINT",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]


@pytest.mark.integration
class TestScanFileCppIntegration:
    """Integration tests for scan_file with C/C++ files."""

    def test_scan_file_cpp_nolint_in_line_comment(self) -> None:
        """scan_file detects NOLINT in // comment."""
        findings = scan_file(
            "test.cpp",
            "int x = 1; // NOLINT\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_nolint_in_line_comment_directive(self) -> None:
        """scan_file reports correct directive for NOLINT."""
        findings = scan_file(
            "test.cpp",
            "int x = 1; // NOLINT\n",
            frozenset({"clang-tidy"}),
        )
        assert findings[0].directive == "NOLINT"

    def test_scan_file_cpp_nolint_in_block_comment(self) -> None:
        """scan_file detects NOLINT in inline block comment."""
        findings = scan_file(
            "test.cpp",
            "int x = 1; /* NOLINT */\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_multiline_block_comment(self) -> None:
        """scan_file detects NOLINT in multiline block comment."""
        findings = scan_file(
            "test.cpp",
            "/*\n * NOLINT\n */\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_multiline_block_comment_line_number(self) -> None:
        """scan_file reports correct line for multiline block comment."""
        findings = scan_file(
            "test.cpp",
            "/*\n * NOLINT\n */\n",
            frozenset({"clang-tidy"}),
        )
        assert findings[0].line_number == 2

    def test_scan_file_cpp_entire_line_inside_block(self) -> None:
        """scan_file detects NOLINT on line inside block comment."""
        findings = scan_file(
            "test.cpp",
            "/* start\nNOLINT\nend */\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_string_literal_not_detected(self) -> None:
        """scan_file ignores NOLINT in C string literal."""
        findings = scan_file(
            "test.cpp",
            'const char* s = "NOLINT";\n',
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_string_with_escaped_quote(self) -> None:
        """scan_file handles escaped quote in C string literal."""
        findings = scan_file(
            "test.cpp",
            r'const char* s = "escaped \" NOLINT";' + "\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_string_with_escaped_backslash(self) -> None:
        """scan_file handles escaped backslash in C string literal."""
        findings = scan_file(
            "test.cpp",
            r'const char* s = "path\\NOLINT";' + "\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_char_literal(self) -> None:
        """scan_file handles char literal correctly."""
        findings = scan_file(
            "test.cpp",
            "char c = 'N';\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_char_literal_with_escape(self) -> None:
        """scan_file handles char literal with escape sequence."""
        findings = scan_file(
            "test.cpp",
            "char c = '\\'';\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_comment_after_char_literal(self) -> None:
        """scan_file detects NOLINT after char literal."""
        findings = scan_file(
            "test.cpp",
            "char c = 'x'; // NOLINT\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_comment_after_string_literal(self) -> None:
        """scan_file detects NOLINT in comment after string."""
        findings = scan_file(
            "test.cpp",
            'const char* s = "text"; // NOLINT\n',
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_pragma_detected(self) -> None:
        """scan_file detects #pragma clang diagnostic ignored."""
        findings = scan_file(
            "test.cpp",
            '#pragma clang diagnostic ignored "-Wfoo"\n',
            frozenset({"clang-diagnostic"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_pragma_in_block_comment_not_detected(self) -> None:
        """scan_file ignores #pragma inside block comment."""
        findings = scan_file(
            "test.cpp",
            "/*\n"
            '#pragma clang diagnostic ignored "-Wfoo"\n'
            "*/\n",
            frozenset({"clang-diagnostic"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_block_closes_then_line_comment(self) -> None:
        """scan_file joins comment_parts from block and line comment."""
        findings = scan_file(
            "test.cpp",
            "/* safe */ int x = 1; // NOLINT\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_multiple_block_comments_joined(self) -> None:
        """scan_file handles multiple block comments on one line."""
        findings = scan_file(
            "test.cpp",
            "int /* a */ x /* b */ = 1;\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_unclosed_block_then_next_line(self) -> None:
        """scan_file handles block comment spanning two lines."""
        findings = scan_file(
            "test.cpp",
            "int x = 1; /* NOLINT\nend of comment */\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_block_continuation_closes(self) -> None:
        """scan_file block from previous line closes mid-line."""
        findings = scan_file(
            "test.cpp",
            "/* start\nend */ int x = 1;\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_clean_file(self) -> None:
        """scan_file returns no findings for clean C++ file."""
        findings = scan_file(
            "test.cpp",
            "int main() {\n    return 0;\n}\n",
            frozenset({"clang-tidy"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_clang_format_off(self) -> None:
        """scan_file detects clang-format off."""
        findings = scan_file(
            "test.cpp",
            "// clang-format off\nint x=1;\n",
            frozenset({"clang-format"}),
        )
        assert len(findings) == 1

    def test_scan_file_cpp_clang_format_on_not_detected(self) -> None:
        """scan_file does not detect clang-format on."""
        findings = scan_file(
            "test.cpp",
            "// clang-format on\n",
            frozenset({"clang-format"}),
        )
        assert len(findings) == 0

    def test_scan_file_cpp_allow_pattern(self) -> None:
        """scan_file respects allow patterns for C++ files."""
        findings = scan_file(
            "test.cpp",
            "int x = 1; // NOLINT(bugprone-*)\n",
            frozenset({"clang-tidy"}),
            allow_patterns=["NOLINT(bugprone-*)"],
        )
        assert len(findings) == 0
