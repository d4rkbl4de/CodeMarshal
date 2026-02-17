"""
patterns/templates.py - Pattern template registry and rendering helpers.

Local-only template system used by CLI/Desktop pattern creation workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from patterns.loader import PatternDefinition


@dataclass(frozen=True)
class TemplateField:
    """Single input field required by a pattern template."""

    key: str
    label: str
    description: str
    required: bool = True
    default: str = ""
    field_type: str = "string"


@dataclass(frozen=True)
class PatternTemplate:
    """Template used to generate a `PatternDefinition`."""

    id: str
    name: str
    category: str
    description: str
    regex_template: str
    message_template: str
    fields: list[TemplateField] = field(default_factory=list)
    severity: str = "warning"
    tags: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TemplateInstance:
    """Materialized template output."""

    template_id: str
    values: dict[str, str]
    pattern: PatternDefinition


class PatternTemplateRegistry:
    """Registry of built-in pattern templates."""

    def __init__(self) -> None:
        self._templates = self._build_templates()

    def list_templates(self, category: str | None = None) -> list[PatternTemplate]:
        """List available templates, optionally filtered by category."""
        if category is None:
            return list(self._templates.values())
        normalized = category.strip().lower()
        return [
            template
            for template in self._templates.values()
            if template.category.lower() == normalized
        ]

    def get_template(self, template_id: str) -> PatternTemplate | None:
        """Resolve a template by id."""
        return self._templates.get(template_id.strip().lower())

    def validate_inputs(
        self,
        template_id: str,
        values: dict[str, str] | None,
    ) -> tuple[bool, list[str]]:
        """Validate required fields for a template."""
        template = self.get_template(template_id)
        if template is None:
            return False, [f"Unknown template: {template_id}"]

        payload = values or {}
        errors: list[str] = []

        for field_def in template.fields:
            raw = str(payload.get(field_def.key, field_def.default)).strip()
            if field_def.required and not raw:
                errors.append(f"Missing required field: {field_def.key}")

        return len(errors) == 0, errors

    def render_pattern(
        self,
        template_id: str,
        values: dict[str, str] | None,
        *,
        pattern_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        severity: str | None = None,
        tags: list[str] | None = None,
        languages: list[str] | None = None,
    ) -> TemplateInstance:
        """Render template and return a validated pattern definition."""
        template = self.get_template(template_id)
        if template is None:
            raise ValueError(f"Unknown template: {template_id}")

        valid, errors = self.validate_inputs(template_id, values)
        if not valid:
            raise ValueError("; ".join(errors))

        payload = self._normalized_values(template, values or {})
        rendered_regex = template.regex_template.format(**payload)
        rendered_message = template.message_template.format(**payload)

        generated_id = (pattern_id or f"tpl_{template.id}_{payload['slug']}").strip()
        generated_name = (name or f"{template.name}: {payload['label']}").strip()
        generated_description = (
            description or template.description.format(**payload)
        ).strip()

        pattern = PatternDefinition(
            id=generated_id,
            name=generated_name,
            pattern=rendered_regex,
            severity=(severity or template.severity).strip().lower(),
            description=generated_description,
            message=rendered_message,
            tags=list(tags) if tags is not None else list(template.tags),
            languages=list(languages)
            if languages is not None
            else list(template.languages),
            enabled=True,
        )
        return TemplateInstance(template_id=template.id, values=payload, pattern=pattern)

    def _normalized_values(
        self,
        template: PatternTemplate,
        values: dict[str, str],
    ) -> dict[str, str]:
        payload: dict[str, str] = {}
        for field_def in template.fields:
            raw = str(values.get(field_def.key, field_def.default)).strip()
            payload[field_def.key] = raw

        # Shared placeholders available to all templates.
        label_seed = payload.get("label", "")
        if not label_seed:
            label_seed = payload.get("identifier", "")
        payload["label"] = label_seed
        payload["slug"] = self._slugify(label_seed or template.id)
        return payload

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
        collapsed = "_".join(part for part in cleaned.split("_") if part)
        return collapsed or "pattern"

    @staticmethod
    def _build_templates() -> dict[str, PatternTemplate]:
        templates = [
            PatternTemplate(
                id="security.keyword_assignment",
                name="Security Keyword Assignment",
                category="security",
                description=(
                    "Detects assignments where `{identifier}` appears in variable names."
                ),
                regex_template=r"({identifier})\s*[=:]\s*['\"][^'\"]+['\"]",
                message_template=(
                    "Potential secret assignment ({identifier}) at {{{{file}}}}:{{{{line}}}}"
                ),
                fields=[
                    TemplateField(
                        key="identifier",
                        label="Identifier",
                        description="Sensitive token to detect (e.g., api_key).",
                    ),
                ],
                severity="critical",
                tags=["security", "secrets"],
                languages=["python", "javascript", "java", "go", "ruby"],
            ),
            PatternTemplate(
                id="performance.loop_call",
                name="Expensive Call In Loop",
                category="performance",
                description=(
                    "Detects loop bodies containing `{identifier}` calls that may be costly."
                ),
                regex_template=r"for\s+.+:\s*\n(?:\s+.+\n)*?\s*{identifier}\s*\(",
                message_template=(
                    "Potential expensive call `{identifier}` in loop at {{{{file}}}}:{{{{line}}}}"
                ),
                fields=[
                    TemplateField(
                        key="identifier",
                        label="Function Name",
                        description="Function or call pattern expected inside loops.",
                    ),
                ],
                severity="warning",
                tags=["performance", "loops"],
                languages=["python"],
            ),
            PatternTemplate(
                id="style.naming_prefix",
                name="Naming Prefix Enforcement",
                category="style",
                description=(
                    "Detects identifiers missing required `{identifier}` prefix."
                ),
                regex_template=r"\b(?!{identifier}_)[a-zA-Z_][a-zA-Z0-9_]*\b",
                message_template=(
                    "Identifier does not use required `{identifier}_` prefix at {{{{file}}}}:{{{{line}}}}"
                ),
                fields=[
                    TemplateField(
                        key="identifier",
                        label="Required Prefix",
                        description="Naming prefix without trailing underscore.",
                    ),
                ],
                severity="info",
                tags=["style", "naming"],
                languages=["python", "javascript", "typescript"],
            ),
            PatternTemplate(
                id="architecture.cross_layer_import",
                name="Cross-Layer Import Guard",
                category="architecture",
                description=(
                    "Detects imports where `{identifier}` directly references restricted layers."
                ),
                regex_template=r"from\s+{identifier}\..+\s+import\s+.+|import\s+{identifier}\..+",
                message_template=(
                    "Possible cross-layer import from `{identifier}` at {{{{file}}}}:{{{{line}}}}"
                ),
                fields=[
                    TemplateField(
                        key="identifier",
                        label="Restricted Layer",
                        description="Layer root/package that should not be imported directly.",
                    ),
                ],
                severity="warning",
                tags=["architecture", "boundaries"],
                languages=["python"],
            ),
        ]
        return {template.id.lower(): template for template in templates}
