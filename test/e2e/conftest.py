"""End-to-end test configuration."""

import subprocess


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess."""
    return subprocess.run(
        ["assert-no-inline-directives", *args],
        capture_output=True,
        text=True,
        check=False,
    )
