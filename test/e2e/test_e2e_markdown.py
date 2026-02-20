"""End-to-end tests for markdownlint tool support."""

import subprocess
from pathlib import Path

import pytest


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess."""
    return subprocess.run(
        ["assert-no-inline-directives", *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.e2e
class TestCliMarkdownlint:
    """E2E tests for markdownlint directive detection."""

    def test_disable_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for markdownlint-disable."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable -->\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 1

    def test_disable_output(self, tmp_path: Path) -> None:
        """Output contains markdownlint-disable directive."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable -->\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert "markdownlint:markdownlint-disable" in result.stdout

    def test_disable_next_line_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for markdownlint-disable-next-line."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "<!-- markdownlint-disable-next-line MD001 -->\n"
        )
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 1

    def test_disable_next_line_output(self, tmp_path: Path) -> None:
        """Output contains markdownlint-disable-next-line directive."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "<!-- markdownlint-disable-next-line MD001 -->\n"
        )
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert (
            "markdownlint:markdownlint-disable-next-line" in result.stdout
        )

    def test_disable_line_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for markdownlint-disable-line."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "# Title <!-- markdownlint-disable-line MD001 -->\n"
        )
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 1

    def test_disable_file_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for markdownlint-disable-file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable-file -->\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 1

    def test_capture_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for markdownlint-capture."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-capture -->\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 1

    def test_configure_file_returncode(self, tmp_path: Path) -> None:
        """Exit code 1 for markdownlint-configure-file."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            '<!-- markdownlint-configure-file { "MD013": false } -->\n'
        )
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 1

    def test_clean_file_returncode(self, tmp_path: Path) -> None:
        """Exit code 0 for clean markdown file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\nSome text.\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestCliMarkdownlintEnableNotDetected:
    """E2E tests that markdownlint enable directives are NOT detected."""

    def test_enable_not_detected(self, tmp_path: Path) -> None:
        """markdownlint-enable is not detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-enable -->\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 0

    def test_enable_with_rules_not_detected(self, tmp_path: Path) -> None:
        """markdownlint-enable with rules is not detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-enable MD001 -->\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 0

    def test_restore_not_detected(self, tmp_path: Path) -> None:
        """markdownlint-restore is not detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-restore -->\n")
        result = run_cli("--tools", "markdownlint", str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestCliMarkdownlintExtensionFiltering:
    """E2E tests for markdownlint extension filtering."""

    def test_md_files_scanned_returncode(self, tmp_path: Path) -> None:
        """markdownlint scans .md files - exit code 1."""
        md_file = tmp_path / "test.md"
        md_file.write_text("<!-- markdownlint-disable -->\n")
        result = run_cli("--tools", "markdownlint", str(md_file))
        assert result.returncode == 1

    def test_md_files_scanned_output(self, tmp_path: Path) -> None:
        """markdownlint scans .md files - output contains filename."""
        md_file = tmp_path / "test.md"
        md_file.write_text("<!-- markdownlint-disable -->\n")
        result = run_cli("--tools", "markdownlint", str(md_file))
        assert "test.md" in result.stdout

    def test_py_files_skipped(self, tmp_path: Path) -> None:
        """markdownlint skips .py files."""
        py_file = tmp_path / "test.py"
        py_file.write_text("<!-- markdownlint-disable -->\n")
        result = run_cli("--tools", "markdownlint", str(py_file))
        assert result.returncode == 0
