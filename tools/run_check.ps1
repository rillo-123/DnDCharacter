param(
    [Parameter(Mandatory=$true)][ValidateSet('check_slugs','check_sources','check_spellcasting','check_domain_flag','check_domain_spells')]
    [string]$Script,
    [string]$File,
    [string]$ExportsDir = "exports",
    [string]$Domain = "life",
    [int]$Level = 9
)

$root = Split-Path -Parent $PSScriptRoot
$oldDir = Get-Location
Set-Location $root
$python = Join-Path $root '.venv' 'Scripts' 'python.exe'
if (-not (Test-Path $python)) {
    $python = 'python'
}

$scriptPath = Join-Path $PSScriptRoot 'checks' "$Script.py"
if (-not (Test-Path $scriptPath)) {
    Write-Error "Script not found: $scriptPath"
    exit 1
}

$argsList = @($scriptPath, '--exports-dir', $ExportsDir)
if ($File)   { $argsList += @('--file', $File) }
if ($Script -eq 'check_domain_spells') {
    if ($Domain) { $argsList += @('--domain', $Domain) }
    if ($Level)  { $argsList += @('--level', $Level) }
}

& $python @argsList
$code = $LASTEXITCODE
Set-Location $oldDir
if ($code -ne 0) { exit $code }
