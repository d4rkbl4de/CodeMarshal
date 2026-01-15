# setup.ps1 - Windows setup script
Write-Host "Setting up CodeMarshal development environment..." -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version
if ($pythonVersion -notmatch "Python 3\.(1[1-9]|2\d)") {
    Write-Host "Warning: CodeMarshal requires Python 3.11+ (You have: $pythonVersion)" -ForegroundColor Yellow
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -e .
pip install psutil windows-curses

# Verify
Write-Host "`nVerification:" -ForegroundColor Green
python -c "import sys; sys.path.insert(0,'.'); import core; print('✅ Core imports working')"
python -c "from bridge.entry.tui import TUI_AVAILABLE; print(f'✅ TUI_AVAILABLE = {TUI_AVAILABLE}')"

Write-Host "`nSetup complete! Activate with: .\venv\Scripts\Activate" -ForegroundColor Green
Write-Host "Test with: codemarshal --help" -ForegroundColor Green