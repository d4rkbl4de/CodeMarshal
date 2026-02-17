# CodeMarshal Release Checklist: v2.2.0-rc1

**Date:** February 17, 2026  
**Release Line:** `2.2.0-rc1`  
**Validation Environment:** Windows 10, Python 3.12.10, project virtualenv (`.venv`)

---

## Gate Summary

- Core + CLI + desktop + collaboration test suite passes in `.venv`.
- RC metadata is aligned across package manifests and release-facing docs.
- VS Code extension TypeScript build passes.
- JetBrains plugin Gradle build was executed with local JDK + Gradle bootstrap and currently fails with a Gradle Kotlin DSL compile error in `jetbrains-plugin/build.gradle.kts`.

---

## Required Commands

### 1) Python package install and dependency integrity

```powershell
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m pip check
```

Status: `PASS`  
Notes: package version resolves to `2.2.0rc1` in editable install.

### 2) Full regression suite

```powershell
.venv\Scripts\python -m pytest -q
```

Status: `PASS`  
Result: `274 passed, 1 warning`

### 3) CLI version/info smoke

```powershell
.venv\Scripts\python -m bridge.entry.cli --version
.venv\Scripts\python -m bridge.entry.cli --info
```

Status: `PASS`  
Notes:
- Version reports `CodeMarshal v2.2.0rc1`.
- Current runtime prints a constitutional import warning from `core.shutdown`; non-blocking for RC, tracked for post-RC cleanup.

### 4) VS Code extension build

```powershell
cmd /c npm run build
```

Working directory: `vscode-extension`  
Status: `PASS`

### 5) JetBrains plugin build

Executed command:

```powershell
$env:JAVA_HOME=(Resolve-Path '.tools\jdk-17.0.18+8').Path
$env:GRADLE_USER_HOME=(Resolve-Path '.test_tmp\gradle_home').Path
$tmp=(Resolve-Path '.test_tmp\gradle_tmp').Path
$env:TEMP=$tmp; $env:TMP=$tmp; $env:TMPDIR=$tmp
.tools\gradle-8.10.2\bin\gradle.bat -Djava.io.tmpdir=$tmp -p jetbrains-plugin build --no-daemon
```

Status: `FAIL`  
Failure:

- File: `jetbrains-plugin/build.gradle.kts`
- Line: `48`
- Error: `Unresolved reference: tokens`

Notes:

- The build is now reproducible in this environment with bootstrapped toolchain:
  - JDK: `.tools\jdk-17.0.18+8`
  - Gradle: `.tools\gradle-8.10.2`
- This failure is a release blocker for JetBrains plugin packaging until the Gradle script is corrected.

---

## Version Alignment Checklist

- [x] `pyproject.toml` -> `2.2.0rc1`
- [x] `__init__.py` -> `2.2.0rc1`
- [x] `README.md` release status -> `v2.2.0-rc1`
- [x] `docs/index.md` -> `2.2.0-rc1`
- [x] `docs/USER_GUIDE.md` -> `2.2.0-rc1`
- [x] `docs/FEATURES.md` -> `2.2.0-rc1`
- [x] `docs/CHANGELOG.md` has `2.2.0-rc1` section
- [x] `vscode-extension/package.json` -> `2.2.0-rc.1`
- [x] `jetbrains-plugin/build.gradle.kts` -> `2.2.0-rc1`
- [x] `jetbrains-plugin/src/main/resources/META-INF/plugin.xml` -> `2.2.0-rc1`

---

## Artifact Hygiene Checklist

- [x] Ignore runtime backup/transaction directories in `.gitignore`:
  - `storage/.backups/`
  - `storage/transactions/`
  - `storage/knowledge_runtime/`
  - `.codemarshal/audit_logs/recovery/`

---

## RC Exit Criteria

RC can be tagged when:

1. Full `.venv` regression remains green on final pre-tag run.
2. No unresolved blocker defects are open for release-critical paths.
3. Version alignment checklist remains fully checked.
4. JetBrains plugin build verification is either executed on a Gradle-capable machine or explicitly waived for RC.
