# assert-no-inline-directives

A CLI tool to assert that files contain no inline directives for
yamllint, pylint, mypy, and coverage.

## Installation

```bash
pip install assert-no-inline-directives
```

## Usage

```bash
assert-no-inline-directives --tools TOOLS [OPTIONS] PATH [PATH ...]
```

### Required Arguments

- `--tools TOOLS` - Comma-separated list of tools: `coverage,mypy,pylint,yamllint`
- `PATH` - One or more file paths, directory paths, or glob patterns to scan
  (directories are scanned recursively, globs support hidden directories)

### Optional Arguments

- `--exclude PATTERNS` - Comma-separated glob patterns to exclude files
- `--quiet` - Suppress output, exit code only
- `--count` - Print finding count only
- `-v, --verbose` - Show tools, files scanned, findings, and summary
- `--fail-fast` - Exit on first finding
- `--warn-only` - Always exit 0, report only
- `--allow PATTERNS` - Comma-separated patterns to allow

### Examples

```bash
# Check for pylint and mypy suppressions in files
assert-no-inline-directives --tools pylint,mypy src/*.py

# Scan a directory recursively
assert-no-inline-directives --tools pylint,mypy src/

# Use glob patterns (including hidden directories like .github)
assert-no-inline-directives --tools yamllint "**/*.yml" "**/*.yaml"

# Check all tools, exclude vendor files
assert-no-inline-directives --tools coverage,mypy,pylint,yamllint \
    --exclude "*vendor*" src/ config/

# Allow specific type: ignore patterns
assert-no-inline-directives --tools mypy \
    --allow "type: ignore[import]" src/*.py

# Check for coverage pragmas
assert-no-inline-directives --tools coverage src/

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
src/example.py:10:pylint:pylint: disable
src/example.py:15:mypy:type: ignore
src/example.py:20:coverage:pragma: no cover
config.yaml:5:yamllint:yamllint disable
```

**Count format** (`--count`):

```text
2
```

## Detected Directives

### coverage

- `pragma: no cover`
- `pragma: no branch`

### mypy (suppressions only)

- `type: ignore` (including bracketed forms like `type: ignore[attr-defined]`)
- `mypy: ignore-errors`

### pylint (suppressions only)

- `pylint: disable`
- `pylint: disable-next`
- `pylint: disable-line`
- `pylint: skip-file`

### yamllint (suppressions only)

- `yamllint disable-line`
- `yamllint disable`
- `yamllint disable-file`

## Matching Behavior

- Case-insensitive matching
- Tolerates extra whitespace (e.g., `pylint:  disable`, `type:   ignore`)
- Only detects directives in comments (after `#`), not in string literals
- Does **not** flag "enable" directives (e.g., `yamllint enable`)
- Files are scanned in alphabetical order for consistent output
- Glob patterns support hidden directories (e.g., `.github`)
- Tools only check files with matching extensions:
  - `coverage`: `.py`, `.toml`
  - `mypy`: `.py`, `.toml`
  - `pylint`: `.py`, `.toml`
  - `yamllint`: `.yaml`, `.yml`, `.toml`

## License

Apache 2.0 - see [LICENSE.txt](LICENSE.txt)
