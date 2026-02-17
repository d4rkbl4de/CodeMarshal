# Pattern Library and Marketplace

CodeMarshal ships a local-first pattern marketplace and template workflow.

## Command Overview

```bash
codemarshal pattern search "security"
codemarshal pattern apply hardcoded_password .
codemarshal pattern create --template security.keyword_assignment --set identifier=api_key --dry-run
codemarshal pattern share hardcoded_password --bundle-out hardcoded_password.cmpattern.yaml
```

`codemarshal patterns` is an alias for `codemarshal pattern`.

## Marketplace Model

- Local-only by default.
- No account registration and no network dependency.
- Share/install via `.cmpattern.yaml` bundle files.

## Bundle Format

Shared bundles are YAML files with:

- `schema_version`
- `package` metadata (`id`, `pattern_id`, `version`, `created_at`)
- `pattern` payload compatible with `PatternDefinition`

## Template Workflow

Use templates to generate custom patterns with predictable structure:

- `security.keyword_assignment`
- `performance.loop_call`
- `style.naming_prefix`
- `architecture.cross_layer_import`

Template value format is `key=value`, repeated with `--set`.

## Contribution Flow (Local)

1. Create or import a pattern.
2. Validate submission through the local collector.
3. Optionally curate/approve in local metadata.
4. Share with bundle export.

## Recommendations

- Prefer narrow regex patterns to reduce noise.
- Add tags and languages for better discovery.
- Keep pattern IDs stable using `namespace.name` style.
