$ErrorActionPreference = "Continue"
$paths = @(
  "C:\Users\LENOVO\Documents\CodeMarshal\.pytest_tmp",
  "C:\Users\LENOVO\Documents\CodeMarshal\storage\pytest_tmp",
  "C:\Users\LENOVO\Documents\CodeMarshal\tmp_local\pytest-of-LENOVO"
)

$empty = Join-Path $env:TEMP "empty_cleanup_dir"
New-Item -ItemType Directory -Force -Path $empty | Out-Null

foreach ($p in $paths) {
  Write-Host "== $p"
  if (-not (Test-Path -LiteralPath $p)) {
    Write-Host "missing"
    continue
  }

  cmd /c "takeown /f \"$p\" /a"
  cmd /c "icacls \"$p\" /setowner %USERNAME% /c"
  cmd /c "icacls \"$p\" /inheritance:e /grant:r %USERNAME%:(OI)(CI)F /c"
  cmd /c "attrib -r -s -h \"$p\" /s /d"

  # Mirror an empty directory first to clear inaccessible descendants.
  cmd /c "robocopy \"$empty\" \"$p\" /MIR /R:0 /W:0 >nul"
  cmd /c "rd /s /q \"$p\""

  if (Test-Path -LiteralPath $p) {
    Write-Host "still-present"
  } else {
    Write-Host "removed"
  }
}
