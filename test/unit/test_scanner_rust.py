"""Unit tests for the scanner module - Rust attributes."""

import pytest
from test_rust_sample import SAMPLE_RS, SAMPLE_RS_FINDINGS

from assert_no_inline_directives.scanner import (
    get_tools_for_extension,
    parse_tools,
    scan_file,
)

RUST_TOOLS = frozenset({"clippy", "coverage", "rustc", "rustdoc", "rustfmt"})


def rust_findings(
    content: str,
    tools: frozenset[str] = RUST_TOOLS,
    allow_patterns: list[str] | None = None,
) -> list[str]:
    """Scan content as a Rust file and return line:tool:directive strings."""
    findings = scan_file("lib.rs", content, tools, allow_patterns)
    return [f"{f.line_number}:{f.tool}:{f.directive}" for f in findings]


@pytest.mark.unit
class TestRustTools:
    """Tests for the Rust tool names and the .rs suffix."""

    @pytest.mark.parametrize("tool", ["clippy", "rustc", "rustdoc", "rustfmt"])
    def test_parse_tools_accepts_rust_tool(self, tool: str) -> None:
        """parse_tools accepts each Rust tool."""
        assert parse_tools(tool) == frozenset({tool})

    def test_rs_suffix_applies_to_rust_tools_and_coverage(self) -> None:
        """Each Rust tool and coverage applies to .rs, and no other tool does."""
        tools = frozenset({"clippy", "coverage", "mypy", "pylint", "rustc",
                           "rustdoc", "rustfmt", "clang-tidy"})
        assert get_tools_for_extension(".rs", tools) == RUST_TOOLS


@pytest.mark.unit
class TestRustLints:
    """Tests for lint levels: allow, expect, warn, deny and forbid."""

    @pytest.mark.parametrize(("source", "expected"), [
        ("#[allow(dead_code)]\nfn f() {}\n", ["1:rustc:allow"]),
        ("#[expect(dead_code)]\nfn f() {}\n", ["1:rustc:expect"]),
        ("#![allow(dead_code)]\n", ["1:rustc:allow"]),
        ("#![expect(dead_code)]\n", ["1:rustc:expect"]),
        ("#[allow(clippy::pedantic)]\nfn f() {}\n", ["1:clippy:allow"]),
        ("#![expect(clippy::pedantic)]\n", ["1:clippy:expect"]),
        ("#[allow(rustdoc::broken_intra_doc_links)]\nfn f() {}\n",
         ["1:rustdoc:allow"]),
        ("#![expect(rustdoc::all)]\n", ["1:rustdoc:expect"]),
        ("fn f() {\n    #![allow(unused)]\n}\n", ["2:rustc:allow"]),
        ("#[warn(missing_docs)]\nfn f() {}\n", ["1:rustc:warn"]),
        ("#[deny(missing_docs)]\nfn f() {}\n", ["1:rustc:deny"]),
        ("#![forbid(unsafe_code)]\n", ["1:rustc:forbid"]),
        ("#![deny(clippy::pedantic)]\n", ["1:clippy:deny"]),
        ("#[warn(rustdoc::all)]\nfn f() {}\n", ["1:rustdoc:warn"]),
        ("#[cfg_attr(test, forbid(unsafe_code))]\nfn f() {}\n",
         ["1:rustc:forbid"]),
    ])
    def test_lint_level_reported(
        self, source: str, expected: list[str]
    ) -> None:
        """Each lint level is reported for the tool whose lint it names."""
        assert rust_findings(source) == expected

    def test_two_tools_reported_once_each(self) -> None:
        """An attribute naming lints of two tools is reported for each."""
        source = "#[allow(dead_code, unused, clippy::pedantic,)]\nfn f() {}\n"
        assert rust_findings(source) == ["1:rustc:allow", "1:clippy:allow"]

    def test_only_tools_asked_for(self) -> None:
        """A lint of a tool not asked for is not reported."""
        source = "#[allow(dead_code, clippy::pedantic)]\nfn f() {}\n"
        assert rust_findings(source, frozenset({"clippy"})) == [
            "1:clippy:allow"
        ]

    def test_empty_allow_not_reported(self) -> None:
        """An allow that names no lint sets no level."""
        assert not rust_findings("#[allow()]\nfn f() {}\n")

    def test_allow_without_arguments_not_reported(self) -> None:
        """An allow with no arguments sets no level."""
        assert not rust_findings("#[allow]\nfn f() {}\n")


@pytest.mark.unit
class TestRustfmt:
    """Tests for rustfmt::skip."""

    @pytest.mark.parametrize(("source", "expected"), [
        ("#[rustfmt::skip]\nfn f() {}\n", ["1:rustfmt:rustfmt::skip"]),
        ("#![rustfmt::skip]\n", ["1:rustfmt:rustfmt::skip"]),
        ("#[rustfmt::skip::macros(vec)]\nfn f() {}\n",
         ["1:rustfmt:rustfmt::skip::macros"]),
        ("#[rustfmt::skip::attributes(derive)]\nfn f() {}\n",
         ["1:rustfmt:rustfmt::skip::attributes"]),
    ])
    def test_rustfmt_skip_reported(
        self, source: str, expected: list[str]
    ) -> None:
        """rustfmt::skip and its ::macros and ::attributes forms are reported."""
        assert rust_findings(source) == expected

    def test_other_rustfmt_path_not_reported(self) -> None:
        """A rustfmt path other than skip is not reported."""
        assert not rust_findings("#[rustfmt::skip::other]\nfn f() {}\n")


@pytest.mark.unit
class TestRustCoverage:
    """Tests for coverage(off), cfg(coverage) and cfg!(coverage)."""

    @pytest.mark.parametrize(("source", "expected"), [
        ("#[coverage(off)]\nfn f() {}\n", ["1:coverage:coverage(off)"]),
        ("#[cfg(coverage)]\nfn f() {}\n", ["1:coverage:cfg(coverage)"]),
        ("#[cfg(not(coverage))]\nfn f() {}\n", ["1:coverage:cfg(coverage)"]),
        ("#[cfg(coverage_nightly)]\nfn f() {}\n",
         ["1:coverage:cfg(coverage_nightly)"]),
        ("fn f() -> bool {\n    cfg!(coverage)\n}\n",
         ["2:coverage:cfg!(coverage)"]),
    ])
    def test_coverage_reported(self, source: str, expected: list[str]) -> None:
        """Attributes and macros that steer coverage are reported."""
        assert rust_findings(source) == expected

    @pytest.mark.parametrize("source", [
        "#[coverage(on)]\nfn f() {}\n",
        "#[cfg(test)]\nfn f() {}\n",
        "#[cfg(feature = \"coverage\")]\nfn f() {}\n",
        "fn f() -> bool {\n    cfg!(test)\n}\n",
        "fn f() {\n    println!(\"coverage\");\n}\n",
    ])
    def test_coverage_not_reported(self, source: str) -> None:
        """coverage(on) and cfgs that do not name coverage are not reported."""
        assert not rust_findings(source)


@pytest.mark.unit
class TestRustCfgAttr:
    """Tests for attributes wrapped in cfg_attr."""

    @pytest.mark.parametrize(("source", "expected"), [
        ("#[cfg_attr(test, allow(dead_code))]\nfn f() {}\n",
         ["1:rustc:allow"]),
        ("#[cfg_attr(test, expect(clippy::pedantic))]\nfn f() {}\n",
         ["1:clippy:expect"]),
        ("#[cfg_attr(test, rustfmt::skip)]\nfn f() {}\n",
         ["1:rustfmt:rustfmt::skip"]),
        ("#[cfg_attr(test, coverage(off))]\nfn f() {}\n",
         ["1:coverage:coverage(off)"]),
        ("#[cfg_attr(test, cfg(coverage))]\nfn f() {}\n",
         ["1:coverage:cfg(coverage)"]),
        ("#[cfg_attr(coverage, derive(Debug))]\nstruct S;\n",
         ["1:coverage:cfg_attr(coverage)"]),
        ("#[cfg_attr(all(unix, not(coverage_nightly)), inline)]\nfn f() {}\n",
         ["1:coverage:cfg_attr(coverage_nightly)"]),
        ("#[cfg_attr(test, allow(unused), rustfmt::skip)]\nfn f() {}\n",
         ["1:rustc:allow", "1:rustfmt:rustfmt::skip"]),
    ])
    def test_cfg_attr_read_through(
        self, source: str, expected: list[str]
    ) -> None:
        """cfg_attr's condition and each attribute it wraps are read."""
        assert rust_findings(source) == expected

    def test_coverage_once_per_line(self) -> None:
        """A coverage condition wrapping coverage(off) is reported once."""
        source = "#[cfg_attr(coverage_nightly, coverage(off))]\nfn f() {}\n"
        assert rust_findings(source) == [
            "1:coverage:cfg_attr(coverage_nightly)"
        ]

    def test_empty_cfg_attr_not_reported(self) -> None:
        """A cfg_attr with no arguments inside it is not reported."""
        assert not rust_findings("#[cfg_attr()]\nfn f() {}\n")


@pytest.mark.unit
class TestRustNotReported:
    """Tests for text that is not a directive."""

    @pytest.mark.parametrize("source", [
        'const S: &str = "#[allow(dead_code)]";\n',
        'const R: &str = r#"#[rustfmt::skip]"#;\n',
        "// #[allow(dead_code)]\n",
        "/* #[cfg(coverage)] */\n",
        "#[cfg(test)]\nmod tests {}\n",
        "#[derive(Debug)]\nstruct S;\n",
        "#[doc = \"allow\"]\nfn f() {}\n",
        "#[must_use]\nfn f() -> u8 { 0 }\n",
    ])
    def test_not_reported(self, source: str) -> None:
        """Strings, comments and attributes that set no lint level are clean."""
        assert not rust_findings(source)

    def test_attribute_below_lifetime_reported(self) -> None:
        """An attribute below a line holding a lifetime is still reported."""
        source = "fn f() -> &'static str {\n    \"\"\n}\n#[allow(unused)]\nfn g() {}\n"
        assert rust_findings(source) == ["4:rustc:allow"]

    def test_multiline_attribute_on_first_line(self) -> None:
        """An attribute spanning lines is reported on the line it starts on."""
        source = "#[allow(\n    dead_code,\n)]\nfn f() {}\n"
        assert rust_findings(source) == ["1:rustc:allow"]


@pytest.mark.unit
class TestRustFiles:
    """Tests for --allow against Rust lines and the sample from issue 21."""

    def test_allow_pattern_skips_line(self) -> None:
        """A line matching an allow pattern is not reported."""
        source = "#[allow(dead_code)]\nfn f() {}\n#[allow(unused)]\nfn g() {}\n"
        assert rust_findings(source, allow_patterns=["dead_code"]) == [
            "3:rustc:allow"
        ]

    def test_sample_findings(self) -> None:
        """The sample reports exactly its directive lines."""
        tools = frozenset({"clippy", "coverage", "rustc", "rustfmt"})
        assert rust_findings(SAMPLE_RS, tools) == SAMPLE_RS_FINDINGS
