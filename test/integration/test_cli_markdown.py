"""Integration tests for markdownlint tool CLI handling."""

from pathlib import Path
from typing import Any

import pytest

from ..conftest import run_main_with_args


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

    def test_markdownlint_scans_md_files(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """markdownlint scans .md files."""
        md_file = tmp_path / "test.md"
        py_file = tmp_path / "test.py"
        md_file.write_text("<!-- markdownlint-disable -->\n")
        py_file.write_text("<!-- markdownlint-disable -->\n")
        run_main_with_args([
            "--tools", "markdownlint",
            str(md_file),
            str(py_file),
        ])
        captured = capsys.readouterr()
        assert "test.md" in captured.out

    def test_markdownlint_skips_py_files(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """markdownlint skips .py files."""
        md_file = tmp_path / "test.md"
        py_file = tmp_path / "test.py"
        md_file.write_text("<!-- markdownlint-disable -->\n")
        py_file.write_text("<!-- markdownlint-disable -->\n")
        run_main_with_args([
            "--tools", "markdownlint",
            str(md_file),
            str(py_file),
        ])
        captured = capsys.readouterr()
        assert "test.py" not in captured.out

    def test_combined_markdownlint_and_python_tools(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Combined markdownlint and Python tools scan appropriate files."""
        md_file = tmp_path / "test.md"
        py_file = tmp_path / "test.py"
        md_file.write_text("<!-- markdownlint-disable -->\n")
        py_file.write_text("x = 1  # type: ignore\n")
        run_main_with_args([
            "--tools", "markdownlint,mypy",
            str(md_file),
            str(py_file),
        ])
        captured = capsys.readouterr()
        assert "markdownlint-disable" in captured.out
        assert "type: ignore" in captured.out


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
