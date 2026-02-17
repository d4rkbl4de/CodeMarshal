# CodeMarshal User Guide

**Version:** 2.2.0-rc1  
**Last Updated:** February 16, 2026

---

## 1. Project Status

Current delivery status:

- Completed phases: `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`
- Latest validation:
  - `274 collected, 274 passed, 0 failed` (project `.venv`, `python -m pytest -q`)
  - coverage gate remains `fail_under = 90` (`pytest --cov=. --cov-report=term -q`)

Roadmap details are in [ROADMAP.md](../ROADMAP.md).

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

Pattern detection, marketplace workflows, and custom pattern management.

```bash
codemarshal pattern list [--category {security,performance,style,architecture}] [--show-disabled] [--output {table,json}]
codemarshal pattern scan [path] [--pattern ID] [--category {security,performance,style,architecture}] [--glob PATTERN] [--output {table,json}] [--max-files N]
codemarshal pattern add --id ID --name NAME --pattern REGEX [--severity {critical,warning,info}] [--description TEXT] [--message TEXT] [--tags TAG] [--languages LANG]
codemarshal pattern search [QUERY] [--tag TAG] [--severity {critical,warning,info}] [--language LANG] [--limit N] [--output {table,json}]
codemarshal pattern apply PATTERN_REF [path] [--glob PATTERN] [--max-files N] [--output {table,json}]
codemarshal pattern create --template TEMPLATE_ID [--set key=value] [--dry-run] [--output BUNDLE_PATH] [--json]
codemarshal pattern share PATTERN_ID [--bundle-out PATH] [--include-examples] [--output {table,json}]
```

`codemarshal patterns ...` is supported as an alias for `codemarshal pattern ...`.
`codemarshal pattern ...` is deprecated and now prints a migration warning.

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

### Collaboration commands (`team`, `share`, `comment`)

Collaboration data is local and encrypted. Set a passphrase in an environment variable, then unlock a workspace key once per shell session.

```bash
# PowerShell
$env:CM_PASS="strong-passphrase"
# bash/zsh
export CM_PASS=strong-passphrase
codemarshal team unlock --workspace-id default --passphrase-env CM_PASS --initialize
```

Create and manage teams:

```bash
codemarshal team create "Alpha Team" --owner-id owner_1 --owner-name "Owner One"
codemarshal team add <team_id> user_2 --name "User Two" --role member --by owner_1
codemarshal team list
```

Share investigation artifacts:

```bash
codemarshal share create <session_id> --by owner_1 --target-team <team_id> --permission read --passphrase-env CM_PASS
codemarshal share list --session-id <session_id>
codemarshal share resolve <share_id> --accessor <team_id> --passphrase-env CM_PASS
codemarshal share revoke <share_id> --by owner_1
```

Threaded comments:

```bash
codemarshal comment add <share_id> --by owner_1 --name "Owner One" --body "Please review import boundaries." --passphrase-env CM_PASS
codemarshal comment list <share_id> --passphrase-env CM_PASS
codemarshal comment resolve <comment_id> --by owner_1 --passphrase-env CM_PASS
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

### GUI first-run onboarding

On first launch, the desktop app opens a short onboarding dialog:

- choose project path
- choose first action (`Investigate` or `Observe`)
- enable/disable contextual hints

You can reopen onboarding anytime with `F1` or `Help -> Show Onboarding`.
Keyboard shortcuts are listed under `Help -> Keyboard Shortcuts`.

### GUI accessibility options

Desktop GUI accessibility settings are available under `View -> Accessibility`:

- theme mode: `Standard` or `High Contrast`
- font scale: `100%`, `115%`, `130%`
- reset accessibility defaults in one action

Desktop visual-shell settings are available under `View`:

- `Theme`: `Editorial Noir Premium`, `Editorial Noir Classic`, `Ledger Brass`, `Linen Daylight`, `Harbor Light`
- `Density`: `Comfortable`, `Compact`
- `Accent`: `Soft`, `Normal`, `Bold`
- `Motion`: `Full Motion`, `Standard Motion`, `Reduced Motion`, plus `Force Reduced Motion`
- `Toggle Sidebar` (`Ctrl+B`) and `Reset Visual Defaults`

Desktop phase-7 panels:

- `Patterns` route includes `Marketplace` and `Template Builder` panels.
- `Knowledge` route includes `History Timeline`, `Knowledge Canvas`, and `Comments` panels.
- Diff interactions use the dedicated `Diff Viewer` dialog with fold/unfold section controls.

Preferences are persisted in `storage/gui_state.json`.

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
- **[docs/collaboration.md](collaboration.md)** - Collaboration encryption and command workflows
- **[docs/INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)** - CI/CD and editor integration
- **[docs/index.md](index.md)** - Documentation navigation guide
- **[README.truth.md](README.truth.md)** - Truth-preservation philosophy
