param(
    [string]$Filter,
    [switch]$All,
    [switch]$Radon,
    [switch]$Ruff,
    [switch]$Mypy,
    [switch]$Bandit,
    [switch]$Coverage
)

# Ensure we run from repo root
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

try {
    # Build path to the venv python executable
    $python = Join-Path -Path $root -ChildPath '.venv\Scripts\python.exe'
    if (-not (Test-Path $python)) { $python = 'python' }
    
    # If -All is specified, enable all tools
    if ($All) {
        $Radon = $true
        $Ruff = $true
        $Mypy = $true
        $Bandit = $true
        $Coverage = $true
    }
    
    $toolsEnabled = $Radon -or $Ruff -or $Mypy -or $Bandit -or $Coverage

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Running Main Test Suite" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    # Run main test suite (excluding equipment_events to avoid mock contamination)
    $mainPytestArgs = @(
        '-m', 'pytest', 'tests',
        '--ignore=tests\test_equipment_chooser.py',
        '--ignore=tests\test_equipment_events.py'
    )
    if ($Filter) { $mainPytestArgs += @('-k', $Filter) }

    & $python @mainPytestArgs
    $mainExitCode = $LASTEXITCODE

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Running Equipment Events Tests" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    # Run equipment events tests separately (requires browser module mocking)
    $eventsPytestArgs = @(
        '-m', 'pytest', 'tests\test_equipment_events.py', '-v'
    )

    & $python @eventsPytestArgs
    $eventsExitCode = $LASTEXITCODE

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Test Suite Summary" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    if ($mainExitCode -eq 0 -and $eventsExitCode -eq 0) {
        Write-Host "✓ All tests passed!" -ForegroundColor Green
        Write-Host "  - Main test suite: PASSED" -ForegroundColor Green
        Write-Host "  - Equipment events tests: PASSED" -ForegroundColor Green
    } else {
        Write-Host "✗ Some tests failed:" -ForegroundColor Red
        if ($mainExitCode -ne 0) {
            Write-Host "  - Main test suite: FAILED (exit code $mainExitCode)" -ForegroundColor Red
        } else {
            Write-Host "  - Main test suite: PASSED" -ForegroundColor Green
        }
        if ($eventsExitCode -ne 0) {
            Write-Host "  - Equipment events tests: FAILED (exit code $eventsExitCode)" -ForegroundColor Red
        } else {
            Write-Host "  - Equipment events tests: PASSED" -ForegroundColor Green
        }
    }
    
    # Run code quality tools if requested
    if ($toolsEnabled) {
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "Code Quality Tools" -ForegroundColor Cyan
        Write-Host "========================================`n" -ForegroundColor Cyan
        
        if ($Radon) {
            Write-Host "`n--- Radon Complexity Analysis ---" -ForegroundColor Yellow
            & $python -m radon cc static/assets/py -s -nb
            Write-Host ""
        }
        
        if ($Ruff) {
            Write-Host "`n--- Ruff Linter ---" -ForegroundColor Yellow
            & ruff check static/assets/py --statistics
            Write-Host ""
        }
        
        if ($Mypy) {
            Write-Host "`n--- Mypy Type Checker ---" -ForegroundColor Yellow
            & $python -m mypy static/assets/py --ignore-missing-imports --no-error-summary 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ No type errors found" -ForegroundColor Green
            }
            Write-Host ""
        }
        
        if ($Bandit) {
            Write-Host "`n--- Bandit Security Scanner ---" -ForegroundColor Yellow
            & $python -m bandit -r static/assets/py -q -f screen
            Write-Host ""
        }
        
        if ($Coverage) {
            Write-Host "`n--- Test Coverage Report ---" -ForegroundColor Yellow
            & $python -m coverage run -m pytest tests --ignore=tests\test_equipment_chooser.py --ignore=tests\test_equipment_events.py -q
            & $python -m coverage report --include="static/assets/py/*" --omit="*/__pycache__/*"
            Write-Host ""
        }
        
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "Code Quality Summary" -ForegroundColor Cyan
        Write-Host "========================================`n" -ForegroundColor Cyan
        
        if ($Radon) { Write-Host "✓ Complexity analysis complete" -ForegroundColor Green }
        if ($Ruff) { Write-Host "✓ Linting complete" -ForegroundColor Green }
        if ($Mypy) { Write-Host "✓ Type checking complete" -ForegroundColor Green }
        if ($Bandit) { Write-Host "✓ Security scan complete" -ForegroundColor Green }
        if ($Coverage) { Write-Host "✓ Coverage report complete" -ForegroundColor Green }
    }
    
    # Exit with appropriate code
    if ($mainExitCode -eq 0 -and $eventsExitCode -eq 0) {
        exit 0
    } else {
        exit 1
    }
}
finally {
    Pop-Location
}
