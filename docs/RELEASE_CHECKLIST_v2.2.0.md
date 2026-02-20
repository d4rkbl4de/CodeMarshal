# CodeMarshal Release Checklist: v2.2.0 (GA)

**Date:** February 20, 2026  
**Release Line:** `2.2.0`  
**Validation Environment:** Windows, project virtualenv (`.venv`)

---

## Gate Summary

- Version alignment moved from `2.2.0-rc1` to `2.2.0` across package metadata, docs, and plugin manifests.
- GA validation commands and artifacts are captured below.
- JetBrains plugin packaging is treated as a required GA gate.
- Docker validation is currently blocked in this environment because Docker CLI is unavailable.

---

## Required Commands

### 1) Python package install and dependency integrity

```powershell
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m pip check
```

Status: `PASS`  
Notes:
- `codemarshal==2.2.0` installed in editable mode.
- `pip check` returned `No broken requirements found.`

### 2) Full regression suite

```powershell
.venv\Scripts\python -m pytest -q
```

Status: `PASS`  
Result: `274 passed, 1 warning`  
Notes:
- Validation run executed via `.venv\Scripts\python -m pytest -q`.

### 3) CLI version/info smoke

```powershell
.venv\Scripts\python -m bridge.entry.cli --version
.venv\Scripts\python -m bridge.entry.cli --info
```

Status: `PASS`  
Notes:
- `--version` reports `CodeMarshal v2.2.0`.
- `--info` reports `Version: v2.2.0`.
- Current runtime still emits existing constitutional warning from `core.shutdown` import boundaries (non-blocking for this checklist).

### 4) Python distribution package build (CLI distribution)

```powershell
.venv\Scripts\python -m build
```

Status: `PASS`  
Artifacts:
- `dist/codemarshal-2.2.0.tar.gz`
- `dist/codemarshal-2.2.0-py3-none-any.whl`

### 5) VS Code extension build and package

```powershell
cmd /c npm run build
cmd /c npm run package
```

Working directory: `vscode-extension`  
Status: `PASS`  
Artifact:
- `vscode-extension/codemarshal.vsix`
Notes:
- Packaging warnings present for missing `repository` field and missing extension-local `LICENSE`/`.vscodeignore`.

### 6) JetBrains plugin build

```powershell
$env:JAVA_HOME=(Resolve-Path '.tools\jdk-17.0.18+8').Path
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"
.tools\gradle-8.10.2\bin\gradle.bat -p jetbrains-plugin buildPlugin --no-daemon --console=plain
```

Status: `PASS`  
Artifact:
- `jetbrains-plugin/build/distributions/jetbrains-plugin-2.2.0.zip`
Notes:
- Build completed successfully with warnings from searchable options generation and action-group registration (`NavigationPopupMenu`) during IDE indexing simulation.

### 7) Windows GUI packaging

```powershell
.\desktop\packaging\build_windows.ps1 -PythonExe .venv\Scripts\python.exe
```

Status: `PASS`  
Artifact:
- `dist/CodeMarshal.exe`
Notes:
- PyInstaller was installed automatically by the packaging script.

### 8) Docker build validation

```powershell
docker build -f Dockerfile -t codemarshal:latest .
docker build -f Dockerfile.dev -t codemarshal:dev .
```

Status: `BLOCKED`  
Notes:
- `docker` command is not available in this environment (`CommandNotFoundException`).

---

## Version Alignment Checklist

- [x] `pyproject.toml` -> `2.2.0`
- [x] `__init__.py` -> `2.2.0`
- [x] `README.md` release status -> `v2.2.0`
- [x] `ROADMAP.md` exists and tracks execution phases
- [x] `docs/index.md` -> `2.2.0`
- [x] `docs/USER_GUIDE.md` -> `2.2.0`
- [x] `docs/FEATURES.md` -> `2.2.0`
- [x] `docs/CHANGELOG.md` has `2.2.0` section
- [x] `vscode-extension/package.json` -> `2.2.0`
- [x] `jetbrains-plugin/build.gradle.kts` -> `2.2.0`
- [x] `jetbrains-plugin/src/main/resources/META-INF/plugin.xml` -> `2.2.0`

---

## Artifact Hygiene Checklist

- [x] Runtime backup/transaction directories are ignored in `.gitignore`
- [x] Release workflow uploads build artifacts for GUI, VS Code, and JetBrains outputs

---

## GA Exit Criteria

GA can be tagged when:

1. Full regression suite remains green on final pre-tag run.
2. JetBrains plugin `buildPlugin` passes and distributable artifact is archived.
3. Version alignment checklist remains fully checked.
4. Required artifacts are generated (CLI package, GUI exe, VSIX, JetBrains zip, Docker images or documented Docker gate waiver).
5. Changelog + roadmap are synchronized with GA status.

## Tagging Status

- `v2.2.0` tag creation is pending final clean release commit.
- Planned command: `git tag -a v2.2.0 -m "CodeMarshal v2.2.0 GA"` followed by `git push origin v2.2.0`.
