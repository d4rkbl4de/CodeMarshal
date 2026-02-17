"""CLI metadata command coverage."""

from __future__ import annotations

from bridge.entry.cli import CodeMarshalCLI


def test_version_flag_works_without_subcommand(capsys) -> None:
    """`--version` must not require a command parser target."""
    cli = CodeMarshalCLI()
    exit_code = cli.run(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CodeMarshal v" in captured.out


def test_info_flag_works_without_subcommand(capsys) -> None:
    """`--info` must not require a command parser target."""
    cli = CodeMarshalCLI()
    exit_code = cli.run(["--info"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CodeMarshal System Information" in captured.out
