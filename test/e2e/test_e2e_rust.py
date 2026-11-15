"""End-to-end tests for Rust attribute support."""

import subprocess

import pytest
from test_rust_sample import SAMPLE_RS_FINDINGS


@pytest.mark.e2e
class TestCliRust:
    """E2E tests for Rust directive detection."""

    def test_sample_returncode(
        self, sample_rust_result: subprocess.CompletedProcess[str]
    ) -> None:
        """Exit code 1 for the sample file."""
        assert sample_rust_result.returncode == 1

    def test_sample_findings(
        self, sample_rust_result: subprocess.CompletedProcess[str]
    ) -> None:
        """The installed script reports each directive of the sample."""
        lines = sample_rust_result.stdout.splitlines()
        assert [line.split("sample.rs:", 1)[1] for line in lines] == (
            SAMPLE_RS_FINDINGS
        )
