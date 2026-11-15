"""Core scanner logic for detecting inline directives."""

import os
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import tree_sitter_rust
from tree_sitter import Language, Node, Parser


VALID_TOOLS = frozenset({
    "yamllint", "pylint", "mypy", "coverage",
    "clang-tidy", "clang-format", "clang-diagnostic",
    "markdownlint",
    "clippy", "rustc", "rustdoc", "rustfmt",
})

# C/C++ file extensions that use // and /* */ comments
C_EXTENSIONS = frozenset({
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".m", ".mm",
})

RUST_EXTENSIONS = frozenset({".rs"})

# File extensions relevant to each tool
# .toml included for Python tools to catch directives in pyproject.toml comments
TOOL_EXTENSIONS: dict[str, frozenset[str]] = {
    "yamllint": frozenset({".yaml", ".yml", ".toml"}),
    "pylint": frozenset({".py", ".toml"}),
    "mypy": frozenset({".py", ".toml"}),
    "coverage": frozenset({".py", ".toml", ".rs"}),
    "clang-tidy": C_EXTENSIONS,
    "clang-format": C_EXTENSIONS,
    "clang-diagnostic": C_EXTENSIONS,
    "markdownlint": frozenset({".md"}),
    "clippy": RUST_EXTENSIONS,
    "rustc": RUST_EXTENSIONS,
    "rustdoc": RUST_EXTENSIONS,
    "rustfmt": RUST_EXTENSIONS,
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

MARKDOWNLINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"<!--\s*markdownlint-disable-next-line", re.IGNORECASE),
        "markdownlint-disable-next-line",
    ),
    (
        re.compile(r"<!--\s*markdownlint-disable-line", re.IGNORECASE),
        "markdownlint-disable-line",
    ),
    (
        re.compile(r"<!--\s*markdownlint-disable-file", re.IGNORECASE),
        "markdownlint-disable-file",
    ),
    (
        re.compile(r"<!--\s*markdownlint-disable(?!-)", re.IGNORECASE),
        "markdownlint-disable",
    ),
    (
        re.compile(r"<!--\s*markdownlint-capture", re.IGNORECASE),
        "markdownlint-capture",
    ),
    (
        re.compile(r"<!--\s*markdownlint-configure-file", re.IGNORECASE),
        "markdownlint-configure-file",
    ),
]

TOOL_LINE_PATTERNS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "clang-diagnostic": CLANG_DIAGNOSTIC_PATTERNS,
    "markdownlint": MARKDOWNLINT_PATTERNS,
}


# Rust directives are attributes, not comments, so a Rust file is read with
# its grammar rather than matched line by line.
RUST = Language(tree_sitter_rust.language())

RUST_ATTRIBUTE_NODES = frozenset({"attribute_item", "inner_attribute_item"})

RUST_PATH_NODES = frozenset({"identifier", "::"})

RUST_LINT_SILENCERS = frozenset({"allow", "expect"})

RUST_LINT_TOOLS = frozenset({"clippy", "rustdoc"})

RUST_DEFAULT_LINT_TOOL = "rustc"

RUSTFMT_SKIP = ("rustfmt", "skip")

RUSTFMT_SKIP_TARGETS = frozenset({"macros", "attributes"})

RUST_COVERAGE_CFGS = frozenset({"coverage", "coverage_nightly"})

RUST_COVERAGE_OFF = "off"

RustPath = tuple[str, ...]


def _rust_text(node: Node, source: bytes) -> str:
    """Return the source text a node spans."""
    return source[node.start_byte:node.end_byte].decode("utf-8")


def _rust_segments(token_tree: Node) -> list[list[Node]]:
    """Split the arguments of a token tree at its top-level commas.

    Args:
        token_tree: A token_tree node, delimiters included.

    Returns:
        The tokens between each pair of commas, empty segments left out.
    """
    segments: list[list[Node]] = [[]]
    for child in token_tree.children[1:-1]:
        if child.type == ",":
            segments.append([])
        else:
            segments[-1].append(child)
    return [segment for segment in segments if segment]


def _rust_meta(
    tokens: Sequence[Node],
    source: bytes,
) -> tuple[RustPath, Node | None]:
    """Read a flat run of tokens as an attribute: a path and its arguments.

    Args:
        tokens: The tokens of one segment of a token tree.
        source: The file's source bytes.

    Returns:
        The path's identifiers, and the token tree that follows the path,
        if one does.
    """
    path: list[str] = []
    rest = list(tokens)
    while rest and rest[0].type in RUST_PATH_NODES:
        token = rest.pop(0)
        if token.type == "identifier":
            path.append(_rust_text(token, source))
    arguments = rest[0] if rest and rest[0].type == "token_tree" else None
    return tuple(path), arguments


def _rust_attribute_meta(
    attribute: Node,
    source: bytes,
) -> tuple[RustPath, Node | None]:
    """Read an attribute node as a path and its arguments."""
    path_node = attribute.children[0]
    path = tuple(
        _rust_text(node, source)
        for node in _rust_descendants(path_node)
        if node.type == "identifier"
    )
    arguments = next(
        (child for child in attribute.children if child.type == "token_tree"),
        None,
    )
    return path, arguments


def _rust_descendants(node: Node) -> Iterator[Node]:
    """Yield a node and every node below it, in source order."""
    yield node
    for child in node.children:
        yield from _rust_descendants(child)


def _rust_names(nodes: Sequence[Node], source: bytes) -> list[str]:
    """Return the text of every identifier in or below the given nodes."""
    return [
        _rust_text(descendant, source)
        for node in nodes
        for descendant in _rust_descendants(node)
        if descendant.type == "identifier"
    ]


def _rust_coverage_cfg(nodes: Sequence[Node], source: bytes) -> str | None:
    """Return the first coverage cfg a predicate names, if it names one."""
    return next(
        (
            name for name in _rust_names(nodes, source)
            if name in RUST_COVERAGE_CFGS
        ),
        None,
    )


def _rust_lint_tool(lint: RustPath) -> str:
    """Return the tool a lint path belongs to."""
    if len(lint) > 1 and lint[0] in RUST_LINT_TOOLS:
        return lint[0]
    return RUST_DEFAULT_LINT_TOOL


def _is_rustfmt_skip(path: RustPath) -> bool:
    """Whether a path is rustfmt::skip or one of its ::macros forms."""
    return path[:2] == RUSTFMT_SKIP and (
        len(path) == 2 or (len(path) == 3 and path[2] in RUSTFMT_SKIP_TARGETS)
    )


def _rust_lint_directives(
    silencer: str,
    arguments: Node,
    source: bytes,
) -> Iterator[tuple[str, str]]:
    """Yield a finding for each tool whose lint allow or expect names."""
    for segment in _rust_segments(arguments):
        lint, _ = _rust_meta(segment, source)
        if lint:
            yield _rust_lint_tool(lint), silencer


def _rust_cfg_attr_directives(
    arguments: Node,
    source: bytes,
) -> Iterator[tuple[str, str]]:
    """Yield findings for a cfg_attr: its condition, then its attributes."""
    condition, *attributes = _rust_segments(arguments) or [[]]
    cfg = _rust_coverage_cfg(condition, source)
    if cfg is not None:
        yield "coverage", f"cfg_attr({cfg})"
    for segment in attributes:
        yield from _rust_directives(*_rust_meta(segment, source), source)


def _rust_directives(
    path: RustPath,
    arguments: Node | None,
    source: bytes,
) -> Iterator[tuple[str, str]]:
    """Yield the (tool, directive) findings of one attribute.

    Args:
        path: The attribute's path, such as ("allow",) or ("rustfmt", "skip").
        arguments: The token tree after the path, if there is one.
        source: The file's source bytes.
    """
    if _is_rustfmt_skip(path):
        yield "rustfmt", "::".join(path)
    if arguments is None:
        return
    name = path[0] if len(path) == 1 else None
    if name in RUST_LINT_SILENCERS:
        yield from _rust_lint_directives(path[0], arguments, source)
    elif name == "coverage":
        if RUST_COVERAGE_OFF in _rust_names([arguments], source):
            yield "coverage", f"coverage({RUST_COVERAGE_OFF})"
    elif name == "cfg":
        cfg = _rust_coverage_cfg([arguments], source)
        if cfg is not None:
            yield "coverage", f"cfg({cfg})"
    elif name == "cfg_attr":
        yield from _rust_cfg_attr_directives(arguments, source)


def _rust_macro_directives(
    macro: Node,
    source: bytes,
) -> Iterator[tuple[str, str]]:
    """Yield a coverage finding for a cfg! macro that names coverage."""
    name = macro.child_by_field_name("macro")
    if name is None or _rust_text(name, source) != "cfg":
        return
    cfg = _rust_coverage_cfg(macro.children, source)
    if cfg is not None:
        yield "coverage", f"cfg!({cfg})"


def scan_rust(content: str) -> list[tuple[int, str, str]]:
    """Find the directives of a Rust file by parsing it.

    Reads each attribute, outer or inner, and each cfg! macro. A finding is
    placed on the line its attribute or macro starts on.

    Args:
        content: The Rust source.

    Returns:
        A (line_number, tool, directive) tuple for each finding, in source
        order, for every tool.
    """
    source = content.encode("utf-8")
    root = Parser(RUST).parse(source).root_node
    findings: list[tuple[int, str, str]] = []
    for node in _rust_descendants(root):
        if node.type in RUST_ATTRIBUTE_NODES:
            attribute = next(
                child for child in node.children if child.type == "attribute"
            )
            found = _rust_directives(
                *_rust_attribute_meta(attribute, source), source,
            )
        elif node.type == "macro_invocation":
            found = _rust_macro_directives(node, source)
        else:
            continue
        line_number = node.start_point[0] + 1
        findings.extend((line_number, tool, directive) for tool, directive in found)
    return findings


def _scan_rust_file(
    path: str,
    content: str,
    tools: frozenset[str],
    allow_patterns: list[str],
) -> list[Finding]:
    """Scan a Rust file, reporting each tool at most once per line."""
    lines = content.splitlines()
    seen: set[tuple[int, str]] = set()
    findings: list[Finding] = []
    for line_number, tool, directive in scan_rust(content):
        if tool not in tools or (line_number, tool) in seen:
            continue
        seen.add((line_number, tool))
        if not _is_allowed(lines[line_number - 1], allow_patterns):
            findings.append(Finding(
                path=path,
                line_number=line_number,
                tool=tool,
                directive=directive,
            ))
    return findings


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
    by tracking state across lines. A Rust file is parsed with its grammar,
    since its directives are attributes rather than comments.

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

    extension = os.path.splitext(path)[1].lower()
    if extension in RUST_EXTENSIONS:
        return _scan_rust_file(path, content, tools, allow_patterns)
    return _scan_comment_file(
        path, content, tools, allow_patterns, extension in C_EXTENSIONS,
    )


def _scan_comment_file(
    path: str,
    content: str,
    tools: frozenset[str],
    allow_patterns: list[str],
    is_c_family: bool,
) -> list[Finding]:
    """Scan a file whose directives are comments or line-based patterns.

    Args:
        path: The file path (used for reporting).
        content: The file content to scan.
        tools: Set of tools to check.
        allow_patterns: List of patterns to allow (skip matching directives).
        is_c_family: Whether the file uses C-style comments.

    Returns:
        A list of Finding objects for each directive found.
    """
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
