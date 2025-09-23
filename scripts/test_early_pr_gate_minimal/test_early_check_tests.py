"""
Unit tests for check_tests function in scripts/pr_gate_minimal.py

Covers:
- Happy paths: pytest runs and returns success/failure as expected.
- Edge cases: subprocess errors, unexpected return codes, etc.

Assumes tests are located as sibling to scripts/pr_gate_minimal.py.
"""

import pytest
from unittest import mock

from scripts.pr_gate_minimal import check_tests

@pytest.mark.usefixtures("patch_subprocess_run")
class TestCheckTests:
    # --- Happy Path Tests ---

    @pytest.mark.happy_path
    def test_pytest_success(self, patch_subprocess_run):
        """Test that check_tests returns True when pytest succeeds (returncode 0)."""
        patch_subprocess_run.return_value.returncode = 0
        assert check_tests() is True

    @pytest.mark.happy_path
    def test_pytest_failure(self, patch_subprocess_run):
        """Test that check_tests returns False when pytest fails (returncode nonzero)."""
        patch_subprocess_run.return_value.returncode = 1
        assert check_tests() is False

    # --- Edge Case Tests ---

    @pytest.mark.edge_case
    def test_pytest_returncode_negative(self, patch_subprocess_run):
        """Test that check_tests returns False when pytest returns a negative code."""
        patch_subprocess_run.return_value.returncode = -1
        assert check_tests() is False

    @pytest.mark.edge_case
    def test_pytest_returncode_large(self, patch_subprocess_run):
        """Test that check_tests returns False when pytest returns a large nonzero code."""
        patch_subprocess_run.return_value.returncode = 255
        assert check_tests() is False

    @pytest.mark.edge_case
    def test_subprocess_run_raises_exception(self, patch_subprocess_run):
        """Test that check_tests raises if subprocess.run throws an exception."""
        patch_subprocess_run.side_effect = RuntimeError("subprocess error")
        with pytest.raises(RuntimeError):
            check_tests()

    @pytest.mark.edge_case
    def test_subprocess_run_called_with_expected_args(self, patch_subprocess_run):
        """Test that check_tests calls subprocess.run with correct arguments."""
        patch_subprocess_run.return_value.returncode = 0
        check_tests()
        patch_subprocess_run.assert_called_once_with(
            ["pytest", "-q"], capture_output=True
        )

# --- Fixtures ---

@pytest.fixture
def patch_subprocess_run():
    """Fixture to patch subprocess.run for all tests in this class."""
    with mock.patch("scripts.pr_gate_minimal.subprocess.run") as m:
        # Default: returncode 0 unless overridden
        m.return_value.returncode = 0
        yield m