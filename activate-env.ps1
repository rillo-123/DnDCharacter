# DnD Character Sheet - Windows Setup Script
# Usage: .\activate-env.ps1 or .\activate-env.ps1 -StartServer
# Idempotent: Safe to run multiple times, kills existing processes

param(
    [switch]$StartServer
)

# Create logs directory
$logsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Setup logging
$logFile = Join-Path $logsDir "activate-env.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$timestamp] PowerShell setup started" | Add-Content $logFile

# Function to log messages
function Log-Message {
    param([string]$message)
    Write-Host $message
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $message" | Add-Content $logFile
}

Write-Host "=" * 70
Write-Host "DnD Character Sheet - Environment Setup (Windows)"
Write-Host "=" * 70

$venvPath = Join-Path $PSScriptRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts" "python.exe"
$activateScript = Join-Path $venvPath "Scripts" "Activate.ps1"
$backendFile = Join-Path $PSScriptRoot "backend.py"
$reqFile = Join-Path $PSScriptRoot "requirements.txt"

# Kill any existing Flask processes before starting
function Kill-FlaskProcesses {
    try {
        $procs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*backend.py*" }
        if ($procs) {
            Write-Host "🔪 Killing existing Flask processes..."
            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
            Write-Host "✓ Cleaned up existing Flask processes"
        }
    } catch {
        # No processes found, that's fine
    }
}

# Step 1: Create venv if it doesn't exist
if (-not (Test-Path $activateScript)) {
    Write-Host "`n📦 Creating virtual environment..."
    try {
        python -m venv $venvPath
        Write-Host "✓ Virtual environment created at $venvPath"
    } catch {
        Write-Host "✗ Failed to create venv: $_"
        exit 1
    }
} else {
    Write-Host "`n✓ Virtual environment already exists at $venvPath"
}

# Step 2: Activate venv (idempotent - safe if already activated)
Write-Host "`n🔌 Activating virtual environment..."
& $activateScript

# Step 3: Install/check dependencies
if (Test-Path $reqFile) {
    Write-Host "`n📋 Checking dependencies from requirements.txt..."
    
    # Skip pip version check - it's too slow (makes network calls to PyPI)
    # Pip in venv is fresh enough and doesn't need frequent upgrades
    
    # Check installed packages
    Write-Host "📥 Checking installed packages..."
    try {
        $installedOutput = & python -m pip list --format=json
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Could not list installed packages (exit code: $LASTEXITCODE)"
            exit 1
        }
        
        $installed = @{}
        try {
            $pkgList = $installedOutput | ConvertFrom-Json
            foreach ($pkg in $pkgList) {
                $installed[$pkg.name.ToLower()] = $pkg.version
            }
            Write-Host "   Found $($installed.Count) installed package(s)"
        } catch {
            Write-Host "✗ Could not parse installed packages: $_"
            exit 1
        }
    } catch {
        Write-Host "✗ Error checking installed packages: $_"
        exit 1
    }
    
    # Read requirements file
    if (-not (Test-Path $reqFile)) {
        Write-Host "⚠️  requirements.txt not found"
        exit 1
    }
    
    $requirements = @()
    Get-Content $reqFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            $requirements += $line
        }
    }
    
    if ($requirements.Count -eq 0) {
        Write-Host "⚠️  No requirements found in requirements.txt"
    } else {
        # Parse and install only missing packages
        $missing = @()
        foreach ($req in $requirements) {
            $pkgName = $req -replace '==.*', '' -replace '>=.*', '' -replace '<=.*', '' -replace '>.*', '' -replace '<.*', ''
            $pkgName = $pkgName.Trim().ToLower()
            
            if (-not $pkgName) {
                Write-Host "⚠️  Could not parse package name from: $req"
                continue
            }
            
            if (-not $installed.ContainsKey($pkgName)) {
                $missing += $req
            }
        }
        
        if ($missing.Count -gt 0) {
            $pkgNames = @()
            foreach ($m in $missing) {
                $pkgNames += ($m -replace '==.*', '' -replace '>=.*', '' -replace '<=.*', '' -replace '>.*', '' -replace '<.*', '').Trim()
            }
            Write-Host "📥 Installing $($missing.Count) missing package(s): $($pkgNames -join ', ')..."
            try {
                & python -m pip install $missing
                Write-Host "✓ Installed $($missing.Count) package(s)"
            } catch {
                Write-Host "✗ Failed to install packages: $_"
                exit 1
            }
        } else {
            Write-Host "✓ All required packages are already installed"
        }
        
        Write-Host "✓ All dependencies satisfied"
    }
} else {
    Write-Host "⚠️  requirements.txt not found"
}

# Step 4: Print status
Write-Host "`n" + ("=" * 70)
Write-Host "✓ ENVIRONMENT READY"
Write-Host ("=" * 70)

Write-Host "`n📝 The venv is now activated. You can:"
Write-Host "   - Run: python backend.py (to start the Flask server)"
Write-Host "   - Run: python -m pytest tests/ (to run tests)"

Write-Host "`n💡 To activate the venv in future sessions, run:"
Write-Host "   & `"$activateScript`""

Write-Host "`n" + ("=" * 70)

# Step 5: Optionally start server (kills existing processes first)
if ($StartServer) {
    Write-Host "`n🚀 Starting Flask server..."
    Kill-FlaskProcesses
    python $backendFile
}
