from patterns.templates import PatternTemplateRegistry


def test_template_registry_lists_defaults() -> None:
    registry = PatternTemplateRegistry()
    templates = registry.list_templates()
    template_ids = {template.id for template in templates}

    assert "security.keyword_assignment" in template_ids
    assert "architecture.cross_layer_import" in template_ids


def test_render_pattern_from_template() -> None:
    registry = PatternTemplateRegistry()

    instance = registry.render_pattern(
        "security.keyword_assignment",
        {"identifier": "api_key"},
    )

    assert instance.template_id == "security.keyword_assignment"
    assert instance.pattern.id.startswith("tpl_security.keyword_assignment")
    assert "api_key" in instance.pattern.pattern
    assert instance.pattern.severity == "critical"
    assert "{{file}}" in instance.pattern.message


def test_template_validation_rejects_missing_required_fields() -> None:
    registry = PatternTemplateRegistry()
    valid, errors = registry.validate_inputs("security.keyword_assignment", {})

    assert valid is False
    assert any("identifier" in error for error in errors)
