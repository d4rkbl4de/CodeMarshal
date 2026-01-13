"""
config/schema.py — VALIDATION & CONSTITUTIONAL FILTER
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from pathlib import Path
import re

from .user import (
    UserOverrides, WitnessCommand, InvestigateCommand, 
    CommandType
)


@dataclass
class ValidationError:
    """A configuration validation error (data class, not exception)."""
    message: str
    field: str = ""
    rule: str = ""
    
    def __str__(self) -> str:
        if self.field:
            return f"{self.field}: {self.message}"
        return self.message


class ConfigValidationError(Exception):
    """Exception raised for configuration validation failures."""
    def __init__(self, message: str, field: str = "", rule: str = ""):
        self.message = message
        self.field = field
        self.rule = rule
        super().__init__(f"{field}: {message}" if field else message)


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    errors: List[ValidationError] = field(default_factory=lambda: [])
    constitutional_violations: List[ValidationError] = field(default_factory=lambda: [])
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0 and len(self.constitutional_violations) == 0
    
    def add_error(self, message: str, field: str = "", rule: str = "") -> None:
        self.errors.append(ValidationError(message, field, rule))
    
    def add_constitutional_violation(self, message: str, field: str = "", rule: str = "") -> None:
        self.constitutional_violations.append(ValidationError(message, field, rule))


class ConfigSchema:
    """Constitutional validator for configuration."""
    
    def __init__(self) -> None:
        # Constitutional rules (Tier 1 violations)
        self.constitutional_rules = {
            "no_network": "Network access is constitutionally prohibited (Article 12)",
            "no_inference": "Inference is constitutionally prohibited (Article 1)",
            "no_mutation": "Mutation of observations is prohibited (Article 9)",
        }
        
        # Field constraints
        self.field_constraints = {
            "max_recursion_depth": (1, 50),
            "max_total_size_mb": (1, 5000),
            "max_file_count": (1, 50000),
            "max_workers": (1, 64),
            "timeout_seconds": (1, 3600),
            "max_file_size_mb": (0, 100),
        }
        
        # Pattern validation
        self.patterns = {
            "path": r'^[^<>:"|?*]{1,4096}$',  # Basic path validation
            "investigation_id": r'^[a-zA-Z0-9_-]{1,100}$',
            "exclude_pattern": r'^[^*?"<>|]*$',  # Safe glob pattern
        }
    
    def validate_user_overrides(self, overrides: UserOverrides) -> ValidationResult:
        """Validate user configuration overrides."""
        result = ValidationResult()
        
        # Constitutional validation
        self._validate_constitutional(overrides, result)
        
        # Field type validation
        self._validate_field_types(overrides, result)
        
        # Command-specific validation
        if overrides.command:
            self._validate_command(overrides, result)
        
        # Cross-field validation
        self._validate_cross_field(overrides, result)
        
        return result
    
    def validate_cli_args(self, cli_args: Dict[str, Any]) -> ValidationResult:
        """Validate raw CLI arguments."""
        result = ValidationResult()
        
        # Check for constitutional violations in CLI args
        if cli_args.get('enable_network', False):
            result.add_constitutional_violation(
                self.constitutional_rules["no_network"],
                field="enable_network",
                rule="no_network"
            )
        
        if cli_args.get('enable_inference', False):
            result.add_constitutional_violation(
                self.constitutional_rules["no_inference"],
                field="enable_inference",
                rule="no_inference"
            )
        
        # Validate field values
        for field_name, (min_val, max_val) in self.field_constraints.items():
            if field_name in cli_args:
                value = cli_args[field_name]
                if not isinstance(value, (int, float)):
                    result.add_error(
                        f"{field_name} must be a number",
                        field=field_name,
                        rule="type_mismatch"
                    )
                elif value < min_val or value > max_val:
                    result.add_error(
                        f"{field_name} must be between {min_val} and {max_val}",
                        field=field_name,
                        rule="range_violation"
                    )
        
        # Check contradictions
        if cli_args.get('verbose', False) and cli_args.get('quiet', False):
            result.add_error(
                "Cannot be both verbose and quiet",
                field="verbose/quiet",
                rule="contradiction"
            )
        
        if cli_args.get('color', False) and cli_args.get('no_color', False):
            result.add_error(
                "Cannot specify both color and no_color",
                field="color/no_color",
                rule="contradiction"
            )
        
        return result
    
    def _validate_constitutional(self, overrides: UserOverrides, result: ValidationResult) -> None:
        """Validate constitutional constraints."""
        # Network access is prohibited
        if overrides.enable_network:
            result.add_constitutional_violation(
                self.constitutional_rules["no_network"],
                field="enable_network",
                rule="no_network"
            )
        
        # Inference is prohibited
        if overrides.enable_inference:
            result.add_constitutional_violation(
                self.constitutional_rules["no_inference"],
                field="enable_inference",
                rule="no_inference"
            )
        
        # Check for mutation permissions (if any exist in future)
        if hasattr(overrides, 'allow_mutation') and getattr(overrides, 'allow_mutation', False):
            result.add_constitutional_violation(
                self.constitutional_rules["no_mutation"],
                field="allow_mutation",
                rule="no_mutation"
            )
    
    def _validate_field_types(self, overrides: UserOverrides, result: ValidationResult) -> None:
        """Validate field types and basic constraints."""
        # Validate numeric fields
        for field_name, (min_val, max_val) in self.field_constraints.items():
            value = getattr(overrides, field_name, None)
            if value is not None:
                if not isinstance(value, (int, float)):
                    result.add_error(
                        f"{field_name} must be a number, got {type(value).__name__}",
                        field=field_name,
                        rule="type_mismatch"
                    )
                elif value < min_val or value > max_val:
                    result.add_error(
                        f"{field_name} must be between {min_val} and {max_val}",
                        field=field_name,
                        rule="range_violation"
                    )
        
        # Validate boolean fields
        boolean_fields = ['verbose', 'quiet', 'color', 'no_color', 'no_cache', 
                         'force_refresh', 'enable_experimental', 'enable_network',
                         'enable_inference', 'append_output']
        
        for field_name in boolean_fields:
            value = getattr(overrides, field_name, None)
            if value is not None and not isinstance(value, bool):
                result.add_error(
                    f"{field_name} must be a boolean",
                    field=field_name,
                    rule="type_mismatch"
                )
        
        # Validate path fields - simplified since types are already checked
        path_fields = ['cache_dir', 'output_file']
        for field_name in path_fields:
            value = getattr(overrides, field_name, None)
            if value is not None:
                # For string paths, try to convert to Path
                if isinstance(value, str):
                    try:
                        Path(value)
                    except Exception:
                        result.add_error(
                            f"{field_name} must be a valid path",
                            field=field_name,
                            rule="invalid_path"
                        )
                # For Path objects, no conversion needed
    
    def _validate_command(self, overrides: UserOverrides, result: ValidationResult) -> None:
        """Validate command-specific configuration."""
        if overrides.command == CommandType.WITNESS and overrides.witness:
            self._validate_witness(overrides.witness, result)
        elif overrides.command == CommandType.INVESTIGATE and overrides.investigate:
            self._validate_investigate(overrides.investigate, result)
        elif overrides.command == CommandType.EXPORT and overrides.export:
            self._validate_export(overrides.export, result)
    
    def _validate_witness(self, witness: WitnessCommand, result: ValidationResult) -> None:
        """Validate witness command configuration."""
        if witness.path is not None:
            # Path validation - we know it's either Path or None from the type
            try:
                path_obj = witness.path  # Already a Path from type annotation
                # Check if path is absolute (not required, but good to know)
                if not path_obj.is_absolute():
                    # It's okay, just a relative path
                    pass
            except Exception as e:
                result.add_error(
                    f"Invalid witness path: {e}",
                    field="witness.path",
                    rule="invalid_path"
                )
        
        if witness.max_file_size_mb is not None:
            if witness.max_file_size_mb < 0 or witness.max_file_size_mb > 100:
                result.add_error(
                    "witness.max_file_size_mb must be between 0 and 100",
                    field="witness.max_file_size_mb",
                    rule="range_violation"
                )
        
        if witness.exclude_patterns is not None:
            # Type is guaranteed by dataclass to be Optional[List[str]]
            # We only need to validate the content, not the type
            # Check each pattern
            for i, pattern in enumerate(witness.exclude_patterns):
                # Type is guaranteed to be str by List[str]
                if not re.match(self.patterns["exclude_pattern"], pattern):
                    result.add_error(
                        f"witness.exclude_patterns[{i}] contains invalid characters",
                        field=f"witness.exclude_patterns[{i}]",
                        rule="invalid_pattern"
                    )
    
    def _validate_investigate(self, investigate: InvestigateCommand, result: ValidationResult) -> None:
        """Validate investigate command configuration."""
        if investigate.depth is not None:
            if investigate.depth < 0 or investigate.depth > 50:
                result.add_error(
                    "investigate.depth must be between 0 and 50",
                    field="investigate.depth",
                    rule="range_violation"
                )
    
    def _validate_export(self, export: Any, result: ValidationResult) -> None:
        """Validate export command configuration."""
        # This is a stub - actual validation would depend on ExportCommand structure
        if hasattr(export, 'investigation_id') and export.investigation_id:
            if not re.match(self.patterns["investigation_id"], export.investigation_id):
                result.add_error(
                    "export.investigation_id must contain only alphanumeric characters, dashes, and underscores",
                    field="export.investigation_id",
                    rule="pattern_mismatch"
                )
    
    def _validate_cross_field(self, overrides: UserOverrides, result: ValidationResult) -> None:
        """Validate cross-field dependencies and contradictions."""
        # Verbose and quiet cannot both be True
        if overrides.verbose and overrides.quiet:
            result.add_error(
                "Cannot be both verbose and quiet",
                field="verbose/quiet",
                rule="contradiction"
            )
        
        # Color and no_color cannot both be True
        if overrides.color and overrides.no_color:
            result.add_error(
                "Cannot specify both color and no_color",
                field="color/no_color",
                rule="contradiction"
            )
        
        # Check rules should not overlap with skip rules
        if overrides.check_rules and overrides.skip_rules:
            check_set = set(overrides.check_rules)
            skip_set = set(overrides.skip_rules)
            overlap = check_set.intersection(skip_set)
            if overlap:
                result.add_error(
                    f"Rules cannot be both checked and skipped: {', '.join(overlap)}",
                    field="check_rules/skip_rules",
                    rule="overlap"
                )


def validate_and_raise(overrides: UserOverrides) -> None:
    """Validate user overrides and raise ConfigValidationError if invalid."""
    schema = ConfigSchema()
    result = schema.validate_user_overrides(overrides)
    
    all_errors = result.errors + result.constitutional_violations
    
    if all_errors:
        error_messages = [str(error) for error in all_errors]
        raise ConfigValidationError(
            f"Configuration validation failed with {len(all_errors)} error(s):\n" +
            "\n".join(f"  - {msg}" for msg in error_messages[:10])
        )


__all__ = [
    "ConfigSchema",
    "ValidationError",
    "ConfigValidationError",
    "ValidationResult",
    "validate_and_raise",
]