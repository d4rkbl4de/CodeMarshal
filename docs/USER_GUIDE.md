# CodeMarshal User Guide

**Version:** 2.1.0  
**Last Updated:** February 13, 2026

---

## 1. Project Status

Current delivery status:

- Completed phases: `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`
- Latest validation:
  - `175 passed, 3 skipped` (`pytest -q`)
  - `93.53%` coverage (`pytest --cov=. --cov-report=term-missing -q`)

Roadmap details are in `ROADMAP.md`.

---

## 2. Installation

### Base install

```bash
python -m pip install -e .
```

### Optional extras

```bash
python -m pip install -e .[dev]
python -m pip install -e .[gui]
python -m pip install -e .[export_pdf]
```

### Verify CLI

```bash
codemarshal --help
codemarshal --version
codemarshal --info
```

---

## 3. Quick Workflow

1. Investigate a codebase.

```bash
codemarshal investigate . --scope=module --intent=initial_scan
```

2. Ask a structured query.

```bash
codemarshal query <investigation_id> \
  --question="What modules exist?" \
  --question-type=structure \
  --limit=25
```

3. Export findings.

```bash
codemarshal export <investigation_id> --format=markdown --output=report.md --confirm-overwrite
```

---

## 4. Command Reference

### `investigate`

Start a tracked investigation session.

```bash
codemarshal investigate <path> \
  --scope {file,module,package,project} \
  --intent {initial_scan,constitutional_check,dependency_analysis,architecture_review} \
  [--name NAME] [--notes NOTES] [--confirm-large]
```

Example:

```bash
codemarshal investigate ./core --scope=project --intent=architecture_review --name="core-arch-review"
```

### `observe`

Collect observations without creating a full investigation flow.

```bash
codemarshal observe <path> \
  --scope {file,module,package,project} \
  [--depth DEPTH] [--include-binary] [--follow-symlinks] \
  [--constitutional] [--dump] [--persist]
```

Examples:

```bash
codemarshal observe . --scope=module --constitutional
codemarshal observe . --scope=project --persist
```

### `query`

Ask anchored questions about an existing investigation.

```bash
codemarshal query <investigation_id> \
  --question "..." \
  --question-type {structure,purpose,connections,anomalies,thinking} \
  [--focus PATH] [--limit N]
```

Examples:

```bash
codemarshal query <id> --question="Show circular dependencies" --question-type=connections
codemarshal query <id> --question="What risks are present?" --question-type=thinking --limit=20
```

### `search`

Search code with regex or plain text. Supports context, type filters, and result limits.

```bash
codemarshal search <query> [path] \
  [--case-insensitive|-i] \
  [--context|-C N] \
  [--glob|-g PATTERN] \
  [--type|-t TYPE] \
  [--limit|-m N] \
  [--output|-o {text,json,count}] \
  [--json-file FILE] \
  [--threads N] \
  [--exclude|-e PATTERN] \
  [--files-with-matches|-l]
```

Examples:

```bash
codemarshal search "TODO" . -m 50
codemarshal search "class\\s+\\w+" . -C 2 -g "*.py"
codemarshal search "@deprecated" . -l --type=py
codemarshal search "from .* import" . -o json --json-file imports.json
```

### `pattern`

Pattern detection and custom pattern management.

```bash
codemarshal pattern list [--category {security,performance,style}] [--show-disabled] [--output {table,json}]
codemarshal pattern scan [path] [--pattern ID] [--category {security,performance,style}] [--glob PATTERN] [--output {table,json}] [--max-files N]
codemarshal pattern add --id ID --name NAME --pattern REGEX [--severity {critical,warning,info}] [--description TEXT] [--message TEXT] [--tags TAG] [--languages LANG]
```

### `export`

Export investigation output to external formats.

```bash
codemarshal export <investigation_id> \
  --format {json,markdown,html,plain,csv,jupyter,pdf,svg} \
  --output OUTPUT \
  [--confirm-overwrite] [--include-notes] [--include-patterns]
```

Examples:

```bash
codemarshal export <id> --format=json --output=investigation.json --confirm-overwrite
codemarshal export <id> --format=jupyter --output=investigation.ipynb --confirm-overwrite
codemarshal export <id> --format=svg --output=architecture.svg --confirm-overwrite
codemarshal export <id> --format=pdf --output=report.pdf --confirm-overwrite
```

### `gui`

Desktop GUI entrypoint.

```bash
codemarshal gui [path]
```

### `tui`

Launch the terminal UI.

```bash
codemarshal tui [--path PATH]
```

### Maintenance and system commands

```bash
codemarshal config {show,edit,reset,validate}
codemarshal backup --help
codemarshal cleanup --help
codemarshal repair --help
codemarshal test --help
codemarshal migrate --help
```

---

## 5. Query and Search Limits (`-m` / `--limit`)

Two commands use result limits explicitly:

- `query`: `--limit N`
- `search`: `--limit N` or short form `-m N`

Examples:

```bash
codemarshal query <id> --question="What modules exist?" --question-type=structure --limit=10
codemarshal search "TODO" . -m 25
```

---

## 6. Export Formats

Supported formats:

- `json`
- `markdown`
- `html`
- `plain`
- `csv`
- `jupyter`
- `pdf`
- `svg`

Notes:

- Use `--confirm-overwrite` for existing files.
- Add `--include-notes` and `--include-patterns` when needed.

---

## 7. PDF Export Dependencies

PDF export relies on WeasyPrint and native rendering libraries.

### Local install

```bash
python -m pip install -e .[export_pdf]
```

- On Windows: install GTK runtime/native libs on host.
- On Linux: install required native packages (`libcairo2`, `libpango-1.0-0`, `libgdk-pixbuf-2.0-0`, `libffi-dev`, `shared-mime-info`, fonts).

### Docker route (recommended for reproducible PDF support)

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev shared-mime-info fonts-dejavu \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip && python -m pip install -e .[export_pdf]
```

---

## 8. Desktop GUI Prerequisites

GUI requires PySide6:

```bash
python -m pip install -e .[gui]
```

If missing, GUI-related checks/tests may be skipped in certain environments.

---

## 9. Validation Commands

### Run tests

```bash
pytest -q
```

### Run coverage gate

```bash
pytest --cov=. --cov-report=term-missing -q
```

Expected gate:

- `fail_under = 90`

---

## 10. Troubleshooting

### `codemarshal gui` does not start

- Confirm PySide6 is installed: `python -m pip install -e .[gui]`
- Verify environment: `codemarshal --info`

### PDF export fails

- Confirm extra installed: `python -m pip install -e .[export_pdf]`
- Install native libs (host or Docker image).

### Search returns too many results

- Use `-m` or `--limit`.
- Use `--files-with-matches` to list files only.
- Narrow scope with `--glob`, `--type`, and `--exclude`.

---

## 11. Related Docs

- **[ROADMAP.md](../ROADMAP.md)** - Current execution status and implementation milestones
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and what's new
- **[docs/FEATURES.md](FEATURES.md)** - Complete feature matrix and capabilities
- **[docs/API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Programmatic API reference
- **[docs/architecture.md](architecture.md)** - System architecture and layers
- **[docs/INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)** - CI/CD and editor integration
- **[docs/index.md](index.md)** - Documentation navigation guide
- **[README.truth.md](README.truth.md)** - Truth-preservation philosophy
