"""Integration tests for Rust attribute handling via the CLI."""

import pytest
from test_run_main import run_main_with_args
from test_rust_sample import SAMPLE_RS_FINDINGS

from assert_no_inline_directives.scanner import scan_file

SAMPLE_TOOLS = "clippy,coverage,rustc,rustfmt"

MACROS_RS = '''fn f() -> bool {
    println!("coverage");
    cfg!(coverage)
}
'''


@pytest.mark.integration
class TestCliRustIntegration:
    """Integration tests for Rust tools via the CLI."""

    def test_sample_exit_code(self, sample_path: str) -> None:
        """Exit code 1 for the sample file."""
        exit_code = run_main_with_args(["--tools", SAMPLE_TOOLS, sample_path])
        assert exit_code == 1

    def test_sample_reports_directive_lines(
        self, sample_path: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The sample reports lines 1, 2, 4, 7, 15, 18 and 21 only."""
        run_main_with_args(["--tools", SAMPLE_TOOLS, sample_path])
        captured = capsys.readouterr()
        expected = [f"{sample_path}:{line}" for line in SAMPLE_RS_FINDINGS]
        assert captured.out.splitlines() == expected

    def test_tool_not_asked_for_not_reported(
        self, sample_path: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Only the tools asked for are reported."""
        run_main_with_args(["--tools", "rustfmt", sample_path])
        captured = capsys.readouterr()
        assert captured.out.splitlines() == [
            f"{sample_path}:15:rustfmt:rustfmt::skip"
        ]

    def test_allow_pattern(
        self, sample_path: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--allow matches against the text of a Rust line."""
        args = ["--tools", "rustc", "--allow", "unused_variables", sample_path]
        run_main_with_args(args)
        captured = capsys.readouterr()
        assert captured.out.splitlines() == [f"{sample_path}:1:rustc:allow"]

    def test_rs_skipped_for_python_tools(
        self, sample_path: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A tool that does not apply to .rs scans no Rust file."""
        run_main_with_args(["--tools", "mypy", "--count", sample_path])
        captured = capsys.readouterr()
        assert captured.out.strip() == "0"


@pytest.mark.integration
class TestScanFileRustIntegration:
    """Integration tests for scan_file over Rust content."""

    def test_cfg_macro(self) -> None:
        """cfg!(coverage) is reported and other macros are not."""
        findings = scan_file("lib.rs", MACROS_RS, frozenset({"coverage"}))
        assert [str(f) for f in findings] == ["lib.rs:3:coverage:cfg!(coverage)"]

    def test_rustdoc_lint(self) -> None:
        """A rustdoc lint is reported for rustdoc."""
        content = "#![allow(rustdoc::all)]\n"
        findings = scan_file("lib.rs", content, frozenset({"rustdoc"}))
        assert [str(f) for f in findings] == ["lib.rs:1:rustdoc:allow"]

    def test_empty_cfg_attr_and_allow(self) -> None:
        """An empty cfg_attr and an allow without arguments are clean."""
        content = "#[cfg_attr()]\n#[allow]\n#[allow()]\nfn f() {}\n"
        assert not scan_file("lib.rs", content, frozenset({"rustc"}))
