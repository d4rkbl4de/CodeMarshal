"""
config/loader.py — MERGE + FREEZE (THE ONLY ENTRY POINT)

This module is the single entry point for configuration loading.
It merges defaults with user overrides, validates against the constitution,
and returns an immutable Config object.
"""

import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

from .defaults import BoundaryStrictness, CommandType, OutputFormat, SystemDefaults
from .schema import ConfigSchema, validate_and_raise
from .user import (
    UserOverrides,
    from_cli_args,
    from_config_file,
)

# Type variable for generic config classes
T = TypeVar("T")


@dataclass(frozen=True)
class WitnessConfig:
    """Configuration for the witness command."""

    path: Path
    output_format: OutputFormat = OutputFormat.BOTH
    include_hidden: bool = False
    max_file_size_mb: int = 10
    follow_symlinks: bool = False
    exclude_patterns: list[str] = field(default_factory=lambda: [])
    only_python: bool = True
    skip_binary: bool = True
    detect_encoding: bool = True
    record_checksums: bool = True


@dataclass(frozen=True)
class InvestigateConfig:
    """Configuration for the investigate command."""

    path: Path
    focus: str | None = None
    rule: str | None = None
    depth: int = 3
    check_constitutional: bool = True
    check_imports: bool = True
    check_boundaries: bool = True
    boundary_strictness: BoundaryStrictness = BoundaryStrictness.STRICT


@dataclass(frozen=True)
class AskConfig:
    """Configuration for the ask command."""

    path: Path
    question: str | None = None
    question_type: str | None = None
    about: str | None = None
    relation: str | None = None
    metric: str | None = None


@dataclass(frozen=True)
class PatternsConfig:
    """Configuration for the patterns command."""

    path: Path
    pattern_type: str | None = None
    min_threshold: float | None = None
    max_threshold: float | None = None
    window_size: int = 10
    include_uncertainty: bool = True


@dataclass(frozen=True)
class ExportConfig:
    """Configuration for the export command."""

    investigation_id: str | None = None
    format: OutputFormat = OutputFormat.MARKDOWN
    output_path: Path | None = None
    include_evidence: bool = True
    include_notes: bool = True
    export_all: bool = False
    export_summary: bool = True
    export_raw: bool = False


@dataclass(frozen=True)
class GlobalConfig:
    """Global configuration shared by all commands."""

    verbose: bool = False
    quiet: bool = False
    color: bool = field(default_factory=lambda: sys.stdout.isatty())
    no_color: bool = False
    max_workers: int = 4
    cache_dir: Path = field(
        default_factory=lambda: Path.home() / ".codemarshal" / "cache"
    )
    no_cache: bool = False
    force_refresh: bool = False
    max_total_size_mb: int = 1000
    max_file_count: int = 10000
    max_recursion_depth: int = 20
    timeout_seconds: int = 300
    check_rules: list[str] = field(default_factory=lambda: [])
    skip_rules: list[str] = field(default_factory=lambda: [])
    enable_experimental: bool = False
    enable_network: bool = False
    enable_inference: bool = False
    output_file: Path | None = None
    append_output: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate global configuration invariants."""
        if self.no_color and self.color:
            object.__setattr__(self, "color", False)

        # Enforce constitutional constraints
        if self.enable_network:
            from .schema import ConfigValidationError

            raise ConfigValidationError(
                "Network access is constitutionally prohibited (Article 12)",
                field="enable_network",
                rule="no_network",
            )

        if self.enable_inference:
            from .schema import ConfigValidationError

            raise ConfigValidationError(
                "Inference is constitutionally prohibited (Article 1)",
                field="enable_inference",
                rule="no_inference",
            )


@dataclass(frozen=True)
class Config:
    """Immutable, validated configuration for CodeMarshal."""

    global_config: GlobalConfig
    command: CommandType
    witness: WitnessConfig | None = None
    investigate: InvestigateConfig | None = None
    ask: AskConfig | None = None
    patterns: PatternsConfig | None = None
    export: ExportConfig | None = None
    config_source: str = "defaults"
    config_hash: str = ""
    config_version: str = "1.0.0"

    def __post_init__(self) -> None:
        """Validate config invariants and compute hash."""
        # Validate command-specific config exists
        command_to_config: dict[CommandType, Any | None] = {
            CommandType.WITNESS: self.witness,
            CommandType.INVESTIGATE: self.investigate,
            CommandType.ASK: self.ask,
            CommandType.PATTERNS: self.patterns,
            CommandType.EXPORT: self.export,
        }

        required_config = command_to_config.get(self.command)
        if required_config is None:
            from .schema import ConfigValidationError

            raise ConfigValidationError(
                f"Command '{self.command}' requires corresponding configuration, but got None",
                field=self.command.value,
                rule="command_config_required",
            )

        # Compute deterministic config hash for audit trail
        config_dict = self._to_serializable_dict()
        config_str = json.dumps(config_dict, sort_keys=True, default=str)
        config_hash = hashlib.sha256(config_str.encode("utf-8")).hexdigest()[:16]
        object.__setattr__(self, "config_hash", config_hash)

    def _to_serializable_dict(self) -> dict[str, Any]:
        """Convert config to serializable dictionary."""

        # Create type-stable dict factory
        def _strict_dict_factory(items: list[tuple[str, Any]]) -> dict[str, Any]:
            """Strict dictionary factory for dataclasses.asdict."""
            result: dict[str, Any] = {}
            for key, value in items:
                if isinstance(value, Path):
                    result[key] = str(value)
                elif isinstance(value, (OutputFormat, BoundaryStrictness, CommandType)):
                    result[key] = value.value
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, Enum):
                    result[key] = value.value
                else:
                    result[key] = value
            return result

        result: dict[str, Any] = {
            "command": self.command.value,
            "config_source": self.config_source,
            "config_version": self.config_version,
            "global": asdict(self.global_config, dict_factory=_strict_dict_factory),
        }

        # Add command-specific config
        if self.witness:
            result["witness"] = asdict(self.witness, dict_factory=_strict_dict_factory)
        if self.investigate:
            result["investigate"] = asdict(
                self.investigate, dict_factory=_strict_dict_factory
            )
        if self.ask:
            result["ask"] = asdict(self.ask, dict_factory=_strict_dict_factory)
        if self.patterns:
            result["patterns"] = asdict(
                self.patterns, dict_factory=_strict_dict_factory
            )
        if self.export:
            result["export"] = asdict(self.export, dict_factory=_strict_dict_factory)

        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for debugging/reporting."""
        result = self._to_serializable_dict()
        result["config_hash"] = self.config_hash
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert config to JSON string."""
        return json.dumps(
            self.to_dict(), indent=indent, ensure_ascii=False, default=str
        )


class ConfigLoader:
    """Main configuration loader - the single entry point for config creation."""

    def __init__(self) -> None:
        self._defaults = SystemDefaults()
        self._user_overrides: UserOverrides | None = None
        self._merged_config: Config | None = None
        self._schema = ConfigSchema()

    def load_from_cli(self, cli_args: dict[str, Any]) -> Config:
        """Load configuration from CLI arguments."""
        # Load CLI arguments as primary source
        cli_overrides = from_cli_args(cli_args)

        # Merge with config file if specified
        config_overrides = UserOverrides()
        if cli_overrides.config_file:
            config_overrides = self._load_config_file_overrides(
                cli_overrides.config_file
            )

        # Merge CLI and config file overrides (CLI takes precedence)
        merged_overrides = self._merge_overrides(config_overrides, cli_overrides)

        # Apply environment variables (lowest priority)
        env_overrides = self._load_from_environment()
        self._user_overrides = self._merge_overrides(env_overrides, merged_overrides)

        return self._build_config()

    def load_from_file(self, config_file: Path) -> Config:
        """Load configuration from config file."""
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        self._user_overrides = self._load_config_file_overrides(config_file)

        # Apply environment variables
        env_overrides = self._load_from_environment()
        self._user_overrides = self._merge_overrides(
            env_overrides, self._user_overrides
        )

        return self._build_config()

    def load_defaults(self) -> Config:
        """Load system defaults only."""
        self._user_overrides = UserOverrides()
        return self._build_config()

    def _load_config_file_overrides(self, config_file: Path) -> UserOverrides:
        """Load configuration file and convert to UserOverrides."""
        suffix = config_file.suffix.lower()

        try:
            if suffix == ".json":
                with open(config_file, encoding="utf-8") as f:
                    config_dict: dict[str, Any] = json.load(f)
            elif suffix in (".yaml", ".yml"):
                try:
                    import yaml

                    with open(config_file, encoding="utf-8") as f:
                        loaded = yaml.safe_load(f)
                        config_dict = loaded if loaded is not None else {}
                except ImportError:
                    raise ImportError(
                        "PyYAML required for YAML config files. "
                        "Install with: pip install pyyaml"
                    ) from None
            else:
                raise ValueError(
                    f"Unsupported config file format: {suffix}. "
                    "Supported formats: .json, .yaml, .yml"
                )
        except Exception as e:
            from .schema import ConfigValidationError

            raise ConfigValidationError(
                f"Failed to load config file {config_file}: {e}",
                field="config_file",
                rule="config_file_load_error",
            ) from e

        return from_config_file(config_dict)

    def _load_from_environment(self) -> UserOverrides:
        """Load configuration from environment variables."""
        env_config: dict[str, Any] = {}
        prefix = "CODEMARSHAL_"

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            clean_key = key[len(prefix) :].lower()

            # Parse boolean values
            if value.lower() in ("1", "true", "yes", "on"):
                env_config[clean_key] = True
            elif value.lower() in ("0", "false", "no", "off"):
                env_config[clean_key] = False
            else:
                # Try numeric types
                try:
                    env_config[clean_key] = int(value)
                except ValueError:
                    try:
                        env_config[clean_key] = float(value)
                    except ValueError:
                        env_config[clean_key] = value

        return from_config_file(env_config)

    def _merge_overrides(
        self, base: UserOverrides, override: UserOverrides
    ) -> UserOverrides:
        """Merge two UserOverrides objects (override takes precedence)."""
        # Start with base values
        merged_data: dict[str, Any] = {}

        # Copy non-None values from base
        for field_obj in fields(base):
            field_name = field_obj.name
            base_value = getattr(base, field_name)
            if base_value is not None:
                merged_data[field_name] = base_value

        # Override with non-None values from override
        for field_obj in fields(override):
            field_name = field_obj.name
            override_value = getattr(override, field_name)
            if override_value is not None:
                merged_data[field_name] = override_value

        return UserOverrides(**merged_data)

    def _build_config(self) -> Config:
        """Build final immutable Config from defaults and overrides."""
        if self._user_overrides is None:
            self._user_overrides = UserOverrides()

        # Validate user overrides
        validate_and_raise(self._user_overrides)

        # Determine config source
        config_source = self._determine_config_source()

        # Build global config
        global_config = self._build_global_config()

        # Get command type
        command = self._user_overrides.command or CommandType.WITNESS

        # Build command-specific configs
        command_configs = self._build_command_configs(global_config)

        # Create final config
        config = Config(
            global_config=global_config,
            command=command,
            witness=command_configs.get("witness"),
            investigate=command_configs.get("investigate"),
            ask=command_configs.get("ask"),
            patterns=command_configs.get("patterns"),
            export=command_configs.get("export"),
            config_source=config_source,
            config_version=self._defaults.CONFIG_VERSION,
        )

        # Final validation
        self._validate_final_config(config)

        # Store for debugging
        self._merged_config = config

        return config

    def _determine_config_source(self) -> str:
        """Determine where config came from."""
        if self._user_overrides is None:
            return "defaults"

        if self._user_overrides.config_file:
            return f"file:{self._user_overrides.config_file}"

        # Check if any non-default values are set
        default_user = UserOverrides()
        has_user_settings = False

        for field_obj in fields(default_user):
            field_name = field_obj.name
            if field_name == "config_file":
                continue

            user_value = getattr(self._user_overrides, field_name)
            default_value = getattr(default_user, field_name)

            if user_value != default_value:
                has_user_settings = True
                break

        if has_user_settings:
            return "cli"

        return "defaults"

    def _build_global_config(self) -> GlobalConfig:
        """Build global configuration from defaults and overrides."""
        # Start with system defaults using proper typing
        defaults_obj = SystemDefaults()
        defaults_dict: dict[str, Any] = {}

        # Copy with explicit type casting
        defaults_dict.update(getattr(defaults_obj, "GLOBAL_DEFAULTS", {}))

        # Apply user overrides
        if self._user_overrides is not None:
            # Map UserOverrides fields to GlobalConfig fields
            field_mapping = {
                "verbose": "verbose",
                "quiet": "quiet",
                "color": "color",
                "no_color": "no_color",
                "max_workers": "max_workers",
                "cache_dir": "cache_dir",
                "no_cache": "no_cache",
                "force_refresh": "force_refresh",
                "max_total_size_mb": "max_total_size_mb",
                "max_file_count": "max_file_count",
                "max_recursion_depth": "max_recursion_depth",
                "timeout_seconds": "timeout_seconds",
                "check_rules": "check_rules",
                "skip_rules": "skip_rules",
                "enable_experimental": "enable_experimental",
                "enable_network": "enable_network",
                "enable_inference": "enable_inference",
                "output_file": "output_file",
                "append_output": "append_output",
            }

            for user_field, config_field in field_mapping.items():
                user_value = getattr(self._user_overrides, user_field, None)
                if user_value is not None:
                    # Special handling for Path fields
                    if config_field in ("cache_dir", "output_file"):
                        defaults_dict[config_field] = (
                            Path(user_value) if user_value else None
                        )
                    else:
                        defaults_dict[config_field] = user_value

        # Enforce constitutional constraints
        defaults_dict["enable_network"] = False
        defaults_dict["enable_inference"] = False

        # Handle color/no_color contradiction
        if defaults_dict.get("no_color", False):
            defaults_dict["color"] = False

        # Remove None values for constructor
        constructor_args: dict[str, Any] = {
            k: v for k, v in defaults_dict.items() if v is not None
        }

        return GlobalConfig(**constructor_args)

    def _build_command_configs(self, global_config: GlobalConfig) -> dict[str, Any]:
        """Build command-specific configurations."""
        configs: dict[str, Any] = {}

        if self._user_overrides is None:
            return configs

        # Witness config
        if self._user_overrides.witness:
            witness_user = self._user_overrides.witness
            defaults_obj = SystemDefaults()
            witness_defaults: dict[str, Any] = getattr(
                defaults_obj, "WITNESS_DEFAULTS", {}
            )

            path = witness_user.path or global_config.cache_dir / "witness"

            configs["witness"] = WitnessConfig(
                path=Path(path),
                output_format=witness_user.output_format
                or witness_defaults.get("output_format", OutputFormat.BOTH),
                include_hidden=witness_user.include_hidden
                if witness_user.include_hidden is not None
                else witness_defaults.get("include_hidden", False),
                max_file_size_mb=witness_user.max_file_size_mb
                or witness_defaults.get("max_file_size_mb", 10),
                follow_symlinks=witness_user.follow_symlinks
                if witness_user.follow_symlinks is not None
                else witness_defaults.get("follow_symlinks", False),
                exclude_patterns=witness_user.exclude_patterns
                or witness_defaults.get("exclude_patterns", []),
                only_python=witness_user.only_python
                if witness_user.only_python is not None
                else witness_defaults.get("only_python", True),
                skip_binary=witness_user.skip_binary
                if witness_user.skip_binary is not None
                else witness_defaults.get("skip_binary", True),
                detect_encoding=witness_user.detect_encoding
                if witness_user.detect_encoding is not None
                else witness_defaults.get("detect_encoding", True),
                record_checksums=witness_user.record_checksums
                if witness_user.record_checksums is not None
                else witness_defaults.get("record_checksums", True),
            )

        # Investigate config
        if self._user_overrides.investigate:
            investigate_user = self._user_overrides.investigate
            defaults_obj = SystemDefaults()
            investigate_defaults: dict[str, Any] = getattr(
                defaults_obj, "INVESTIGATE_DEFAULTS", {}
            )

            path = investigate_user.path or global_config.cache_dir / "investigate"

            configs["investigate"] = InvestigateConfig(
                path=Path(path),
                focus=investigate_user.focus,
                rule=investigate_user.rule,
                depth=investigate_user.depth or investigate_defaults.get("depth", 3),
                check_constitutional=investigate_user.check_constitutional
                if investigate_user.check_constitutional is not None
                else investigate_defaults.get("check_constitutional", True),
                check_imports=investigate_user.check_imports
                if investigate_user.check_imports is not None
                else investigate_defaults.get("check_imports", True),
                check_boundaries=investigate_user.check_boundaries
                if investigate_user.check_boundaries is not None
                else investigate_defaults.get("check_boundaries", True),
                boundary_strictness=investigate_user.boundary_strictness
                or investigate_defaults.get(
                    "boundary_strictness", BoundaryStrictness.STRICT
                ),
            )

        # Ask config
        if self._user_overrides.ask:
            ask_user = self._user_overrides.ask
            configs["ask"] = AskConfig(
                path=Path(ask_user.path or global_config.cache_dir / "ask"),
                question=ask_user.question,
                question_type=ask_user.question_type,
                about=ask_user.about,
                relation=ask_user.relation,
                metric=ask_user.metric,
            )

        # Patterns config
        if self._user_overrides.patterns:
            patterns_user = self._user_overrides.patterns
            configs["patterns"] = PatternsConfig(
                path=Path(patterns_user.path or global_config.cache_dir / "patterns"),
                pattern_type=patterns_user.pattern_type,
                min_threshold=patterns_user.min_threshold,
                max_threshold=patterns_user.max_threshold,
                window_size=patterns_user.window_size or 10,
                include_uncertainty=patterns_user.include_uncertainty
                if patterns_user.include_uncertainty is not None
                else True,
            )

        # Export config
        if self._user_overrides.export:
            export_user = self._user_overrides.export
            configs["export"] = ExportConfig(
                investigation_id=export_user.investigation_id,
                format=export_user.format or OutputFormat.MARKDOWN,
                output_path=Path(export_user.output_path)
                if export_user.output_path
                else None,
                include_evidence=export_user.include_evidence
                if export_user.include_evidence is not None
                else True,
                include_notes=export_user.include_notes
                if export_user.include_notes is not None
                else True,
                export_all=export_user.export_all or False,
                export_summary=export_user.export_summary or True,
                export_raw=export_user.export_raw or False,
            )

        return configs

    def _validate_final_config(self, config: Config) -> None:
        """Final validation of the built config."""
        # Validate contradictions
        if config.global_config.verbose and config.global_config.quiet:
            from .schema import ConfigValidationError

            raise ConfigValidationError(
                "Contradiction: cannot be both verbose and quiet",
                field="global_config.verbose/quiet",
                rule="verbosity_contradiction",
            )

        # Validate path exists (if not using defaults)
        if config.witness and config.witness.path and not config.witness.path.exists():
            from .schema import ConfigValidationError

            raise ConfigValidationError(
                f"Witness path does not exist: {config.witness.path}",
                field="witness.path",
                rule="path_exists",
            )


def load_config(cli_args: dict[str, Any] | None = None) -> Config:
    """
    Main entry point for loading configuration.

    Args:
        cli_args: Dictionary of CLI arguments, typically from argparse

    Returns:
        Immutable, validated Config object

    Raises:
        ConfigValidationError: If configuration violates constitutional rules
        FileNotFoundError: If specified config file doesn't exist
        ValueError: For invalid configuration values
    """
    loader = ConfigLoader()

    if cli_args:
        return loader.load_from_cli(cli_args)

    # Check for default config file
    default_config = Path.home() / ".codemarshal" / "config.yaml"
    if default_config.exists():
        return loader.load_from_file(default_config)

    # Fall back to system defaults
    return loader.load_defaults()


def get_default_config() -> Config:
    """Get configuration with only system defaults."""
    loader = ConfigLoader()
    return loader.load_defaults()


def get_active_config(cli_args: dict[str, Any] | None = None) -> Config:
    """Backward-compatible alias for load_config."""
    return load_config(cli_args)


__all__ = [
    "Config",
    "GlobalConfig",
    "WitnessConfig",
    "InvestigateConfig",
    "AskConfig",
    "PatternsConfig",
    "ExportConfig",
    "ConfigLoader",
    "load_config",
    "get_default_config",
    "get_active_config",
]
