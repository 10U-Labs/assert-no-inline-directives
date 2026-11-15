"""A Rust file holding one of each kind of directive, from issue 21."""

SAMPLE_RS = '''#![allow(dead_code)]
#![cfg_attr(coverage_nightly, feature(coverage_attribute))]

#[allow(clippy::too_many_arguments)]
fn silenced_clippy() {}

#[expect(unused_variables)]
fn expected() {
    let unused = 1;
}

#[warn(missing_docs)]
pub fn lowered() {}

#[rustfmt::skip]
fn unformatted() {}

#[cfg_attr(coverage_nightly, coverage(off))]
fn unmeasured() {}

#[cfg(not(coverage))]
fn gated() {}

fn text() -> &'static str {
    let s = "#[allow(dead_code)]";
    let r = r#"#[rustfmt::skip]"#;
    // #[allow(dead_code)]
    s
}
'''

SAMPLE_RS_FINDINGS = [
    "1:rustc:allow",
    "2:coverage:cfg_attr(coverage_nightly)",
    "4:clippy:allow",
    "7:rustc:expect",
    "12:rustc:warn",
    "15:rustfmt:rustfmt::skip",
    "18:coverage:cfg_attr(coverage_nightly)",
    "21:coverage:cfg(coverage)",
]
