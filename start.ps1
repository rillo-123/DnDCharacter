param(
    [string]$HostName = "localhost",
    [int]$Port = 8080,
    [switch]$NoUpdate,
    [switch]$Reload,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$ensureScript = Join-Path $projectRoot "ensure_venv.ps1"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$backendScript = Join-Path $projectRoot "backend_fastapi.py"

function Stop-ExistingBackend {
    $processes = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object {
            $_.CommandLine -and (
                $_.CommandLine -like "*backend_fastapi.py*" -or
                $_.CommandLine -like "*uvicorn*backend_fastapi*"
            )
        }

    foreach ($process in $processes) {
        Write-Host "Stopping existing backend process PID $($process.ProcessId)"
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath $ensureScript)) {
    throw "ensure_venv.ps1 not found: $ensureScript"
}

if ($NoUpdate) {
    & $ensureScript -NoUpdate
} else {
    & $ensureScript
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment Python not found: $venvPython"
}

if (-not (Test-Path -LiteralPath $backendScript)) {
    throw "FastAPI backend not found: $backendScript"
}

Stop-ExistingBackend

$serverArgs = @($backendScript, "--host", $HostName, "--port", "$Port")
if ($Reload) {
    $serverArgs += "--reload"
}
if ($Debug) {
    $serverArgs += "--debug"
}

Write-Host "Starting FastAPI backend at http://${HostName}:$Port"
& $venvPython @serverArgs
