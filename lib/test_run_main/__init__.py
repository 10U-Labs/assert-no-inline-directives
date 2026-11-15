"""Run the CLI entry point in-process."""

from unittest.mock import patch

from assert_no_inline_directives.cli import main


def run_main_with_args(args: list[str]) -> int:
    """Run main() with given args and return exit code."""
    with patch("sys.argv", ["assert-no-inline-directives", *args]):
        try:
            main()
            return 0
        except SystemExit as e:
            return int(e.code) if e.code is not None else 0
