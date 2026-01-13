"""
FORWARD-COMPATIBLE CHANGES

Handles controlled evolution of stored evidence, not spontaneous mutation.
Migrations are code-reviewed historical events, not helpers.

Constitutional Rules:
1. Never migrate silently
2. Never auto-run without explicit trigger
3. Never combine migration with validation
4. Always preserve the ability to verify pre/post conditions
5. If migration fails, the system must stop or quarantine data
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass 
from datetime import datetime
from enum import Enum, auto


class MigrationError(Exception):
    """Base exception for migration failures."""
    pass


class UnsupportedVersionError(MigrationError):
    """Version is not supported for migration."""
    pass


class MigrationPreconditionError(MigrationError):
    """Precondition check failed."""
    pass


class MigrationPostconditionError(MigrationError):
    """Postcondition check failed."""
    pass


class DryRunError(MigrationError):
    """Error occurred during dry-run."""
    pass


class MigrationDirection(Enum):
    """Direction of migration."""
    FORWARD = auto()   # Upgrade to newer version
    BACKWARD = auto()  # Downgrade to older version (rare, but possible)


@dataclass(frozen=True)
class MigrationStep:
    """
    A single migration step from one version to another.
    
    Immutable to ensure reproducibility.
    """
    from_version: str
    to_version: str
    description: str
    migration_function: Callable[[Path, bool], tuple[bool, str]]
    preconditions: List[Callable[[Path], tuple[bool, str]]]
    postconditions: List[Callable[[Path], tuple[bool, str]]]
    requires_explicit_confirmation: bool = False
    idempotent: bool = True  # Can be safely re-run
    
    def __post_init__(self):
        # Validate version format
        if not self.from_version.startswith('v') or not self.to_version.startswith('v'):
            raise ValueError(f"Versions must start with 'v': {self.from_version} -> {self.to_version}")
        
        # Extract numeric parts for comparison
        from_num = self.from_version[1:]
        to_num = self.to_version[1:]
        
        if not from_num.isdigit() or not to_num.isdigit():
            raise ValueError(f"Version numbers must be numeric: {self.from_version} -> {self.to_version}")
        
        if int(from_num) >= int(to_num):
            raise ValueError(f"Migration must move forward: {self.from_version} -> {self.to_version}")
        
        # Validate description
        if not self.description:
            raise ValueError("Description must be non-empty string")


@dataclass(frozen=True)
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    from_version: str
    to_version: str
    steps_performed: int
    steps_attempted: int
    errors: List[tuple[str, str]]  # (step_name, error_message)
    warnings: List[tuple[str, str]]  # (step_name, warning_message)
    backup_path: Optional[Path] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        import time
        object.__setattr__(self, 'timestamp', time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "steps_performed": self.steps_performed,
            "steps_attempted": self.steps_attempted,
            "errors": self.errors,
            "warnings": self.warnings,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "timestamp": self.timestamp
        }


class VersionDetector:
    """Detects current version of stored data."""
    
    @staticmethod
    def detect_investigation_version(investigation_root: Path) -> Optional[str]:
        """
        Detect version of an investigation.
        
        Args:
            investigation_root: Path to investigation root
            
        Returns:
            Version string (e.g., "v1") or None if cannot detect
        """
        # Check for version file
        version_file = investigation_root / "version.txt"
        if version_file.exists():
            try:
                content = version_file.read_text(encoding='utf-8').strip()
                if content.startswith('v') and content[1:].isdigit():
                    return content
            except (OSError, UnicodeDecodeError):
                pass
        
        # Check for metadata file with version
        metadata_file = investigation_root / "metadata" / "investigation.json"
        if metadata_file.exists():
            try:
                content = metadata_file.read_text(encoding='utf-8')
                metadata = json.loads(content)
                version = metadata.get("schema_version")
                if version and isinstance(version, str) and version.startswith('v'):
                    return version
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        # Check for layout patterns to infer version
        # v1 layout has specific directory structure
        if (investigation_root / "evidence").exists():
            return "v1"
        
        return None
    
    @staticmethod
    def detect_snapshot_version(snapshot_dir: Path) -> Optional[str]:
        """
        Detect version of a snapshot.
        
        Args:
            snapshot_dir: Path to snapshot directory
            
        Returns:
            Version string or None if cannot detect
        """
        # Check for snapshot metadata
        metadata_file = snapshot_dir / "metadata.json"
        if metadata_file.exists():
            try:
                content = metadata_file.read_text(encoding='utf-8')
                metadata = json.loads(content)
                version = metadata.get("schema_version")
                if version and isinstance(version, str) and version.startswith('v'):
                    return version
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        # Check for v1 layout
        if (snapshot_dir / "files").exists():
            return "v1"
        
        return None


class MigrationBackup:
    """Creates and manages backups during migration."""
    
    @staticmethod
    def create_backup(source_path: Path, backup_suffix: str = ".pre_migration") -> Path:
        """
        Create a backup of data before migration.
        
        Args:
            source_path: Path to back up
            backup_suffix: Suffix for backup directory
            
        Returns:
            Path to backup directory
            
        Raises:
            MigrationError: If backup fails
        """
        if not source_path.exists():
            raise MigrationError(f"Cannot backup non-existent path: {source_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.name}_{timestamp}{backup_suffix}"
        backup_path = source_path.parent / backup_name
        
        try:
            if source_path.is_file():
                shutil.copy2(source_path, backup_path)
            else:
                shutil.copytree(source_path, backup_path, symlinks=False)
            
            # Write backup metadata
            metadata: Dict[str, Any] = {
                "original_path": str(source_path.absolute()),
                "backup_created": datetime.now().isoformat(),
                "backup_type": "pre_migration",
                "source_size": MigrationBackup._get_path_size(source_path)
            }
            
            metadata_file = backup_path / ".backup_metadata.json"
            if backup_path.is_dir():
                metadata_file.write_text(json.dumps(metadata, indent=2))
            
            return backup_path
        except (shutil.Error, OSError, IOError) as e:
            raise MigrationError(f"Failed to create backup of {source_path}: {e}") from e
    
    @staticmethod
    def _get_path_size(path: Path) -> int:
        """Get total size of a path (file or directory)."""
        if path.is_file():
            return path.stat().st_size
        else:
            total = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
            return total
    
    @staticmethod
    def verify_backup_integrity(original_path: Path, backup_path: Path) -> tuple[bool, str]:
        """
        Verify backup integrity by comparing file counts and sizes.
        
        Args:
            original_path: Original path
            backup_path: Backup path
            
        Returns:
            (success, message)
        """
        if not backup_path.exists():
            return False, f"Backup does not exist: {backup_path}"
        
        try:
            # Compare file counts
            if original_path.is_file() and backup_path.is_file():
                return True, "Single file backup verified"
            
            # For directories, compare structure
            orig_files = set(p.relative_to(original_path) for p in original_path.rglob('*') if p.is_file())
            backup_files = set(p.relative_to(backup_path) for p in backup_path.rglob('*') if p.is_file())
            
            if orig_files != backup_files:
                missing = orig_files - backup_files
                extra = backup_files - orig_files
                return False, f"File mismatch: missing {len(missing)}, extra {len(extra)}"
            
            # Check file sizes (quick check)
            for rel_path in orig_files:
                orig_size = (original_path / rel_path).stat().st_size
                backup_size = (backup_path / rel_path).stat().st_size
                if orig_size != backup_size:
                    return False, f"Size mismatch for {rel_path}: {orig_size} vs {backup_size}"
            
            return True, f"Backup verified: {len(orig_files)} files"
        except (OSError, IOError) as e:
            return False, f"Error verifying backup: {e}"


class MigrationRegistry:
    """Registry of available migration steps."""
    
    def __init__(self):
        self._migrations: Dict[tuple[str, str], MigrationStep] = {}
        self._version_chain: List[str] = []
    
    def register(self, migration: MigrationStep) -> None:
        """
        Register a migration step.
        
        Args:
            migration: Migration step to register
            
        Raises:
            ValueError: If migration conflicts with existing registration
        """
        key = (migration.from_version, migration.to_version)
        
        if key in self._migrations:
            existing = self._migrations[key]
            raise ValueError(
                f"Migration from {migration.from_version} to {migration.to_version} "
                f"already registered: {existing.description}"
            )
        
        # Update version chain
        if migration.from_version not in self._version_chain:
            self._version_chain.append(migration.from_version)
        if migration.to_version not in self._version_chain:
            self._version_chain.append(migration.to_version)
        
        # Sort version chain
        self._version_chain.sort(key=lambda v: int(v[1:]) if v[1:].isdigit() else 0)
        
        self._migrations[key] = migration
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[MigrationStep]:
        """
        Get migration path between versions.
        
        Args:
            from_version: Starting version
            to_version: Target version
            
        Returns:
            List of migration steps in order
            
        Raises:
            UnsupportedVersionError: If path cannot be found
        """
        # Check if direct migration exists
        direct_key = (from_version, to_version)
        if direct_key in self._migrations:
            return [self._migrations[direct_key]]
        
        # Find path through intermediate versions
        path = self._find_migration_path(from_version, to_version, set())
        if not path:
            raise UnsupportedVersionError(
                f"No migration path from {from_version} to {to_version}"
            )
        
        return [self._migrations[key] for key in path]
    
    def _find_migration_path(
        self,
        current: str,
        target: str,
        visited: Set[str]
    ) -> List[tuple[str, str]]:
        """
        Find migration path using DFS.
        
        Args:
            current: Current version
            target: Target version
            visited: Set of visited versions
            
        Returns:
            List of migration keys (from, to) in order
        """
        if current == target:
            return []
        
        if current in visited:
            return []
        
        visited.add(current)
        
        # Get all possible migrations from current version
        possible_steps = [
            (from_v, to_v) for (from_v, to_v) in self._migrations.keys()
            if from_v == current
        ]
        
        for step in possible_steps:
            _, next_version = step
            if next_version == target:
                return [step]
            
            # Recursively find path from next_version to target
            subpath = self._find_migration_path(next_version, target, visited.copy())
            if subpath:
                return [step] + subpath
        
        return []
    
    def get_latest_version(self) -> Optional[str]:
        """Get the latest version in the registry."""
        if not self._version_chain:
            return None
        
        # Assuming versions are in order v1, v2, v3, etc.
        return max(self._version_chain, key=lambda v: int(v[1:]) if v[1:].isdigit() else 0)
    
    def get_supported_versions(self) -> List[str]:
        """Get list of all supported versions."""
        return self._version_chain.copy()


class MigrationExecutor:
    """Executes migration steps with validation."""
    
    def __init__(self, registry: MigrationRegistry):
        self.registry = registry
        self.dry_run: bool = False
    
    def migrate_investigation(
        self,
        investigation_root: Path,
        target_version: str,
        create_backup: bool = True,
        confirm_callback: Optional[Callable[[MigrationStep], bool]] = None
    ) -> MigrationResult:
        """
        Migrate an investigation to target version.
        
        Args:
            investigation_root: Investigation root directory
            target_version: Target version (e.g., "v2")
            create_backup: Whether to create backup before migration
            confirm_callback: Optional callback for confirmation of each step
            
        Returns:
            MigrationResult with success/failure details
        """
        # Detect current version
        current_version = VersionDetector.detect_investigation_version(investigation_root)
        if current_version is None:
            return MigrationResult(
                success=False,
                from_version="unknown",
                to_version=target_version,
                steps_performed=0,
                steps_attempted=0,
                errors=[("detection", "Cannot detect current version")],
                warnings=[]
            )
        
        # Check if already at target
        if current_version == target_version:
            return MigrationResult(
                success=True,
                from_version=current_version,
                to_version=target_version,
                steps_performed=0,
                steps_attempted=0,
                errors=[],
                warnings=[("already_current", f"Already at version {target_version}")]
            )
        
        # Get migration path
        try:
            migration_path = self.registry.get_migration_path(current_version, target_version)
        except UnsupportedVersionError as e:
            return MigrationResult(
                success=False,
                from_version=current_version,
                to_version=target_version,
                steps_performed=0,
                steps_attempted=0,
                errors=[("path_finding", str(e))],
                warnings=[]
            )
        
        # Create backup if requested
        backup_path = None
        if create_backup and not self.dry_run:
            try:
                backup_path = MigrationBackup.create_backup(investigation_root)
            except MigrationError as e:
                return MigrationResult(
                    success=False,
                    from_version=current_version,
                    to_version=target_version,
                    steps_performed=0,
                    steps_attempted=0,
                    errors=[("backup", f"Backup failed: {e}")],
                    warnings=[],
                    backup_path=None
                )
        
        # Execute migration steps
        errors: List[tuple[str, str]] = []
        warnings: List[tuple[str, str]] = []
        steps_performed = 0
        
        for step in migration_path:
            step_name = f"{step.from_version}->{step.to_version}"
            
            # Check if confirmation required
            if (step.requires_explicit_confirmation and 
                confirm_callback is not None and 
                not confirm_callback(step)):
                errors.append((step_name, "User declined confirmation"))
                break
            
            # Execute step
            try:
                success, message = self._execute_step(step, investigation_root)
                if success:
                    steps_performed += 1
                    if message:
                        warnings.append((step_name, message))
                else:
                    errors.append((step_name, message))
                    break  # Stop on first error
            except Exception as e:
                errors.append((step_name, f"Unexpected error: {e}"))
                break
        
        success = len(errors) == 0
        
        return MigrationResult(
            success=success,
            from_version=current_version,
            to_version=target_version,
            steps_performed=steps_performed,
            steps_attempted=len(migration_path),
            errors=errors,
            warnings=warnings,
            backup_path=backup_path
        )
    
    def _execute_step(self, step: MigrationStep, target_path: Path) -> tuple[bool, str]:
        """
        Execute a single migration step.
        
        Args:
            step: Migration step to execute
            target_path: Path to migrate
            
        Returns:
            (success, message)
        """
        # Check preconditions
        for precondition in step.preconditions:
            try:
                success, message = precondition(target_path)
                if not success:
                    return False, f"Precondition failed: {message}"
            except Exception as e:
                return False, f"Precondition error: {e}"
        
        # Execute migration
        try:
            success, message = step.migration_function(target_path, self.dry_run)
            if not success:
                return False, f"Migration failed: {message}"
        except Exception as e:
            return False, f"Migration error: {e}"
        
        # Skip postconditions in dry-run
        if self.dry_run:
            return True, "Dry-run successful"
        
        # Check postconditions
        for postcondition in step.postconditions:
            try:
                success, message = postcondition(target_path)
                if not success:
                    return False, f"Postcondition failed: {message}"
            except Exception as e:
                return False, f"Postcondition error: {e}"
        
        return True, "Migration step completed"
    
    def dry_run_migration(
        self,
        investigation_root: Path,
        target_version: str
    ) -> MigrationResult:
        """
        Perform dry-run migration without modifying data.
        
        Args:
            investigation_root: Investigation root directory
            target_version: Target version
            
        Returns:
            MigrationResult showing what would be done
        """
        self.dry_run = True
        try:
            result = self.migrate_investigation(
                investigation_root,
                target_version,
                create_backup=False,
                confirm_callback=None
            )
            # Ensure backup_path is None for dry-run
            object.__setattr__(result, 'backup_path', None)
            return result
        finally:
            self.dry_run = False


# Predefined migration utilities

def create_version_file_precondition(version: str) -> Callable[[Path], tuple[bool, str]]:
    """
    Create precondition that checks for existence of version file.
    
    Args:
        version: Expected version
        
    Returns:
        Precondition function
    """
    def precondition(path: Path) -> tuple[bool, str]:
        version_file = path / "version.txt"
        if not version_file.exists():
            return False, f"Version file not found at {version_file}"
        
        try:
            content = version_file.read_text(encoding='utf-8').strip()
            if content != version:
                return False, f"Version mismatch: expected {version}, got {content}"
            return True, f"Version file correct: {version}"
        except (OSError, UnicodeDecodeError) as e:
            return False, f"Cannot read version file: {e}"
    
    return precondition


def update_version_file_postcondition(version: str) -> Callable[[Path], tuple[bool, str]]:
    """
    Create postcondition that checks version file was updated.
    
    Args:
        version: Expected version after migration
        
    Returns:
        Postcondition function
    """
    def postcondition(path: Path) -> tuple[bool, str]:
        version_file = path / "version.txt"
        if not version_file.exists():
            return False, f"Version file not created at {version_file}"
        
        try:
            content = version_file.read_text(encoding='utf-8').strip()
            if content != version:
                return False, f"Version not updated: expected {version}, got {content}"
            return True, f"Version file updated to {version}"
        except (OSError, UnicodeDecodeError) as e:
            return False, f"Cannot read version file: {e}"
    
    return postcondition


def schema_migration_function(
    schema_name: str,
    transform_function: Callable[[Dict[str, Any]], Dict[str, Any]]
) -> Callable[[Path, bool], tuple[bool, str]]:
    """
    Create migration function for JSON schema files.
    
    Args:
        schema_name: Name of schema to migrate
        transform_function: Function that transforms old data to new
        
    Returns:
        Migration function
    """
    def migrate(path: Path, dry_run: bool) -> tuple[bool, str]:
        schema_file = path / "schemas" / f"{schema_name}.json"
        if not schema_file.exists():
            return False, f"Schema file not found: {schema_file}"
        
        try:
            content = schema_file.read_text(encoding='utf-8')
            old_data = json.loads(content)
            
            # Transform data
            new_data = transform_function(old_data)
            
            if dry_run:
                return True, f"Would update {schema_name}.json (dry run)"
            
            # Write back
            schema_file.write_text(json.dumps(new_data, indent=2))
            return True, f"Updated {schema_name}.json"
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            return False, f"Error migrating schema: {e}"
    
    return migrate


# Example migration steps (these would be registered by the system)

def create_v1_to_v2_migration() -> MigrationStep:
    """
    Example migration from v1 to v2.
    
    In v1, evidence was stored directly in investigation_root/evidence.
    In v2, we add metadata files and version tracking.
    """
    
    def migration_function(path: Path, dry_run: bool) -> tuple[bool, str]:
        # Create metadata directory
        metadata_dir = path / "metadata"
        if not metadata_dir.exists() and not dry_run:
            metadata_dir.mkdir(exist_ok=True)
        
        # Create version file
        version_file = path / "version.txt"
        if not dry_run:
            version_file.write_text("v2\n")
        
        return True, "Created v2 structure"
    
    def v1_precondition(path: Path) -> tuple[bool, str]:
        # Check v1 structure exists
        evidence_dir = path / "evidence"
        if not evidence_dir.exists():
            return False, "v1 evidence directory not found"
        
        # Check no v2 files exist
        version_file = path / "version.txt"
        if version_file.exists():
            return False, "Already has version file (not v1)"
        
        return True, "v1 structure confirmed"
    
    def v2_postcondition(path: Path) -> tuple[bool, str]:
        # Check v2 structure created
        version_file = path / "version.txt"
        if not version_file.exists():
            return False, "Version file not created"
        
        metadata_dir = path / "metadata"
        if not metadata_dir.exists():
            return False, "Metadata directory not created"
        
        return True, "v2 structure confirmed"
    
    return MigrationStep(
        from_version="v1",
        to_version="v2",
        description="Add metadata directory and version tracking",
        migration_function=migration_function,
        preconditions=[v1_precondition],
        postconditions=[v2_postcondition],
        requires_explicit_confirmation=True,
        idempotent=True
    )


# Export public API
__all__ = [
    'MigrationError',
    'UnsupportedVersionError',
    'MigrationPreconditionError',
    'MigrationPostconditionError',
    'DryRunError',
    'MigrationDirection',
    'MigrationStep',
    'MigrationResult',
    'VersionDetector',
    'MigrationBackup',
    'MigrationRegistry',
    'MigrationExecutor',
    'create_version_file_precondition',
    'update_version_file_postcondition',
    'schema_migration_function',
    'create_v1_to_v2_migration',
]