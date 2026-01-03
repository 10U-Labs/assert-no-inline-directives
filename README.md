# assert-no-inline-lint-disables

A CLI tool to assert that files contain no inline lint-disable directives for
yamllint, pylint, and mypy.

## Installation

```bash
pip install assert-no-inline-lint-disables
```

## Usage

```bash
assert-no-inline-lint-disables --linters LINTERS [OPTIONS] PATH [PATH ...]
```

### Required Arguments

- `--linters LINTERS` - Comma-separated list of linters: `yamllint,pylint,mypy`
- `PATH` - One or more file or directory paths to scan (directories are scanned
  recursively)

### Optional Arguments

- `--exclude PATTERNS` - Comma-separated glob patterns to exclude files
- `--quiet` - Suppress output, exit code only
- `--count` - Print finding count only
- `-v, --verbose` - Show linters, files scanned, findings, and summary
- `--fail-fast` - Exit on first finding
- `--warn-only` - Always exit 0, report only
- `--allow PATTERNS` - Comma-separated patterns to allow

### Examples

```bash
# Check for pylint and mypy suppressions in files
assert-no-inline-lint-disables --linters pylint,mypy src/*.py

# Scan a directory recursively
assert-no-inline-lint-disables --linters pylint,mypy src/

# Check all linters, exclude vendor files
assert-no-inline-lint-disables --linters yamllint,pylint,mypy \
    --exclude "*vendor*" src/ config/

# Allow specific type: ignore patterns
assert-no-inline-lint-disables --linters mypy \
    --allow "type: ignore[import]" src/*.py

# CI mode: quiet, just exit code
assert-no-inline-lint-disables --linters pylint,mypy --quiet src/

# Verbose mode: show progress
assert-no-inline-lint-disables --linters pylint,mypy --verbose src/

# Non-blocking check (always exit 0)
assert-no-inline-lint-disables --linters mypy --warn-only src/
```

### Exit Codes

- `0` - No inline lint-disable directives found
- `1` - One or more inline lint-disable directives found
- `2` - Usage or runtime error (e.g., file not found, invalid linter)

### Output Formats

**Default format** (one finding per line):

```text
src/example.py:10:pylint:pylint: disable
src/example.py:15:mypy:type: ignore
config.yaml:5:yamllint:yamllint disable
```

**Count format** (`--count`):

```text
2
```

## Detected Directives

### yamllint (suppressions only)

- `yamllint disable-line`
- `yamllint disable`
- `yamllint disable-file`

### pylint (suppressions only)

- `pylint: disable`
- `pylint: disable-next`
- `pylint: disable-line`
- `pylint: skip-file`

### mypy (suppressions only)

- `type: ignore` (including bracketed forms like `type: ignore[attr-defined]`)
- `mypy: ignore-errors`

## Matching Behavior

- Case-insensitive matching
- Tolerates extra whitespace (e.g., `pylint:  disable`, `type:   ignore`)
- Finds matches anywhere in the line
- Does **not** flag "enable" directives (e.g., `yamllint enable`)

## License

Apache 2.0 - see [LICENSE.txt](LICENSE.txt)
