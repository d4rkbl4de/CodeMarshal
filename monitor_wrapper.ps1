#!/usr/bin/env pwsh
# PowerShell wrapper for monitoring CodeMarshal execution

param(
    [Parameter(Mandatory=$true)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$startTime = Get-Date
$process = Start-Process -FilePath $Command -ArgumentList $Arguments -PassThru -NoNewWindow

Write-Host "Starting monitoring for process $($process.Id)..." -ForegroundColor Green

while (-not $process.HasExited) {
    $elapsed = (Get-Date) - $startTime
    
    # Get memory usage (working set in MB)
    try {
        $memUsage = [math]::Round($process.WorkingSet64 / 1MB, 2)
    } catch {
        $memUsage = "N/A"
    }
    
    # Count processed files (observations)
    $obsDir = "$env:USERPROFILE\.codemarshal\sessions\latest\observations"
    if (Test-Path $obsDir) {
        $filesProcessed = (Get-ChildItem -Path $obsDir -Filter "*.json" -Recurse).Count
    } else {
        $filesProcessed = 0
    }
    
    Write-Host -NoNewline "`rTime: $($elapsed.ToString('hh\:mm\:ss')) | Memory: ${memUsage}MB | Files: $filesProcessed"
    Start-Sleep -Seconds 2
}

$process.WaitForExit()
$exitCode = $process.ExitCode

Write-Host "`nDone. Exit code: $exitCode" -ForegroundColor Green

# Generate final report
$totalTime = (Get-Date) - $startTime
Write-Host "Total execution time: $($totalTime.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan

if (Test-Path $obsDir) {
    $finalFiles = (Get-ChildItem -Path $obsDir -Filter "*.json" -Recurse).Count
    Write-Host "Total files processed: $finalFiles" -ForegroundColor Cyan
    
    if ($totalTime.TotalSeconds -gt 0) {
        $filesPerSec = [math]::Round($finalFiles / $totalTime.TotalSeconds, 2)
        Write-Host "Processing speed: $filesPerSec files/second" -ForegroundColor Cyan
    }
}

exit $exitCode
