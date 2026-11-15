# assert-no-inline-directives

A CLI tool to assert that files contain no inline directives for
clang-diagnostic, clang-format, clang-tidy, clippy, coverage,
markdownlint, mypy, pylint, rustc, rustdoc, rustfmt, and yamllint.

## Usage

```bash
assert-no-inline-directives --tools TOOLS [OPTIONS] PATH [PATH ...]
```

### Required Arguments

- `--tools TOOLS` - Comma-separated list of tools: `clang-diagnostic,clang-format,clang-tidy,clippy,coverage,markdownlint,mypy,pylint,rustc,rustdoc,rustfmt,yamllint`
- `PATH` - One or more file paths, directory paths, or glob patterns to scan
  (directories are scanned recursively, globs support hidden directories)

### Optional Arguments

- `--allow PATTERNS` - Comma-separated patterns to allow
- `--count` - Print finding count only
- `--exclude PATTERNS` - Comma-separated glob patterns to exclude files
- `--fail-fast` - Exit on first finding
- `--quiet` - Suppress output, exit code only
- `-v, --verbose` - Show tools, files scanned, findings, and summary
- `--warn-only` - Always exit 0, report only

### Examples

```bash
# Check all clang tools
assert-no-inline-directives --tools clang-tidy,clang-format,clang-diagnostic src/

# Check for clang-tidy NOLINT directives in C++ files
assert-no-inline-directives --tools clang-tidy "**/*.cpp" "**/*.h"

# Check for coverage pragmas
assert-no-inline-directives --tools coverage src/

# Check Rust attributes that set lint levels or silence rustfmt or coverage
assert-no-inline-directives --tools clippy,coverage,rustc,rustdoc,rustfmt src/

# Check for markdownlint suppressions in markdown files
assert-no-inline-directives --tools markdownlint "**/*.md"

# Check for pylint and mypy suppressions in files
assert-no-inline-directives --tools pylint,mypy src/*.py

# Scan a directory recursively
assert-no-inline-directives --tools pylint,mypy src/

# Use glob patterns (including hidden directories like .github)
assert-no-inline-directives --tools yamllint "**/*.yml" "**/*.yaml"

# Check all Python/YAML tools, exclude vendor files
assert-no-inline-directives --tools coverage,mypy,pylint,yamllint \
    --exclude "*vendor*" src/ config/

# Allow specific type: ignore patterns
assert-no-inline-directives --tools mypy \
    --allow "type: ignore[import]" src/*.py

# CI mode: quiet, just exit code
assert-no-inline-directives --tools pylint,mypy --quiet src/

# Verbose mode: show progress
assert-no-inline-directives --tools pylint,mypy --verbose src/

# Non-blocking check (always exit 0)
assert-no-inline-directives --tools mypy --warn-only src/
```

### Exit Codes

- `0` - No inline directives found
- `1` - One or more inline directives found
- `2` - Usage or runtime error (e.g., file not found, invalid tool)

### Output Formats

**Default format** (one finding per line):

```text
config.yaml:5:yamllint:yamllint disable
README.md:3:markdownlint:markdownlint-disable
src/example.py:10:pylint:pylint: disable
src/example.py:15:mypy:type: ignore
src/example.py:20:coverage:pragma: no cover
src/main.cpp:8:clang-tidy:NOLINT
src/lib.rs:4:clippy:allow
```

**Count format** (`--count`):

```text
2
```

## Detected Directives

### clang-diagnostic (suppressions only)

- `#pragma clang diagnostic ignored`

### clang-format (suppressions only)

- `clang-format off`

### clang-tidy (suppressions only)

- `NOLINT` (including check-specific forms like `NOLINT(bugprone-*)`)
- `NOLINTBEGIN`
- `NOLINTNEXTLINE`

### clippy

- `#[allow(clippy::...)]`, `#[expect(clippy::...)]`, `#[warn(clippy::...)]`,
  `#[deny(clippy::...)]` and `#[forbid(clippy::...)]`

### coverage

- `pragma: no branch`
- `pragma: no cover`
- `#[coverage(off)]` (Rust)
- `#[cfg(...)]`, `#[cfg_attr(...)]` and `cfg!(...)` whose predicate names
  `coverage` or `coverage_nightly` (Rust)

### markdownlint (suppressions only)

- `markdownlint-capture`
- `markdownlint-configure-file`
- `markdownlint-disable`
  (including rule-specific forms like `markdownlint-disable MD001`)
- `markdownlint-disable-file`
- `markdownlint-disable-line`
- `markdownlint-disable-next-line`

### mypy (suppressions only)

- `mypy: ignore-errors`
- `type: ignore` (including bracketed forms like `type: ignore[attr-defined]`)

### pylint (suppressions only)

- `pylint: disable`
- `pylint: disable-line`
- `pylint: disable-next`
- `pylint: skip-file`

### rustc

- `#[allow(LINT)]`, `#[expect(LINT)]`, `#[warn(LINT)]`, `#[deny(LINT)]`
  and `#[forbid(LINT)]` for a lint with no tool prefix

### rustdoc

- `#[allow(rustdoc::...)]`, `#[expect(rustdoc::...)]`, `#[warn(rustdoc::...)]`,
  `#[deny(rustdoc::...)]` and `#[forbid(rustdoc::...)]`

### rustfmt (suppressions only)

- `#[rustfmt::skip]`
- `#[rustfmt::skip::attributes(...)]`
- `#[rustfmt::skip::macros(...)]`

### yamllint (suppressions only)

- `yamllint disable`
- `yamllint disable-file`
- `yamllint disable-line`

## Matching Behavior

- A Rust directive is an attribute, so a `.rs` file is parsed with
  `tree-sitter-rust` and its attributes read, rather than a pattern
  matched in a comment:
  - outer (`#[...]`) and inner (`#![...]`) attributes are both read,
    and a finding is reported on the line the attribute starts on
  - an attribute that names lints of several tools,
    such as `#[allow(dead_code, clippy::pedantic)]`,
    is reported once for each tool
  - `#[cfg_attr(CONDITION, ATTRIBUTE, ...)]` is read through:
    its condition as the predicate of a `cfg`,
    and each wrapped attribute as though it stood alone
  - every lint level is reported (`allow`, `expect`, `warn`, `deny`
    and `forbid`), since a lint's level belongs in configuration,
    not inline, in either direction
  - `#[coverage(on)]` is not reported, as an "enable" directive
  - text in a string, raw string or comment is not an attribute
    and is not reported
- Case-insensitive matching (except Rust, whose attributes are
  case-sensitive)
- Tolerates extra whitespace (e.g., `pylint:  disable`, `type:   ignore`)
- Only detects directives in comments
  (after `#` for Python/YAML,
  `//` and `/* */` for C/C++),
  not in string literals (Rust is read by its grammar, above)
- `clang-diagnostic` matches `#pragma`
  preprocessor directives on the full line
- `markdownlint` matches `<!-- markdownlint-... -->`
  HTML comment directives on the full line
- Does **not** flag "enable" directives
  (e.g., `clang-format on`, `markdownlint-enable`,
  `markdownlint-restore`, `NOLINTEND`,
  `yamllint enable`)
- Files are scanned in alphabetical order
  for consistent output
- Glob patterns support hidden directories
  (e.g., `.github`)
- Tools only check files with matching
  extensions:
  - `clang-diagnostic`:
    `.c`, `.cc`, `.cpp`, `.cxx`,
    `.h`, `.hpp`, `.hxx`, `.m`, `.mm`
  - `clang-format`:
    `.c`, `.cc`, `.cpp`, `.cxx`,
    `.h`, `.hpp`, `.hxx`, `.m`, `.mm`
  - `clang-tidy`:
    `.c`, `.cc`, `.cpp`, `.cxx`,
    `.h`, `.hpp`, `.hxx`, `.m`, `.mm`
  - `clippy`: `.rs`
  - `coverage`: `.py`, `.toml`, `.rs`
  - `markdownlint`: `.md`
  - `mypy`: `.py`, `.toml`
  - `pylint`: `.py`, `.toml`
  - `rustc`: `.rs`
  - `rustdoc`: `.rs`
  - `rustfmt`: `.rs`
  - `yamllint`: `.yaml`, `.yml`, `.toml`
