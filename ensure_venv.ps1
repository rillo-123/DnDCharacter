# Idempotent venv activation and requirements update.
#
# Usage:
#   .\ensure_venv.ps1              # create/activate venv, update requirements if due
#   .\ensure_venv.ps1 -NoUpdate    # create/activate venv, skip requirements
#   .\ensure_venv.ps1 -ForceUpdate # update requirements even if recently checked

[CmdletBinding()]
param(
    [Alias("SkipInstall")]
    [switch]$NoUpdate,
    [switch]$ForceUpdate,
    [switch]$Recreate,
    [switch]$NoCd,
    [int]$CheckWindowMinutes = 1440,
    [int]$PipTimeoutSeconds = 60,
    [int]$PipRetries = 2,
    [string]$Python
)

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$venvDir = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
$requirementsFile = Join-Path $projectRoot "requirements.txt"
$profileScript = Join-Path $projectRoot "profile.ps1"
$pipCheckFile = Join-Path $venvDir ".last_pip_check"

function Get-PythonCommand {
    if ($Python) {
        $resolved = Get-Command $Python -ErrorAction Stop
        return @{
            Exe = $resolved.Source
            Args = @()
        }
    }

    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @{
            Exe = $pyLauncher.Source
            Args = @("-3")
        }
    }

    $pythonCommand = Get-Command "python" -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @{
            Exe = $pythonCommand.Source
            Args = @()
        }
    }

    $python3Command = Get-Command "python3" -ErrorAction SilentlyContinue
    if ($python3Command) {
        return @{
            Exe = $python3Command.Source
            Args = @()
        }
    }

    throw "Could not find Python. Install Python or pass -Python with the executable path."
}

function Import-ProjectProfile {
    if (-not (Test-Path -LiteralPath $profileScript)) {
        return
    }

    $previousQuiet = $env:DNDC_PROFILE_QUIET
    $env:DNDC_PROFILE_QUIET = "1"
    try {
        . $profileScript
    } finally {
        if ($null -eq $previousQuiet) {
            Remove-Item Env:DNDC_PROFILE_QUIET -ErrorAction SilentlyContinue
        } else {
            $env:DNDC_PROFILE_QUIET = $previousQuiet
        }
    }
}

function Reset-GitPromptCache {
    if (Get-Variable -Name GitPromptCache -Scope Global -ErrorAction SilentlyContinue) {
        Set-Variable -Name GitPromptCache -Value @{
            Path = $null
            Branch = $null
            Dirty = $null
            Timestamp = [datetime]::MinValue
        } -Scope Global -Force
    }
}

function Test-PathSame {
    param(
        [string]$Left,
        [string]$Right
    )

    try {
        $leftFull = [System.IO.Path]::GetFullPath($Left).TrimEnd('\')
        $rightFull = [System.IO.Path]::GetFullPath($Right).TrimEnd('\')
        return $leftFull.Equals($rightFull, [System.StringComparison]::OrdinalIgnoreCase)
    } catch {
        return $false
    }
}

if (-not $NoCd) {
    Set-Location -LiteralPath $projectRoot
}

if ($Recreate -and (Test-Path -LiteralPath $venvDir)) {
    Write-Host "Removing existing virtual environment: $venvDir" -ForegroundColor Cyan
    Remove-Item -LiteralPath $venvDir -Recurse -Force
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $pythonCommand = Get-PythonCommand
    Write-Host "Creating virtual environment at $venvDir..." -ForegroundColor Cyan
    & $pythonCommand.Exe @($pythonCommand.Args + @("-m", "venv", $venvDir))
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment."
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
}

if (-not (Test-Path -LiteralPath $activateScript)) {
    throw "Activation script not found: $activateScript"
}

Import-ProjectProfile

$env:VIRTUAL_ENV_DISABLE_PROMPT = "1"

if ($env:VIRTUAL_ENV -and -not (Test-PathSame -Left $env:VIRTUAL_ENV -Right $venvDir)) {
    Write-Host "Switching from active venv '$env:VIRTUAL_ENV' to '$venvDir'" -ForegroundColor Cyan
    if (Get-Command deactivate -ErrorAction SilentlyContinue) {
        deactivate
    }
}

if (-not $env:VIRTUAL_ENV) {
    & $activateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} elseif (Test-PathSame -Left $env:VIRTUAL_ENV -Right $venvDir) {
    Write-Host "[OK] Virtual environment already active" -ForegroundColor Gray
}

if (Get-Command _OLD_VIRTUAL_PROMPT -ErrorAction SilentlyContinue) {
    Remove-Item Function:prompt -ErrorAction SilentlyContinue
    Remove-Item Function:_OLD_VIRTUAL_PROMPT -ErrorAction SilentlyContinue
}

Import-ProjectProfile
Reset-GitPromptCache

if ($NoUpdate) {
    Write-Host "[OK] Skipping package update" -ForegroundColor Gray
    return
}

if (-not (Test-Path -LiteralPath $requirementsFile)) {
    throw "requirements.txt not found: $requirementsFile"
}

$skipPackageCheck = $false
if (-not $ForceUpdate -and (Test-Path -LiteralPath $pipCheckFile)) {
    $lastCheck = Get-Item -LiteralPath $pipCheckFile
    if (((Get-Date) - $lastCheck.LastWriteTime).TotalMinutes -lt $CheckWindowMinutes) {
        $skipPackageCheck = $true
    }
}

if ($skipPackageCheck) {
    $windowText = if ($CheckWindowMinutes -eq 1440) { "24 hours" } else { "$CheckWindowMinutes minutes" }
    Write-Host "[OK] Skipping package check (last check was < $windowText ago)" -ForegroundColor Gray
    return
}

Write-Host "Installing/updating packages from requirements.txt..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade --disable-pip-version-check --no-input --timeout $PipTimeoutSeconds --retries $PipRetries -r $requirementsFile
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install/update requirements."
}

New-Item -Path $pipCheckFile -ItemType File -Force | Out-Null
$windowText = if ($CheckWindowMinutes -eq 1440) { "24 hours" } else { "$CheckWindowMinutes minutes" }
Write-Host "[OK] Package check complete (next check in $windowText)" -ForegroundColor Green
