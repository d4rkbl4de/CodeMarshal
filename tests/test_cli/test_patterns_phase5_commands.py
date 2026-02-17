from types import SimpleNamespace

from bridge.entry.cli import CodeMarshalCLI


def test_patterns_alias_parser_supports_search() -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(["patterns", "search", "security"])

    assert parsed.command == "patterns"
    assert parsed.pattern_command == "search"
    assert parsed.query == "security"


def test_handle_pattern_search_json(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(["pattern", "search", "security", "--output", "json"])

    monkeypatch.setattr(
        "bridge.commands.execute_pattern_search",
        lambda **_kwargs: SimpleNamespace(
            success=True,
            total_count=1,
            patterns=[
                {
                    "pattern_id": "hardcoded_password",
                    "name": "Hardcoded Password",
                    "severity": "critical",
                    "installed": False,
                    "rating": {"average_rating": 0.0, "total_reviews": 0},
                }
            ],
            message="ok",
            error=None,
        ),
    )

    exit_code = cli._handle_pattern(parsed)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "hardcoded_password" in output


def test_handle_pattern_create_json(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(
        [
            "pattern",
            "create",
            "--template",
            "security.keyword_assignment",
            "--set",
            "identifier=api_key",
            "--json",
            "--dry-run",
        ]
    )

    monkeypatch.setattr(
        "bridge.commands.execute_pattern_create",
        lambda **_kwargs: SimpleNamespace(
            success=True,
            template_id="security.keyword_assignment",
            pattern_id="tpl_security_keyword_assignment_api_key",
            created=False,
            installed=False,
            dry_run=True,
            submission_id="sub_123",
            validation_errors=[],
            validation_warnings=[],
            output_path=None,
            pattern={"id": "tpl_security_keyword_assignment_api_key"},
            message="Dry-run successful",
            error=None,
        ),
    )

    exit_code = cli._handle_pattern(parsed)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "tpl_security_keyword_assignment_api_key" in output


def test_handle_pattern_share_json(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(
        ["pattern", "share", "hardcoded_password", "--output", "json"]
    )

    monkeypatch.setattr(
        "bridge.commands.execute_pattern_share",
        lambda **_kwargs: SimpleNamespace(
            success=True,
            pattern_id="hardcoded_password",
            package_id="hardcoded_password-1",
            path="bundle.cmpattern.yaml",
            version="1.0.0",
            created_at="2026-02-16T00:00:00Z",
            message="ok",
            error=None,
        ),
    )

    exit_code = cli._handle_pattern(parsed)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "bundle.cmpattern.yaml" in output


def test_run_warns_on_legacy_pattern_command(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()
    called = {"value": False}

    def _fake_handle(_args):
        called["value"] = True
        return 0

    monkeypatch.setattr(cli, "_handle_pattern", _fake_handle)
    exit_code = cli.run(["pattern", "list", "--output", "json"])
    stderr = capsys.readouterr().err

    assert exit_code == 0
    assert called["value"] is True
    assert "deprecated" in stderr.lower()
    assert "use `patterns` instead" in stderr.lower()


def test_run_does_not_warn_on_patterns_alias(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()

    monkeypatch.setattr(cli, "_handle_pattern", lambda _args: 0)
    exit_code = cli.run(["patterns", "list", "--output", "json"])
    stderr = capsys.readouterr().err

    assert exit_code == 0
    assert "deprecated" not in stderr.lower()
