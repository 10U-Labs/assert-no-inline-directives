"""Integration tests for the scanner module's public API."""

import pytest

from assert_no_inline_directives.scanner import scan_line


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

    def test_scan_line_multiple_tools(self) -> None:
        """scan_line checks all specified tools."""
        result = scan_line(
            "# pylint: disable=foo  # type: ignore",
            frozenset({"pylint", "mypy"}),
        )
        assert len(result) == 2
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

    def test_scan_line_pylint_variants(self) -> None:
        """scan_line detects various pylint directive forms."""
        lines = [
            "# pylint: disable=foo",
            "# pylint: disable-next=bar",
            "# pylint: skip-file",
        ]
        for line in lines:
            result = scan_line(line, frozenset({"pylint"}))
            assert len(result) == 1
            assert result[0][0] == "pylint"

    def test_scan_line_unlisted_tool_ignored(self) -> None:
        """scan_line only checks tools in the provided set."""
        result = scan_line("# type: ignore", frozenset({"pylint"}))
        assert not result
