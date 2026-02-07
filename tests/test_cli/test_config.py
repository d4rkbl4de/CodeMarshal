"""
tests/test_cli/test_config.py - Tests for config CLI command
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from bridge.commands.config import (
    ConfigEditCommand,
    ConfigResetCommand,
    ConfigShowCommand,
    ConfigValidateCommand,
)


class TestConfigShowCommand:
    """Test config show command."""

    def test_show_default_config(self):
        """Test showing default configuration."""
        cmd = ConfigShowCommand()
        result = cmd.execute()

        assert result.success is True
        assert "version" in result.config
        assert result.config_path is not None

    def test_show_with_yaml_format(self):
        """Test showing config in YAML format."""
        cmd = ConfigShowCommand()
        result = cmd.execute(format="yaml")

        assert result.success is True
        assert "version" in result.formatted_output

    def test_show_with_json_format(self):
        """Test showing config in JSON format."""
        cmd = ConfigShowCommand()
        result = cmd.execute(format="json")

        assert result.success is True
        assert (
            '"version"' in result.formatted_output
            or "version" in result.formatted_output
        )

    def test_show_with_custom_config(self):
        """Test showing custom config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config = {"version": "1.0.0", "test": True}
            yaml.dump(config, f)
            temp_path = Path(f.name)

        try:
            cmd = ConfigShowCommand()
            result = cmd.execute(path=temp_path)

            assert result.success is True
            assert result.config["test"] is True
        finally:
            temp_path.unlink()

    def test_mask_secrets(self):
        """Test that secrets are masked."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config = {"password": "secret123", "api_key": "key123", "normal": "value"}
            yaml.dump(config, f)
            temp_path = Path(f.name)

        try:
            cmd = ConfigShowCommand()
            result = cmd.execute(path=temp_path, show_secrets=False)

            assert result.success is True
            assert result.config["password"] == "********"
            assert result.config["api_key"] == "********"
            assert result.config["normal"] == "value"
        finally:
            temp_path.unlink()


class TestConfigResetCommand:
    """Test config reset command."""

    def test_reset_creates_default_config(self):
        """Test that reset creates default config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("old: config")
            temp_path = Path(f.name)

        try:
            cmd = ConfigResetCommand()
            result = cmd.execute(path=temp_path, confirm=True)

            assert result.success is True
            assert temp_path.exists()

            # Verify it's been reset to defaults
            with open(temp_path) as f:
                config = yaml.safe_load(f)
            assert "version" in config
            assert "old" not in config
        finally:
            temp_path.unlink()

    def test_reset_creates_backup(self):
        """Test that reset creates backup."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("old: config")
            temp_path = Path(f.name)

        try:
            cmd = ConfigResetCommand()
            result = cmd.execute(path=temp_path, confirm=True, create_backup=True)

            assert result.success is True
            assert result.backup_path is not None
            assert result.backup_path.exists()
        finally:
            temp_path.unlink()
            if result.backup_path and result.backup_path.exists():
                result.backup_path.unlink()


class TestConfigValidateCommand:
    """Test config validate command."""

    def test_validate_valid_config(self):
        """Test validating a valid config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config = {"version": "1.0.0"}
            yaml.dump(config, f)
            temp_path = Path(f.name)

        try:
            cmd = ConfigValidateCommand()
            result = cmd.execute(path=temp_path)

            assert result.success is True
            assert len(result.errors) == 0
        finally:
            temp_path.unlink()

    def test_validate_missing_version(self):
        """Test validating config missing version."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config = {"other": "value"}
            yaml.dump(config, f)
            temp_path = Path(f.name)

        try:
            cmd = ConfigValidateCommand()
            result = cmd.execute(path=temp_path)

            assert result.success is False
            assert any("version" in e.lower() for e in result.errors)
        finally:
            temp_path.unlink()

    def test_validate_invalid_yaml(self):
        """Test validating invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: :::")
            temp_path = Path(f.name)

        try:
            cmd = ConfigValidateCommand()
            result = cmd.execute(path=temp_path)

            assert result.success is False
            assert len(result.errors) > 0
        finally:
            temp_path.unlink()


class TestConfigCommandsIntegration:
    """Integration tests for config commands."""

    def test_full_config_workflow(self):
        """Test full config workflow: show -> validate -> reset -> validate."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Show (should use defaults since file is empty)
            show_cmd = ConfigShowCommand()
            show_result = show_cmd.execute(path=temp_path)
            assert show_result.success is True

            # Reset
            reset_cmd = ConfigResetCommand()
            reset_result = reset_cmd.execute(path=temp_path, confirm=True)
            assert reset_result.success is True

            # Validate
            validate_cmd = ConfigValidateCommand()
            validate_result = validate_cmd.execute(path=temp_path)
            assert validate_result.success is True

        finally:
            temp_path.unlink()
