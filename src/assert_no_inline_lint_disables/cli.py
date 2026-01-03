"""Command-line interface for assert-no-inline-lint-disables."""

import argparse
import fnmatch
import os
import sys
from dataclasses import dataclass, field

from assert_no_inline_lint_disables.scanner import (
    Finding,
    get_linters_for_extension,
    get_relevant_extensions,
    parse_linters,
    scan_file,
)

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="assert-no-inline-lint-disables",
        description="Assert that files contain no inline lint-disable directives.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more file paths to scan.",
    )
    parser.add_argument(
        "--linters",
        required=True,
        metavar="LINTERS",
        help="Comma-separated linters to check: yamllint,pylint,mypy",
    )
    parser.add_argument(
        "--exclude",
        metavar="PATTERNS",
        help="Comma-separated glob patterns to exclude files.",
    )

    # Output mode group (mutually exclusive)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output, exit code only.",
    )
    output_group.add_argument(
        "--count",
        action="store_true",
        help="Print finding count only.",
    )
    output_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show linters, files scanned/skipped, findings, and summary.",
    )

    # Behavior modifiers (mutually exclusive)
    behavior_group = parser.add_mutually_exclusive_group()
    behavior_group.add_argument(
        "--fail-fast",
        action="store_true",
        help="Exit on first finding.",
    )
    behavior_group.add_argument(
        "--warn-only",
        action="store_true",
        help="Always exit 0, report only.",
    )

    parser.add_argument(
        "--allow",
        metavar="PATTERNS",
        help="Comma-separated patterns to allow.",
    )

    return parser


def parse_patterns(patterns_str: str | None) -> list[str]:
    """Parse comma-separated patterns string into a list."""
    if not patterns_str:
        return []
    return [p.strip() for p in patterns_str.split(",") if p.strip()]


def _output_findings(findings: list[Finding], use_count: bool) -> None:
    """Output findings in the appropriate format."""
    if use_count:
        print(len(findings))
    else:
        for finding in findings:
            print(finding)


def _should_skip_file(
    path: str,
    relevant_extensions: frozenset[str],
    exclude_patterns: list[str],
) -> bool:
    """Check if a file should be skipped (not a matching file or excluded)."""
    _, ext = os.path.splitext(path)
    if ext.lower() not in relevant_extensions:
        return True
    if any(fnmatch.fnmatch(path, pattern) for pattern in exclude_patterns):
        return True
    return False


def _iter_files(paths: list[str]) -> tuple[list[str], list[str]]:
    """Expand paths to a list of files, recursively walking directories.

    Returns:
        Tuple of (files, missing_paths) where missing_paths are paths that don't exist.
    """
    result: list[str] = []
    missing: list[str] = []
    for path in paths:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for filename in files:
                    result.append(os.path.join(root, filename))
        elif os.path.isfile(path):
            result.append(path)
        else:
            missing.append(path)
    return result, missing


@dataclass
class _ScanResult:
    """Result of scanning files."""

    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    had_error: bool = False


def _scan_single_file(
    path: str,
    linters: frozenset[str],
    allow_patterns: list[str] | None,
    result: _ScanResult,
) -> list[Finding] | None:
    """Scan a single file and update result. Returns findings or None on error."""
    # Filter linters to only those relevant to this file's extension
    _, ext = os.path.splitext(path)
    file_linters = get_linters_for_extension(ext, linters)

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        result.had_error = True
        return None
    return scan_file(path, content, file_linters, allow_patterns)


def _process_files(
    args: argparse.Namespace,
    linters: frozenset[str],
    exclude_patterns: list[str],
    allow_patterns: list[str] | None,
) -> _ScanResult:
    """Process files and return scan result."""
    result = _ScanResult()
    relevant_extensions = get_relevant_extensions(linters)

    # Expand directories to files
    all_files, missing_paths = _iter_files(args.files)

    # Report missing paths as errors
    for path in missing_paths:
        print(f"Error: {path}: No such file or directory", file=sys.stderr)
        result.had_error = True

    for path in all_files:
        if _should_skip_file(path, relevant_extensions, exclude_patterns):
            continue

        if args.verbose:
            print(f"Scanning: {path}")
        result.files_scanned += 1

        findings = _scan_single_file(path, linters, allow_patterns, result)
        if findings is None:
            continue

        if findings and args.fail_fast:
            if args.verbose:
                print(findings[0])
                print(f"Scanned {result.files_scanned} file(s), found 1 finding")
            elif not args.quiet:
                _output_findings([findings[0]], args.count)
            sys.exit(EXIT_FINDINGS)

        if args.verbose:
            for finding in findings:
                print(finding)

        result.findings.extend(findings)

    return result


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        linters = parse_linters(args.linters)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    if args.verbose:
        print(f"Checking for: {', '.join(sorted(linters))}")

    exclude_patterns = parse_patterns(args.exclude)
    allow_patterns = parse_patterns(args.allow) or None

    result = _process_files(args, linters, exclude_patterns, allow_patterns)

    if args.verbose:
        print(f"Scanned {result.files_scanned} file(s), found {len(result.findings)} finding(s)")
    elif not args.quiet:
        _output_findings(result.findings, args.count)

    if args.warn_only:
        sys.exit(EXIT_SUCCESS)
    if result.findings:
        sys.exit(EXIT_FINDINGS)
    if result.had_error:
        sys.exit(EXIT_ERROR)
    sys.exit(EXIT_SUCCESS)
