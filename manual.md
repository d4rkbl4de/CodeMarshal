# Manual Cleanup: Locked Pytest Temp Directories

Use this when these paths are stuck with `Access is denied`:

- `C:\Users\LENOVO\Documents\CodeMarshal\.pytest_tmp`
- `C:\Users\LENOVO\Documents\CodeMarshal\storage\pytest_tmp`
- `C:\Users\LENOVO\Documents\CodeMarshal\tmp_local\pytest-of-LENOVO`

## 1. Open Admin PowerShell

Open **Windows PowerShell** as **Administrator**.

## 2. Run Cleanup Commands

Copy/paste this exact block:

```powershell
$ErrorActionPreference = "Continue"
$paths = @(
  "C:\Users\LENOVO\Documents\CodeMarshal\.pytest_tmp",
  "C:\Users\LENOVO\Documents\CodeMarshal\storage\pytest_tmp",
  "C:\Users\LENOVO\Documents\CodeMarshal\tmp_local\pytest-of-LENOVO"
)

$empty = Join-Path $env:TEMP "empty_cleanup_dir"
New-Item -ItemType Directory -Force -Path $empty | Out-Null

foreach ($p in $paths) {
  if (-not (Test-Path -LiteralPath $p)) {
    Write-Host "Missing: $p"
    continue
  }

  cmd /c "takeown /f ""$p"" /r /d y"
  cmd /c "icacls ""$p"" /inheritance:e /grant:r %USERNAME%:(OI)(CI)F /t /c"
  cmd /c "attrib -r -s -h ""$p"" /s /d"
  cmd /c "robocopy ""$empty"" ""$p"" /MIR /R:0 /W:0 >nul"
  cmd /c "rd /s /q ""$p"""

  if (Test-Path -LiteralPath $p) {
    Write-Host "Still present: $p"
  } else {
    Write-Host "Removed: $p"
  }
}
```

## 3. Verify

Run this:

```powershell
Test-Path "C:\Users\LENOVO\Documents\CodeMarshal\.pytest_tmp"
Test-Path "C:\Users\LENOVO\Documents\CodeMarshal\storage\pytest_tmp"
Test-Path "C:\Users\LENOVO\Documents\CodeMarshal\tmp_local\pytest-of-LENOVO"
```

Expected output:

```text
False
False
False
```

## 4. Confirm In Repo

From repo root, run:

```powershell
git status --short
```

You should no longer see permission warnings for those directories.
