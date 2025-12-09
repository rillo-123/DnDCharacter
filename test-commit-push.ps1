#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run tests, then commit with message, then push if all tests pass.

.DESCRIPTION
    This script ensures code quality by running the full test suite before committing.
    Workflow:
    1. Run all tests (pytest)
    2. If tests fail, stop and display failures
    3. If tests pass, commit with provided message
    4. Push to remote repository

.PARAMETER Message
    The commit message to use. Required.

.EXAMPLE
    .\test-commit-push.ps1 "Fix: Description of changes"
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Message
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "TEST-COMMIT-PUSH Pipeline" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Run tests
Write-Host "Step 1: Running tests..." -ForegroundColor Yellow
Write-Host "Command: python -m pytest tests/ -v" -ForegroundColor Gray
Write-Host ""

python -m pytest tests/ -v

$testExitCode = $LASTEXITCODE

if ($testExitCode -ne 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "TESTS FAILED - Aborting commit and push" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    exit $testExitCode
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "All tests passed!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Step 2: Commit
Write-Host "Step 2: Committing changes..." -ForegroundColor Yellow
Write-Host "Commit message: $Message" -ForegroundColor Gray
Write-Host ""

git add -A
git commit -m $Message

$commitExitCode = $LASTEXITCODE

if ($commitExitCode -ne 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "COMMIT FAILED" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    exit $commitExitCode
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "Commit successful!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Step 3: Push
Write-Host "Step 3: Pushing to remote..." -ForegroundColor Yellow
Write-Host ""

git push

$pushExitCode = $LASTEXITCODE

if ($pushExitCode -ne 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "PUSH FAILED" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    exit $pushExitCode
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "Push successful!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Workflow complete: Tests → Commit → Push" -ForegroundColor Green
Write-Host ""

exit 0
