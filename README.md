# assert-no-inline-lint-disables

A CLI tool to assert that files contain no inline lint-disable directives for
yamllint, pylint, and mypy.

## Installation

```bash
pip install assert-no-inline-lint-disables
```

## Usage

```bash
assert-no-inline-lint-disables --linters LINTERS [OPTIONS] FILE [FILE ...]
```

### Required Arguments

- `--linters LINTERS` - Comma-separated list of linters: `yamllint,pylint,mypy`
- `FILE` - One or more file paths to scan

### Optional Arguments

- `--exclude PATTERNS` - Comma-separated glob patterns to exclude files
- `--quiet` - Suppress output, exit code only
- `--count` - Print finding count only
- `--json` - Output findings as JSON
- `--fail-fast` - Exit on first finding
- `--warn-only` - Always exit 0, report only
- `--allow PATTERNS` - Comma-separated patterns to allow

### Examples

```bash
# Check for pylint and mypy suppressions
assert-no-inline-lint-disables --linters pylint,mypy src/*.py

# Check all linters, exclude vendor files
assert-no-inline-lint-disables --linters yamllint,pylint,mypy \
    --exclude "*vendor*" src/*.py config/*.yaml

# Allow specific type: ignore patterns
assert-no-inline-lint-disables --linters mypy \
    --allow "type: ignore[import]" src/*.py

# CI mode: quiet, just exit code
assert-no-inline-lint-disables --linters pylint,mypy --quiet src/*.py

# Get JSON output for tooling integration
assert-no-inline-lint-disables --linters pylint --json src/*.py

# Non-blocking check (always exit 0)
assert-no-inline-lint-disables --linters mypy --warn-only src/*.py
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

**JSON format** (`--json`):

```json
[
  {"path": "src/example.py", "line": 10, "linter": "pylint"},
  {"path": "src/example.py", "line": 15, "linter": "mypy"}
]
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
