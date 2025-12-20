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

# Prompt helper: show git branch and dirty marker in the prompt
# Implements a lightweight cache to avoid calling git on every prompt when directory doesn't change.
# Shows branch name and '*' when working tree has unstaged/uncommitted changes.
function Get-GitBranch {
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null | ForEach-Object { $_.Trim() }
        if ($LASTEXITCODE -eq 0 -and $branch) { return $branch }
        return $null
    } catch {
        return $null
    }
}

function Get-GitDirtyMarker {
    try {
        $status = git status --porcelain 2>$null
        if ($LASTEXITCODE -eq 0 -and $status -and $status.Trim()) { return '*' }
        return ''
    } catch {
        return ''
    }
}

# Cache structure to reduce git calls
if (-not (Test-Path Variable:GitPromptCache)) {
    Set-Variable -Name GitPromptCache -Value @{ Path = $null; Branch = $null; Dirty = $null; Timestamp = [datetime]::MinValue } -Scope Global
}

function Update-GitPromptCache {
    param([string]$path)
    $cache = Get-Variable -Name GitPromptCache -Scope Global -ValueOnly
    if ($cache.Path -eq $path -and ((Get-Date) - $cache.Timestamp).TotalSeconds -lt 1) {
        return $cache
    }

    $branch = Get-GitBranch
    $dirty = Get-GitDirtyMarker
    $cache.Path = $path
    $cache.Branch = $branch
    $cache.Dirty = $dirty
    $cache.Timestamp = Get-Date
    Set-Variable -Name GitPromptCache -Value $cache -Scope Global
    return $cache
}

function global:prompt {
    try {
        $path = (Get-Location).Path

        # Virtualenv prefix
        $venvPart = ""
        if ($env:VIRTUAL_ENV) {
            $venvName = Split-Path -Leaf $env:VIRTUAL_ENV
            $venvPart = "($venvName) "
        }

        # Git branch + dirty marker (if git available and in a repo)
        $branchPartRaw = ""
        if (Get-Command git -ErrorAction SilentlyContinue) {
            $cache = Update-GitPromptCache -path $path
            if ($cache.Branch) {
                $marker = $cache.Dirty ? "*" : ""
                $branchPartRaw = "($($cache.Branch)$marker) "
            }
        }

        # Color support
        $useColor = $false
        try { $useColor = $Host.UI.SupportsVirtualTerminal } catch { $useColor = $false }

        if ($useColor) {
            $esc = "`e"
            $c_venv = ""
            $c_branch = ""
            if ($venvPart) { $c_venv = "${esc}[36m$venvPart${esc}[0m" }
            if ($branchPartRaw) { $c_branch = "${esc}[33m$branchPartRaw${esc}[0m" }
            return "$c_venv$c_branch$path> "
        } else {
            return "$venvPart$branchPartRaw$path> "
        }
    } catch {
        return "PS> "
    }
}

# Step 3: Install/check dependencies
if (Test-Path $reqFile) {
    Write-Host "`n📋 Checking dependencies from requirements.txt..."
    
    # Pip upgrade disabled to speed up setup (removed per user request)
    Write-Host "ℹ️  Skipping pip upgrade (disabled to speed up setup)."

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

            # Install all missing packages in a single pip call (fast) and stream output
            $pkgArg = $missing -join ' '
            try {
                Write-Host "📦 Running: python -m pip install $pkgArg"
                & python -m pip install $pkgArg
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "✗ Some packages failed to install (see pip output above)"
                    exit 1
                } else {
                    Write-Host "✓ Installed $($missing.Count) package(s)"
                }
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
