"""Core scanner logic for detecting inline directives."""

import os
import re
from dataclasses import dataclass


VALID_TOOLS = frozenset({
    "yamllint", "pylint", "mypy", "coverage",
    "clang-tidy", "clang-format", "clang-diagnostic",
})

# C/C++ file extensions that use // and /* */ comments
C_EXTENSIONS = frozenset({
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".m", ".mm",
})

# File extensions relevant to each tool
# .toml included for Python tools to catch directives in pyproject.toml comments
TOOL_EXTENSIONS: dict[str, frozenset[str]] = {
    "yamllint": frozenset({".yaml", ".yml", ".toml"}),
    "pylint": frozenset({".py", ".toml"}),
    "mypy": frozenset({".py", ".toml"}),
    "coverage": frozenset({".py", ".toml"}),
    "clang-tidy": C_EXTENSIONS,
    "clang-format": C_EXTENSIONS,
    "clang-diagnostic": C_EXTENSIONS,
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

CLANG_TIDY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"NOLINTNEXTLINE", re.IGNORECASE), "NOLINTNEXTLINE"),
    (re.compile(r"NOLINTBEGIN", re.IGNORECASE), "NOLINTBEGIN"),
    (re.compile(r"NOLINT(?!NEXTLINE|BEGIN|END)", re.IGNORECASE), "NOLINT"),
]

CLANG_FORMAT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"clang-format\s+off", re.IGNORECASE), "clang-format off"),
]

# Comment-based patterns (matched against comment text)
TOOL_PATTERNS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "yamllint": YAMLLINT_PATTERNS,
    "pylint": PYLINT_PATTERNS,
    "mypy": MYPY_PATTERNS,
    "coverage": COVERAGE_PATTERNS,
    "clang-tidy": CLANG_TIDY_PATTERNS,
    "clang-format": CLANG_FORMAT_PATTERNS,
}

# Line-based patterns (matched against the full line, not just comments)
# Used for preprocessor directives like #pragma
CLANG_DIAGNOSTIC_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"^\s*#\s*pragma\s+clang\s+diagnostic\s+ignored",
            re.IGNORECASE,
        ),
        "#pragma clang diagnostic ignored",
    ),
]

TOOL_LINE_PATTERNS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "clang-diagnostic": CLANG_DIAGNOSTIC_PATTERNS,
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


def _skip_c_string_literal(line: str, i: int, quote: str) -> int:
    """Skip past a C/C++ string or character literal.

    Advances past the contents of a string or character literal,
    handling backslash escape sequences.

    Args:
        line: The line of text.
        i: Index just after the opening quote character.
        quote: The quote character ('"' or "'").

    Returns:
        Index of the closing quote character, or end of line.
    """
    while i < len(line):
        if line[i] == "\\":
            i += 2
            continue
        if line[i] == quote:
            break
        i += 1
    return i


def _get_c_comment_portion(
    line: str,
    in_block_comment: bool,
) -> tuple[str | None, bool]:
    """Get the comment portion of a C/C++ line, tracking block comment state.

    Handles // line comments, /* */ block comments, string literals, and
    character literals.

    Args:
        line: The line of text to scan.
        in_block_comment: Whether we are inside a /* */ block comment.

    Returns:
        Tuple of (comment_portion, new_block_comment_state).
        comment_portion is None if the line has no comment outside strings.
    """
    comment_parts: list[str] = []
    i = 0

    if in_block_comment:
        end = line.find("*/")
        if end == -1:
            # Entire line is inside block comment
            return line, True
        comment_parts.append(line[:end])
        i = end + 2
        in_block_comment = False

    while i < len(line):
        two = line[i:i + 2]

        if two == "//":
            comment_parts.append(line[i:])
            break

        if two == "/*":
            end = line.find("*/", i + 2)
            if end == -1:
                # Block comment continues to next line
                comment_parts.append(line[i:])
                return " ".join(comment_parts), True
            comment_parts.append(line[i:end + 2])
            i = end + 2
            continue

        if line[i] in ('"', "'"):
            i = _skip_c_string_literal(line, i + 1, line[i])

        i += 1

    if comment_parts:
        return " ".join(comment_parts), in_block_comment
    return None, in_block_comment


def _find_comment_directives(
    comment: str | None,
    tools: frozenset[str],
) -> list[tuple[str, str]]:
    """Find matching directives in the comment portion of a line.

    Checks each tool's comment-based patterns against the comment text.
    Only reports the first matching pattern per tool.

    Args:
        comment: The comment portion of the line, or None.
        tools: Set of tools to check.

    Returns:
        A list of (tool, directive) tuples for each finding.
    """
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


def _find_line_directives(
    line: str,
    tools: frozenset[str],
) -> list[tuple[str, str]]:
    """Find matching line-based directives (e.g., #pragma).

    Checks each tool's line-based patterns against the full line text.
    Only reports the first matching pattern per tool.

    Args:
        line: The full line of text.
        tools: Set of tools to check.

    Returns:
        A list of (tool, directive) tuples for each finding.
    """
    findings: list[tuple[str, str]] = []
    for tool in tools:
        patterns = TOOL_LINE_PATTERNS.get(tool, [])
        for pattern, directive in patterns:
            if pattern.search(line):
                findings.append((tool, directive))
                break  # Only report one finding per tool per line
    return findings


def scan_line(
    line: str,
    tools: frozenset[str],
    *,
    c_style_comments: bool = False,
) -> list[tuple[str, str]]:
    """Scan a single line for inline directives.

    Searches the comment portion of the line and checks line-based patterns.
    Note: This function does not handle multiline strings or block comments
    across lines. Use scan_file for proper multiline handling.

    Args:
        line: The line of text to scan.
        tools: Set of tools to check.
        c_style_comments: If True, use C/C++ comment syntax (// and /* */).

    Returns:
        A list of (tool, directive) tuples for each finding.
    """
    if c_style_comments:
        comment, _ = _get_c_comment_portion(line, False)
    else:
        comment, _ = _get_comment_portion(line, None)

    findings = _find_comment_directives(comment, tools)
    findings.extend(_find_line_directives(line, tools))
    return findings


def _is_allowed(line: str, allow_patterns: list[str]) -> bool:
    """Check if a line matches any allow pattern.

    Args:
        line: The line of text to check.
        allow_patterns: List of patterns to allow.

    Returns:
        True if the line matches any allow pattern.
    """
    line_lower = line.lower()
    return any(
        allow_pat.lower() in line_lower
        for allow_pat in allow_patterns
    )


def scan_file(
    path: str,
    content: str,
    tools: frozenset[str],
    allow_patterns: list[str] | None = None,
) -> list[Finding]:
    """Scan file content for inline directives.

    Properly handles multiline strings (Python) and block comments (C/C++)
    by tracking state across lines.

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

    is_c_family = os.path.splitext(path)[1].lower() in C_EXTENSIONS

    findings: list[Finding] = []
    in_string: str | None = None
    in_block_comment: bool = False

    for line_number, line in enumerate(content.splitlines(), start=1):
        was_in_block_comment = in_block_comment

        if is_c_family:
            comment, in_block_comment = _get_c_comment_portion(
                line, in_block_comment,
            )
        else:
            comment, in_string = _get_comment_portion(line, in_string)

        line_findings = _find_comment_directives(comment, tools)

        # Check line-based patterns (e.g., #pragma directives)
        # Skip if line started inside a block comment
        if not was_in_block_comment:
            line_findings.extend(_find_line_directives(line, tools))

        for tool, directive in line_findings:
            if not _is_allowed(line, allow_patterns):
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
