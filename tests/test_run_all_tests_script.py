"""
Test for run_all_tests.ps1 script parameter validation.

This test verifies that the run_all_tests.ps1 PowerShell script
has the correct parameters defined, including the -All parameter.
"""
import subprocess
import pytest


def test_powershell_script_has_all_parameter():
    """Test that run_all_tests.ps1 PowerShell script accepts -All parameter."""
    # Check if PowerShell is available
    try:
        subprocess.run(
            ['pwsh', '--version'],
            check=True,
            capture_output=True,
            timeout=5
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        pytest.skip("PowerShell not available")
    
    # Get the script parameters
    result = subprocess.run(
        ['pwsh', '-Command', '(Get-Command ./run_all_tests.ps1).Parameters.Keys'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Verify -All parameter exists
    params = result.stdout.lower()
    assert 'all' in params, "The -All parameter should be defined in run_all_tests.ps1"
    
    # Verify other expected parameters
    assert 'filter' in params, "The -Filter parameter should be defined"
    assert 'radon' in params, "The -Radon parameter should be defined"
    assert 'ruff' in params, "The -Ruff parameter should be defined"
    assert 'mypy' in params, "The -Mypy parameter should be defined"
    assert 'bandit' in params, "The -Bandit parameter should be defined"
    assert 'coverage' in params, "The -Coverage parameter should be defined"


def test_powershell_script_help_includes_all_parameter():
    """Test that run_all_tests.ps1 help documentation includes -All parameter."""
    try:
        subprocess.run(
            ['pwsh', '--version'],
            check=True,
            capture_output=True,
            timeout=5
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        pytest.skip("PowerShell not available")
    
    # Get the script help
    result = subprocess.run(
        ['pwsh', '-Command', 'Get-Help ./run_all_tests.ps1'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Verify help output contains -All parameter
    help_text = result.stdout.lower()
    assert '-all' in help_text, "The help text should mention the -All parameter"
