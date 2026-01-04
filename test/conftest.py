"""Root pytest configuration and shared test utilities."""

from unittest.mock import patch

import pytest

from assert_no_inline_directives.cli import main


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


def run_main_with_args(args: list[str]) -> int:
    """Run main() with given args and return exit code.

    Shared utility for CLI tests across unit, integration, and e2e test suites.
    """
    with patch("sys.argv", ["assert-no-inline-directives", *args]):
        try:
            main()
            return 0
        except SystemExit as e:
            return int(e.code) if e.code is not None else 0
