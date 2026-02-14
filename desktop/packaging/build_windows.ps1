param(
    [string]$PythonExe = "python",
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\\..")
Set-Location $repoRoot

Write-Host "Using Python executable: $PythonExe"

if (-not $SkipDependencyInstall) {
    & $PythonExe -m pip install --upgrade pip
}

& $PythonExe -c "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('PyInstaller') else 1)"
if ($LASTEXITCODE -ne 0) {
    if ($SkipDependencyInstall) {
        throw "PyInstaller is not installed. Install it first or rerun without -SkipDependencyInstall."
    }

    Write-Host "PyInstaller not found, installing..."
    & $PythonExe -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller. Check network/pip configuration and retry."
    }
}

$specPath = Join-Path $repoRoot "desktop\\packaging\\codemarshal_gui.spec"
& $PythonExe -m PyInstaller --clean --noconfirm $specPath

$outputPath = Join-Path $repoRoot "dist\\CodeMarshal.exe"
if (-not (Test-Path $outputPath)) {
    throw "Expected build artifact not found: $outputPath"
}

Write-Host "Build complete: $outputPath"
