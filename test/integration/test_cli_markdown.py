"""Integration tests for markdownlint tool CLI handling."""

from pathlib import Path
from typing import Any

import pytest
from test_run_main import run_main_with_args


@pytest.mark.integration
class TestCliMarkdownlintIntegration:
    """Integration tests for markdownlint tool via CLI."""

    def test_exit_1_with_disable(self, tmp_path: Path) -> None:
        """Exit code 1 for file with markdownlint-disable."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable -->\n# Title\n")
        exit_code = run_main_with_args([
            "--tools", "markdownlint", str(test_file)
        ])
        assert exit_code == 1

    def test_output_contains_disable(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Output contains markdownlint-disable directive."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable -->\n# Title\n")
        run_main_with_args(["--tools", "markdownlint", str(test_file)])
        captured = capsys.readouterr()
        assert "markdownlint-disable" in captured.out

    def test_exit_0_clean_md_file(self, tmp_path: Path) -> None:
        """Exit code 0 for clean markdown file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n\nSome text.\n")
        exit_code = run_main_with_args([
            "--tools", "markdownlint", str(test_file)
        ])
        assert exit_code == 0

    def test_disable_next_line_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """markdownlint-disable-next-line is detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "<!-- markdownlint-disable-next-line MD001 -->\n# Title\n"
        )
        run_main_with_args(["--tools", "markdownlint", str(test_file)])
        captured = capsys.readouterr()
        assert "markdownlint-disable-next-line" in captured.out

    def test_disable_line_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """markdownlint-disable-line is detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "# Title <!-- markdownlint-disable-line MD001 -->\n"
        )
        run_main_with_args(["--tools", "markdownlint", str(test_file)])
        captured = capsys.readouterr()
        assert "markdownlint-disable-line" in captured.out

    def test_disable_file_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """markdownlint-disable-file is detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable-file -->\n")
        run_main_with_args(["--tools", "markdownlint", str(test_file)])
        captured = capsys.readouterr()
        assert "markdownlint-disable-file" in captured.out

    def test_capture_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """markdownlint-capture is detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-capture -->\n")
        run_main_with_args(["--tools", "markdownlint", str(test_file)])
        captured = capsys.readouterr()
        assert "markdownlint-capture" in captured.out

    def test_configure_file_detected(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """markdownlint-configure-file is detected."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            '<!-- markdownlint-configure-file { "MD013": false } -->\n'
        )
        run_main_with_args(["--tools", "markdownlint", str(test_file)])
        captured = capsys.readouterr()
        assert "markdownlint-configure-file" in captured.out

    def test_enable_not_detected(self, tmp_path: Path) -> None:
        """markdownlint-enable is not detected (enable directive)."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-enable -->\n")
        exit_code = run_main_with_args([
            "--tools", "markdownlint", str(test_file)
        ])
        assert exit_code == 0

    def test_restore_not_detected(self, tmp_path: Path) -> None:
        """markdownlint-restore is not detected (enable directive)."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-restore -->\n")
        exit_code = run_main_with_args([
            "--tools", "markdownlint", str(test_file)
        ])
        assert exit_code == 0


@pytest.mark.integration
class TestCliMarkdownlintExtensionFiltering:
    """Integration tests for markdownlint file extension filtering."""

    def test_markdownlint_scans_md_files(self, markdownlint_md_py_output: str) -> None:
        """markdownlint scans .md files."""
        assert "test.md" in markdownlint_md_py_output

    def test_markdownlint_skips_py_files(self, markdownlint_md_py_output: str) -> None:
        """markdownlint skips .py files."""
        assert "test.py" not in markdownlint_md_py_output

    def test_combined_tools_detect_markdownlint(
        self, markdownlint_and_mypy_output: str
    ) -> None:
        """Combined tools detect markdownlint in .md files."""
        assert "markdownlint-disable" in markdownlint_and_mypy_output

    def test_combined_tools_detect_mypy(
        self, markdownlint_and_mypy_output: str
    ) -> None:
        """Combined tools detect mypy in .py files."""
        assert "type: ignore" in markdownlint_and_mypy_output


@pytest.mark.integration
class TestCliMarkdownlintAllowIntegration:
    """Integration tests for --allow flag with markdownlint."""

    def test_allow_specific_disable(self, tmp_path: Path) -> None:
        """Allowed markdownlint-disable pattern is skipped."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable MD013 -->\n")
        exit_code = run_main_with_args([
            "--tools", "markdownlint",
            "--allow", "markdownlint-disable MD013",
            str(test_file),
        ])
        assert exit_code == 0

    def test_allow_does_not_skip_other_disable(
        self, tmp_path: Path
    ) -> None:
        """Allow pattern does not skip non-matching disable."""
        test_file = tmp_path / "test.md"
        test_file.write_text("<!-- markdownlint-disable -->\n")
        exit_code = run_main_with_args([
            "--tools", "markdownlint",
            "--allow", "markdownlint-disable MD013",
            str(test_file),
        ])
        assert exit_code == 1
