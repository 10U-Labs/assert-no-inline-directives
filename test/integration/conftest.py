"""Integration test configuration."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from _pytest.capture import CaptureResult
from test_run_main import run_main_with_args
from test_write_files import write_files


def run_and_capture(
    capsys: pytest.CaptureFixture[str], args: list[str]
) -> CaptureResult[str]:
    """Run main() with args and return what it printed."""
    run_main_with_args(args)
    return capsys.readouterr()


@pytest.fixture(name="two_file_finding_lines")
def fixture_two_file_finding_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> list[str]:
    """Output lines for one finding in each of a.py and b.py."""
    paths = write_files(tmp_path, {
        "a.py": "x = 1  # type: ignore\n",
        "b.py": "# pylint: disable=foo\n",
    })
    out = run_and_capture(capsys, ["--tools", "pylint,mypy", *paths]).out
    return out.strip().split("\n")


@pytest.fixture(name="exclude_vendor_output")
def fixture_exclude_vendor_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Output for test.py and vendor.py with *vendor* excluded."""
    paths = write_files(tmp_path, {
        "test.py": "x = 1  # type: ignore\n",
        "vendor.py": "y = 2  # type: ignore\n",
    })
    args = ["--tools", "mypy", "--exclude", "*vendor*", *paths]
    return run_and_capture(capsys, args).out


@pytest.fixture(name="allow_multiple_lines")
def fixture_allow_multiple_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> list[str]:
    """Output lines when two of three directives are allowed."""
    paths = write_files(tmp_path, {
        "test.py": (
            "# pylint: disable=too-many-arguments\n"
            "x = 1  # type: ignore[import]\n"
            "y = 2  # type: ignore\n"
        ),
    })
    out = run_and_capture(capsys, [
        "--tools", "pylint,mypy",
        "--allow", "type: ignore[import],too-many-arguments",
        *paths,
    ]).out
    return out.strip().split("\n")


@pytest.fixture(name="pylint_py_yaml_output")
def fixture_pylint_py_yaml_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Pylint output for a .py and a .yaml file holding the same directive."""
    paths = write_files(tmp_path, {
        "test.py": "# pylint: disable=foo\n",
        "test.yaml": "# pylint: disable=foo\n",
    })
    return run_and_capture(capsys, ["--tools", "pylint", *paths]).out


@pytest.fixture(name="yamllint_output")
def fixture_yamllint_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Yamllint output for .yaml, .yml and .py files with the same directive."""
    directive = "# yamllint disable\n"
    paths = write_files(tmp_path, {
        "test.yaml": directive,
        "test.yml": directive,
        "test.py": directive,
    })
    return run_and_capture(capsys, ["--tools", "yamllint", *paths]).out


@pytest.fixture(name="combined_linters_output")
def fixture_combined_linters_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Pylint and yamllint output for .py, .yaml and .txt files."""
    paths = write_files(tmp_path, {
        "test.py": "# pylint: disable=foo\n",
        "test.yaml": "# yamllint disable\n",
        "test.txt": "# pylint: disable=foo\n",
    })
    return run_and_capture(capsys, ["--tools", "pylint,yamllint", *paths]).out


@pytest.fixture(name="verbose_fail_fast_output")
def fixture_verbose_fail_fast_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Verbose fail-fast output for two files with findings."""
    paths = write_files(tmp_path, {
        "first.py": "# pylint: disable=one\n",
        "second.py": "# pylint: disable=two\n",
    })
    args = ["--tools", "pylint", "--verbose", "--fail-fast", *paths]
    return run_and_capture(capsys, args).out


@pytest.fixture(name="unreadable_in_directory")
def fixture_unreadable_in_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> Iterator[CaptureResult[str]]:
    """Output for a directory holding an unreadable and a readable file."""
    subdir = tmp_path / "subdir"
    write_files(subdir, {
        "unreadable.py": "content\n",
        "readable.py": "x = 1  # type: ignore\n",
    })
    unreadable = subdir / "unreadable.py"
    unreadable.chmod(0o000)
    try:
        yield run_and_capture(capsys, ["--tools", "mypy", str(subdir)])
    finally:
        unreadable.chmod(0o644)


@pytest.fixture(name="glob_three_files_output")
def fixture_glob_three_files_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Output for *.py matching two files with findings and one without."""
    write_files(tmp_path, {
        "alpha.py": "a = 1  # type: ignore\n",
        "beta.py": "b = 2  # type: ignore\n",
        "gamma.py": "clean code\n",
    })
    args = ["--tools", "mypy", str(tmp_path / "*.py")]
    return run_and_capture(capsys, args).out


@pytest.fixture(name="recursive_glob_output")
def fixture_recursive_glob_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Output for **/*.py matching a root and a deeply nested file."""
    write_files(tmp_path, {
        "src/pkg/subpkg/module.py": "# pylint: disable=all\n",
        "root.py": "# pylint: disable=all\n",
    })
    args = ["--tools", "pylint", str(tmp_path / "**" / "*.py")]
    return run_and_capture(capsys, args).out


@pytest.fixture(name="clang_tidy_and_mypy_output")
def fixture_clang_tidy_and_mypy_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Clang-tidy and mypy output for a .cpp and a .py file."""
    paths = write_files(tmp_path, {
        "test.cpp": "int x = 1; // NOLINT\n",
        "test.py": "x = 1  # type: ignore\n",
    })
    return run_and_capture(capsys, ["--tools", "clang-tidy,mypy", *paths]).out


@pytest.fixture(name="markdownlint_md_py_output")
def fixture_markdownlint_md_py_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Markdownlint output for a .md and a .py file with the same directive."""
    directive = "<!-- markdownlint-disable -->\n"
    paths = write_files(tmp_path, {"test.md": directive, "test.py": directive})
    return run_and_capture(capsys, ["--tools", "markdownlint", *paths]).out


@pytest.fixture(name="markdownlint_and_mypy_output")
def fixture_markdownlint_and_mypy_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> str:
    """Markdownlint and mypy output for a .md and a .py file."""
    paths = write_files(tmp_path, {
        "test.md": "<!-- markdownlint-disable -->\n",
        "test.py": "x = 1  # type: ignore\n",
    })
    args = ["--tools", "markdownlint,mypy", *paths]
    return run_and_capture(capsys, args).out
