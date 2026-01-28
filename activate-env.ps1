# DnD Character Sheet - Windows Setup Script
# Usage: .\activate-env.ps1 or .\activate-env.ps1 -StartServer

param(
    [switch]$StartServer,
    [switch]$Upgrade,
    [switch]$NoCheck,
    [switch]$NoCheckExceptSyntax
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
if (-not $NoCheck -and -not $NoCheckExceptSyntax -and (Test-Path $reqFile)) {
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
} elseif ($NoCheck -or $NoCheckExceptSyntax) {
    Write-Host "Skipping dependency check (-NoCheck or -NoCheckExceptSyntax)"
} else {
    Write-Host "requirements.txt not found"
}

Write-Host "Environment ready!"
Write-Host "   - Run: python backend.py (to start Flask server)"
Write-Host "   - Run: python -m pytest tests/ (to run tests)"
Write-Host "   - Run: .\activate-env.ps1 -StartServer (to start server)"
Write-Host "   - Run: .\activate-env.ps1 -StartServer -NoCheck (fast restart, skip all checks)"
Write-Host "   - Run: .\activate-env.ps1 -StartServer -NoCheckExceptSyntax (fast restart, check syntax only)"

# Step 4: Check Python syntax if starting server (or with -NoCheckExceptSyntax)
if (-not $NoCheck -and ($StartServer -or $NoCheckExceptSyntax)) {
    Write-Host ""
    Write-Host "Checking Python syntax on all *.py files..."
    
    # Find all Python files (excluding __pycache__ and .venv)
    $pyFiles = @(Get-ChildItem -Path $PSScriptRoot -Filter "*.py" -Recurse -ErrorAction SilentlyContinue | 
                 Where-Object { $_.FullName -notmatch "(__pycache__|\.venv)" })
    
    if ($pyFiles.Count -eq 0) {
        Write-Host "No Python files found"
        exit 1
    }
    
    Write-Host "Found $($pyFiles.Count) Python file(s) to check"
    
    $syntaxErrors = @()
    foreach ($file in $pyFiles) {
        # Use forward slashes to avoid PowerShell escape sequence issues
        $filePath = $file.FullName.Replace('\', '/')
        $result = & python -c "
import ast
try:
    with open(r'$($file.FullName)', 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print('OK')
except SyntaxError as e:
    print(f'SYNTAX_ERROR: {e}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1
        
        if ($result -contains "OK" -or $result -match "^OK`$") {
            Write-Host "  [OK] $($file.Name)"
        } else {
            Write-Host "  [ERROR] $($file.Name)" -ForegroundColor Red
            $syntaxErrors += @{file = $file.FullName; error = ($result -join "; ")}
        }
    }
    
    if ($syntaxErrors.Count -gt 0) {
        Write-Host ""
        Write-Host "[ERROR] SYNTAX ERRORS found:" -ForegroundColor Red
        foreach ($err in $syntaxErrors) {
            Write-Host "  File: $($err.file)" -ForegroundColor Red
            Write-Host "  Error: $($err.error)" -ForegroundColor Red
        }
        Write-Host "Server NOT started due to syntax errors" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "[OK] All Python files passed syntax check"
    }
}

# Step 5: Start server if requested
if ($StartServer) {
    Write-Host ""
    Write-Host "Starting Flask server..."
    python $backendFile
}
