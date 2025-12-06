param(
    [string]$Filter
)

# Ensure we run from repo root
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

try {
    $python = Join-Path $root '.venv' 'Scripts' 'python.exe'
    if (-not (Test-Path $python)) { $python = 'python' }

    $pytestArgs = @('-m', 'pytest', 'tests')
    if ($Filter) { $pytestArgs += @('-k', $Filter) }

    & $python $pytestArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
