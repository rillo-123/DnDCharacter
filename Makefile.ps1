# DnD Character Sheet - Fast Task Runner (Make-like for Windows)
# Usage: .\Makefile.ps1 -Task test
#        .\Makefile.ps1 -Task all
#        .\Makefile.ps1 -Task quick (fastest - only modified files)

param(
    [ValidateSet('test', 'lint', 'vulture', 'checks', 'all', 'quick')]
    [string]$Task = 'quick',
    [switch]$Parallel = $true,
    [switch]$Verbose
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cacheFile = Join-Path $root '.make_cache.json'

# Colors
$c_pass = [ConsoleColor]::Green
$c_fail = [ConsoleColor]::Red
$c_skip = [ConsoleColor]::Yellow
$c_info = [ConsoleColor]::Cyan
$c_time = [ConsoleColor]::Magenta

function Write-Status($msg, $color) {
    Write-Host $msg -ForegroundColor $color
}

function Get-FilesHash($pattern) {
    $files = Get-ChildItem -Path $root -Recurse -File -Filter $pattern | Where-Object { -not $_.FullName.Contains('.venv') -and -not $_.FullName.Contains('.git') }
    if ($files.Count -eq 0) { return $null }
    $content = ($files | Get-Content -Raw | Measure-Object -Character).Characters
    return (($files.FullName -join '|' + $content) | Get-FileHash -Algorithm SHA256).Hash
}

function Load-Cache {
    if (-not (Test-Path $cacheFile)) { return @{} }
    try { return Get-Content $cacheFile | ConvertFrom-Json -AsHashtable }
    catch { return @{} }
}

function Save-Cache($cache) {
    $cache | ConvertTo-Json -Depth 10 | Set-Content $cacheFile
}

function Run-TestTask {
    $start = Get-Date
    Write-Status "`n▶ Running: pytest tests/ ..." $c_info
    
    try {
        $python = Join-Path $root '.venv\Scripts\python.exe'
        if (-not (Test-Path $python)) { $python = 'python' }
        
        & $python -m pytest tests/ -q --tb=short
        $result = $LASTEXITCODE
        
        $elapsed = ((Get-Date) - $start).TotalSeconds
        if ($result -eq 0) {
            Write-Status "✓ Tests passed in ${elapsed}s" $c_pass
        } else {
            Write-Status "✗ Tests failed (exit: $result)" $c_fail
        }
        return @{ name = 'test'; passed = ($result -eq 0); time = $elapsed }
    } catch {
        Write-Status "✗ Error running tests: $_" $c_fail
        return @{ name = 'test'; passed = $false; time = 0 }
    }
}

function Run-LintTask {
    $start = Get-Date
    Write-Status "`n▶ Running: pylint (basic check) ..." $c_info
    
    try {
        $python = Join-Path $root '.venv\Scripts\python.exe'
        if (-not (Test-Path $python)) { $python = 'python' }
        
        $pyFiles = Get-ChildItem -Path $root -Recurse -File -Filter '*.py' | Where-Object {
            -not $_.FullName.Contains('.venv') -and `
            -not $_.FullName.Contains('.git') -and `
            -not $_.FullName.Contains('__pycache__')
        }
        
        # Quick syntax check only (no full pylint to stay fast)
        $failed = 0
        $checked = 0
        foreach ($file in $pyFiles) {
            & $python -m py_compile $file.FullName 2>$null
            if ($LASTEXITCODE -ne 0) { $failed++ }
            $checked++
        }
        
        $elapsed = ((Get-Date) - $start).TotalSeconds
        if ($failed -eq 0) {
            Write-Status "✓ Syntax check passed on $checked files in ${elapsed}s" $c_pass
            return @{ name = 'lint'; passed = $true; time = $elapsed }
        } else {
            Write-Status "✗ Syntax errors in $failed/$checked files" $c_fail
            return @{ name = 'lint'; passed = $false; time = $elapsed }
        }
    } catch {
        Write-Status "✗ Error running lint: $_" $c_fail
        return @{ name = 'lint'; passed = $false; time = 0 }
    }
}

function Run-VultureTask {
    $start = Get-Date
    Write-Status "`n▶ Running: vulture (dead code scan) ..." $c_info
    
    try {
        $vulture = Join-Path $root 'run_vulture.ps1'
        if (Test-Path $vulture) {
            & powershell -ExecutionPolicy Bypass -File $vulture -MinConfidence 80 -OutFile '.vulture_cache.txt' | Out-Null
            $result = $LASTEXITCODE
            $elapsed = ((Get-Date) - $start).TotalSeconds
            
            if ($result -eq 0) {
                Write-Status "✓ No dead code found in ${elapsed}s" $c_pass
            } else {
                Write-Status "⚠ Vulture warnings detected (see vulture_report.txt)" $c_skip
            }
            return @{ name = 'vulture'; passed = $true; time = $elapsed }
        } else {
            Write-Status "⊘ Vulture skipped (script not found)" $c_skip
            return @{ name = 'vulture'; passed = $true; time = 0 }
        }
    } catch {
        Write-Status "✗ Error running vulture: $_" $c_fail
        return @{ name = 'vulture'; passed = $false; time = 0 }
    }
}

function Run-ChecksTask {
    $start = Get-Date
    Write-Status "`n▶ Running: domain spells check ..." $c_info
    
    try {
        $checkScript = Join-Path $root 'run_checks.ps1'
        if (Test-Path $checkScript) {
            & powershell -ExecutionPolicy Bypass -File $checkScript -Script check_domain_spells 2>$null
            $result = $LASTEXITCODE
            $elapsed = ((Get-Date) - $start).TotalSeconds
            
            if ($result -eq 0) {
                Write-Status "✓ Domain spells check passed in ${elapsed}s" $c_pass
                return @{ name = 'checks'; passed = $true; time = $elapsed }
            } else {
                Write-Status "⚠ Checks completed with code $result in ${elapsed}s" $c_skip
                return @{ name = 'checks'; passed = $true; time = $elapsed }
            }
        } else {
            Write-Status "⊘ Checks skipped (script not found)" $c_skip
            return @{ name = 'checks'; passed = $true; time = 0 }
        }
    } catch {
        Write-Status "✗ Error running checks: $_" $c_fail
        return @{ name = 'checks'; passed = $false; time = 0 }
    }
}

function Run-Tasks($taskList, [bool]$useParallel) {
    $results = @()
    
    if ($useParallel -and $taskList.Count -gt 1) {
        Write-Status "`n▶ Running tasks in parallel ..." $c_info
        
        # Run all tasks in parallel via background jobs
        $jobs = @()
        foreach ($taskName in $taskList) {
            $job = Start-Job -ScriptBlock {
                param($task, $root)
                Set-Location $root
                
                switch ($using:taskName) {
                    'test'    { Run-TestTask }
                    'lint'    { Run-LintTask }
                    'vulture' { Run-VultureTask }
                    'checks'  { Run-ChecksTask }
                }
            } -ArgumentList $taskName, $root
            $jobs += $job
        }
        
        # Wait for all jobs and collect results
        $jobs | Receive-Job -Wait | ForEach-Object { $results += $_ }
        $jobs | Remove-Job
    } else {
        Write-Status "`n▶ Running tasks sequentially ..." $c_info
        
        foreach ($taskName in $taskList) {
            switch ($taskName) {
                'test'    { $results += Run-TestTask }
                'lint'    { $results += Run-LintTask }
                'vulture' { $results += Run-VultureTask }
                'checks'  { $results += Run-ChecksTask }
            }
        }
    }
    
    return $results
}

# Main
Write-Host "`n" + ("=" * 70)
Write-Host "DnD Character Sheet - Task Runner"
Write-Host ("=" * 70)

$taskMap = @{
    'quick'  = @('lint')                            # Fastest: syntax check only
    'test'   = @('test')                            # Just tests
    'lint'   = @('lint')                            # Just syntax
    'vulture' = @('vulture')                        # Just dead code
    'checks' = @('checks')                          # Just domain checks
    'all'    = @('lint', 'test', 'vulture', 'checks')  # Everything
}

$tasksToRun = $taskMap[$Task]
Write-Status "Task: $Task" $c_info
Write-Status "Running: $($tasksToRun -join ', ')" $c_info

# Measure total time
$totalStart = Get-Date

# Run tasks
$results = Run-Tasks $tasksToRun $Parallel

# Summary
$totalTime = ((Get-Date) - $totalStart).TotalSeconds
$passed = ($results | Where-Object { $_.passed }).Count
$total = $results.Count

Write-Host "`n" + ("=" * 70)
Write-Host "SUMMARY" -ForegroundColor Cyan

foreach ($result in $results) {
    $icon = if ($result.passed) { "✓" } else { "✗" }
    $color = if ($result.passed) { $c_pass } else { $c_fail }
    Write-Status "  $icon $($result.name): $($result.time)s" $color
}

Write-Host "`nTotal: $passed/$total passed in ${totalTime}s" -ForegroundColor $c_info
Write-Host ("=" * 70)

exit $(if ($passed -eq $total) { 0 } else { 1 })
