"""
bridge.commands.config - Configuration management commands

This module provides CLI commands for managing CodeMarshal configuration.

Commands:
- config show: Display current configuration
- config edit: Edit configuration in external editor
- config reset: Reset configuration to defaults
- config validate: Validate configuration structure
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ConfigResult:
    """Base result for config commands."""

    success: bool
    message: str = ""
    error: str | None = None


@dataclass
class ConfigShowResult(ConfigResult):
    """Result of config show command."""

    config: dict = field(default_factory=dict)
    config_path: Path | None = None
    formatted_output: str = ""


@dataclass
class ConfigEditResult(ConfigResult):
    """Result of config edit command."""

    config_path: Path | None = None
    backup_path: Path | None = None
    editor_used: str = ""
    validated: bool = False
    backup_restored: bool = False


@dataclass
class ConfigResetResult(ConfigResult):
    """Result of config reset command."""

    config_path: Path | None = None
    backup_path: Path | None = None


@dataclass
class ConfigValidateResult(ConfigResult):
    """Result of config validate command."""

    config_path: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    valid_count: int = 0
    rule_count: int = 0


class ConfigShowCommand:
    """Display current configuration."""

    def execute(
        self,
        path: Path | None = None,
        format: str = "yaml",
        show_secrets: bool = False,
    ) -> ConfigShowResult:
        """
        Execute config show command.

        Args:
            path: Optional path to config file
            format: Output format (yaml/json)
            show_secrets: Whether to show sensitive values

        Returns:
            ConfigShowResult with formatted output
        """
        config_path = path or self._get_default_config_path()

        # Load configuration
        config = self._load_config(config_path)

        # Mask secrets if not requested
        if not show_secrets:
            config = self._mask_secrets(config)

        # Format output
        if format == "json":
            import json

            formatted_output = json.dumps(config, indent=2)
        else:
            formatted_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True
            )

        return ConfigShowResult(
            success=True,
            config=config,
            formatted_output=formatted_output,
            config_path=config_path,
            message=f"Configuration loaded from {config_path}",
        )

    def _get_default_config_path(self) -> Path:
        """Get the default configuration path."""
        # Check environment variable
        env_path = os.environ.get("CODEMARSHAL_CONFIG")
        if env_path:
            return Path(env_path)

        # Check user-level config
        user_config = Path.home() / ".config" / "codemarshal" / "config.yaml"

        return user_config

    def _load_config(self, path: Path) -> dict:
        """Load configuration from file."""
        if not path.exists():
            return self._get_default_config()

        try:
            with open(path) as f:
                config = yaml.safe_load(f)
                return config if config else self._get_default_config()
        except Exception:
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            "version": "1.0.0",
            "constitutional_rules": [],
            "boundaries": {
                "include": ["src/", "lib/", "packages/"],
                "exclude": ["**/node_modules/", "**/.git/", "**/__pycache__/"],
            },
            "settings": {
                "auto_backup": True,
                "max_cache_size_mb": 1024,
                "parallel_analysis": True,
                "max_workers": 4,
            },
            "export": {
                "default_format": "markdown",
                "include_patterns": True,
                "include_notes": True,
            },
            "ui": {
                "colors": True,
                "progress_style": "rich",
            },
        }

    def _mask_secrets(self, config: dict) -> dict:
        """Mask sensitive configuration values."""
        import copy

        masked = copy.deepcopy(config)

        # Define sensitive keys
        secret_patterns = [
            "password",
            "secret",
            "api_key",
            "token",
            "credential",
            "auth",
            "private_key",
            "passphrase",
        ]

        def mask_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    key_lower = key.lower()
                    if any(pattern in key_lower for pattern in secret_patterns):
                        obj[key] = "********"
                    else:
                        mask_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    mask_recursive(item)

        mask_recursive(masked)
        return masked


class ConfigEditCommand:
    """Edit configuration in external editor."""

    def execute(
        self,
        path: Path | None = None,
        editor: str | None = None,
    ) -> ConfigEditResult:
        """
        Execute config edit command.

        Args:
            path: Optional path to config file
            editor: Editor to use (defaults to $EDITOR or vi)

        Returns:
            ConfigEditResult with edit status
        """
        config_path = path or self._get_default_config_path()

        # Ensure config file exists
        if not config_path.exists():
            self._create_default_config(config_path)

        # Get editor
        editor = editor or os.environ.get("EDITOR", "vi")

        # Validate editor exists
        editor_path = shutil.which(editor)
        if not editor_path:
            return ConfigEditResult(
                success=False,
                error=f"Editor '{editor}' not found. Set $EDITOR or use --editor flag.",
            )

        # Create backup before editing
        backup_path = config_path.with_suffix(config_path.suffix + ".backup")
        shutil.copy2(config_path, backup_path)

        # Open editor
        try:
            subprocess.run(
                [editor, str(config_path)],
                check=True,
                env={**os.environ, "VISUAL": editor},
            )
        except subprocess.CalledProcessError as e:
            return ConfigEditResult(
                success=False,
                error=f"Editor exited with error: {e}",
            )
        except KeyboardInterrupt:
            # User cancelled, restore backup
            shutil.copy2(backup_path, config_path)
            return ConfigEditResult(
                success=False,
                error="Edit cancelled by user",
                backup_restored=True,
            )

        # Validate edited config
        validation_result = ConfigValidateCommand().execute(path=config_path)

        if not validation_result.success:
            # Restore backup if invalid
            shutil.copy2(backup_path, config_path)
            return ConfigEditResult(
                success=False,
                error="Configuration validation failed. Backup restored.",
                validation_errors=validation_result.errors,
            )

        return ConfigEditResult(
            success=True,
            config_path=config_path,
            backup_path=backup_path,
            editor_used=editor,
            validated=True,
        )

    def _get_default_config_path(self) -> Path:
        """Get the default configuration path."""
        env_path = os.environ.get("CODEMARSHAL_CONFIG")
        if env_path:
            return Path(env_path)
        return Path.home() / ".config" / "codemarshal" / "config.yaml"

    def _create_default_config(self, path: Path) -> None:
        """Create default configuration file."""
        default_config = ConfigShowCommand()._get_default_config()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)


class ConfigResetCommand:
    """Reset configuration to defaults."""

    def execute(
        self,
        path: Path | None = None,
        confirm: bool = False,
        create_backup: bool = True,
    ) -> ConfigResetResult:
        """
        Execute config reset command.

        Args:
            path: Optional path to config file
            confirm: Skip confirmation if True
            create_backup: Create backup before resetting

        Returns:
            ConfigResetResult with reset status
        """
        config_path = path or self._get_default_config_path()

        if not config_path.exists():
            # Nothing to reset
            return ConfigResetResult(
                success=True,
                message="No configuration file exists. Default configuration will be used.",
                config_path=config_path,
            )

        # Create backup
        backup_path = None
        if create_backup:
            timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = config_path.with_suffix(f".backup_{timestamp}")
            shutil.copy2(config_path, backup_path)

        # Get default configuration
        default_config = ConfigShowCommand()._get_default_config()

        # Write default config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        return ConfigResetResult(
            success=True,
            config_path=config_path,
            backup_path=backup_path,
            message="Configuration reset to defaults",
        )

    def _get_default_config_path(self) -> Path:
        """Get the default configuration path."""
        env_path = os.environ.get("CODEMARSHAL_CONFIG")
        if env_path:
            return Path(env_path)
        return Path.home() / ".config" / "codemarshal" / "config.yaml"


class ConfigValidateCommand:
    """Validate configuration against schema."""

    def execute(
        self,
        path: Path | None = None,
        strict: bool = False,
    ) -> ConfigValidateResult:
        """
        Execute config validate command.

        Args:
            path: Optional path to config file
            strict: Fail on warnings

        Returns:
            ConfigValidateResult with validation status
        """
        config_path = path or self._get_default_config_path()

        if not config_path.exists():
            return ConfigValidateResult(
                success=False,
                errors=["Configuration file not found"],
                config_path=config_path,
            )

        # Load configuration
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            return ConfigValidateResult(
                success=False,
                errors=[f"YAML parsing error: {e}"],
                config_path=config_path,
            )

        errors = []
        warnings = []

        # Validate required fields
        if "version" not in config:
            errors.append("Missing required field: 'version'")

        # Validate rules
        rule_errors = self._validate_rules(config.get("constitutional_rules", []))
        errors.extend(rule_errors)

        # Validate boundaries
        boundary_warnings = self._validate_boundaries(config.get("boundaries", {}))
        warnings.extend(boundary_warnings)

        success = len(errors) == 0 and (len(warnings) == 0 or not strict)

        return ConfigValidateResult(
            success=success,
            errors=errors,
            warnings=warnings,
            config_path=config_path,
            rule_count=len(config.get("constitutional_rules", [])),
        )

    def _get_default_config_path(self) -> Path:
        """Get the default configuration path."""
        env_path = os.environ.get("CODEMARSHAL_CONFIG")
        if env_path:
            return Path(env_path)
        return Path.home() / ".config" / "codemarshal" / "config.yaml"

    def _validate_rules(self, rules: list) -> list[str]:
        """Validate constitutional rule definitions."""
        errors = []
        rule_names = set()

        for i, rule in enumerate(rules):
            rule_id = f"rule[{i}]"

            # Check required fields
            if "name" not in rule:
                errors.append(f"{rule_id}: Missing required 'name' field")
            else:
                name = rule["name"]
                if name in rule_names:
                    errors.append(f"{rule_id}: Duplicate rule name '{name}'")
                rule_names.add(name)

            if "pattern" not in rule:
                errors.append(f"{rule_id}: Missing required 'pattern' field")

        return errors

    def _validate_boundaries(self, boundaries: dict) -> list[str]:
        """Validate boundary definitions."""
        warnings = []

        include = boundaries.get("include", [])
        exclude = boundaries.get("exclude", [])

        # Check for overlapping boundaries
        for inc in include:
            for exc in exclude:
                if inc.startswith(exc) or exc.startswith(inc):
                    warnings.append(f"Boundary overlap detected: '{inc}' and '{exc}'")

        return warnings


# Convenience function for direct execution
def execute_config_show(
    path: Path | None = None,
    format: str = "yaml",
    show_secrets: bool = False,
) -> ConfigShowResult:
    """Convenience function for config show."""
    cmd = ConfigShowCommand()
    return cmd.execute(path=path, format=format, show_secrets=show_secrets)


def execute_config_edit(
    path: Path | None = None,
    editor: str | None = None,
) -> ConfigEditResult:
    """Convenience function for config edit."""
    cmd = ConfigEditCommand()
    return cmd.execute(path=path, editor=editor)


def execute_config_reset(
    path: Path | None = None,
    confirm: bool = False,
    create_backup: bool = True,
) -> ConfigResetResult:
    """Convenience function for config reset."""
    cmd = ConfigResetCommand()
    return cmd.execute(path=path, confirm=confirm, create_backup=create_backup)


def execute_config_validate(
    path: Path | None = None,
    strict: bool = False,
) -> ConfigValidateResult:
    """Convenience function for config validate."""
    cmd = ConfigValidateCommand()
    return cmd.execute(path=path, strict=strict)
