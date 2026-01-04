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

    def test_multiple_directives_same_line(self) -> None:
        """Detects multiple different tool directives on same line."""
        result = scan_line("# pylint: disable=foo  # type: ignore", ALL)
        assert len(result) == 2
        assert ("pylint", "pylint: disable") in result
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

    def test_filter_multiple_tools(self) -> None:
        """Detects multiple specified tools."""
        line = "# pylint: disable=foo  # type: ignore  # yamllint disable"
        result = scan_line(line, frozenset({"pylint", "mypy"}))
        assert len(result) == 2
        assert ("pylint", "pylint: disable") in result
        assert ("mypy", "type: ignore") in result
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
        assert len(findings) == 1
        assert findings[0] == Finding(
            path="test.py",
            line_number=1,
            tool="mypy",
            directive="type: ignore",
        )

    def test_multiple_findings_different_lines(self) -> None:
        """File with directives on different lines returns all findings."""
        content = (
            "# pylint: disable=foo\n"
            "x = 1\n"
            "y = 2  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, [])
        assert len(findings) == 2
        assert findings[0].line_number == 1
        assert findings[0].tool == "pylint"
        assert findings[1].line_number == 3
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

    def test_coverage_finding(self) -> None:
        """File with coverage directive returns finding."""
        content = "if DEBUG:  # pragma: no cover\n    pass\n"
        findings = scan_file("test.py", content, ALL, [])
        assert len(findings) == 1
        assert findings[0].tool == "coverage"
        assert findings[0].directive == "pragma: no cover"


@pytest.mark.unit
class TestScanFileToolFiltering:
    """Tests for tool filtering in scan_file."""

    def test_filter_single_tool(self) -> None:
        """Only detects specified tool in file."""
        content = "# pylint: disable=foo\nx = 1  # type: ignore\n"
        findings = scan_file("test.py", content, frozenset({"mypy"}), [])
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_filter_excludes_other_tools(self) -> None:
        """Excludes unspecified tools."""
        content = "# pylint: disable=foo\n# yamllint disable\n"
        findings = scan_file("test.py", content, frozenset({"mypy"}), [])
        assert not findings

    def test_filter_coverage(self) -> None:
        """Filter to only coverage directives."""
        content = "# pragma: no cover\n# pylint: disable=foo\n"
        findings = scan_file("test.py", content, frozenset({"coverage"}), [])
        assert len(findings) == 1
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

    def test_allow_does_not_affect_others(self) -> None:
        """Allow pattern only affects matching directives."""
        content = (
            "x = foo()  # type: ignore[import]\n"
            "y = bar()  # type: ignore\n"
        )
        findings = scan_file("test.py", content, ALL, ["type: ignore[import]"])
        assert len(findings) == 1
        assert findings[0].line_number == 2

    def test_allow_case_insensitive(self) -> None:
        """Allow pattern matching is case-insensitive."""
        content = "x = foo()  # TYPE: IGNORE[IMPORT]\n"
        findings = scan_file("test.py", content, ALL, ["type: ignore[import]"])
        assert not findings

    def test_multiple_allow_patterns(self) -> None:
        """Multiple allow patterns work together."""
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
