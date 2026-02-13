"""Unit tests for the scanner module."""

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
class TestScanLineBasic:
    """Basic tests for the scan_line function."""

    def test_no_directives(self) -> None:
        """Line with no directives returns empty list."""
        assert not scan_line("normal code here", ALL)

    def test_empty_line(self) -> None:
        """Empty line returns empty list."""
        assert not scan_line("", ALL)


@pytest.mark.unit
class TestScanLineStringLiterals:
    """Tests that string literals do not trigger false positives."""

    def test_string_literal_pylint_not_detected(self) -> None:
        """Pylint directive in string literal is not detected."""
        assert not scan_line('s = "pylint: disable=foo"', ALL)

    def test_string_literal_mypy_not_detected(self) -> None:
        """Mypy directive in string literal is not detected."""
        assert not scan_line('s = "type: ignore"', ALL)

    def test_string_literal_yamllint_not_detected(self) -> None:
        """Yamllint directive in string literal is not detected."""
        assert not scan_line('s = "yamllint disable"', ALL)

    def test_regex_pattern_not_detected(self) -> None:
        """Regex pattern definition is not detected."""
        assert not scan_line('re.compile(r"pylint:\\s*disable")', ALL)

    def test_fstring_with_directive_not_detected(self) -> None:
        """F-string containing directive pattern is not detected."""
        assert not scan_line('msg = f"Found: pylint: disable"', ALL)

    def test_triple_quoted_string_not_detected(self) -> None:
        """Triple-quoted string with directive is not detected."""
        assert not scan_line('s = """# pylint: disable"""', ALL)

    def test_triple_single_quoted_string_not_detected(self) -> None:
        """Triple single-quoted string with directive is not detected."""
        assert not scan_line("s = '''# type: ignore'''", ALL)

    def test_comment_after_triple_quoted_string(self) -> None:
        """Comment after triple-quoted string is detected."""
        result = scan_line('s = """text"""  # pylint: disable=foo', ALL)
        assert result == [("pylint", "pylint: disable")]

    def test_directive_in_string_with_hash(self) -> None:
        """String containing # followed by directive is not detected."""
        assert not scan_line('s = "# pylint: disable=foo"', ALL)


@pytest.mark.unit
class TestScanLineYamllint:
    """Tests for yamllint directive detection."""

    def test_yamllint_disable_line(self) -> None:
        """Detects yamllint disable-line directive."""
        result = scan_line("# yamllint disable-line rule:line-length", ALL)
        assert result == [("yamllint", "yamllint disable-line")]

    def test_yamllint_disable(self) -> None:
        """Detects yamllint disable directive."""
        result = scan_line("# yamllint disable rule:line-length", ALL)
        assert result == [("yamllint", "yamllint disable")]

    def test_yamllint_disable_file(self) -> None:
        """Detects yamllint disable-file directive."""
        result = scan_line("# yamllint disable-file", ALL)
        assert result == [("yamllint", "yamllint disable-file")]

    def test_yamllint_enable_not_detected(self) -> None:
        """Does not detect yamllint enable directive."""
        assert not scan_line("# yamllint enable", ALL)

    def test_yamllint_enable_line_not_detected(self) -> None:
        """Does not detect yamllint enable-line directive."""
        assert not scan_line("# yamllint enable-line", ALL)


@pytest.mark.unit
class TestScanLinePylint:
    """Tests for pylint directive detection."""

    def test_pylint_disable(self) -> None:
        """Detects pylint: disable directive."""
        result = scan_line("# pylint: disable=missing-docstring", ALL)
        assert result == [("pylint", "pylint: disable")]

    def test_pylint_disable_next(self) -> None:
        """Detects pylint: disable-next directive."""
        result = scan_line("# pylint: disable-next=line-too-long", ALL)
        assert result == [("pylint", "pylint: disable-next")]

    def test_pylint_disable_line(self) -> None:
        """Detects pylint: disable-line directive."""
        result = scan_line("# pylint: disable-line=invalid-name", ALL)
        assert result == [("pylint", "pylint: disable-line")]

    def test_pylint_skip_file(self) -> None:
        """Detects pylint: skip-file directive."""
        result = scan_line("# pylint: skip-file", ALL)
        assert result == [("pylint", "pylint: skip-file")]

    def test_pylint_enable_not_detected(self) -> None:
        """Does not detect pylint: enable directive."""
        assert not scan_line("# pylint: enable=missing-docstring", ALL)

    def test_pylint_enable_next_not_detected(self) -> None:
        """Does not detect pylint: enable-next directive."""
        assert not scan_line("# pylint: enable-next=line-too-long", ALL)


@pytest.mark.unit
class TestScanLineMypy:
    """Tests for mypy directive detection."""

    def test_mypy_type_ignore(self) -> None:
        """Detects type: ignore directive."""
        result = scan_line("x = foo()  # type: ignore", ALL)
        assert result == [("mypy", "type: ignore")]

    def test_mypy_type_ignore_bracketed(self) -> None:
        """Detects type: ignore with bracketed error codes."""
        result = scan_line("x = foo()  # type: ignore[attr-defined]", ALL)
        assert result == [("mypy", "type: ignore")]

    def test_mypy_ignore_errors(self) -> None:
        """Detects mypy: ignore-errors directive."""
        result = scan_line("# mypy: ignore-errors", ALL)
        assert result == [("mypy", "mypy: ignore-errors")]


@pytest.mark.unit
class TestScanLineCoverage:
    """Tests for coverage directive detection."""

    def test_pragma_no_cover(self) -> None:
        """Detects pragma: no cover directive."""
        result = scan_line("if DEBUG:  # pragma: no cover", ALL)
        assert result == [("coverage", "pragma: no cover")]

    def test_pragma_no_branch(self) -> None:
        """Detects pragma: no branch directive."""
        result = scan_line("if condition:  # pragma: no branch", ALL)
        assert result == [("coverage", "pragma: no branch")]

    def test_pragma_no_cover_case_insensitive(self) -> None:
        """Pragma detection is case-insensitive."""
        result = scan_line("x = 1  # PRAGMA: NO COVER", ALL)
        assert result == [("coverage", "pragma: no cover")]

    def test_pragma_no_cover_extra_whitespace(self) -> None:
        """Tolerates extra whitespace in pragma directive."""
        result = scan_line("x = 1  # pragma:   no   cover", ALL)
        assert result == [("coverage", "pragma: no cover")]

    def test_pragma_in_string_not_detected(self) -> None:
        """Pragma directive in string literal is not detected."""
        assert not scan_line('s = "# pragma: no cover"', ALL)


@pytest.mark.unit
class TestScanLineCaseInsensitivity:
    """Tests for case-insensitive matching."""

    def test_case_insensitive_yamllint(self) -> None:
        """Yamllint detection is case-insensitive."""
        result = scan_line("# YAMLLINT DISABLE-LINE", ALL)
        assert result == [("yamllint", "yamllint disable-line")]

    def test_case_insensitive_pylint(self) -> None:
        """Pylint detection is case-insensitive."""
        result = scan_line("# PYLINT: DISABLE=foo", ALL)
        assert result == [("pylint", "pylint: disable")]

    def test_case_insensitive_mypy(self) -> None:
        """Mypy detection is case-insensitive."""
        result = scan_line("x = foo()  # TYPE: IGNORE", ALL)
        assert result == [("mypy", "type: ignore")]


@pytest.mark.unit
class TestScanLineWhitespace:
    """Tests for whitespace tolerance."""

    def test_extra_whitespace_pylint(self) -> None:
        """Tolerates extra whitespace in pylint directive."""
        result = scan_line("# pylint:   disable=foo", ALL)
        assert result == [("pylint", "pylint: disable")]

    def test_extra_whitespace_mypy(self) -> None:
        """Tolerates extra whitespace in mypy directive."""
        result = scan_line("x = foo()  # type:    ignore", ALL)
        assert result == [("mypy", "type: ignore")]

    def test_extra_whitespace_yamllint(self) -> None:
        """Tolerates extra whitespace in yamllint directive."""
        result = scan_line("# yamllint   disable-line", ALL)
        assert result == [("yamllint", "yamllint disable-line")]


@pytest.mark.unit
class TestScanLineMultiple:
    """Tests for multiple directives."""

    def test_multiple_directives_same_line_count(self) -> None:
        """Detects multiple directives - returns count of 2."""
        result = scan_line("# pylint: disable=foo  # type: ignore", ALL)
        assert len(result) == 2

    def test_multiple_directives_same_line_contains_pylint(self) -> None:
        """Detects multiple directives - contains pylint."""
        result = scan_line("# pylint: disable=foo  # type: ignore", ALL)
        assert ("pylint", "pylint: disable") in result

    def test_multiple_directives_same_line_contains_mypy(self) -> None:
        """Detects multiple directives - contains mypy."""
        result = scan_line("# pylint: disable=foo  # type: ignore", ALL)
        assert ("mypy", "type: ignore") in result

    def test_multiple_same_tool_directives(self) -> None:
        """Only reports one finding per tool per line."""
        result = scan_line("# pylint: disable=foo pylint: disable-next=bar", ALL)
        assert result == [("pylint", "pylint: disable-next")]

    def test_directive_mid_line(self) -> None:
        """Detects directive in middle of line."""
        result = scan_line("code here  # pylint: disable=foo  # more", ALL)
        assert result == [("pylint", "pylint: disable")]


@pytest.mark.unit
class TestScanLineToolFiltering:
    """Tests for tool filtering in scan_line."""

    def test_filter_single_tool(self) -> None:
        """Only detects specified tool."""
        line = "# pylint: disable=foo  # type: ignore"
        result = scan_line(line, frozenset({"pylint"}))
        assert result == [("pylint", "pylint: disable")]

    def test_filter_multiple_tools_count(self) -> None:
        """Detects multiple specified tools - returns count of 2."""
        line = "# pylint: disable=foo  # type: ignore  # yamllint disable"
        result = scan_line(line, frozenset({"pylint", "mypy"}))
        assert len(result) == 2

    def test_filter_multiple_tools_contains_pylint(self) -> None:
        """Detects multiple specified tools - contains pylint."""
        line = "# pylint: disable=foo  # type: ignore  # yamllint disable"
        result = scan_line(line, frozenset({"pylint", "mypy"}))
        assert ("pylint", "pylint: disable") in result

    def test_filter_multiple_tools_contains_mypy(self) -> None:
        """Detects multiple specified tools - contains mypy."""
        line = "# pylint: disable=foo  # type: ignore  # yamllint disable"
        result = scan_line(line, frozenset({"pylint", "mypy"}))
        assert ("mypy", "type: ignore") in result

    def test_filter_multiple_tools_excludes_yamllint(self) -> None:
        """Detects multiple specified tools - excludes yamllint."""
        line = "# pylint: disable=foo  # type: ignore  # yamllint disable"
        result = scan_line(line, frozenset({"pylint", "mypy"}))
        assert ("yamllint", "yamllint disable") not in result

    def test_filter_no_match(self) -> None:
        """Returns empty when filtered tool not present."""
        line = "# pylint: disable=foo"
        result = scan_line(line, frozenset({"mypy"}))
        assert not result

    def test_all_tools_checks_all(self) -> None:
        """ALL tools parameter checks all tools."""
        line = "# pylint: disable=foo  # type: ignore"
        result = scan_line(line, ALL)
        assert len(result) == 2

    def test_filter_coverage_only(self) -> None:
        """Only detects coverage when specified."""
        line = "# pragma: no cover  # pylint: disable=foo"
        result = scan_line(line, frozenset({"coverage"}))
        assert result == [("coverage", "pragma: no cover")]


@pytest.mark.unit
class TestScanFile:
    """Tests for the scan_file function."""

    def test_empty_file(self) -> None:
        """Empty file returns no findings."""
        assert not scan_file("test.py", "", ALL, [])

    def test_file_with_no_directives(self) -> None:
        """File with no directives returns no findings."""
        content = "def foo():\n    return 42\n"
        assert not scan_file("test.py", content, ALL, [])

    def test_single_finding(self) -> None:
        """File with one directive returns one finding."""
        content = "x = 1  # type: ignore\n"
        findings = scan_file("test.py", content, ALL, [])
        assert findings == [Finding(
            path="test.py",
            line_number=1,
            tool="mypy",
            directive="type: ignore",
        )]

    def test_multiple_findings_different_lines_count(self) -> None:
        """File with directives on different lines - returns count of 2."""
        content = (
            "# pylint: disable=foo\n"
            "x = 1\n"
            "y = 2  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, [])
        assert len(findings) == 2

    def test_multiple_findings_different_lines_first_line(self) -> None:
        """File with directives - first finding is on line 1."""
        content = (
            "# pylint: disable=foo\n"
            "x = 1\n"
            "y = 2  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, [])
        assert findings[0].line_number == 1

    def test_multiple_findings_different_lines_first_tool(self) -> None:
        """File with directives - first finding is pylint."""
        content = (
            "# pylint: disable=foo\n"
            "x = 1\n"
            "y = 2  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, [])
        assert findings[0].tool == "pylint"

    def test_multiple_findings_different_lines_second_line(self) -> None:
        """File with directives - second finding is on line 3."""
        content = (
            "# pylint: disable=foo\n"
            "x = 1\n"
            "y = 2  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, [])
        assert findings[1].line_number == 3

    def test_multiple_findings_different_lines_second_tool(self) -> None:
        """File with directives - second finding is mypy."""
        content = (
            "# pylint: disable=foo\n"
            "x = 1\n"
            "y = 2  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, [])
        assert findings[1].tool == "mypy"

    def test_multiple_findings_same_line(self) -> None:
        """File with multiple directives on same line returns all."""
        content = "x = 1  # pylint: disable=foo  # type: ignore\n"
        findings = scan_file("test.py", content, ALL, [])
        assert len(findings) == 2

    def test_finding_str_format(self) -> None:
        """Finding string format is correct."""
        finding = Finding(
            path="src/foo.py",
            line_number=42,
            tool="pylint",
            directive="pylint: disable",
        )
        assert str(finding) == "src/foo.py:42:pylint:pylint: disable"

    def test_coverage_finding_count(self) -> None:
        """File with coverage directive returns one finding."""
        content = "if DEBUG:  # pragma: no cover\n    pass\n"
        findings = scan_file("test.py", content, ALL, [])
        assert len(findings) == 1

    def test_coverage_finding_tool(self) -> None:
        """File with coverage directive - finding has tool 'coverage'."""
        content = "if DEBUG:  # pragma: no cover\n    pass\n"
        findings = scan_file("test.py", content, ALL, [])
        assert findings[0].tool == "coverage"

    def test_coverage_finding_directive(self) -> None:
        """File with coverage directive - finding has correct directive."""
        content = "if DEBUG:  # pragma: no cover\n    pass\n"
        findings = scan_file("test.py", content, ALL, [])
        assert findings[0].directive == "pragma: no cover"


@pytest.mark.unit
class TestScanFileToolFiltering:
    """Tests for tool filtering in scan_file."""

    def test_filter_single_tool_count(self) -> None:
        """Only detects specified tool - returns one finding."""
        content = "# pylint: disable=foo\nx = 1  # type: ignore\n"
        findings = scan_file("test.py", content, frozenset({"mypy"}), [])
        assert len(findings) == 1

    def test_filter_single_tool_name(self) -> None:
        """Only detects specified tool - finding has correct tool."""
        content = "# pylint: disable=foo\nx = 1  # type: ignore\n"
        findings = scan_file("test.py", content, frozenset({"mypy"}), [])
        assert findings[0].tool == "mypy"

    def test_filter_excludes_other_tools(self) -> None:
        """Excludes unspecified tools."""
        content = "# pylint: disable=foo\n# yamllint disable\n"
        findings = scan_file("test.py", content, frozenset({"mypy"}), [])
        assert not findings

    def test_filter_coverage_count(self) -> None:
        """Filter to only coverage - returns one finding."""
        content = "# pragma: no cover\n# pylint: disable=foo\n"
        findings = scan_file("test.py", content, frozenset({"coverage"}), [])
        assert len(findings) == 1

    def test_filter_coverage_tool(self) -> None:
        """Filter to only coverage - finding has correct tool."""
        content = "# pragma: no cover\n# pylint: disable=foo\n"
        findings = scan_file("test.py", content, frozenset({"coverage"}), [])
        assert findings[0].tool == "coverage"


@pytest.mark.unit
class TestScanFileAllowPatterns:
    """Tests for allow patterns in scan_file."""

    def test_default_allow_patterns_is_empty(self) -> None:
        """Default allow_patterns is empty list."""
        content = "x = foo()  # type: ignore\n"
        findings = scan_file("test.py", content, ALL)
        assert len(findings) == 1

    def test_allow_specific_directive(self) -> None:
        """Allowed directive is not reported."""
        content = "x = foo()  # type: ignore[import]\n"
        findings = scan_file("test.py", content, ALL, ["type: ignore[import]"])
        assert not findings

    def test_allow_does_not_affect_others_count(self) -> None:
        """Allow pattern only affects matching - one finding remains."""
        content = (
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, ["type: ignore[import]"])
        assert len(findings) == 1

    def test_allow_does_not_affect_others_line(self) -> None:
        """Allow pattern only affects matching - remaining is on line 2."""
        content = (
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, ["type: ignore[import]"])
        assert findings[0].line_number == 2

    def test_allow_case_insensitive(self) -> None:
        """Allow pattern matching is case-insensitive."""
        content = "x = foo()  # TYPE: IGNORE[IMPORT]\n"
        findings = scan_file("test.py", content, ALL, ["type: ignore[import]"])
        assert not findings

    def test_multiple_allow_patterns_count(self) -> None:
        """Multiple allow patterns - returns one finding."""
        content = (
            "# pylint: disable=too-many-arguments\n"
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        findings = scan_file(
            "test.py",
            content,
            ALL,
            ["type: ignore[import]", "too-many-arguments"],
        )
        assert len(findings) == 1

    def test_multiple_allow_patterns_line_number(self) -> None:
        """Multiple allow patterns - remaining finding is on line 3."""
        content = (
            "# pylint: disable=too-many-arguments\n"
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        findings = scan_file(
            "test.py",
            content,
            ALL,
            ["type: ignore[import]", "too-many-arguments"],
        )
        assert findings[0].line_number == 3


@pytest.mark.unit
class TestEnableDirectivesNotDetected:
    """Verify that enable directives are NOT detected."""

    def test_yamllint_enable(self) -> None:
        """Yamllint enable is not detected."""
        content = "# yamllint enable\n# yamllint enable-line\n"
        assert not scan_file("test.yaml", content, ALL, [])

    def test_pylint_enable(self) -> None:
        """Pylint enable is not detected."""
        content = "# pylint: enable=foo\n# pylint: enable-next=bar\n"
        assert not scan_file("test.py", content, ALL, [])


@pytest.mark.unit
class TestParseTools:
    """Tests for parse_tools function."""

    def test_single_tool(self) -> None:
        """Parses single tool."""
        result = parse_tools("pylint")
        assert result == frozenset({"pylint"})

    def test_multiple_tools(self) -> None:
        """Parses multiple comma-separated tools."""
        result = parse_tools("pylint,mypy")
        assert result == frozenset({"pylint", "mypy"})

    def test_all_tools(self) -> None:
        """Parses all four tools."""
        result = parse_tools("yamllint,pylint,mypy,coverage")
        assert result == frozenset({"yamllint", "pylint", "mypy", "coverage"})

    def test_whitespace_tolerance(self) -> None:
        """Tolerates whitespace around tool names."""
        result = parse_tools("pylint , mypy")
        assert result == frozenset({"pylint", "mypy"})

    def test_invalid_tool_raises(self) -> None:
        """Raises ValueError for invalid tool name."""
        with pytest.raises(ValueError, match="Invalid tool"):
            parse_tools("eslint")

    def test_mixed_valid_invalid_raises(self) -> None:
        """Raises ValueError when any tool is invalid."""
        with pytest.raises(ValueError, match="Invalid tool"):
            parse_tools("pylint,eslint")

    def test_empty_string_raises(self) -> None:
        """Raises ValueError for empty string."""
        with pytest.raises(ValueError, match="At least one tool"):
            parse_tools("")

    def test_only_commas_raises(self) -> None:
        """Raises ValueError for string with only commas."""
        with pytest.raises(ValueError, match="At least one tool"):
            parse_tools(",,,")


@pytest.mark.unit
class TestGetRelevantExtensions:
    """Tests for get_relevant_extensions function."""

    def test_pylint_extensions(self) -> None:
        """Pylint returns .py and .toml extensions."""
        result = get_relevant_extensions(frozenset({"pylint"}))
        assert result == frozenset({".py", ".toml"})

    def test_mypy_extensions(self) -> None:
        """Mypy returns .py and .toml extensions."""
        result = get_relevant_extensions(frozenset({"mypy"}))
        assert result == frozenset({".py", ".toml"})

    def test_yamllint_extensions(self) -> None:
        """Yamllint returns .yaml, .yml, and .toml extensions."""
        result = get_relevant_extensions(frozenset({"yamllint"}))
        assert result == frozenset({".yaml", ".yml", ".toml"})

    def test_coverage_extensions(self) -> None:
        """Coverage returns .py and .toml extensions."""
        result = get_relevant_extensions(frozenset({"coverage"}))
        assert result == frozenset({".py", ".toml"})

    def test_combined_python_tools(self) -> None:
        """Pylint and mypy together return .py and .toml extensions."""
        result = get_relevant_extensions(frozenset({"pylint", "mypy"}))
        assert result == frozenset({".py", ".toml"})

    def test_all_tools(self) -> None:
        """All tools return all extensions."""
        result = get_relevant_extensions(frozenset({"yamllint", "pylint", "mypy", "coverage"}))
        assert result == frozenset({".py", ".yaml", ".yml", ".toml"})

    def test_empty_tools(self) -> None:
        """Empty tools set returns empty extensions."""
        result = get_relevant_extensions(frozenset())
        assert result == frozenset()


@pytest.mark.unit
class TestGetToolsForExtension:
    """Tests for get_tools_for_extension function."""

    def test_py_extension_returns_python_tools(self) -> None:
        """Python file extension returns pylint, mypy, and coverage."""
        result = get_tools_for_extension(".py", ALL)
        assert result == frozenset({"pylint", "mypy", "coverage"})

    def test_yaml_extension_returns_yamllint(self) -> None:
        """YAML file extension returns yamllint."""
        result = get_tools_for_extension(".yaml", ALL)
        assert result == frozenset({"yamllint"})

    def test_yml_extension_returns_yamllint(self) -> None:
        """YML file extension returns yamllint."""
        result = get_tools_for_extension(".yml", ALL)
        assert result == frozenset({"yamllint"})

    def test_filters_by_requested_tools(self) -> None:
        """Only returns tools that were requested."""
        result = get_tools_for_extension(".py", frozenset({"pylint"}))
        assert result == frozenset({"pylint"})

    def test_unknown_extension_returns_empty(self) -> None:
        """Unknown extension returns empty set."""
        result = get_tools_for_extension(".txt", ALL)
        assert result == frozenset()

    def test_case_insensitive_extension(self) -> None:
        """Extension matching is case insensitive."""
        result = get_tools_for_extension(".PY", ALL)
        assert result == frozenset({"pylint", "mypy", "coverage"})


# --- clang-tidy tests ---


@pytest.mark.unit
class TestScanLineClangTidy:
    """Tests for clang-tidy directive detection."""

    def test_nolint(self) -> None:
        """Detects NOLINT directive in C++ comment."""
        result = scan_line("int x = 1; // NOLINT", ALL, c_style_comments=True)
        assert result == [("clang-tidy", "NOLINT")]

    def test_nolint_with_check(self) -> None:
        """Detects NOLINT with check name."""
        result = scan_line(
            "int x = 1; // NOLINT(bugprone-use-after-move)",
            ALL,
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_nolintnextline(self) -> None:
        """Detects NOLINTNEXTLINE directive."""
        result = scan_line(
            "// NOLINTNEXTLINE(modernize-use-nullptr)",
            ALL,
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINTNEXTLINE")]

    def test_nolintbegin(self) -> None:
        """Detects NOLINTBEGIN directive."""
        result = scan_line(
            "// NOLINTBEGIN(readability-*)",
            ALL,
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINTBEGIN")]

    def test_nolintend_not_detected(self) -> None:
        """Does not detect NOLINTEND directive (enable)."""
        assert not scan_line("// NOLINTEND", ALL, c_style_comments=True)

    def test_nolint_block_comment(self) -> None:
        """Detects NOLINT in block comment."""
        result = scan_line(
            "int x = 1; /* NOLINT */",
            ALL,
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_nolint_only_with_clang_tidy_tool(self) -> None:
        """NOLINT only detected when clang-tidy tool is specified."""
        assert not scan_line(
            "int x = 1; // NOLINT",
            frozenset({"pylint"}),
            c_style_comments=True,
        )


# --- clang-format tests ---


@pytest.mark.unit
class TestScanLineClangFormat:
    """Tests for clang-format directive detection."""

    def test_clang_format_off(self) -> None:
        """Detects clang-format off directive."""
        result = scan_line(
            "// clang-format off", ALL, c_style_comments=True
        )
        assert result == [("clang-format", "clang-format off")]

    def test_clang_format_on_not_detected(self) -> None:
        """Does not detect clang-format on directive (enable)."""
        assert not scan_line(
            "// clang-format on", ALL, c_style_comments=True
        )

    def test_clang_format_off_only_with_clang_format_tool(self) -> None:
        """clang-format off only detected when clang-format tool is specified."""
        assert not scan_line(
            "// clang-format off",
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )


# --- clang-diagnostic tests ---


@pytest.mark.unit
class TestScanLineClangDiagnostic:
    """Tests for clang-diagnostic directive detection."""

    def test_pragma_clang_diagnostic_ignored(self) -> None:
        """Detects #pragma clang diagnostic ignored."""
        result = scan_line(
            '#pragma clang diagnostic ignored "-Wunused-variable"',
            ALL,
            c_style_comments=True,
        )
        assert result == [
            ("clang-diagnostic", "#pragma clang diagnostic ignored")
        ]

    def test_pragma_with_leading_whitespace(self) -> None:
        """Detects #pragma with leading whitespace."""
        result = scan_line(
            '  #pragma clang diagnostic ignored "-Wfoo"',
            ALL,
            c_style_comments=True,
        )
        assert result == [
            ("clang-diagnostic", "#pragma clang diagnostic ignored")
        ]

    def test_pragma_push_not_detected(self) -> None:
        """Does not detect #pragma clang diagnostic push."""
        assert not scan_line(
            "#pragma clang diagnostic push",
            ALL,
            c_style_comments=True,
        )

    def test_pragma_pop_not_detected(self) -> None:
        """Does not detect #pragma clang diagnostic pop."""
        assert not scan_line(
            "#pragma clang diagnostic pop",
            ALL,
            c_style_comments=True,
        )

    def test_commented_out_pragma_not_detected(self) -> None:
        """Does not detect commented-out #pragma."""
        assert not scan_line(
            '// #pragma clang diagnostic ignored "-Wfoo"',
            ALL,
            c_style_comments=True,
        )

    def test_pragma_only_with_clang_diagnostic_tool(self) -> None:
        """#pragma only detected when clang-diagnostic tool is specified."""
        assert not scan_line(
            '#pragma clang diagnostic ignored "-Wfoo"',
            frozenset({"clang-tidy"}),
            c_style_comments=True,
        )


# --- clang enable directives not detected ---


@pytest.mark.unit
class TestScanLineClangEnableNotDetected:
    """Verify that clang enable directives are NOT detected."""

    def test_nolintend_not_detected(self) -> None:
        """NOLINTEND is not detected."""
        assert not scan_line("// NOLINTEND", ALL, c_style_comments=True)

    def test_clang_format_on_not_detected(self) -> None:
        """clang-format on is not detected."""
        assert not scan_line(
            "// clang-format on", ALL, c_style_comments=True
        )

    def test_pragma_diagnostic_push_not_detected(self) -> None:
        """#pragma clang diagnostic push is not detected."""
        assert not scan_line(
            "#pragma clang diagnostic push",
            ALL,
            c_style_comments=True,
        )

    def test_pragma_diagnostic_pop_not_detected(self) -> None:
        """#pragma clang diagnostic pop is not detected."""
        assert not scan_line(
            "#pragma clang diagnostic pop",
            ALL,
            c_style_comments=True,
        )


# --- clang case insensitivity ---


@pytest.mark.unit
class TestScanLineClangCaseInsensitivity:
    """Tests for case-insensitive matching of clang directives."""

    def test_case_insensitive_nolint(self) -> None:
        """NOLINT detection is case-insensitive."""
        result = scan_line("int x = 1; // nolint", ALL, c_style_comments=True)
        assert result == [("clang-tidy", "NOLINT")]

    def test_case_insensitive_nolintnextline(self) -> None:
        """NOLINTNEXTLINE detection is case-insensitive."""
        result = scan_line(
            "// NoLintNextLine", ALL, c_style_comments=True
        )
        assert result == [("clang-tidy", "NOLINTNEXTLINE")]

    def test_case_insensitive_clang_format_off(self) -> None:
        """clang-format off detection is case-insensitive."""
        result = scan_line(
            "// CLANG-FORMAT OFF", ALL, c_style_comments=True
        )
        assert result == [("clang-format", "clang-format off")]

    def test_case_insensitive_pragma(self) -> None:
        """#pragma detection is case-insensitive."""
        result = scan_line(
            '#PRAGMA CLANG DIAGNOSTIC IGNORED "-Wfoo"',
            ALL,
            c_style_comments=True,
        )
        assert result == [
            ("clang-diagnostic", "#pragma clang diagnostic ignored")
        ]


# --- clang whitespace tolerance ---


@pytest.mark.unit
class TestScanLineClangWhitespace:
    """Tests for whitespace tolerance in clang directives."""

    def test_extra_whitespace_clang_format(self) -> None:
        """Tolerates extra whitespace in clang-format off."""
        result = scan_line(
            "// clang-format   off", ALL, c_style_comments=True
        )
        assert result == [("clang-format", "clang-format off")]

    def test_extra_whitespace_pragma(self) -> None:
        """Tolerates extra whitespace in #pragma."""
        result = scan_line(
            '#pragma  clang  diagnostic  ignored "-Wfoo"',
            ALL,
            c_style_comments=True,
        )
        assert result == [
            ("clang-diagnostic", "#pragma clang diagnostic ignored")
        ]


# --- clang C/C++ string literal false positives ---


@pytest.mark.unit
class TestScanLineClangStringLiterals:
    """Tests that C/C++ string literals do not trigger false positives."""

    def test_nolint_in_string_not_detected(self) -> None:
        """NOLINT in string literal is not detected."""
        assert not scan_line(
            'const char* s = "NOLINT";', ALL, c_style_comments=True
        )

    def test_clang_format_off_in_string_not_detected(self) -> None:
        """clang-format off in string literal is not detected."""
        assert not scan_line(
            'const char* s = "clang-format off";', ALL, c_style_comments=True
        )

    def test_nolint_after_string_detected(self) -> None:
        """NOLINT in comment after string is detected."""
        result = scan_line(
            'const char* s = "text"; // NOLINT', ALL, c_style_comments=True
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_nolint_in_char_literal_not_detected(self) -> None:
        """Char literal containing quote does not break parsing."""
        result = scan_line(
            "char c = '\"'; // NOLINT", ALL, c_style_comments=True
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_escaped_quote_in_string_not_detected(self) -> None:
        """Escaped quote in string does not break parsing."""
        result = scan_line(
            r'const char* s = "escaped \" NOLINT"; // NOLINT',
            ALL,
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]

    def test_escaped_single_quote_in_char_literal(self) -> None:
        """Escaped single quote in char literal does not break parsing."""
        result = scan_line(
            r"char c = '\''; // NOLINT",
            ALL,
            c_style_comments=True,
        )
        assert result == [("clang-tidy", "NOLINT")]


# --- scan_file with C/C++ files ---


@pytest.mark.unit
class TestScanFileClang:
    """Tests for scan_file with C/C++ files."""

    def test_cpp_file_nolint_detected(self) -> None:
        """NOLINT in C++ file is detected."""
        content = "int x = 1; // NOLINT\n"
        findings = scan_file("test.cpp", content, ALL, [])
        assert findings == [Finding(
            path="test.cpp",
            line_number=1,
            tool="clang-tidy",
            directive="NOLINT",
        )]

    def test_c_file_nolint_detected(self) -> None:
        """NOLINT in C file is detected."""
        content = "int x = 1; // NOLINT\n"
        findings = scan_file("test.c", content, ALL, [])
        assert findings == [Finding(
            path="test.c",
            line_number=1,
            tool="clang-tidy",
            directive="NOLINT",
        )]

    def test_h_file_nolint_detected(self) -> None:
        """NOLINT in header file is detected."""
        content = "int x = 1; // NOLINT\n"
        findings = scan_file("test.h", content, ALL, [])
        assert findings == [Finding(
            path="test.h",
            line_number=1,
            tool="clang-tidy",
            directive="NOLINT",
        )]

    def test_hpp_file_clang_format_off_detected(self) -> None:
        """clang-format off in .hpp file is detected."""
        content = "// clang-format off\nint x = 1;\n"
        findings = scan_file("test.hpp", content, ALL, [])
        assert findings == [Finding(
            path="test.hpp",
            line_number=1,
            tool="clang-format",
            directive="clang-format off",
        )]

    def test_cpp_file_pragma_detected(self) -> None:
        """#pragma clang diagnostic ignored in .cpp file is detected."""
        content = '#pragma clang diagnostic ignored "-Wfoo"\nint x = 1;\n'
        findings = scan_file("test.cpp", content, ALL, [])
        assert findings == [Finding(
            path="test.cpp",
            line_number=1,
            tool="clang-diagnostic",
            directive="#pragma clang diagnostic ignored",
        )]

    def test_cpp_file_no_findings(self) -> None:
        """Clean C++ file returns no findings."""
        content = "int main() {\n    return 0;\n}\n"
        assert not scan_file("test.cpp", content, ALL, [])

    def test_cpp_file_multiple_findings_count(self) -> None:
        """C++ file with multiple directives returns all findings."""
        content = (
            "// NOLINT\n"
            "int x = 1;\n"
            "// clang-format off\n"
        )
        findings = scan_file("test.cpp", content, ALL, [])
        assert len(findings) == 2

    def test_mm_file_nolint_detected(self) -> None:
        """NOLINT in Objective-C++ file is detected."""
        content = "int x = 1; // NOLINT\n"
        findings = scan_file("test.mm", content, ALL, [])
        assert findings == [Finding(
            path="test.mm",
            line_number=1,
            tool="clang-tidy",
            directive="NOLINT",
        )]


# --- scan_file with C/C++ block comments ---


@pytest.mark.unit
class TestScanFileClangBlockComments:
    """Tests for block comment handling in C/C++ files."""

    def test_nolint_in_block_comment(self) -> None:
        """NOLINT in block comment is detected."""
        content = "int x = 1; /* NOLINT */\n"
        findings = scan_file("test.cpp", content, ALL, [])
        assert findings == [Finding(
            path="test.cpp",
            line_number=1,
            tool="clang-tidy",
            directive="NOLINT",
        )]

    def test_nolint_in_multiline_block_comment(self) -> None:
        """NOLINT in multiline block comment is detected."""
        content = "/*\n * NOLINT\n */\n"
        findings = scan_file("test.cpp", content, ALL, [])
        assert findings == [Finding(
            path="test.cpp",
            line_number=2,
            tool="clang-tidy",
            directive="NOLINT",
        )]

    def test_directive_in_string_not_in_block_comment(self) -> None:
        """Directive in string within block comment context is not detected."""
        content = 'const char* s = "NOLINT";\n'
        assert not scan_file("test.cpp", content, ALL, [])

    def test_multiline_block_comment_no_false_positive(self) -> None:
        """Code after multiline block comment is not falsely detected."""
        content = "/*\n * comment\n */\nint x = 1;\n"
        assert not scan_file("test.cpp", content, ALL, [])


# --- scan_file: #pragma inside block comment NOT detected ---


@pytest.mark.unit
class TestScanFileClangDiagnosticInBlockComment:
    """Tests that #pragma inside block comments is not detected."""

    def test_pragma_in_block_comment_not_detected(self) -> None:
        """#pragma inside block comment is not detected."""
        content = (
            "/*\n"
            '#pragma clang diagnostic ignored "-Wfoo"\n'
            "*/\n"
        )
        assert not scan_file("test.cpp", content, ALL, [])

    def test_pragma_after_block_comment_detected(self) -> None:
        """#pragma after block comment ends is detected."""
        content = (
            "/* comment */\n"
            '#pragma clang diagnostic ignored "-Wfoo"\n'
        )
        findings = scan_file("test.cpp", content, ALL, [])
        assert len(findings) == 1


# --- Updated parse_tools tests ---


@pytest.mark.unit
class TestParseToolsClang:
    """Tests for parse_tools with clang tools."""

    def test_clang_tidy(self) -> None:
        """Parses clang-tidy tool."""
        result = parse_tools("clang-tidy")
        assert result == frozenset({"clang-tidy"})

    def test_clang_format(self) -> None:
        """Parses clang-format tool."""
        result = parse_tools("clang-format")
        assert result == frozenset({"clang-format"})

    def test_clang_diagnostic(self) -> None:
        """Parses clang-diagnostic tool."""
        result = parse_tools("clang-diagnostic")
        assert result == frozenset({"clang-diagnostic"})

    def test_all_tools_including_clang(self) -> None:
        """Parses all seven tools."""
        result = parse_tools(
            "yamllint,pylint,mypy,coverage,clang-tidy,clang-format,clang-diagnostic"
        )
        assert result == frozenset({
            "yamllint", "pylint", "mypy", "coverage",
            "clang-tidy", "clang-format", "clang-diagnostic",
        })


# --- Updated extension tests ---


@pytest.mark.unit
class TestGetRelevantExtensionsClang:
    """Tests for get_relevant_extensions with clang tools."""

    def test_clang_tidy_extensions(self) -> None:
        """clang-tidy returns C/C++ extensions."""
        result = get_relevant_extensions(frozenset({"clang-tidy"}))
        assert result == frozenset({
            ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".m", ".mm",
        })

    def test_clang_format_extensions(self) -> None:
        """clang-format returns C/C++ extensions."""
        result = get_relevant_extensions(frozenset({"clang-format"}))
        assert result == frozenset({
            ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".m", ".mm",
        })

    def test_clang_diagnostic_extensions(self) -> None:
        """clang-diagnostic returns C/C++ extensions."""
        result = get_relevant_extensions(frozenset({"clang-diagnostic"}))
        assert result == frozenset({
            ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".m", ".mm",
        })

    def test_combined_python_and_clang_tools_includes_py(self) -> None:
        """Combined Python and clang tools include .py extension."""
        result = get_relevant_extensions(frozenset({"pylint", "clang-tidy"}))
        assert ".py" in result

    def test_combined_python_and_clang_tools_includes_cpp(self) -> None:
        """Combined Python and clang tools include .cpp extension."""
        result = get_relevant_extensions(frozenset({"pylint", "clang-tidy"}))
        assert ".cpp" in result

    def test_combined_python_and_clang_tools_includes_toml(self) -> None:
        """Combined Python and clang tools include .toml extension."""
        result = get_relevant_extensions(frozenset({"pylint", "clang-tidy"}))
        assert ".toml" in result


@pytest.mark.unit
class TestGetToolsForExtensionClang:
    """Tests for get_tools_for_extension with clang tools."""

    def test_cpp_extension_returns_clang_tools(self) -> None:
        """C++ file extension returns all clang tools."""
        result = get_tools_for_extension(".cpp", ALL)
        assert result == frozenset({
            "clang-tidy", "clang-format", "clang-diagnostic",
        })

    def test_c_extension_returns_clang_tools(self) -> None:
        """C file extension returns all clang tools."""
        result = get_tools_for_extension(".c", ALL)
        assert result == frozenset({
            "clang-tidy", "clang-format", "clang-diagnostic",
        })

    def test_h_extension_returns_clang_tools(self) -> None:
        """Header file extension returns all clang tools."""
        result = get_tools_for_extension(".h", ALL)
        assert result == frozenset({
            "clang-tidy", "clang-format", "clang-diagnostic",
        })

    def test_py_extension_does_not_return_clang_tidy(self) -> None:
        """Python file extension does not return clang-tidy."""
        result = get_tools_for_extension(".py", ALL)
        assert "clang-tidy" not in result

    def test_py_extension_does_not_return_clang_format(self) -> None:
        """Python file extension does not return clang-format."""
        result = get_tools_for_extension(".py", ALL)
        assert "clang-format" not in result

    def test_py_extension_does_not_return_clang_diagnostic(self) -> None:
        """Python file extension does not return clang-diagnostic."""
        result = get_tools_for_extension(".py", ALL)
        assert "clang-diagnostic" not in result

    def test_filters_clang_tools_by_requested(self) -> None:
        """Only returns requested clang tools."""
        result = get_tools_for_extension(
            ".cpp", frozenset({"clang-tidy"})
        )
        assert result == frozenset({"clang-tidy"})
