# CodeMarshal

Truth-preserving investigation tooling for complex codebases.

## Current Status (February 14, 2026)

- Phases complete: `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`
- Full test suite (with PySide6): `186 passed, 2 skipped`
- Full test suite (without PySide6): `184 passed, 3 skipped`
- Coverage gate: `95.70%` with GUI extra / `93.99%` without (`fail_under = 90%`)

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
- `pattern` - list, scan, or add patterns
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
- **[docs/FEATURES.md](docs/FEATURES.md)** - implemented features and phase mapping
- **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - programmatic API notes
- **[docs/architecture.md](docs/architecture.md)** - system architecture
- **[docs/INTEGRATION_EXAMPLES.md](docs/INTEGRATION_EXAMPLES.md)** - CI/CD and editor integration
- **[docs/README.truth.md](docs/README.truth.md)** - truth-preservation principles
