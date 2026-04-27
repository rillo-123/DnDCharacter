# DnD Character Sheet - PowerShell Profile
# This file loads automatically when PowerShell starts
# Copy this file to your PowerShell profile directory or run it manually with: . .\profile.ps1

# Disable the stock venv prompt; this profile owns the prompt decorations.
$env:VIRTUAL_ENV_DISABLE_PROMPT = "1"
$Global:DnDCharacterProjectRoot = $PSScriptRoot

# Git branch and dirty marker helpers for prompt
# These functions work with or without the Flask server running

function global:Get-GitBranch {
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null | ForEach-Object { $_.Trim() }
        if ($LASTEXITCODE -eq 0 -and $branch) { return $branch }
        return $null
    } catch {
        return $null
    }
}

function global:Get-GitDirtyMarker {
    try {
        $status = git status --porcelain 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $status) { return '' }

        $markers = ""

        if ($status -match '^\?\?') {
            $markers += '+'
        }

        if ($status -match '^[ MADRC]') {
            $markers += '*'
        }

        return $markers
    } catch {
        return ''
    }
}

# Cache structure to reduce git calls (improves responsiveness)
if (-not (Test-Path Variable:GitPromptCache)) {
    Set-Variable -Name GitPromptCache -Value @{ 
        Path = $null
        Branch = $null
        Dirty = $null
        Timestamp = [datetime]::MinValue 
    } -Scope Global
}

function global:Update-GitPromptCache {
    param([string]$path)
    $cache = Get-Variable -Name GitPromptCache -Scope Global -ValueOnly
    
    # Cache is valid for 1 second to avoid excessive git calls
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

# Custom prompt that shows virtualenv, git branch, and dirty marker
function global:prompt {
    try {
        $path = (Get-Location).Path

        # Show virtualenv name if active
        $venvPart = ""
        if ($env:VIRTUAL_ENV) {
            $venvName = Split-Path -Leaf $env:VIRTUAL_ENV
            $venvPart = "($venvName) "
        }

        # Show git branch + dirty marker (if in a git repo)
        $branchName = ""
        $branchDirty = ""
        if (Get-Command git -ErrorAction SilentlyContinue) {
            $cache = Update-GitPromptCache -path $path
            if ($cache.Branch) {
                $branchName = $cache.Branch
                $branchDirty = $cache.Dirty
            }
        }

        # Use ANSI colors if terminal supports them
        $useColor = $false
        try { $useColor = $Host.UI.SupportsVirtualTerminal } catch { $useColor = $false }

        if ($useColor) {
            $esc = "`e"
            # Cyan for virtualenv, yellow for git branch, red for dirty marker.
            $c_venv = ""
            $c_git = ""
            if ($venvPart) { $c_venv = "${esc}[36m$venvPart${esc}[0m" }
            if ($branchName) {
                $c_git = "(${esc}[33m$branchName${esc}[0m"
                if ($branchDirty) {
                    $c_git += "${esc}[31m$branchDirty${esc}[0m"
                }
                $c_git += ") "
            }
            return "$c_venv$c_git${esc}[32m$path${esc}[0m`n> "
        } else {
            # Fallback without colors
            $fallbackGit = ""
            if ($branchName) { $fallbackGit = "($branchName$branchDirty) " }
            return "$venvPart$fallbackGit$path`n> "
        }
    } catch {
        return "PS> "
    }
}

function global:ensure_venv {
    $scriptPath = Join-Path $Global:DnDCharacterProjectRoot "ensure_venv.ps1"
    if (Test-Path -LiteralPath $scriptPath) {
        & $scriptPath @args
    } else {
        Write-Error "ensure_venv.ps1 not found at $scriptPath"
    }
}

if (-not $env:DNDC_PROFILE_QUIET) {
    Write-Host "[OK] Git prompt helper loaded. Your prompt will now show:" -ForegroundColor Green
    Write-Host "  - (venv-name) if inside a virtual environment" -ForegroundColor Gray
    Write-Host "  - (branch+*) if in a git repo (+ = untracked, * = modified)" -ForegroundColor Gray
    Write-Host "  - ensure_venv command for this project" -ForegroundColor Gray
}
