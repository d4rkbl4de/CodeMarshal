"""
config/boundaries.py — Boundary Definition Loader

Loads and validates boundary definitions for constitutional analysis.
Supports loading from YAML configuration files for Agent Nexus and other systems.
"""

# Import BoundaryDefinition from observations
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Add observations to path for import
sys.path.insert(0, str(Path(__file__).parent.parent))

from observations.eyes.boundary_sight import BoundaryDefinition, BoundaryType


@dataclass
class BoundaryConfig:
    """Complete boundary configuration loaded from file."""

    project_name: str
    architecture: str
    constitutional_rules: list[str] = field(default_factory=list)
    boundary_definitions: list[BoundaryDefinition] = field(default_factory=list)
    boundary_strictness: str = "strict"
    enabled_eyes: list[str] = field(default_factory=list)
    detect_circular: bool = True
    report_crossings: bool = True

    @property
    def has_boundaries(self) -> bool:
        """Check if any boundaries are defined."""
        return len(self.boundary_definitions) > 0

    @property
    def uses_boundary_sight(self) -> bool:
        """Check if boundary_sight is enabled."""
        return "boundary_sight" in self.enabled_eyes


class BoundaryConfigLoader:
    """Loads boundary configurations from YAML files."""

    def __init__(self):
        self._type_map = {
            "layer": BoundaryType.LAYER,
            "package": BoundaryType.PACKAGE,
            "module": BoundaryType.MODULE,
            "external": BoundaryType.EXTERNAL,
            "custom": BoundaryType.CUSTOM,
        }

    def load_from_file(self, config_path: Path) -> BoundaryConfig:
        """
        Load boundary configuration from a YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            BoundaryConfig object with loaded definitions

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Boundary config not found: {config_path}")

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse config file: {e}") from e

        if not config_data:
            raise ValueError(f"Config file is empty: {config_path}")

        return self._parse_config(config_data, config_path)

    def _parse_config(self, data: dict[str, Any], source_path: Path) -> BoundaryConfig:
        """Parse configuration data into BoundaryConfig."""
        project = data.get("project", {})
        constitutional = data.get("constitutional", {})
        observations = data.get("observations", {})
        boundaries_data = data.get("boundaries", [])

        # Extract project info
        project_name = project.get("name", "Unknown Project")
        architecture = project.get("architecture", "Unknown")

        # Extract constitutional rules
        rules = constitutional.get("rules", [])
        strictness = constitutional.get("boundary_strictness", "strict")

        # Extract observation settings
        enabled_eyes = observations.get("enabled_eyes", [])
        boundary_detection = observations.get("boundary_detection", {})
        detect_circular = boundary_detection.get("detect_circular", True)
        report_crossings = boundary_detection.get("report_crossings", True)

        # Parse boundary definitions
        boundary_definitions = self._parse_boundaries(boundaries_data)

        return BoundaryConfig(
            project_name=project_name,
            architecture=architecture,
            constitutional_rules=rules,
            boundary_definitions=boundary_definitions,
            boundary_strictness=strictness,
            enabled_eyes=enabled_eyes,
            detect_circular=detect_circular,
            report_crossings=report_crossings,
        )

    def _parse_boundaries(
        self, boundaries_data: list[dict[str, Any]]
    ) -> list[BoundaryDefinition]:
        """Parse boundary definitions from config data."""
        definitions: list[BoundaryDefinition] = []

        for boundary_data in boundaries_data:
            try:
                definition = self._parse_single_boundary(boundary_data)
                definitions.append(definition)
            except Exception as e:
                # Log warning but continue
                print(f"Warning: Failed to parse boundary: {e}")
                continue

        return definitions

    def _parse_single_boundary(self, data: dict[str, Any]) -> BoundaryDefinition:
        """Parse a single boundary definition."""
        name = data.get("name")
        if not name:
            raise ValueError("Boundary must have a 'name' field")

        boundary_type_str = data.get("type", "custom")
        boundary_type = self._type_map.get(
            boundary_type_str.lower(), BoundaryType.CUSTOM
        )

        pattern = data.get("pattern", "")
        if not pattern:
            raise ValueError(f"Boundary '{name}' must have a 'pattern' field")

        description = data.get("description", "")

        # Parse allowed_targets
        allowed_targets = data.get("allowed_targets", [])
        if not isinstance(allowed_targets, list):
            allowed_targets = [str(allowed_targets)]

        # Check if prohibited (default: True)
        prohibited = data.get("prohibited", True)

        # Handle prohibited_from (for readability in config)
        if "prohibited_from" in data:
            # This is just documentation in the config, doesn't affect the boundary definition
            pass

        return BoundaryDefinition(
            name=name,
            boundary_type=boundary_type,
            pattern=pattern,
            description=description,
            allowed_targets=tuple(allowed_targets),
            prohibited=prohibited,
        )


def load_boundary_config(config_path: Path) -> BoundaryConfig:
    """
    Convenience function to load boundary configuration.

    Args:
        config_path: Path to the configuration file

    Returns:
        BoundaryConfig object
    """
    loader = BoundaryConfigLoader()
    return loader.load_from_file(config_path)


def find_config_file(
    custom_path: Path | None = None, project_root: Path | None = None
) -> Path | None:
    """
    Find a boundary configuration file.

    Search order:
    1. Custom path (if provided)
    2. project_root/config/agent_nexus.yaml
    3. project_root/.codemarshal.yaml
    4. Current directory config files

    Args:
        custom_path: Explicit path to config file
        project_root: Root directory of the project

    Returns:
        Path to config file if found, None otherwise
    """
    if custom_path and custom_path.exists():
        return custom_path

    # Determine project root
    if not project_root:
        project_root = Path.cwd()

    # Search for common config file names
    search_paths = [
        project_root / "config" / "agent_nexus.yaml",
        project_root / "config" / "boundaries.yaml",
        project_root / ".codemarshal.yaml",
        project_root / ".codemarshal.yml",
        project_root / "codemarshal.yaml",
        project_root / "codemarshal.yml",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def get_agent_nexus_config(project_root: Path | None = None) -> BoundaryConfig | None:
    """
    Try to load Agent Nexus boundary configuration.

    Args:
        project_root: Root directory of the project

    Returns:
        BoundaryConfig if found and loaded successfully, None otherwise
    """
    config_path = find_config_file(project_root=project_root)

    if not config_path:
        return None

    try:
        return load_boundary_config(config_path)
    except Exception as e:
        print(f"Warning: Failed to load boundary config from {config_path}: {e}")
        return None


__all__ = [
    "BoundaryConfig",
    "BoundaryConfigLoader",
    "load_boundary_config",
    "find_config_file",
    "get_agent_nexus_config",
]
