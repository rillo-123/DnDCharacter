# DnD Character Sheet - Windows Setup Script
# Usage: .\activate-env.ps1 or .\activate-env.ps1 -StartServer

param(
    [switch]$StartServer,
    [switch]$Upgrade,
    [switch]$NoCheck
)

$venvPath = Join-Path $PSScriptRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts"
$activateScript = Join-Path $activateScript "Activate.ps1"
$backendFile = Join-Path $PSScriptRoot "backend.py"
$reqFile = Join-Path $PSScriptRoot "requirements.txt"

Write-Host "DnD Character Sheet - Environment Setup"

# Step 1: Create venv if needed
if (-not (Test-Path $activateScript)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvPath
    Write-Host "Virtual environment created"
} else {
    Write-Host "Virtual environment already exists"
}

# Step 2: Activate venv
Write-Host "Activating virtual environment..."
& $activateScript

# Step 3: Install dependencies (only if missing)
if (-not $NoCheck -and (Test-Path $reqFile)) {
    Write-Host "Checking dependencies..."
    
    # Get list of installed packages (fast)
    $installed = & python -m pip freeze
    $installedSet = @{}
    foreach ($line in $installed) {
        $pkg = ($line -split '==|>=|<=|>|<')[0].Trim().ToLower()
        if ($pkg) { $installedSet[$pkg] = $true }
    }
    
    # Check which packages from requirements.txt are missing
    $missing = @()
    Get-Content $reqFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            $pkgName = ($line -split '==|>=|<=|>|<')[0].Trim().ToLower()
            if ($pkgName -and -not $installedSet.ContainsKey($pkgName)) {
                $missing += $line
            }
        }
    }
    
    if ($missing.Count -eq 0) {
        Write-Host "All dependencies already installed"
    } else {
        Write-Host "Installing $($missing.Count) missing package(s)..."
        if ($Upgrade) {
            python -m pip install --upgrade pip -q
        }
        $missing | ForEach-Object { python -m pip install $_ }
        Write-Host "Dependencies installed"
    }
} elseif ($NoCheck) {
    Write-Host "Skipping dependency check (-NoCheck)"
} else {
    Write-Host "requirements.txt not found"
}

Write-Host "Environment ready!"
Write-Host "   - Run: python backend.py (to start Flask server)"
Write-Host "   - Run: python -m pytest tests/ (to run tests)"
Write-Host "   - Run: .\activate-env.ps1 -StartServer (to start server)"
Write-Host "   - Run: .\activate-env.ps1 -StartServer -NoCheck (fast restart, skip dependency check)"

# Step 4: Start server if requested
if ($StartServer) {
    Write-Host "Starting Flask server..."
    python $backendFile
}
