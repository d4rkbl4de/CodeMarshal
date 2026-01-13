"""
config/defaults.py — SYSTEM DEFAULTS (IMMUTABLE LAW)
"""

from typing import Dict, Any, List, FrozenSet
from dataclasses import dataclass, field


from .user import OutputFormat, BoundaryStrictness, CommandType


@dataclass(frozen=True)
class SystemDefaults:
    CONFIG_VERSION: str = "1.0.0"
    
    DEFAULT_CACHE_DIR: str = ".codemarshal"
    CACHE_SUBDIRS: FrozenSet[str] = field(default_factory=lambda: frozenset([
        "witness", "investigate", "patterns", "export", "notes", "sessions"
    ]))
    
    DEFAULT_CONFIG_FILE: str = ".codemarshal.yaml"
    
    MAX_FILE_SIZE_MB: int = 10
    MAX_TOTAL_SIZE_MB: int = 1000
    MAX_FILE_COUNT: int = 10000
    MAX_RECURSION_DEPTH: int = 20
    MAX_WORKERS: int = 4
    MAX_TIMEOUT_SECONDS: int = 300
    
    WITNESS_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "output_format": OutputFormat.BOTH,
        "include_hidden": False,
        "max_file_size_mb": 10,
        "follow_symlinks": False,
        "exclude_patterns": [
            "__pycache__", ".git", ".svn", ".hg", ".DS_Store",
            "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.exe",
        ],
        "only_python": True,
        "skip_binary": True,
        "detect_encoding": True,
        "record_checksums": True,
    })
    
    INVESTIGATE_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "depth": 3,
        "check_constitutional": True,
        "check_imports": True,
        "check_boundaries": True,
        "boundary_strictness": BoundaryStrictness.STRICT,
    })
    
    OBSERVATION_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "enabled_eyes": [
            "file_sight",
            "import_sight",
            "export_sight",
            "encoding_sight",
        ],
        "use_boundary_sight": False,  # Requires boundary definitions
        "boundary_config": None,  # Path to boundary config file
        "detect_circular_deps": True,
        "strict_boundary_mode": True,
    })
    
    # Configuration presets for common use cases
    PRESET_CONSTITUTIONAL: Dict[str, Any] = field(default_factory=lambda: {
        "enabled_eyes": [
            "file_sight",
            "import_sight",
            "boundary_sight",  # Critical for constitutional analysis
            "export_sight",
        ],
        "use_boundary_sight": True,
        "detect_circular_deps": True,
        "strict_boundary_mode": True,
        "check_constitutional": True,
        "check_imports": True,
        "check_boundaries": True,
        "boundary_strictness": BoundaryStrictness.STRICT,
    })
    
    PRESET_QUICK: Dict[str, Any] = field(default_factory=lambda: {
        "enabled_eyes": [
            "file_sight",
            "import_sight",
        ],
        "use_boundary_sight": False,
    })
    
    PATTERNS_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "window_size": 10,
        "include_uncertainty": True,
        "density_threshold": 0.8,
        "coupling_threshold": 0.7,
        "complexity_threshold": 0.6,
    })
    
    EXPORT_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "format": OutputFormat.MARKDOWN,
        "include_evidence": True,
        "include_notes": True,
        "export_summary": True,
        "export_raw": False,
    })
    
    NOTEBOOK_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "max_note_length": 10000,
        "max_tags_per_note": 10,
        "auto_save_interval": 60,
    })
    
    SESSION_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "max_session_age_days": 7,
        "max_sessions": 100,
        "auto_resume": True,
    })
    
    INTEGRITY_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "validate_on_load": True,
        "backup_before_write": True,
        "max_backups": 10,
    })
    
    PERFORMANCE_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "read_chunk_size": 8192,
        "hash_chunk_size": 65536,
        "max_memory_cache_mb": 100,
        "compression_level": 6,
    })
    
    DISPLAY_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "color": True,
        "progress_bars": True,
        "show_limitations": True,
        "show_uncertainty": True,
        "truncate_long_lines": 80,
        "max_items_in_list": 50,
    })
    
    CONSTITUTIONAL_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "allow_inference": False,
        "allow_interpretation": False,
        "allow_guessing": False,
        "allow_network": False,
        "allow_external_services": False,
        "allow_cloud_dependencies": False,
        "allow_randomness": False,
        "allow_time_based_behavior": False,
        "allow_obscuring": False,
        "allow_distortion": False,
        "allow_invention": False,
        "allow_mutation": False,
        "allow_revision": False,
    })
    
    ERROR_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "max_error_count": 1000,
        "suppress_common_errors": False,
        "log_to_file": True,
        "log_level": "WARNING",
    })
    
    VALIDATION_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "validate_paths": True,
        "validate_permissions": True,
        "validate_symlinks": True,
        "validate_encoding": True,
    })
    
    COMMAND_DEFAULTS: Dict[CommandType, Dict[str, Any]] = field(default_factory=lambda: {
        CommandType.WITNESS: {
            "auto_detect_language": True,
            "preserve_hierarchy": True,
            "store_metadata": True,
        },
        CommandType.INVESTIGATE: {
            "follow_imports": True,
            "detect_circular": True,
            "track_dependencies": True,
        },
        CommandType.ASK: {
            "allow_followup": True,
            "show_context": True,
            "include_examples": True,
        },
        CommandType.PATTERNS: {
            "normalize_values": True,
            "calculate_statistics": True,
            "detect_outliers": True,
        },
        CommandType.EXPORT: {
            "preserve_structure": True,
            "include_timestamps": True,
            "add_watermark": True,
        },
    })
    
    FILE_TYPE_DEFAULTS: Dict[str, List[str]] = field(default_factory=lambda: {
        "python_extensions": [".py", ".pyi", ".pyx", ".pxd"],
        "config_extensions": [".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"],
        "document_extensions": [".md", ".rst", ".txt", ".tex"],
        "ignore_extensions": [".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe"],
    })
    
    ENCODING_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "default_encoding": "utf-8",
        "fallback_encodings": ["utf-8", "latin-1", "ascii"],
        "detect_bom": True,
    })
    
    HASHING_DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "algorithm": "sha256",
        "include_metadata": True,
        "include_permissions": True,
        "include_timestamps": False,
    })
    
    USE_DEFAULT: str = "__USE_DEFAULT__"
    NOT_SPECIFIED: str = "__NOT_SPECIFIED__"
    INHERIT: str = "__INHERIT__"


def get_command_defaults(command: CommandType) -> Dict[str, Any]:
    """Get defaults for a specific command."""
    return SystemDefaults().COMMAND_DEFAULTS.get(command, {})


def get_file_type_extensions(file_type: str) -> List[str]:
    """Get file extensions for a given file type."""
    defaults = SystemDefaults()
    type_map = {
        "python": defaults.FILE_TYPE_DEFAULTS["python_extensions"],
        "config": defaults.FILE_TYPE_DEFAULTS["config_extensions"],
        "document": defaults.FILE_TYPE_DEFAULTS["document_extensions"],
        "ignore": defaults.FILE_TYPE_DEFAULTS["ignore_extensions"],
    }
    return type_map.get(file_type, [])


def is_python_file(path: str) -> bool:
    """Check if a file path has a Python extension."""
    return any(path.endswith(ext) for ext in get_file_type_extensions("python"))


def is_ignored_file(path: str) -> bool:
    """Check if a file path should be ignored by default."""
    return any(path.endswith(ext) for ext in get_file_type_extensions("ignore"))


def validate_defaults() -> List[str]:
    """Validate internal consistency of defaults."""
    errors: List[str] = []
    defaults = SystemDefaults()
    
    if defaults.CONSTITUTIONAL_DEFAULTS.get("allow_inference"):
        errors.append("Constitutional violation: allow_inference must be False")
    
    if defaults.CONSTITUTIONAL_DEFAULTS.get("allow_network"):
        errors.append("Constitutional violation: allow_network must be False")
    
    if defaults.MAX_FILE_SIZE_MB <= 0:
        errors.append("MAX_FILE_SIZE_MB must be positive")
    
    if defaults.MAX_TOTAL_SIZE_MB <= 0:
        errors.append("MAX_TOTAL_SIZE_MB must be positive")
    
    if defaults.MAX_FILE_COUNT <= 0:
        errors.append("MAX_FILE_COUNT must be positive")
    
    if defaults.MAX_RECURSION_DEPTH <= 0:
        errors.append("MAX_RECURSION_DEPTH must be positive")
    
    subdirs = list(defaults.CACHE_SUBDIRS)
    if len(subdirs) != len(set(subdirs)):
        errors.append("Cache subdirectories must be unique")
    
    for command in CommandType:
        if command not in defaults.COMMAND_DEFAULTS:
            errors.append(f"No defaults defined for command: {command}")
    
    return errors


DEFAULTS = SystemDefaults()
CONFIG_VERSION = DEFAULTS.CONFIG_VERSION
DEFAULT_CACHE_DIR = DEFAULTS.DEFAULT_CACHE_DIR
DEFAULT_CONFIG_FILE = DEFAULTS.DEFAULT_CONFIG_FILE
MAX_FILE_SIZE_MB = DEFAULTS.MAX_FILE_SIZE_MB
MAX_TOTAL_SIZE_MB = DEFAULTS.MAX_TOTAL_SIZE_MB
MAX_FILE_COUNT = DEFAULTS.MAX_FILE_COUNT
MAX_RECURSION_DEPTH = DEFAULTS.MAX_RECURSION_DEPTH
MAX_WORKERS = DEFAULTS.MAX_WORKERS
MAX_TIMEOUT_SECONDS = DEFAULTS.MAX_TIMEOUT_SECONDS
USE_DEFAULT = DEFAULTS.USE_DEFAULT
NOT_SPECIFIED = DEFAULTS.NOT_SPECIFIED
INHERIT = DEFAULTS.INHERIT

def get_observation_defaults() -> Dict[str, Any]:
    """Get defaults for observation collection."""
    return SystemDefaults().OBSERVATION_DEFAULTS


def get_preset_config(preset_name: str) -> Dict[str, Any]:
    """
    Get a configuration preset by name.
    
    Args:
        preset_name: Name of the preset ('constitutional', 'quick', or 'default')
        
    Returns:
        Dict with preset configuration
        
    Raises:
        ValueError: If preset_name is not recognized
    """
    defaults = SystemDefaults()
    
    preset_map = {
        "constitutional": defaults.PRESET_CONSTITUTIONAL,
        "quick": defaults.PRESET_QUICK,
        "default": defaults.OBSERVATION_DEFAULTS,
    }
    
    preset = preset_map.get(preset_name.lower())
    if preset is None:
        available = ", ".join(preset_map.keys())
        raise ValueError(
            f"Unknown preset '{preset_name}'. Available presets: {available}"
        )
    
    return preset


__all__ = [
    'SystemDefaults',
    'DEFAULTS',
    'CONFIG_VERSION',
    'DEFAULT_CACHE_DIR',
    'DEFAULT_CONFIG_FILE',
    'MAX_FILE_SIZE_MB',
    'MAX_TOTAL_SIZE_MB',
    'MAX_FILE_COUNT',
    'MAX_RECURSION_DEPTH',
    'MAX_WORKERS',
    'MAX_TIMEOUT_SECONDS',
    'USE_DEFAULT',
    'NOT_SPECIFIED',
    'INHERIT',
    'get_command_defaults',
    'get_file_type_extensions',
    'get_observation_defaults',
    'get_preset_config',
    'is_python_file',
    'is_ignored_file',
    'validate_defaults',
]