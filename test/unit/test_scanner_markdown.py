"""Unit tests for the scanner module - markdownlint tool."""

import pytest

from assert_no_inline_directives.scanner import (
    Finding,
    VALID_TOOLS,
    get_tools_for_extension,
    get_relevant_extensions,
    parse_tools,
    scan_file,
    scan_line,
)

# Shorthand for all tools
ALL = VALID_TOOLS


@pytest.mark.unit
class TestScanLineMarkdownlint:
    """Tests for markdownlint directive detection."""

    def test_markdownlint_disable(self) -> None:
        """Detects markdownlint-disable directive."""
        result = scan_line("<!-- markdownlint-disable -->", ALL)
        assert result == [("markdownlint", "markdownlint-disable")]

    def test_markdownlint_disable_with_rules(self) -> None:
        """Detects markdownlint-disable with specific rules."""
        result = scan_line("<!-- markdownlint-disable MD001 MD002 -->", ALL)
        assert result == [("markdownlint", "markdownlint-disable")]

    def test_markdownlint_disable_line(self) -> None:
        """Detects markdownlint-disable-line directive."""
        result = scan_line("<!-- markdownlint-disable-line -->", ALL)
        assert result == [("markdownlint", "markdownlint-disable-line")]

    def test_markdownlint_disable_line_with_rules(self) -> None:
        """Detects markdownlint-disable-line with specific rules."""
        result = scan_line(
            "<!-- markdownlint-disable-line MD001 -->", ALL
        )
        assert result == [("markdownlint", "markdownlint-disable-line")]

    def test_markdownlint_disable_next_line(self) -> None:
        """Detects markdownlint-disable-next-line directive."""
        result = scan_line("<!-- markdownlint-disable-next-line -->", ALL)
        assert result == [
            ("markdownlint", "markdownlint-disable-next-line")
        ]

    def test_markdownlint_disable_next_line_with_rules(self) -> None:
        """Detects markdownlint-disable-next-line with specific rules."""
        result = scan_line(
            "<!-- markdownlint-disable-next-line MD001 -->", ALL
        )
        assert result == [
            ("markdownlint", "markdownlint-disable-next-line")
        ]

    def test_markdownlint_disable_file(self) -> None:
        """Detects markdownlint-disable-file directive."""
        result = scan_line("<!-- markdownlint-disable-file -->", ALL)
        assert result == [("markdownlint", "markdownlint-disable-file")]

    def test_markdownlint_disable_file_with_rules(self) -> None:
        """Detects markdownlint-disable-file with specific rules."""
        result = scan_line(
            "<!-- markdownlint-disable-file MD001 -->", ALL
        )
        assert result == [("markdownlint", "markdownlint-disable-file")]

    def test_markdownlint_capture(self) -> None:
        """Detects markdownlint-capture directive."""
        result = scan_line("<!-- markdownlint-capture -->", ALL)
        assert result == [("markdownlint", "markdownlint-capture")]

    def test_markdownlint_configure_file(self) -> None:
        """Detects markdownlint-configure-file directive."""
        result = scan_line(
            '<!-- markdownlint-configure-file { "MD013": false } -->', ALL
        )
        assert result == [
            ("markdownlint", "markdownlint-configure-file")
        ]

    def test_markdownlint_only_with_markdownlint_tool(self) -> None:
        """Directive only detected when markdownlint tool is specified."""
        assert not scan_line(
            "<!-- markdownlint-disable -->",
            frozenset({"pylint"}),
        )


@pytest.mark.unit
class TestScanLineMarkdownlintEnableNotDetected:
    """Verify that markdownlint enable/restore directives are NOT detected."""

    def test_markdownlint_enable_not_detected(self) -> None:
        """markdownlint-enable is not detected."""
        assert not scan_line("<!-- markdownlint-enable -->", ALL)

    def test_markdownlint_enable_with_rules_not_detected(self) -> None:
        """markdownlint-enable with rules is not detected."""
        assert not scan_line("<!-- markdownlint-enable MD001 -->", ALL)

    def test_markdownlint_restore_not_detected(self) -> None:
        """markdownlint-restore is not detected."""
        assert not scan_line("<!-- markdownlint-restore -->", ALL)


@pytest.mark.unit
class TestScanLineMarkdownlintCaseInsensitivity:
    """Tests for case-insensitive matching of markdownlint directives."""

    def test_case_insensitive_disable(self) -> None:
        """markdownlint-disable detection is case-insensitive."""
        result = scan_line("<!-- MARKDOWNLINT-DISABLE -->", ALL)
        assert result == [("markdownlint", "markdownlint-disable")]

    def test_case_insensitive_disable_next_line(self) -> None:
        """markdownlint-disable-next-line detection is case-insensitive."""
        result = scan_line(
            "<!-- Markdownlint-Disable-Next-Line -->", ALL
        )
        assert result == [
            ("markdownlint", "markdownlint-disable-next-line")
        ]

    def test_case_insensitive_capture(self) -> None:
        """markdownlint-capture detection is case-insensitive."""
        result = scan_line("<!-- MARKDOWNLINT-CAPTURE -->", ALL)
        assert result == [("markdownlint", "markdownlint-capture")]


@pytest.mark.unit
class TestScanLineMarkdownlintWhitespace:
    """Tests for whitespace tolerance in markdownlint directives."""

    def test_extra_whitespace_after_comment_open(self) -> None:
        """Tolerates extra whitespace after <!--."""
        result = scan_line("<!--   markdownlint-disable -->", ALL)
        assert result == [("markdownlint", "markdownlint-disable")]

    def test_no_whitespace_after_comment_open(self) -> None:
        """Detects with no whitespace after <!--."""
        result = scan_line("<!--markdownlint-disable -->", ALL)
        assert result == [("markdownlint", "markdownlint-disable")]


@pytest.mark.unit
class TestScanFileMarkdownlint:
    """Tests for scan_file with markdown files."""

    def test_md_file_disable_detected(self) -> None:
        """markdownlint-disable in .md file is detected."""
        content = "<!-- markdownlint-disable -->\n# Title\n"
        findings = scan_file("test.md", content, ALL, [])
        assert findings == [Finding(
            path="test.md",
            line_number=1,
            tool="markdownlint",
            directive="markdownlint-disable",
        )]

    def test_md_file_multiple_findings(self) -> None:
        """Multiple markdownlint directives in .md file are detected."""
        content = (
            "<!-- markdownlint-disable -->\n"
            "# Title\n"
            "<!-- markdownlint-disable-next-line MD001 -->\n"
        )
        findings = scan_file("test.md", content, ALL, [])
        assert len(findings) == 2

    def test_md_file_multiple_findings_first(self) -> None:
        """First finding is markdownlint-disable on line 1."""
        content = (
            "<!-- markdownlint-disable -->\n"
            "# Title\n"
            "<!-- markdownlint-disable-next-line MD001 -->\n"
        )
        findings = scan_file("test.md", content, ALL, [])
        assert findings[0] == Finding(
            path="test.md",
            line_number=1,
            tool="markdownlint",
            directive="markdownlint-disable",
        )

    def test_md_file_multiple_findings_second(self) -> None:
        """Second finding is markdownlint-disable-next-line on line 3."""
        content = (
            "<!-- markdownlint-disable -->\n"
            "# Title\n"
            "<!-- markdownlint-disable-next-line MD001 -->\n"
        )
        findings = scan_file("test.md", content, ALL, [])
        assert findings[1] == Finding(
            path="test.md",
            line_number=3,
            tool="markdownlint",
            directive="markdownlint-disable-next-line",
        )

    def test_md_file_no_findings(self) -> None:
        """Clean .md file returns no findings."""
        content = "# Title\n\nSome text.\n"
        assert not scan_file("test.md", content, ALL, [])

    def test_md_file_enable_not_detected(self) -> None:
        """markdownlint-enable in .md file is not detected."""
        content = "<!-- markdownlint-enable -->\n"
        assert not scan_file("test.md", content, ALL, [])

    def test_md_file_allow_pattern(self) -> None:
        """Allow pattern skips matching markdownlint directive."""
        content = "<!-- markdownlint-disable MD013 -->\n"
        findings = scan_file(
            "test.md", content, ALL, ["markdownlint-disable MD013"]
        )
        assert not findings


@pytest.mark.unit
class TestParseToolsMarkdownlint:
    """Tests for parse_tools with markdownlint."""

    def test_markdownlint(self) -> None:
        """Parses markdownlint tool."""
        result = parse_tools("markdownlint")
        assert result == frozenset({"markdownlint"})

    def test_all_tools_including_markdownlint(self) -> None:
        """Parses all eight tools."""
        result = parse_tools(
            "yamllint,pylint,mypy,coverage,"
            "clang-tidy,clang-format,clang-diagnostic,markdownlint"
        )
        assert result == frozenset({
            "yamllint", "pylint", "mypy", "coverage",
            "clang-tidy", "clang-format", "clang-diagnostic",
            "markdownlint",
        })


@pytest.mark.unit
class TestGetRelevantExtensionsMarkdownlint:
    """Tests for get_relevant_extensions with markdownlint."""

    def test_markdownlint_extensions(self) -> None:
        """markdownlint returns .md extension."""
        result = get_relevant_extensions(frozenset({"markdownlint"}))
        assert result == frozenset({".md"})

    def test_combined_markdownlint_and_pylint(self) -> None:
        """Combined markdownlint and pylint returns .md, .py, and .toml."""
        result = get_relevant_extensions(
            frozenset({"markdownlint", "pylint"})
        )
        assert result == frozenset({".md", ".py", ".toml"})


@pytest.mark.unit
class TestGetToolsForExtensionMarkdownlint:
    """Tests for get_tools_for_extension with markdownlint."""

    def test_md_extension_returns_markdownlint(self) -> None:
        """Markdown file extension returns markdownlint."""
        result = get_tools_for_extension(".md", ALL)
        assert result == frozenset({"markdownlint"})

    def test_py_extension_does_not_return_markdownlint(self) -> None:
        """Python file extension does not return markdownlint."""
        result = get_tools_for_extension(".py", ALL)
        assert "markdownlint" not in result

    def test_filters_markdownlint_by_requested(self) -> None:
        """Only returns markdownlint when requested."""
        result = get_tools_for_extension(
            ".md", frozenset({"markdownlint"})
        )
        assert result == frozenset({"markdownlint"})
