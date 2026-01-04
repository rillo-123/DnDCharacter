param(
    [Parameter(Mandatory=$true)][ValidateSet('check_slugs','check_sources','check_spellcasting','check_domain_flag','check_domain_spells')]
    [string]$Script,
    [string]$File,
    [string]$ExportsDir = "exports",
    [string]$Domain = "life",
    [int]$Level = 9
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

try {
    $shim = Join-Path -Path $root -ChildPath 'tools' | Join-Path -ChildPath 'run_check.ps1'
    if (-not (Test-Path $shim)) { Write-Error "Shim not found: $shim"; exit 1 }

    $argsList = @('-Script', $Script, '-ExportsDir', $ExportsDir)
    if ($File)   { $argsList += @('-File', $File) }
    if ($Script -eq 'check_domain_spells') {
        if ($Domain) { $argsList += @('-Domain', $Domain) }
        if ($Level)  { $argsList += @('-Level', $Level) }
    }

    & $shim @argsList
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
