"""End-to-end test configuration."""

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from test_run_cli import run_cli
from test_write_files import write_files

MIXED_PYTHON = '''"""Module docstring."""

import os
import sys  # type: ignore[import]

# pylint: disable=too-many-arguments
def complex_function(a, b, c, d, e, f):
    """Do something complex."""
    result = a + b + c + d + e + f
    return result  # type: ignore


class MyClass:
    """A class."""

    def method(self):
        """A method."""
        pass  # pylint: disable=unnecessary-pass
'''

MIXED_YAML = '''---
# yamllint disable-file
name: example
settings:
  debug: true
  log_level: info  # yamllint disable-line rule:truthy
  max_connections: 100
'''

CLEAN_PYTHON = '''"""Clean module."""

from typing import List


def add_numbers(numbers: List[int]) -> int:
    """Add all numbers in the list."""
    return sum(numbers)


def main() -> None:
    """Main entry point."""
    result = add_numbers([1, 2, 3, 4, 5])
    print(f"Sum: {result}")


if __name__ == "__main__":
    main()
'''


@pytest.fixture(name="exclude_two_patterns_result")
def fixture_exclude_two_patterns_result(
    tmp_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Result for three files with *vendor* and *generated* excluded."""
    paths = write_files(tmp_path, {
        "test.py": "x = 1  # type: ignore\n",
        "vendor.py": "y = 2  # type: ignore\n",
        "generated.py": "z = 3  # type: ignore\n",
    })
    return run_cli(
        "--tools", "mypy", "--exclude", "*vendor*,*generated*", *paths
    )


@pytest.fixture(name="unreadable_in_directory_result")
def fixture_unreadable_in_directory_result(
    tmp_path: Path,
) -> Iterator[subprocess.CompletedProcess[str]]:
    """Result for a directory holding an unreadable and a readable file."""
    subdir = tmp_path / "subdir"
    write_files(subdir, {
        "unreadable.py": "clean\n",
        "readable.py": "# pylint: disable=foo\n",
    })
    unreadable = subdir / "unreadable.py"
    unreadable.chmod(0o000)
    try:
        yield run_cli("--tools", "pylint", str(subdir))
    finally:
        unreadable.chmod(0o644)


@pytest.fixture(name="mixed_python_result")
def fixture_mixed_python_result(
    tmp_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Result for a realistic Python file with four directives."""
    paths = write_files(tmp_path, {"example.py": MIXED_PYTHON})
    return run_cli("--tools", "pylint,mypy", *paths)


@pytest.fixture(name="mixed_yaml_result")
def fixture_mixed_yaml_result(
    tmp_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Result for a realistic YAML file with two directives."""
    paths = write_files(tmp_path, {"config.yaml": MIXED_YAML})
    return run_cli("--tools", "yamllint", *paths)


@pytest.fixture(name="clean_python_result")
def fixture_clean_python_result(
    tmp_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Result for a realistic Python file with no directives."""
    paths = write_files(tmp_path, {"clean.py": CLEAN_PYTHON})
    return run_cli("--tools", "pylint,mypy", *paths)


@pytest.fixture(name="alphabetical_scan_lines")
def fixture_alphabetical_scan_lines(tmp_path: Path) -> list[str]:
    """Verbose Scanning: lines for three files written out of order."""
    write_files(tmp_path, {
        "z_file.py": "# pylint: disable=a\n",
        "a_file.py": "# pylint: disable=b\n",
        "m_file.py": "# pylint: disable=c\n",
    })
    result = run_cli("--tools", "pylint", "--verbose", str(tmp_path))
    lines = result.stdout.splitlines()
    return [line for line in lines if line.startswith("Scanning:")]
