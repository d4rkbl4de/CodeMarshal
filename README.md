# CodeMarshal

Truth-preserving investigation tooling for complex codebases.

## Current Status (February 16, 2026)

- Phases complete: `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`
- Release line: `v2.2.0-rc1`
- Latest local validation run (project `.venv`, `python -m pytest -q`): `274 collected, 274 passed, 0 failed`
- Coverage policy: `fail_under = 90%` (run `pytest --cov=. --cov-report=term -q` for current value)

See `ROADMAP.md` for the execution-status roadmap.

## Quick Start

```bash
python -m pip install -e .
codemarshal --help
```

Run a first investigation:

```bash
codemarshal investigate . --scope=module --intent=initial_scan
```

Query results:

```bash
codemarshal query <investigation_id> \
  --question="What modules exist?" \
  --question-type=structure \
  --limit=25
```

Search code with result limits:

```bash
codemarshal search "TODO" . --limit=50
codemarshal search "TODO" . -m 50
codemarshal search "TODO" . -l --glob "*.py"
```

Export results:

```bash
codemarshal export <investigation_id> --format=markdown --output=report.md --confirm-overwrite
codemarshal export <investigation_id> --format=pdf --output=report.pdf --confirm-overwrite
```

## Command Set

- `investigate` - create a tracked investigation
- `observe` - collect observations without full investigation
- `query` - ask evidence-anchored questions
- `search` - regex/text search with limit/context/file filters
- `pattern` / `patterns` - list, scan, add, search, apply, create, or share patterns

Note: `pattern` is deprecated; prefer `patterns`.
- `history`, `graph`, `recommendations` - inspect knowledge timeline, graph, and suggested next steps
- `team` - manage local collaboration teams and workspace key unlock
- `share` - create/list/revoke/resolve encrypted share artifacts
- `comment` - add/list/resolve encrypted threaded comments
- `export` - export investigation data (`json`, `markdown`, `html`, `plain`, `csv`, `jupyter`, `pdf`, `svg`)
- `gui` - desktop GUI entrypoint
- `tui` - terminal UI
- `config`, `backup`, `cleanup`, `repair`, `test`, `migrate`

## Optional Dependencies

Install extras based on what you use:

```bash
python -m pip install -e .[gui]
python -m pip install -e .[export_pdf]
python -m pip install -e .[dev]
```

## Desktop GUI Highlights

- Diff viewer with fold/unfold hunk sections and line-aware coloring.
- Pattern template and marketplace panels integrated into the Patterns route.
- Knowledge canvas + history sidebar + threaded comments panel in the Knowledge route.
- Expanded theme catalog with dark and light variants.

## Docker Note (PDF Export)

For Linux containers, install native libraries required by WeasyPrint in the image so users do not need manual host setup:

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

On Windows host environments, PDF export still requires GTK runtime/native libraries if not using this Linux container route.

## Documentation

- **[ROADMAP.md](ROADMAP.md)** - execution status and implementation milestones
- **[CHANGELOG.md](CHANGELOG.md)** - version history and migration guides
- **[docs/index.md](docs/index.md)** - documentation navigation guide
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - command usage and workflows
- **[docs/RELEASE_CHECKLIST_v2.2.0-rc1.md](docs/RELEASE_CHECKLIST_v2.2.0-rc1.md)** - release-candidate gate checklist and results
- **[docs/FEATURES.md](docs/FEATURES.md)** - implemented features and phase mapping
- **[docs/pattern_library.md](docs/pattern_library.md)** - local marketplace and template workflows
- **[docs/collaboration.md](docs/collaboration.md)** - team, share, and comment collaboration workflows
- **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - programmatic API notes
- **[docs/architecture.md](docs/architecture.md)** - system architecture
- **[docs/INTEGRATION_EXAMPLES.md](docs/INTEGRATION_EXAMPLES.md)** - CI/CD and editor integration
- **[docs/README.truth.md](docs/README.truth.md)** - truth-preservation principles
