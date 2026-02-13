# **CODEMARSHAL INTEGRATION EXAMPLES**

**Version:** 2.1.0  
**Last Updated:** February 12, 2026  

---

## **OVERVIEW**

This guide provides practical examples for integrating CodeMarshal into various development workflows and tools. Each example demonstrates constitutional compliance and truth-preserving investigation practices.

Note: Examples use `codemarshal` on PATH. If you rely on a virtual environment, use `./venv/bin/codemarshal` (macOS/Linux) or `.\venv\Scripts\codemarshal.exe` (Windows).

---

## **EDITOR INTEGRATION**

### **VS Code Extension**

#### **Basic Extension Structure**
```typescript
// src/extension.ts
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    console.log('CodeMarshal extension activated');
    
    // Register investigation command
    let disposable = vscode.commands.registerCommand(
        'codemarshal.investigate',
        () => investigateCurrentFile(context),
        {
            title: 'Investigate Current File',
            category: 'CodeMarshal'
        }
    );
    
    context.subscriptions.push(disposable);
}

function investigateCurrentFile(context: vscode.ExtensionContext) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }
    
    const filePath = editor.document.fileName;
    const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    
    if (!workspacePath) {
        vscode.window.showErrorMessage('No workspace opened');
        return;
    }
    
    // Run CodeMarshal investigation
    const isWindows = process.platform === 'win32';
    const venvCandidate = isWindows
        ? path.join(workspacePath, 'venv', 'Scripts', 'codemarshal.exe')
        : path.join(workspacePath, 'venv', 'bin', 'codemarshal');
    const codemarshalPath = fs.existsSync(venvCandidate) ? venvCandidate : 'codemarshal';

    exec(`"${codemarshalPath}" investigate "${filePath}" --scope=file --intent=initial_scan`, 
         { cwd: workspacePath },
         (error, stdout, stderr) => {
             if (error) {
                 vscode.window.showErrorMessage(`Investigation failed: ${error.message}`);
             } else {
                 // Show results in new tab
                 const outputChannel = vscode.window.createOutputChannel('CodeMarshal');
                 outputChannel.appendLine(stdout);
                 outputChannel.show();
             }
         }
    );
}
```

#### **Package.json Configuration**
```json
{
    "name": "codemarshal-vscode",
    "displayName": "CodeMarshal Investigation",
    "description": "Truth-preserving code investigation in VS Code",
    "version": "2.0.0",
    "engines": {
        "vscode": "^1.75.0"
    },
    "categories": ["Other"],
    "activationEvents": [
        "onCommand:codemarshal.investigate"
    ],
    "main": "./out/extension.js",
    "contributes": {
        "commands": [
            {
                "command": "codemarshal.investigate",
                "title": "Investigate Current File",
                "category": "CodeMarshal"
            },
            {
                "command": "codemarshal.investigate.directory",
                "title": "Investigate Directory",
                "category": "CodeMarshal"
            },
            {
                "command": "codemarshal.export.session",
                "title": "Export Session",
                "category": "CodeMarshal"
            }
        ],
        "keybindings": [
            {
                "command": "codemarshal.investigate",
                "key": "ctrl+shift+i",
                "mac": "cmd+shift+i"
            }
        ]
    }
}
```

### **Neovim Plugin**

#### **Lua Plugin Structure**
```lua
-- ~/.config/nvim/lua/codemarshal.lua
local M = {}

local function resolve_codemarshal()
    local venv = vim.fn.getcwd() .. "/venv"
    local is_windows = vim.fn.has("win32") == 1 or vim.fn.has("win64") == 1
    local candidate = is_windows
        and (venv .. "/Scripts/codemarshal.exe")
        or (venv .. "/bin/codemarshal")

    if vim.fn.executable(candidate) == 1 then
        return candidate
    end

    return "codemarshal"
end

function M.investigate_current_file()
    local file_path = vim.fn.expand('%:p')
    local workspace_path = vim.fn.getcwd()
    
    -- Run CodeMarshal investigation
    local cmd = string.format(
        'cd %s && "%s" investigate "%s" --scope=file --intent=initial_scan',
        workspace_path,
        resolve_codemarshal(),
        file_path
    )
    
    -- Open results in new buffer
    vim.fn.jobstart(cmd, {
        on_stdout = function(_, data)
            vim.schedule(function()
                local buf = vim.api.nvim_create_buf(false, 'results')
                vim.api.nvim_buf_set_lines(buf, 0, -1, false, vim.split(data, '\n'))
                vim.api.nvim_buf_set_option(buf, 'filetype', 'json')
                vim.api.nvim_win_set_buf(0, buf)
            end, 0)
        end,
        on_stderr = function(_, data)
            vim.schedule(function()
                vim.notify('CodeMarshal Error: ' .. data, vim.log.levels.ERROR)
            end, 0)
        end
    })
end

function M.investigate_directory()
    local dir_path = vim.fn.input('Directory to investigate: ', '', 'file')
    if dir_path == '' then return end
    
    local cmd = string.format(
        'cd %s && "%s" investigate "%s" --scope=project --intent=initial_scan --confirm-large',
        vim.fn.getcwd(),
        resolve_codemarshal(),
        dir_path
    )
    
    vim.fn.jobstart(cmd, {
        on_stdout = function(_, data)
            vim.schedule(function()
                vim.notify('Investigation started: ' .. data, vim.log.levels.INFO)
            end, 0)
        end
    })
end

function M.export_session()
    local session_id = vim.fn.input('Session ID to export: ', '', 'file')
    if session_id == '' then return end
    
    local cmd = string.format(
        'cd %s && "%s" export %s --format=json --output=session_%s.json',
        vim.fn.getcwd(),
        resolve_codemarshal(),
        session_id,
        session_id
    )
    
    vim.fn.jobstart(cmd)
end

-- Setup commands
vim.api.nvim_create_user_command('CodeMarshalInvestigate', M.investigate_current_file, {})
vim.api.nvim_create_user_command('CodeMarshalInvestigateDir', M.investigate_directory, {})
vim.api.nvim_create_user_command('CodeMarshalExport', M.export_session, {})

return M
```

#### **Init.lua Configuration**
```lua
-- ~/.config/nvim/init.lua
require('codemarshal')

-- Key bindings
vim.keymap.set('n', '<leader>ci', '<cmd>CodeMarshalInvestigate<CR>', 
    { noremap = true, silent = true, desc = 'Investigate with CodeMarshal' })
vim.keymap.set('n', '<leader>ce', '<cmd>CodeMarshalExport<CR>', 
    { noremap = true, silent = true, desc = 'Export CodeMarshal session' })
```

---

## **CI/CD INTEGRATION**

### **GitHub Actions**

#### **Constitutional Validation Workflow**
```yaml
# .github/workflows/constitutional-validation.yml
name: Constitutional Compliance Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  constitutional-check:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Ensure CodeMarshal is available
      run: |
        # Assumes CodeMarshal is pre-installed or available from a local artifact
        # e.g., via a custom action that sets up the environment, or a local build step.
        # For network-free CI, avoid 'pip install' from PyPI.
        # Example: verify executable exists
        command -v codemarshal >/dev/null 2>&1 || { echo >&2 "CodeMarshal not found. Ensure it's pre-installed or available."; exit 1; }
        
    - name: Run constitutional validation
      run: |
        python -m integrity.validation.complete_constitutional

        
    - name: Run network prohibition tests
      run: |
        python -m integrity.prohibitions.network_prohibition
        
    - name: Upload validation results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: constitutional-validation-results
        path: |
          constitutional_audit_report.json
          network_prohibition_results.json
```

#### **Investigation Workflow**
```yaml
# .github/workflows/investigate-changes.yml
name: Investigate Changes

on:
  pull_request:
    branches: [ main ]

jobs:
  investigate:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
        
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Ensure CodeMarshal is available
      run: |
        # Assumes CodeMarshal is pre-installed or available from a local artifact
        command -v codemarshal >/dev/null 2>&1 || { echo >&2 "CodeMarshal not found. Ensure it's pre-installed or available."; exit 1; }
        
    - name: Investigate changes
      run: |
        # Get changed files
        git diff --name-only HEAD~1 HEAD > changed_files.txt
        
        # Run a full investigation once (required for queries)
        codemarshal investigate . --scope=project --intent=initial_scan --confirm-large

        # Query against the most recent session, focusing on each changed file
        for file in $(cat changed_files.txt); do
          echo "Investigating: $file"
          codemarshal query latest --question="What does this file do?" --question-type=purpose --focus="$file"
        done
        
    - name: Generate investigation report
      run: |
        codemarshal export latest --format=markdown --output=pr_investigation.md
        
    - name: Upload investigation report
      uses: actions/upload-artifact@v3
      with:
        name: pr-investigation
        path: pr_investigation.md
```

#### **Architectural Review Workflow**
```yaml
# .github/workflows/architectural-review.yml
name: Architectural Review

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Ensure CodeMarshal is available
      run: |
        # Assumes CodeMarshal is pre-installed or available from a local artifact
        command -v codemarshal >/dev/null 2>&1 || { echo >&2 "CodeMarshal not found. Ensure it's pre-installed or available."; exit 1; }
        
    - name: Full architectural investigation
      run: |
        codemarshal investigate . --scope=project --intent=architecture_review --confirm-large
        
    - name: Check architectural boundaries
      run: |
        codemarshal query latest --question="What are the architectural layers?" --question-type=structure
        codemarshal query latest --question="Find boundary violations" --question-type=anomalies --focus=.
        
    - name: Generate architectural report
      run: |
        codemarshal export latest --format=html --output=architectural_review.html --include-patterns
        
    - name: Upload architectural review
      uses: actions/upload-artifact@v3
      with:
        name: architectural-review
        path: architectural_review.html
```

### **GitLab CI**

#### **GitLab CI Configuration**
```yaml
# .gitlab-ci.yml
stages:
  - validate
  - investigate
  - report

variables:
  CODEMARSHAL_VERSION: "2.0.0"

constitutional_validation:
  stage: validate
  script:
    - # Assumes CodeMarshal is pre-installed or available from a local artifact.
    - # For network-free CI, avoid 'pip install' from PyPI.
    - # Example: verify executable exists
    - command -v codemarshal >/dev/null 2>&1 || { echo >&2 "CodeMarshal not found. Ensure it's pre-installed or available."; exit 1; }
    - python -m integrity.validation.complete_constitutional
    - python -m integrity.prohibitions.network_prohibition
  artifacts:
    reports:
      junit: constitutional-results.xml
    paths:
      - constitutional_audit_report.json
      - network_prohibition_results.json
  only:
    - merge_requests
    - main

investigation:
  stage: investigate
  script:
    - # Assumes CodeMarshal is pre-installed or available from a local artifact.
    - command -v codemarshal >/dev/null 2>&1 || { echo >&2 "CodeMarshal not found. Ensure it's pre-installed or available."; exit 1; }
    - codemarshal investigate . --scope=project --intent=initial_scan --confirm-large
    - codemarshal query latest --question="What are the main components?" --question-type=structure
  artifacts:
    paths:
      - investigation_results/
  only:
    - main

reporting:
  stage: report
  script:
    - # Assumes CodeMarshal is pre-installed or available from a local artifact.
    - command -v codemarshal >/dev/null 2>&1 || { echo >&2 "CodeMarshal not found. Ensure it's pre-installed or available."; exit 1; }
    - codemarshal export latest --format=markdown --output=weekly_report.md --include-patterns
  artifacts:
    paths:
      - weekly_report.md
  only:
    - main
```

---

## **BUILD SYSTEM INTEGRATION**

### **Makefile Integration**

#### **Development Makefile**
```makefile
# Makefile for CodeMarshal-integrated development
.PHONY: investigate validate export clean install

CODEMARSHAL ?= codemarshal

# Investigation targets
investigate:
	$(CODEMARSHAL) investigate . --scope=project --intent=initial_scan --confirm-large

investigate-deep:
	$(CODEMARSHAL) investigate . --scope=project --intent=dependency_analysis --confirm-large

investigate-arch:
	$(CODEMARSHAL) investigate . --scope=project --intent=architecture_review --confirm-large

# Validation targets
validate:
	@echo "Running constitutional validation..."
	python -m integrity.validation.complete_constitutional
	python -m integrity.prohibitions.network_prohibition

validate-quick:
	@echo "Quick validation check..."
	python -m integrity --validate-only

# Export targets
export-json:
	$(CODEMARSHAL) export latest --format=json --output=investigation.json

export-md:
	$(CODEMARSHAL) export latest --format=markdown --output=investigation.md

export-html:
	$(CODEMARSHAL) export latest --format=html --output=investigation.html

export-all:
	$(CODEMARSHAL) export latest --format=json --output=investigation.json
	$(CODEMARSHAL) export latest --format=markdown --output=investigation.md
	$(CODEMARSHAL) export latest --format=html --output=investigation.html

# Development targets
install:
	pip install -e .

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf investigation_results/

# CI target
ci: validate investigate-deep export-all
	@echo "Complete CI pipeline executed"

# Help target
help:
	@echo "CodeMarshal Integration Makefile"
	@echo ""
	@echo "Investigation:"
	@echo "  investigate      - Basic project investigation"
	@echo "  investigate-deep - Deep project analysis"
	@echo "  investigate-arch  - Architectural investigation"
	@echo ""
	@echo "Validation:"
	@echo "  validate        - Full constitutional validation"
	@echo "  validate-quick   - Quick validation check"
	@echo ""
	@echo "Export:"
	@echo "  export-json     - Export as JSON"
	@echo "  export-md       - Export as Markdown"
	@echo "  export-html     - Export as HTML"
	@echo "  export-all      - Export in all formats"
```

### **Docker Integration**

#### **Dockerfile for CodeMarshal**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy CodeMarshal source
COPY . /app

# Install CodeMarshal
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 codemarshal
USER codemarshal

# Default command
CMD ["codemarshal", "--help"]

# Investigation command
ENTRYPOINT ["codemarshal", "investigate", ".", "--scope=project", "--intent=initial_scan", "--confirm-large"]
```

#### **Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  codemarshal:
    build: .
    volumes:
      - ./code:/workspace:rw
      - ./results:/output:rw
    working_dir: /workspace
    command: ["codemarshal", "investigate", "/workspace", "--scope=project", "--intent=initial_scan", "--confirm-large"]
    environment:
      - CODEMARSHAL_OUTPUT_DIR=/output
      - CODEMARSHAL_CONFIG_PATH=/workspace/.codemarshal.yaml

  investigation-service:
    build: .
    volumes:
      - ./code:/workspace:rw
      - ./results:/output:rw
    working_dir: /workspace
    command: ["codemarshal", "investigate", "/workspace", "--scope=project", "--intent=architecture_review", "--confirm-large"]
    depends_on:
      - codemarshal

  batch-investigation:
    build: .
    volumes:
      - ./code:/workspace:ro
      - ./results:/output:rw
    working_dir: /workspace
    command: >
      bash -c "
        codemarshal investigate /workspace --scope=project --intent=initial_scan --confirm-large &&
        codemarshal export latest --format=json --output=/output/batch_results.json
      "
```

---

## **API INTEGRATION**

### **Python API Wrapper**

#### **Investigation API Class**
```python
# codemarshal_api.py
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional

class CodeMarshalAPI:
    """Python API wrapper for CodeMarshal operations."""
    
    def __init__(self, codemarshal_path: Optional[Path] = None):
        self.codemarshal_path = codemarshal_path or self._find_codemarshal()
    
    def _find_codemarshal(self) -> Path:
        """Find CodeMarshal installation."""
        # Try common locations
        candidates = [
            Path("./venv/bin/codemarshal"),
            Path("./venv/Scripts/codemarshal.exe"),
            Path.home() / ".local" / "bin" / "codemarshal",
            Path("/usr/local/bin/codemarshal")
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        raise FileNotFoundError("CodeMarshal not found")
    
    def investigate(self, path: str, **kwargs) -> Dict[str, Any]:
        """Run investigation on given path."""
        cmd = [str(self.codemarshal_path), "investigate", path]
        
        # Add optional arguments
        if kwargs.get('scope'):
            cmd.extend(["--scope", kwargs['scope']])
        if kwargs.get('intent'):
            cmd.extend(["--intent", kwargs['intent']])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Investigation failed: {result.stderr}")
        
        return {"stdout": result.stdout, "stderr": result.stderr}
    
    def query(
        self,
        investigation_id: str,
        question: str,
        question_type: str = "structure",
        focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ask question about an investigation."""
        cmd = [
            str(self.codemarshal_path),
            "query",
            investigation_id,
            "--question",
            question,
            "--question-type",
            question_type,
        ]
        
        if focus:
            cmd.extend(["--focus", focus])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Query failed: {result.stderr}")
        
        return {"answer": result.stdout}
    
    def export(
        self,
        session_id: str,
        format: str = "json",
        output: Optional[str] = None,
        confirm_overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Export investigation session."""
        if not output:
            raise ValueError("output is required for export")
        
        cmd = [
            str(self.codemarshal_path),
            "export",
            session_id,
            f"--format={format}",
            "--output",
            output,
        ]
        
        if confirm_overwrite:
            cmd.append("--confirm-overwrite")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Export failed: {result.stderr}")
        
        return {"exported": result.stdout}

# Usage example
api = CodeMarshalAPI()

# Investigate current directory
result = api.investigate(".", scope="project", intent="initial_scan")
print("Investigation results:", result["stdout"])

# Ask specific question
answer = api.query("latest", "What are the main modules?", question_type="structure")
print("Query answer:", answer["answer"])

# Export session
export_result = api.export("latest", format="markdown", output="report.md", confirm_overwrite=True)
print("Exported:", export_result["exported"])
```

### **FastAPI Integration**

#### **REST API Server**
```python
# codemarshal_server.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from codemarshal_api import CodeMarshalAPI

app = FastAPI(title="CodeMarshal API")
api = CodeMarshalAPI()

class InvestigationRequest(BaseModel):
    path: str
    scope: str = "project"
    intent: str = "initial_scan"

class QueryRequest(BaseModel):
    investigation_id: str
    question: str
    question_type: str = "structure"
    focus: Optional[str] = None

@app.post("/investigate")
async def investigate(request: InvestigationRequest):
    try:
        result = api.investigate(
            request.path,
            scope=request.scope,
            intent=request.intent
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query(request: QueryRequest):
    try:
        result = api.query(
            request.investigation_id,
            request.question,
            question_type=request.question_type,
            focus=request.focus,
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "codemarshal-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## **SCRIPTING INTEGRATION**

### **Pre-commit Hook**

#### **Constitutional Validation Hook**
```bash
#!/bin/sh
# .git/hooks/pre-commit
echo "Running CodeMarshal constitutional validation..."

# Run constitutional checks
python -m integrity.validation.complete_constitutional
if [ $? -ne 0 ]; then
    echo "❌ Constitutional validation failed"
    echo "Please fix violations before committing"
    exit 1
fi

# Run network prohibition checks
python -m integrity.prohibitions.network_prohibition
if [ $? -ne 0 ]; then
    echo "❌ Network prohibition validation failed"
    echo "Please remove network dependencies before committing"
    exit 1
fi

echo "✅ All validations passed"
exit 0
```

#### **Installation**
```bash
# Make executable and install as pre-commit hook
chmod +x .git/hooks/pre-commit
cp pre-commit-hook .git/hooks/pre-commit

# Or use pre-commit framework
pip install pre-commit
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: local
    hooks:
      - id: codemarshal-constitutional
        name: CodeMarshal Constitutional Validation
        entry: python -m integrity.validation.complete_constitutional
        language: system
        pass_filenames: false
        always_run: true
      
      - id: codemarshal-network-prohibition
        name: CodeMarshal Network Prohibition
        entry: python -m integrity.prohibitions.network_prohibition
        language: system
        pass_filenames: false
        always_run: true
EOF

pre-commit install
```

### **Automated Investigation Script**

#### **Daily Investigation Script**
```python
#!/usr/bin/env python3
# daily_investigation.py
import os
import json
from datetime import datetime
from pathlib import Path
from codemarshal_api import CodeMarshalAPI

def daily_investigation():
    """Run daily investigation and generate report."""
    
    # Configuration
    workspace_path = Path("/path/to/your/project")
    output_dir = Path("/path/to/reports")
    api = CodeMarshalAPI()
    
    # Run investigation
    print(f"Starting daily investigation of {workspace_path}")
    result = api.investigate(
        str(workspace_path),
        scope="project",
        intent="initial_scan"
    )
    
    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d")
    report_file = output_dir / f"daily_investigation_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "workspace": str(workspace_path),
            "investigation": result["stdout"],
            "metadata": {
                "type": "daily_investigation",
                "version": "2.0.0"
            }
        }, f, indent=2)
    
    print(f"Daily investigation report saved to {report_file}")

if __name__ == "__main__":
    daily_investigation()
```

#### **Cron Job Setup**
```bash
# Add to crontab with: crontab -e
# Run daily at 2 AM
0 2 * * * /usr/bin/python3 /path/to/daily_investigation.py >> /var/log/codemarshal_daily.log 2>&1

# Run weekly architectural review
0 0 * * 0 /usr/bin/python3 /path/to/architectural_review.py >> /var/log/codemarshal_weekly.log 2>&1
```

---

## **TESTING INTEGRATION**

### **Pytest Integration**

#### **Constitutional Test Plugin**
```python
# tests/conftest.py
import pytest
from pathlib import Path
import subprocess
import sys

@pytest.fixture(scope="session", autouse=True)
def constitutional_compliance():
    """Run constitutional validation before each test session."""
    
    print("Running constitutional compliance check...")
    
    result = subprocess.run([
        sys.executable, "-m", "integrity.validation.complete_constitutional"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        pytest.fail(f"Constitutional violations detected: {result.stderr}")
    
    print("✅ Constitutional compliance verified")

@pytest.fixture
def investigation_workspace(tmp_path):
    """Create a temporary workspace for testing investigations."""
    
    # Create test project structure
    test_project = tmp_path / "test_project"
    test_project.mkdir()
    
    (test_project / "main.py").write_text("""
def main():
    return "Hello, World!"

if __name__ == "__main__":
    main()
""")
    
    (test_project / "utils.py").write_text("""
def helper_function():
    return "This is a utility function"
""")
    
    return test_project
```

#### **Test Example**
```python
# tests/test_investigation_integration.py
import pytest
from codemarshal_api import CodeMarshalAPI

def test_full_investigation_workflow(investigation_workspace):
    """Test complete investigation workflow."""
    
    api = CodeMarshalAPI()
    
    # Step 1: Investigate
    result = api.investigate(
        str(investigation_workspace),
        scope="project",
        intent="initial_scan",
    )
    assert "Investigation started" in result["stdout"]
    
    # Step 2: Query
    answer = api.query(
        "latest",
        "What are the main files?",
        question_type="structure",
    )
    assert "main.py" in answer["answer"]
    
    # Step 3: Export
    export_result = api.export("latest", format="json", output="report.json", confirm_overwrite=True)
    assert export_result["exported"]
    
    print("✅ Full investigation workflow test passed")
```

---

## **MONITORING INTEGRATION**

### **Prometheus Metrics**

#### **Metrics Exporter**
```python
# codemarshal_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from codemarshal_api import CodeMarshalAPI

# Metrics
investigation_counter = Counter('codemarshal_investigations_total', 'Total investigations')
investigation_duration = Histogram('codemarshal_investigation_duration_seconds', 'Investigation duration')
constitutional_violations = Counter('codemarshal_constitutional_violations_total', 'Constitutional violations')

app = CodeMarshalAPI()

def investigate_with_metrics(path: str):
    """Investigation with Prometheus metrics."""
    start_time = time.time()
    
    try:
        result = app.investigate(path)
        investigation_counter.inc()
        
        duration = time.time() - start_time
        investigation_duration.observe(duration)
        
        return result
        
    except Exception as e:
        constitutional_violations.inc()
        raise

# Start metrics server
start_http_server(8001)
```

### **Grafana Dashboard**

#### **Dashboard Configuration**
```json
{
  "dashboard": {
    "title": "CodeMarshal Monitoring",
    "panels": [
      {
        "title": "Investigation Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(codemarshal_investigations_total[5m])",
            "legendFormat": "{{value}} investigations/min"
          }
        ]
      },
      {
        "title": "Investigation Duration",
        "type": "histogram",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(codemarshal_investigation_duration_seconds_bucket[5m])))",
            "legendFormat": "95th percentile: {{value}}s"
          }
        ]
      },
      {
        "title": "Constitutional Violations",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(codemarshal_constitutional_violations_total[5m])",
            "legendFormat": "{{value}} violations/5min"
          }
        ]
      }
    ]
  }
}
```

---

## **TROUBLESHOOTING INTEGRATION**

### **Common Integration Issues**

#### **Path Resolution**
```python
# Find CodeMarshal installation
import shutil
import os

def find_codemarshal():
    """Find CodeMarshal in common locations."""
    candidates = [
        "./venv/bin/codemarshal",
        "./venv/Scripts/codemarshal.exe",
        shutil.which("codemarshal"),
        os.path.expanduser("~/.local/bin/codemarshal"),
        "/usr/local/bin/codemarshal"
    ]
    
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    
    raise FileNotFoundError("CodeMarshal not found. Install with: pip install codemarshal")

# Usage
codemarshal_path = find_codemarshal()
print(f"Using CodeMarshal at: {codemarshal_path}")
```

#### **Permission Issues**
```bash
# Fix permission issues
chmod +x ./venv/bin/codemarshal
sudo chown $USER:$USER ./venv/bin/codemarshal

# Windows (PowerShell)
# Unblock-File .\venv\Scripts\codemarshal.exe

# For Docker
RUN useradd -m -u 1000 codemarshal
USER codemarshal
```

#### **Environment Conflicts**
```python
# Handle virtual environment conflicts
import sys
import os

def ensure_codemarshal_env():
    """Ensure CodeMarshal runs in correct environment."""
    
    if 'VIRTUAL_ENV' not in os.environ:
        print("Warning: Not in virtual environment")
        print("Activating CodeMarshal virtual environment...")
        
        venv_path = os.path.join(os.getcwd(), 'venv')
        if os.path.exists(venv_path):
            activate_dir = "Scripts" if os.name == "nt" else "bin"
            activate_script = os.path.join(venv_path, activate_dir, 'activate')
            exec(open(activate_script).read())
    
    # Check CodeMarshal installation
    try:
        import codemarshal
        print("✅ CodeMarshal environment ready")
    except ImportError:
        print("❌ CodeMarshal not installed or not in PATH")
        sys.exit(1)

ensure_codemarshal_env()
```

---

## **BEST PRACTICES**

### **Integration Guidelines**

#### **1. Constitutional Compliance**
- Always validate before integration
- Include constitutional tests in CI/CD
- Monitor for violations in production
- Handle violations gracefully

#### **2. Error Handling**
- Never suppress constitutional violations
- Log all integration errors
- Provide clear error messages
- Include evidence in error reports

#### **3. Performance Considerations**
- Cache investigation results when appropriate
- Use streaming for large exports
- Monitor resource usage
- Implement timeouts for long operations

#### **4. Security Considerations**
- Validate all input paths
- Sanitize user queries
- Run in least-privilege mode when possible
- Audit integration access logs

---

---

## Related Documentation

- **[ROADMAP.md](../ROADMAP.md)** - Execution status and remaining work
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and changes
- **[docs/USER_GUIDE.md](USER_GUIDE.md)** - Command reference and tutorials
- **[docs/API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Programmatic API
- **[docs/architecture.md](architecture.md)** - System architecture
- **[docs/FEATURES.md](FEATURES.md)** - Feature matrix
- **[docs/index.md](index.md)** - Documentation navigation

---

**Integration Examples Version: 2.1.0**  
**Last Updated: February 12, 2026**  
**Next Update: Based on community feedback and use cases**
