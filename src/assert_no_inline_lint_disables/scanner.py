"""Core scanner logic for detecting inline lint-disable directives."""

import re
from dataclasses import dataclass


VALID_LINTERS = frozenset({"yamllint", "pylint", "mypy"})

# File extensions relevant to each linter
LINTER_EXTENSIONS: dict[str, frozenset[str]] = {
    "yamllint": frozenset({".yaml", ".yml"}),
    "pylint": frozenset({".py"}),
    "mypy": frozenset({".py"}),
}


@dataclass(frozen=True)
class Finding:
    """Represents a single finding of an inline lint-disable directive."""

    path: str
    line_number: int
    linter: str
    directive: str

    def __str__(self) -> str:
        """Format finding as path:line:linter:directive."""
        return f"{self.path}:{self.line_number}:{self.linter}:{self.directive}"


# Patterns for detecting inline lint-disable directives (suppressions only).
# Each pattern uses \\s* to tolerate extra whitespace.
# All patterns are case-insensitive.

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

LINTER_PATTERNS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "yamllint": YAMLLINT_PATTERNS,
    "pylint": PYLINT_PATTERNS,
    "mypy": MYPY_PATTERNS,
}


def scan_line(
    line: str,
    linters: frozenset[str],
) -> list[tuple[str, str]]:
    """Scan a single line for inline lint-disable directives.

    Args:
        line: The line of text to scan.
        linters: Set of linters to check.

    Returns:
        A list of (linter, directive) tuples for each finding.
    """
    findings: list[tuple[str, str]] = []
    for linter in linters:
        patterns = LINTER_PATTERNS.get(linter, [])
        for pattern, directive in patterns:
            if pattern.search(line):
                findings.append((linter, directive))
                break  # Only report one finding per linter per line
    return findings


def scan_file(
    path: str,
    content: str,
    linters: frozenset[str],
    allow_patterns: list[str] | None = None,
) -> list[Finding]:
    """Scan file content for inline lint-disable directives.

    Args:
        path: The file path (used for reporting).
        content: The file content to scan.
        linters: Set of linters to check.
        allow_patterns: List of patterns to allow (skip matching directives).

    Returns:
        A list of Finding objects for each directive found.
    """
    if allow_patterns is None:
        allow_patterns = []

    findings: list[Finding] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for linter, directive in scan_line(line, linters):
            # Check if this directive matches any allow pattern
            is_allowed = any(
                allow_pat.lower() in line.lower()
                for allow_pat in allow_patterns
            )
            if not is_allowed:
                findings.append(Finding(
                    path=path,
                    line_number=line_number,
                    linter=linter,
                    directive=directive,
                ))
    return findings


def parse_linters(linters_str: str) -> frozenset[str]:
    """Parse comma-separated linters string and validate.

    Args:
        linters_str: Comma-separated list of linter names.

    Returns:
        Frozenset of valid linter names.

    Raises:
        ValueError: If any linter name is invalid.
    """
    linters = frozenset(l.strip() for l in linters_str.split(",") if l.strip())

    invalid = linters - VALID_LINTERS
    if invalid:
        valid_list = ", ".join(sorted(VALID_LINTERS))
        invalid_list = ", ".join(sorted(invalid))
        raise ValueError(
            f"Invalid linter(s): {invalid_list}. Valid options: {valid_list}"
        )

    if not linters:
        raise ValueError("At least one linter must be specified")

    return linters


def get_relevant_extensions(linters: frozenset[str]) -> frozenset[str]:
    """Get file extensions relevant to the specified linters.

    Args:
        linters: Set of linter names.

    Returns:
        Frozenset of file extensions (including the dot, e.g., ".py").
    """
    extensions: set[str] = set()
    for linter in linters:
        extensions.update(LINTER_EXTENSIONS.get(linter, set()))
    return frozenset(extensions)


def get_linters_for_extension(
    extension: str,
    linters: frozenset[str],
) -> frozenset[str]:
    """Get linters that apply to a specific file extension.

    Args:
        extension: File extension (including the dot, e.g., ".py").
        linters: Set of linter names to filter.

    Returns:
        Frozenset of linters that apply to this extension.
    """
    ext_lower = extension.lower()
    return frozenset(
        linter for linter in linters
        if ext_lower in LINTER_EXTENSIONS.get(linter, frozenset())
    )
