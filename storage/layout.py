"""
DIRECTORY & FILE LAYOUT RULES

Defines where truth lives on disk, not how it is written.
This is the canonical map of disk reality.

Constitutional Rules:
1. Path construction must be deterministic
2. No dynamic inference of structure
3. No I/O operations
4. No directory creation
5. Pure functions only: input → output path
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum, auto
from dataclasses import dataclass
import hashlib


class StorageRole(Enum):
    """Well-known roles for storage directories."""
    INVESTIGATION_ROOT = auto()          # Top-level investigation directory
    EVIDENCE = auto()                    # Raw observation evidence
    SNAPSHOTS = auto()                   # Observation snapshots
    ANCHORS = auto()                     # Hash anchors and references
    METADATA = auto()                    # Investigation metadata
    CORRUPTION_MARKERS = auto()          # Corruption markers
    NOTEBOOK = auto()                    # Human thinking space
    PATTERNS = auto()                    # Pattern analysis results
    SCHEMAS = auto()                     # Schema definitions
    VERSIONS = auto()                    # Version tracking


@dataclass(frozen=True)
class LayoutContext:
    """
    Context for path construction.
    
    Immutable to ensure deterministic paths.
    """
    investigation_id: str
    layout_version: str = "v1"
    
    def __post_init__(self):
        # Validate investigation ID format
        if not self.investigation_id:
            raise ValueError("investigation_id cannot be empty")
        if len(self.investigation_id) > 255:
            raise ValueError("investigation_id too long (max 255 chars)")
        
        # Validate layout version
        if not self.layout_version.startswith("v"):
            raise ValueError(f"layout_version must start with 'v', got {self.layout_version}")
        if not self.layout_version[1:].isdigit():
            raise ValueError(f"layout_version must be v<number>, got {self.layout_version}")


class LayoutError(Exception):
    """Base exception for layout-related errors."""
    pass


class InvalidPathComponentError(LayoutError):
    """Path component violates naming rules."""
    pass


def _validate_path_component(component: str, role: str = "path component") -> str:
    """
    Validate a single path component.
    
    Args:
        component: Path component to validate
        role: Description for error messages
        
    Returns:
        Validated component
        
    Raises:
        InvalidPathComponentError: If component violates rules
    """
    if not component:
        raise InvalidPathComponentError(f"{role} cannot be empty")
    
    # Forbid path traversal
    if component in {".", ".."}:
        raise InvalidPathComponentError(f"{role} cannot be '.' or '..'")
    
    # Forbid absolute paths in components
    if os.path.isabs(component):
        raise InvalidPathComponentError(f"{role} cannot be absolute path: {component}")
    
    # Check for path separators
    if '/' in component or '\\' in component:
        raise InvalidPathComponentError(f"{role} cannot contain path separators: {component}")
    
    # Platform-specific forbidden characters
    forbidden_chars = set('<>:"|?*')
    if sys.platform.startswith('win'):
        forbidden_chars.update('<>:"|?*')
    else:
        forbidden_chars.update('/')
    
    found_forbidden = [c for c in component if c in forbidden_chars]
    if found_forbidden:
        raise InvalidPathComponentError(
            f"{role} contains forbidden characters {found_forbidden}: {component}"
        )
    
    # Check length
    if len(component) > 255:
        raise InvalidPathComponentError(f"{role} too long (max 255 chars): {component}")
    
    # Check for control characters
    if any(ord(c) < 32 for c in component):
        raise InvalidPathComponentError(f"{role} contains control characters: {component}")
    
    return component


def _safe_join_path(base: Path, *components: str) -> Path:
    """
    Safely join path components with validation.
    
    Args:
        base: Base path
        *components: Path components to join
        
    Returns:
        Joined path
        
    Raises:
        InvalidPathComponentError: If any component is invalid
    """
    result = base
    for i, component in enumerate(components):
        validated = _validate_path_component(component, f"path component {i}")
        result = result / validated
    return result


def investigation_root(
    base_directory: Path,
    investigation_id: str
) -> Path:
    """
    Get the investigation root directory path.
    
    Args:
        base_directory: Base directory for all investigations
        investigation_id: Unique investigation identifier
        
    Returns:
        Path to investigation root directory
        
    Examples:
        >>> investigation_root(Path("/data"), "my-project-2024")
        PosixPath('/data/investigation_my-project-2024')
    """
    validated_id = _validate_path_component(investigation_id, "investigation_id")
    
    # Investigation root naming: investigation_<id>
    investigation_dir = f"investigation_{validated_id}"
    return _safe_join_path(base_directory, investigation_dir)


def evidence_directory(investigation_root: Path) -> Path:
    """
    Get the evidence directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to evidence directory
    """
    return _safe_join_path(investigation_root, "evidence")


def snapshots_directory(investigation_root: Path) -> Path:
    """
    Get the snapshots directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to snapshots directory
    """
    evidence_dir = evidence_directory(investigation_root)
    return _safe_join_path(evidence_dir, "snapshots")


def snapshot_directory(
    investigation_root: Path,
    snapshot_id: str,
    timestamp: Optional[str] = None
) -> Path:
    """
    Get a specific snapshot directory path.
    
    Args:
        investigation_root: Investigation root directory
        snapshot_id: Unique snapshot identifier
        timestamp: Optional timestamp for directory naming
        
    Returns:
        Path to snapshot directory
        
    Examples:
        Without timestamp: snapshot_<id>
        With timestamp: snapshot_<id>_<timestamp>
    """
    snapshots_dir = snapshots_directory(investigation_root)
    validated_id = _validate_path_component(snapshot_id, "snapshot_id")
    
    if timestamp:
        validated_timestamp = _validate_path_component(timestamp, "timestamp")
        dir_name = f"snapshot_{validated_id}_{validated_timestamp}"
    else:
        dir_name = f"snapshot_{validated_id}"
    
    return _safe_join_path(snapshots_dir, dir_name)


def snapshot_files_directory(snapshot_dir: Path) -> Path:
    """
    Get the files directory within a snapshot.
    
    Args:
        snapshot_dir: Snapshot directory
        
    Returns:
        Path to snapshot files directory
    """
    return _safe_join_path(snapshot_dir, "files")


def snapshot_file_path(
    snapshot_dir: Path,
    relative_file_path: str,
    preserve_extension: bool = True
) -> Path:
    """
    Get the path for a file within a snapshot.
    
    Args:
        snapshot_dir: Snapshot directory
        relative_file_path: File path relative to observed directory
        preserve_extension: Whether to keep original file extension
        
    Returns:
        Path to stored file
        
    Note:
        This uses a flat structure with encoded filenames to avoid
        deep directory nesting and path length issues.
    """
    files_dir = snapshot_files_directory(snapshot_dir)
    
    # Validate and clean relative path
    if not relative_file_path:
        raise InvalidPathComponentError("relative_file_path cannot be empty")
    
    # Split into components and validate each
    parts = relative_file_path.replace('\\', '/').split('/')
    validated_parts: List[str] = []
    for part in parts:
        if part:  # Skip empty parts from leading/trailing slashes
            validated_parts.append(_validate_path_component(part, "file path component"))
    
    if not validated_parts:
        raise InvalidPathComponentError("relative_file_path has no valid components")
    
    # Reconstruct safe path
    safe_path = '/'.join(validated_parts)
    
    # Create deterministic filename that preserves original path info
    # Use hash of original path to avoid collisions
    path_hash = hashlib.sha256(safe_path.encode('utf-8')).hexdigest()[:16]
    
    if preserve_extension:
        # Extract extension from last component
        last_part = validated_parts[-1]
        if '.' in last_part:
            _, ext = last_part.rsplit('.', 1)
            # Validate extension (basic check)
            if ext and all(c.isalnum() or c in '_-' for c in ext):
                filename = f"{path_hash}.{ext}"
            else:
                filename = path_hash
        else:
            filename = path_hash
    else:
        filename = path_hash
    
    # Store with metadata about original path
    return _safe_join_path(files_dir, filename)


def anchors_directory(investigation_root: Path) -> Path:
    """
    Get the anchors directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to anchors directory
    """
    return _safe_join_path(investigation_root, "anchors")


def anchor_file_path(
    investigation_root: Path,
    anchor_type: str,
    anchor_id: Optional[str] = None
) -> Path:
    """
    Get an anchor file path.
    
    Args:
        investigation_root: Investigation root directory
        anchor_type: Type of anchor (e.g., 'snapshot', 'file', 'hash')
        anchor_id: Optional anchor identifier
        
    Returns:
        Path to anchor file
        
    Examples:
        >>> anchor_file_path(root, 'snapshot_hashes')
        PosixPath('<root>/anchors/snapshot_hashes.json')
        
        >>> anchor_file_path(root, 'file', 'abc123')
        PosixPath('<root>/anchors/file_abc123.json')
    """
    anchors_dir = anchors_directory(investigation_root)
    validated_type = _validate_path_component(anchor_type, "anchor_type")
    
    if anchor_id:
        validated_id = _validate_path_component(anchor_id, "anchor_id")
        filename = f"{validated_type}_{validated_id}.json"
    else:
        filename = f"{validated_type}.json"
    
    return _safe_join_path(anchors_dir, filename)


def metadata_directory(investigation_root: Path) -> Path:
    """
    Get the metadata directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to metadata directory
    """
    return _safe_join_path(investigation_root, "metadata")


def investigation_metadata_file(investigation_root: Path) -> Path:
    """
    Get the investigation metadata file path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to investigation metadata file
    """
    metadata_dir = metadata_directory(investigation_root)
    return _safe_join_path(metadata_dir, "investigation.json")


def layout_version_file(investigation_root: Path) -> Path:
    """
    Get the layout version file path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to layout version file
    """
    return _safe_join_path(investigation_root, "version.txt")


def corruption_markers_directory(investigation_root: Path) -> Path:
    """
    Get the corruption markers directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to corruption markers directory
    """
    return _safe_join_path(investigation_root, "corruption_markers")


def corruption_marker_path(
    investigation_root: Path,
    corrupted_path: Path,
    marker_suffix: str = ".corrupted"
) -> Path:
    """
    Get the path for a corruption marker file.
    
    Args:
        investigation_root: Investigation root directory
        corrupted_path: Path to the corrupted file (relative to investigation)
        marker_suffix: Suffix for marker file
        
    Returns:
        Path to corruption marker file
    """
    markers_dir = corruption_markers_directory(investigation_root)
    
    # Create a deterministic name for the marker
    # Use hash of corrupted path to avoid collisions
    corrupted_str = str(corrupted_path).replace('\\', '/')
    path_hash = hashlib.sha256(corrupted_str.encode('utf-8')).hexdigest()[:16]
    
    # Include original filename in marker name for readability
    original_name = corrupted_path.name
    if original_name and len(original_name) < 50:  # Keep reasonable length
        safe_name = ''.join(c for c in original_name if c.isalnum() or c in '._-')
        if safe_name:
            marker_name = f"{path_hash}_{safe_name}{marker_suffix}"
        else:
            marker_name = f"{path_hash}{marker_suffix}"
    else:
        marker_name = f"{path_hash}{marker_suffix}"
    
    return _safe_join_path(markers_dir, marker_name)


def notebook_directory(investigation_root: Path) -> Path:
    """
    Get the notebook directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to notebook directory
    """
    return _safe_join_path(investigation_root, "notebook")


def notebook_entry_file(
    investigation_root: Path,
    entry_id: str,
    timestamp: Optional[str] = None
) -> Path:
    """
    Get a notebook entry file path.
    
    Args:
        investigation_root: Investigation root directory
        entry_id: Entry identifier
        timestamp: Optional timestamp for filename
        
    Returns:
        Path to notebook entry file
    """
    notebook_dir = notebook_directory(investigation_root)
    validated_id = _validate_path_component(entry_id, "entry_id")
    
    if timestamp:
        validated_timestamp = _validate_path_component(timestamp, "timestamp")
        filename = f"entry_{validated_id}_{validated_timestamp}.json"
    else:
        filename = f"entry_{validated_id}.json"
    
    return _safe_join_path(notebook_dir, filename)


def patterns_directory(investigation_root: Path) -> Path:
    """
    Get the patterns directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to patterns directory
    """
    return _safe_join_path(investigation_root, "patterns")


def pattern_file_path(
    investigation_root: Path,
    pattern_type: str,
    snapshot_id: Optional[str] = None
) -> Path:
    """
    Get a pattern analysis file path.
    
    Args:
        investigation_root: Investigation root directory
        pattern_type: Type of pattern (e.g., 'density', 'coupling')
        snapshot_id: Optional snapshot identifier for scoped patterns
        
    Returns:
        Path to pattern file
    """
    patterns_dir = patterns_directory(investigation_root)
    validated_type = _validate_path_component(pattern_type, "pattern_type")
    
    if snapshot_id:
        validated_snapshot = _validate_path_component(snapshot_id, "snapshot_id")
        filename = f"{validated_type}_{validated_snapshot}.json"
    else:
        filename = f"{validated_type}.json"
    
    return _safe_join_path(patterns_dir, filename)


def schemas_directory(investigation_root: Path) -> Path:
    """
    Get the schemas directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to schemas directory
    """
    return _safe_join_path(investigation_root, "schemas")


def schema_file_path(
    investigation_root: Path,
    schema_name: str,
    version: str = "v1"
) -> Path:
    """
    Get a schema definition file path.
    
    Args:
        investigation_root: Investigation root directory
        schema_name: Name of the schema
        version: Schema version
        
    Returns:
        Path to schema file
    """
    schemas_dir = schemas_directory(investigation_root)
    validated_name = _validate_path_component(schema_name, "schema_name")
    validated_version = _validate_path_component(version, "version")
    
    filename = f"{validated_name}_{validated_version}.json"
    return _safe_join_path(schemas_dir, filename)


def versions_directory(investigation_root: Path) -> Path:
    """
    Get the versions directory path.
    
    Args:
        investigation_root: Investigation root directory
        
    Returns:
        Path to versions directory
    """
    return _safe_join_path(investigation_root, "versions")


def version_marker_file(
    investigation_root: Path,
    version: str
) -> Path:
    """
    Get a version marker file path.
    
    Args:
        investigation_root: Investigation root directory
        version: Version identifier
        
    Returns:
        Path to version marker file
    """
    versions_dir = versions_directory(investigation_root)
    validated_version = _validate_path_component(version, "version")
    
    filename = f"version_{validated_version}.json"
    return _safe_join_path(versions_dir, filename)


def get_all_expected_paths(
    investigation_root: Path,
    context: LayoutContext
) -> Dict[StorageRole, List[Path]]:
    """
    Get all expected paths for an investigation.
    
    Useful for validation and documentation.
    
    Args:
        investigation_root: Investigation root directory
        context: Layout context
        
    Returns:
        Dictionary mapping storage roles to expected paths
    """
    root = Path(investigation_root)
    
    return {
        StorageRole.INVESTIGATION_ROOT: [root],
        StorageRole.EVIDENCE: [evidence_directory(root)],
        StorageRole.SNAPSHOTS: [snapshots_directory(root)],
        StorageRole.ANCHORS: [anchors_directory(root)],
        StorageRole.METADATA: [
            metadata_directory(root),
            investigation_metadata_file(root),
        ],
        StorageRole.CORRUPTION_MARKERS: [corruption_markers_directory(root)],
        StorageRole.NOTEBOOK: [notebook_directory(root)],
        StorageRole.PATTERNS: [patterns_directory(root)],
        StorageRole.SCHEMAS: [schemas_directory(root)],
        StorageRole.VERSIONS: [versions_directory(root)],
    }


def validate_path_component(component: str) -> bool:
    """
    Public validation function for path components.
    
    Args:
        component: Path component to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        _validate_path_component(component, "path component")
        return True
    except InvalidPathComponentError:
        return False


# Export public API
__all__ = [
    'StorageRole',
    'LayoutContext',
    'LayoutError',
    'InvalidPathComponentError',
    'investigation_root',
    'evidence_directory',
    'snapshots_directory',
    'snapshot_directory',
    'snapshot_files_directory',
    'snapshot_file_path',
    'anchors_directory',
    'anchor_file_path',
    'metadata_directory',
    'investigation_metadata_file',
    'layout_version_file',
    'corruption_markers_directory',
    'corruption_marker_path',
    'notebook_directory',
    'notebook_entry_file',
    'patterns_directory',
    'pattern_file_path',
    'schemas_directory',
    'schema_file_path',
    'versions_directory',
    'version_marker_file',
    'get_all_expected_paths',
    'validate_path_component',
]