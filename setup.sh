#!/bin/bash
# setup.sh - Linux/Mac setup script

echo "Setting up CodeMarshal development environment..."

# Check Python version
python_version=$(python3 --version 2>&1)
if [[ ! $python_version =~ Python\ 3\.(1[1-9]|2[0-9]) ]]; then
    echo "Warning: CodeMarshal requires Python 3.11+ (You have: $python_version)"
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -e .
pip install psutil

# Verify
echo -e "\nVerification:"
python -c "import sys; sys.path.insert(0,'.'); import core; print('✅ Core imports working')"
python -c "from bridge.entry.tui import TUI_AVAILABLE; print(f'✅ TUI_AVAILABLE = {TUI_AVAILABLE}')"

echo -e "\nSetup complete! Activate with: source venv/bin/activate"
echo "Test with: codemarshal --help"