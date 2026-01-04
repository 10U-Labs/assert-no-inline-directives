"""Core scanner logic for detecting inline directives."""

import re
from dataclasses import dataclass


VALID_TOOLS = frozenset({"yamllint", "pylint", "mypy", "coverage"})

# File extensions relevant to each tool
# .toml included for all tools to catch directives in pyproject.toml comments
TOOL_EXTENSIONS: dict[str, frozenset[str]] = {
    "yamllint": frozenset({".yaml", ".yml", ".toml"}),
    "pylint": frozenset({".py", ".toml"}),
    "mypy": frozenset({".py", ".toml"}),
    "coverage": frozenset({".py", ".toml"}),
}


@dataclass(frozen=True)
class Finding:
    """Represents a single finding of an inline directive."""

    path: str
    line_number: int
    tool: str
    directive: str

    def __str__(self) -> str:
        """Format finding as path:line:tool:directive."""
        return f"{self.path}:{self.line_number}:{self.tool}:{self.directive}"


# Patterns for detecting inline directives.
# Uses \\s* to tolerate extra whitespace. All patterns are case-insensitive.
# Note: These patterns are applied only to the comment portion of a line
# (after the first # that is not inside a string literal).

YAMLLINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"yamllint\s+disable-line", re.IGNORECASE), "yamllint disable-line"),
    (re.compile(r"yamllint\s+disable-file", re.IGNORECASE), "yamllint disable-file"),
    (re.compile(r"yamllint\s+disable(?!-)", re.IGNORECASE), "yamllint disable"),
]

PYLINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"pylint:\s*disable-next", re.IGNORECASE), "pylint: disable-next"),
    (re.compile(r"pylint:\s*disable-line", re.IGNORECASE), "pylint: disable-line"),
    (re.compile(r"pylint:\s*skip-file", re.IGNORECASE), "pylint: skip-file"),
    (re.compile(r"pylint:\s*disable(?!-)", re.IGNORECASE), "pylint: disable"),
]

MYPY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"type:\s*ignore", re.IGNORECASE), "type: ignore"),
    (re.compile(r"mypy:\s*ignore-errors", re.IGNORECASE), "mypy: ignore-errors"),
]

COVERAGE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"pragma:\s*no\s*cover", re.IGNORECASE), "pragma: no cover"),
    (re.compile(r"pragma:\s*no\s*branch", re.IGNORECASE), "pragma: no branch"),
]

TOOL_PATTERNS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "yamllint": YAMLLINT_PATTERNS,
    "pylint": PYLINT_PATTERNS,
    "mypy": MYPY_PATTERNS,
    "coverage": COVERAGE_PATTERNS,
}


def _get_comment_portion(
    line: str,
    in_string: str | None,
) -> tuple[str | None, str | None]:
    """Get the comment portion of a line, tracking multiline string state.

    Handles single quotes, double quotes, and triple-quoted strings.

    Args:
        line: The line of text to scan.
        in_string: Current string state (None, '"', "'", '\"\"\"', or "'''").

    Returns:
        Tuple of (comment_portion, new_string_state).
        comment_portion is None if the line has no comment outside strings.
    """
    i = 0
    while i < len(line):
        char = line[i]
        if in_string:
            # Check for end of string
            if len(in_string) == 3:
                # Triple-quoted string
                if line[i:i + 3] == in_string:
                    in_string = None
                    i += 2  # Skip the extra 2 chars
            elif char == in_string and (i == 0 or line[i - 1] != "\\"):
                in_string = None
        else:
            # Check for start of string
            if line[i:i + 3] in ('"""', "'''"):
                in_string = line[i:i + 3]
                i += 2  # Skip the extra 2 chars
            elif char in ('"', "'"):
                in_string = char
            elif char == "#":
                return line[i:], in_string
        i += 1
    return None, in_string


def scan_line(
    line: str,
    tools: frozenset[str],
) -> list[tuple[str, str]]:
    """Scan a single line for inline directives.

    Only searches the comment portion of the line (after # not in a string).
    Note: This function does not handle multiline strings. Use scan_file
    for proper multiline string handling.

    Args:
        line: The line of text to scan.
        tools: Set of tools to check.

    Returns:
        A list of (tool, directive) tuples for each finding.
    """
    comment, _ = _get_comment_portion(line, None)
    if comment is None:
        return []

    findings: list[tuple[str, str]] = []
    for tool in tools:
        patterns = TOOL_PATTERNS.get(tool, [])
        for pattern, directive in patterns:
            if pattern.search(comment):
                findings.append((tool, directive))
                break  # Only report one finding per tool per line
    return findings


def scan_file(
    path: str,
    content: str,
    tools: frozenset[str],
    allow_patterns: list[str] | None = None,
) -> list[Finding]:
    """Scan file content for inline directives.

    Properly handles multiline strings by tracking string state across lines.

    Args:
        path: The file path (used for reporting).
        content: The file content to scan.
        tools: Set of tools to check.
        allow_patterns: List of patterns to allow (skip matching directives).

    Returns:
        A list of Finding objects for each directive found.
    """
    if allow_patterns is None:
        allow_patterns = []

    findings: list[Finding] = []
    in_string: str | None = None
    for line_number, line in enumerate(content.splitlines(), start=1):
        comment, in_string = _get_comment_portion(line, in_string)
        if comment is None:
            continue

        # Find all matching directives in this line's comment
        line_findings: list[tuple[str, str]] = []
        for tool in tools:
            patterns = TOOL_PATTERNS.get(tool, [])
            for pattern, directive in patterns:
                if pattern.search(comment):
                    line_findings.append((tool, directive))
                    break  # Only one finding per tool per line

        for tool, directive in line_findings:
            # Check if this directive matches any allow pattern
            is_allowed = any(
                allow_pat.lower() in line.lower()
                for allow_pat in allow_patterns
            )
            if not is_allowed:
                findings.append(Finding(
                    path=path,
                    line_number=line_number,
                    tool=tool,
                    directive=directive,
                ))
    return findings


def parse_tools(tools_str: str) -> frozenset[str]:
    """Parse comma-separated tools string and validate.

    Args:
        tools_str: Comma-separated list of tool names.

    Returns:
        Frozenset of valid tool names.

    Raises:
        ValueError: If any tool name is invalid.
    """
    tools = frozenset(t.strip() for t in tools_str.split(",") if t.strip())

    invalid = tools - VALID_TOOLS
    if invalid:
        valid_list = ", ".join(sorted(VALID_TOOLS))
        invalid_list = ", ".join(sorted(invalid))
        raise ValueError(
            f"Invalid tool(s): {invalid_list}. Valid options: {valid_list}"
        )

    if not tools:
        raise ValueError("At least one tool must be specified")

    return tools


def get_relevant_extensions(tools: frozenset[str]) -> frozenset[str]:
    """Get file extensions relevant to the specified tools.

    Args:
        tools: Set of tool names.

    Returns:
        Frozenset of file extensions (including the dot, e.g., ".py").
    """
    extensions: set[str] = set()
    for tool in tools:
        extensions.update(TOOL_EXTENSIONS.get(tool, set()))
    return frozenset(extensions)


def get_tools_for_extension(
    extension: str,
    tools: frozenset[str],
) -> frozenset[str]:
    """Get tools that apply to a specific file extension.

    Args:
        extension: File extension (including the dot, e.g., ".py").
        tools: Set of tool names to filter.

    Returns:
        Frozenset of tools that apply to this extension.
    """
    ext_lower = extension.lower()
    return frozenset(
        tool for tool in tools
        if ext_lower in TOOL_EXTENSIONS.get(tool, frozenset())
    )
