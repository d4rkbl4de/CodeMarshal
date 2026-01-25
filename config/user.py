"""
config/user.py — USER OVERRIDES (UNTRUSTED INPUT)

This module represents user-provided configuration before validation.
All values are optional - this is what the user asks for, not what the system will do.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class OutputFormat(Enum):
    JSON = "json"
    HUMAN = "human"
    BOTH = "both"
    MARKDOWN = "markdown"
    HTML = "html"


class CommandType(Enum):
    WITNESS = "witness"
    INVESTIGATE = "investigate"
    ASK = "ask"
    PATTERNS = "patterns"
    EXPORT = "export"


class BoundaryStrictness(Enum):
    STRICT = "strict"
    WARN = "warn"
    IGNORE = "ignore"


@dataclass
class WitnessCommand:
    path: Path | None = None
    output_format: OutputFormat | None = None
    include_hidden: bool | None = None
    max_file_size_mb: int | None = None
    follow_symlinks: bool | None = None
    exclude_patterns: list[str] | None = None
    only_python: bool | None = None
    skip_binary: bool | None = None
    detect_encoding: bool | None = None
    record_checksums: bool | None = None


@dataclass
class InvestigateCommand:
    path: Path | None = None
    focus: str | None = None
    rule: str | None = None
    depth: int | None = None
    check_constitutional: bool | None = None
    check_imports: bool | None = None
    check_boundaries: bool | None = None
    boundary_strictness: BoundaryStrictness | None = None


@dataclass
class AskCommand:
    path: Path | None = None
    question: str | None = None
    question_type: str | None = None
    about: str | None = None
    relation: str | None = None
    metric: str | None = None


@dataclass
class PatternsCommand:
    path: Path | None = None
    pattern_type: str | None = None
    min_threshold: float | None = None
    max_threshold: float | None = None
    window_size: int | None = None
    include_uncertainty: bool | None = None


@dataclass
class ExportCommand:
    investigation_id: str | None = None
    format: OutputFormat | None = None
    output_path: Path | None = None
    include_evidence: bool | None = None
    include_notes: bool | None = None
    export_all: bool | None = None
    export_summary: bool | None = None
    export_raw: bool | None = None


@dataclass
class UserOverrides:
    command: CommandType | None = None
    witness: WitnessCommand | None = None
    investigate: InvestigateCommand | None = None
    ask: AskCommand | None = None
    patterns: PatternsCommand | None = None
    export: ExportCommand | None = None
    config_file: Path | None = None
    verbose: bool | None = None
    quiet: bool | None = None
    color: bool | None = None
    no_color: bool | None = None
    max_workers: int | None = None
    cache_dir: Path | None = None
    no_cache: bool | None = None
    force_refresh: bool | None = None
    max_total_size_mb: int | None = None
    max_file_count: int | None = None
    max_recursion_depth: int | None = None
    timeout_seconds: int | None = None
    check_rules: list[str] = field(default_factory=lambda: [])
    skip_rules: list[str] = field(default_factory=lambda: [])
    enable_experimental: bool | None = None
    enable_network: bool | None = None
    enable_inference: bool | None = None
    output_file: Path | None = None
    append_output: bool | None = None


def from_cli_args(args: dict[str, Any]) -> UserOverrides:
    """Convert CLI arguments to UserOverrides."""

    def extract_command_args(args_dict: dict[str, Any], prefix: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in args_dict.items():
            if key.startswith(f"{prefix}_"):
                clean_key = key[len(f"{prefix}_") :]
                result[clean_key] = value
        return result

    command_str: str | None = args.get("command")
    command: CommandType | None = None
    if command_str:
        try:
            command = CommandType(command_str)
        except ValueError:
            command = None

    witness_cmd: WitnessCommand | None = None
    if command == CommandType.WITNESS or args.get("witness_path"):
        witness_args = extract_command_args(args, "witness")

        # Handle output_format with proper type casting
        output_format_val = witness_args.get("output_format")
        output_format: OutputFormat | None = None
        if output_format_val:
            try:
                output_format = OutputFormat(output_format_val)
            except ValueError:
                pass

        witness_cmd = WitnessCommand(
            path=_safe_path(witness_args.get("path") or args.get("witness_path")),
            output_format=output_format,
            include_hidden=witness_args.get("include_hidden"),
            max_file_size_mb=witness_args.get("max_file_size_mb"),
            follow_symlinks=witness_args.get("follow_symlinks"),
            exclude_patterns=witness_args.get("exclude_patterns"),
            only_python=witness_args.get("only_python"),
            skip_binary=witness_args.get("skip_binary"),
            detect_encoding=witness_args.get("detect_encoding"),
            record_checksums=witness_args.get("record_checksums"),
        )

    investigate_cmd: InvestigateCommand | None = None
    if command == CommandType.INVESTIGATE or args.get("investigate_path"):
        investigate_args = extract_command_args(args, "investigate")

        # Handle boundary_strictness with proper type casting
        boundary_strictness_val = investigate_args.get("boundary_strictness")
        boundary_strictness: BoundaryStrictness | None = None
        if boundary_strictness_val:
            try:
                boundary_strictness = BoundaryStrictness(boundary_strictness_val)
            except ValueError:
                pass

        investigate_cmd = InvestigateCommand(
            path=_safe_path(
                investigate_args.get("path") or args.get("investigate_path")
            ),
            focus=investigate_args.get("focus"),
            rule=investigate_args.get("rule"),
            depth=investigate_args.get("depth"),
            check_constitutional=investigate_args.get("check_constitutional"),
            check_imports=investigate_args.get("check_imports"),
            check_boundaries=investigate_args.get("check_boundaries"),
            boundary_strictness=boundary_strictness,
        )

    return UserOverrides(
        command=command,
        witness=witness_cmd,
        investigate=investigate_cmd,
        config_file=_safe_path(args.get("config_file")),
        verbose=args.get("verbose"),
        quiet=args.get("quiet"),
        color=args.get("color"),
        no_color=args.get("no_color"),
        max_workers=args.get("max_workers"),
        cache_dir=_safe_path(args.get("cache_dir")),
        no_cache=args.get("no_cache"),
        force_refresh=args.get("force_refresh"),
        max_total_size_mb=args.get("max_total_size_mb"),
        max_file_count=args.get("max_file_count"),
        max_recursion_depth=args.get("max_recursion_depth"),
        timeout_seconds=args.get("timeout_seconds"),
        check_rules=args.get("check_rules", []),
        skip_rules=args.get("skip_rules", []),
        enable_experimental=args.get("enable_experimental"),
        enable_network=args.get("enable_network"),
        enable_inference=args.get("enable_inference"),
        output_file=_safe_path(args.get("output_file")),
        append_output=args.get("append_output"),
    )


def from_config_file(config_dict: dict[str, Any]) -> UserOverrides:
    """Convert config file contents to UserOverrides."""

    def get_section(data: dict[str, Any], section: str) -> dict[str, Any]:
        return data.get(section, {})

    command_str: str | None = config_dict.get("command")
    command: CommandType | None = None
    if command_str:
        try:
            command = CommandType(command_str)
        except ValueError:
            command = None

    witness_section: dict[str, Any] = get_section(config_dict, "witness")
    witness_cmd: WitnessCommand | None = None
    if witness_section:
        # Handle output_format with proper type casting
        output_format_val = witness_section.get("output_format")
        output_format: OutputFormat | None = None
        if output_format_val:
            try:
                output_format = OutputFormat(output_format_val)
            except ValueError:
                pass

        witness_cmd = WitnessCommand(
            path=_safe_path(witness_section.get("path")),
            output_format=output_format,
            include_hidden=witness_section.get("include_hidden"),
            max_file_size_mb=witness_section.get("max_file_size_mb"),
            follow_symlinks=witness_section.get("follow_symlinks"),
            exclude_patterns=witness_section.get("exclude_patterns"),
            only_python=witness_section.get("only_python"),
            skip_binary=witness_section.get("skip_binary"),
            detect_encoding=witness_section.get("detect_encoding"),
            record_checksums=witness_section.get("record_checksums"),
        )

    investigate_section: dict[str, Any] = get_section(config_dict, "investigate")
    investigate_cmd: InvestigateCommand | None = None
    if investigate_section:
        # Handle boundary_strictness with proper type casting
        boundary_strictness_val = investigate_section.get("boundary_strictness")
        boundary_strictness: BoundaryStrictness | None = None
        if boundary_strictness_val:
            try:
                boundary_strictness = BoundaryStrictness(boundary_strictness_val)
            except ValueError:
                pass

        investigate_cmd = InvestigateCommand(
            path=_safe_path(investigate_section.get("path")),
            focus=investigate_section.get("focus"),
            rule=investigate_section.get("rule"),
            depth=investigate_section.get("depth"),
            check_constitutional=investigate_section.get("check_constitutional"),
            check_imports=investigate_section.get("check_imports"),
            check_boundaries=investigate_section.get("check_boundaries"),
            boundary_strictness=boundary_strictness,
        )

    return UserOverrides(
        command=command,
        witness=witness_cmd,
        investigate=investigate_cmd,
        config_file=_safe_path(config_dict.get("config_file")),
        verbose=config_dict.get("verbose"),
        quiet=config_dict.get("quiet"),
        color=config_dict.get("color"),
        no_color=config_dict.get("no_color"),
        max_workers=config_dict.get("max_workers"),
        cache_dir=_safe_path(config_dict.get("cache_dir")),
        no_cache=config_dict.get("no_cache"),
        force_refresh=config_dict.get("force_refresh"),
        max_total_size_mb=config_dict.get("max_total_size_mb"),
        max_file_count=config_dict.get("max_file_count"),
        max_recursion_depth=config_dict.get("max_recursion_depth"),
        timeout_seconds=config_dict.get("timeout_seconds"),
        check_rules=config_dict.get("check_rules", []),
        skip_rules=config_dict.get("skip_rules", []),
        enable_experimental=config_dict.get("enable_experimental"),
        enable_network=config_dict.get("enable_network"),
        enable_inference=config_dict.get("enable_inference"),
        output_file=_safe_path(config_dict.get("output_file")),
        append_output=config_dict.get("append_output"),
    )


def _safe_path(value: Any) -> Path | None:
    """Safely convert value to Path, preserving None."""
    if value is None:
        return None
    try:
        return Path(value) if not isinstance(value, Path) else value
    except (TypeError, ValueError):
        return None


__all__ = [
    "UserOverrides",
    "WitnessCommand",
    "InvestigateCommand",
    "AskCommand",
    "PatternsCommand",
    "ExportCommand",
    "CommandType",
    "OutputFormat",
    "BoundaryStrictness",
    "from_cli_args",
    "from_config_file",
]
