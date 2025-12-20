param(
    [string]$Filter
)

# Ensure we run from repo root
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

try {
    # Build path to the venv python executable (use -ChildPath to avoid Join-Path positional-arg errors)
    $python = Join-Path -Path $root -ChildPath '.venv\Scripts\python.exe'
    if (-not (Test-Path $python)) { $python = 'python' }

    $pytestArgs = @('-m', 'pytest', 'tests')
    if ($Filter) { $pytestArgs += @('-k', $Filter) }

    # Use splatting to pass the args array correctly
    & $python @pytestArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
