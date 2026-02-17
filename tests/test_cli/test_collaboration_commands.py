import os
from types import SimpleNamespace

from bridge.entry.cli import CodeMarshalCLI


def test_team_unlock_parser() -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(
        ["team", "unlock", "--passphrase-env", "CM_PASS"]
    )
    assert parsed.command == "team"
    assert parsed.team_command == "unlock"
    assert parsed.workspace_id == "default"


def test_handle_team_unlock_json(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(
        ["team", "unlock", "--passphrase-env", "CM_PASS", "--output", "json"]
    )
    monkeypatch.setenv("CM_PASS", "strong-passphrase")
    monkeypatch.setattr(
        "bridge.commands.execute_team_unlock",
        lambda **_kwargs: {
            "success": True,
            "workspace_id": "default",
            "initialized": False,
            "unlocked": True,
        },
    )

    exit_code = cli._handle_team(parsed)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"success": true' in output.lower()


def test_handle_share_create_json(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(
        [
            "share",
            "create",
            "session_1",
            "--by",
            "owner_1",
            "--target-team",
            "team_1",
            "--permission",
            "read",
            "--passphrase-env",
            "CM_PASS",
            "--output",
            "json",
        ]
    )
    monkeypatch.setenv("CM_PASS", "strong-passphrase")
    monkeypatch.setattr(
        "bridge.commands.execute_share_create",
        lambda **_kwargs: {
            "success": True,
            "workspace_id": "default",
            "share": {
                "share_id": "share_1",
                "session_id": "session_1",
                "status": "active",
                "targets": [],
            },
        },
    )

    exit_code = cli._handle_share(parsed)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"share_id": "share_1"' in output


def test_handle_comment_list_json(monkeypatch, capsys) -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(
        [
            "comment",
            "list",
            "share_1",
            "--passphrase-env",
            "CM_PASS",
            "--output",
            "json",
        ]
    )
    monkeypatch.setenv("CM_PASS", "strong-passphrase")
    monkeypatch.setattr(
        "bridge.commands.execute_comment_list",
        lambda **_kwargs: {
            "success": True,
            "count": 1,
            "comments": [{"comment_id": "c1", "body": "hello"}],
        },
    )

    exit_code = cli._handle_comment(parsed)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"comment_id": "c1"' in output


def test_missing_passphrase_env_fails(monkeypatch) -> None:
    cli = CodeMarshalCLI()
    parsed = cli.parser.parse_args(
        ["team", "unlock", "--passphrase-env", "MISSING_ENV", "--output", "json"]
    )
    monkeypatch.delenv("MISSING_ENV", raising=False)

    exit_code = cli._handle_team(parsed)
    assert exit_code == 1

