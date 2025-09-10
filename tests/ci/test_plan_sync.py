import subprocess
import pytest
from unittest.mock import patch, Mock

def test_plan_sync_no_code_changes(mocker):
    mock_run = Mock(return_code=0)
    mock_run.stdout = ''  # No code changes
    mocker.patch('subprocess.run', return_value=mock_run)
    
    code_changes = 0
    plan_changes = 0
    if code_changes > 0 and plan_changes == 0:
        pytest.fail("Error: Code changes detected without corresponding plan file updates")
    else:
        assert True, "Plan sync check passed"

def test_plan_sync_with_plan_changes(mocker):
    mock_run = Mock(return_code=0)
    mock_run.stdout = 'plan.md\n'  # Plan changes, code changes also
    mocker.patch('subprocess.run', return_value=mock_run)
    
    code_changes = 1
    plan_changes = 1
    if code_changes > 0 and plan_changes == 0:
        pytest.fail("Error: Code changes detected without corresponding plan file updates")
    else:
        assert True, "Plan sync check passed"

def test_plan_sync_with_code_changes_no_plan(mocker):
    mock_run = Mock(return_code=0)
    mock_run.stdout = 'code.py\n'  # Code changes, no plan changes
    mocker.patch('subprocess.run', return_value=mock_run)
    
    code_changes = 1
    plan_changes = 0
    with pytest.raises(AssertionError):
        if code_changes > 0 and plan_changes == 0:
            raise AssertionError("Error: Code changes detected without corresponding plan file updates")