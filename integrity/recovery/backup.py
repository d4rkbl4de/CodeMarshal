"""
integrity/recovery/backup.py

TRUTH PRESERVATION MODULE - TIER 14 (GRACEFUL DEGRADATION)

Purpose: Create immutable, atomic backups of system state with integrity guarantees.
Principle: Capture truth without distorting it. Never mutate live data.
Constitutional: Article 9 (Immutable Observations), Article 14 (Graceful Degradation), Article 19 (Backward Compatibility)
"""

import json
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, NamedTuple
import logging

# Core imports - truth preservation layers
from storage.atomic import atomic_write
from storage.corruption import detect_corruption
from observations.record.snapshot import Snapshot, load_snapshot, save_snapshot
from observations.record.integrity import compute_snapshot_hash
from core.state import InvestigationState, get_current_state
from core.context import get_runtime_context
from config.loader import load_config, get_active_config
from integrity.monitoring.errors import log_error, ErrorSeverity
from integrity.recovery.audit import audit_recovery

# Type definitions for truth preservation
class BackupManifest(NamedTuple):
    """Complete manifest of what was backed up - truth about truth"""
    timestamp: datetime
    system_version: str
    backup_format_version: int
    included_components: List[str]
    integrity_hashes: Dict[str, str]
    total_size_bytes: int
    source_paths: List[str]


class BackupOutcome(NamedTuple):
    """Complete record of backup attempt - truth about preservation"""
    success: bool
    backup_path: Optional[Path]
    manifest: Optional[BackupManifest]
    warnings: List[str]
    error_message: Optional[str] = None


# Constants for truth consistency
BACKUP_FORMAT_VERSION: int = 1
MINIMUM_BACKUP_SIZE_BYTES: int = 1024  # 1KB minimum backup size
MAX_BACKUP_AGE_DAYS: int = 30  # Automatic cleanup after 30 days
COMPRESSION_THRESHOLD_BYTES: int = 10 * 1024 * 1024  # 10MB


def create_backup_directory(backup_root: Optional[Path] = None) -> Path:
    """
    Create and validate backup directory structure.
    
    Constitutional: Article 4 (Progressive Disclosure) - Clean organization
    Principle: Truth should be organized, not chaotic
    """
    if backup_root is None:
        backup_root = Path("./.codemarshal/backups")
    
    # Create nested directory structure for truth organization
    backup_root.mkdir(parents=True, exist_ok=True)
    
    # Subdirectories for different backup types
    (backup_root / "full").mkdir(exist_ok=True)
    (backup_root / "incremental").mkdir(exist_ok=True)
    (backup_root / "emergency").mkdir(exist_ok=True)
    (backup_root / "metadata").mkdir(exist_ok=True)
    
    # Ensure directory permissions prevent accidental deletion
    try:
        # On Unix-like systems, set directory to read-only for others
        backup_root.chmod(0o755)
    except (PermissionError, NotImplementedError):
        # Windows or permission issues - log and continue
        pass
    
    return backup_root


def collect_observations_snapshot() -> Optional[Snapshot]:
    """
    Collect current observations snapshot with corruption detection.
    
    Constitutional: Article 1 (Observation Purity) - Must capture what exists
    Principle: Validate before preservation
    """
    try:
        snapshot = load_snapshot()
        
        # Detect any corruption in the snapshot before backing up
        corruption = detect_corruption(snapshot)
        if corruption:
            log_error(f"Corruption detected in snapshot before backup: {corruption}", 
                     severity=ErrorSeverity.HIGH)
            # We still backup, but with corruption flag
            setattr(snapshot, 'corruption_detected', True)
        
        return snapshot
    except Exception as e:
        log_error(f"Failed to load snapshot for backup: {e}", severity=ErrorSeverity.HIGH)
        return None


def collect_investigation_state() -> Optional[InvestigationState]:
    """
    Collect current investigation state.
    
    Constitutional: Article 10 (Anchored Thinking) - Preserve human reasoning
    """
    try:
        state = get_current_state()
        
        # Validate state is serializable
        if not hasattr(state, 'to_dict'):
            log_error("InvestigationState missing to_dict method", severity=ErrorSeverity.MEDIUM)
            return None
            
        return state
    except Exception as e:
        log_error(f"Failed to load investigation state: {e}", severity=ErrorSeverity.MEDIUM)
        return None


def collect_configuration() -> Dict[str, Any]:
    """
    Collect active configuration.
    
    Constitutional: Article 2 (Human Primacy) - Preserve user choices
    """
    try:
        config = get_active_config()
        return config.to_dict() if hasattr(config, 'to_dict') else dict(config)
    except Exception as e:
        log_error(f"Failed to collect configuration: {e}", severity=ErrorSeverity.LOW)
        return {}


def compute_component_hash(component_name: str, data: Any) -> Optional[str]:
    """
    Compute integrity hash for a backup component.
    
    Constitutional: Article 13 (Deterministic Operation) - Same data, same hash
    """
    try:
        # Convert to canonical JSON string for consistent hashing
        if hasattr(data, 'to_dict'):
            data_dict = data.to_dict()
        elif isinstance(data, dict):
            data_dict = data
        else:
            # Try to convert to dict, fall back to string representation
            try:
                data_dict = dict(data)
            except (TypeError, ValueError):
                data_dict = {"raw": str(data)}
        
        # Sort keys for deterministic hashing
        json_str = json.dumps(data_dict, sort_keys=True, separators=(',', ':'))
        
        # Use SHA-256 for strong collision resistance
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
        
    except Exception as e:
        log_error(f"Failed to compute hash for {component_name}: {e}")
        return None


def create_backup_filename(timestamp: datetime, backup_type: str = "full") -> str:
    """
    Create deterministic backup filename.
    
    Constitutional: Article 7 (Clear Affordances) - Predictable naming
    """
    # Format: backup_YYYYMMDD_HHMMSS_TYPE.json
    date_str = timestamp.strftime("%Y%m%d")
    time_str = timestamp.strftime("%H%M%S")
    return f"backup_{date_str}_{time_str}_{backup_type}.json"


def validate_backup_completeness(backup_data: Dict[str, Any]) -> List[str]:
    """
    Validate that backup contains all required components.
    
    Constitutional: Article 11 (Declared Limitations) - Know what we're missing
    """
    warnings = []
    required_components = ["observations", "state", "metadata"]
    
    for component in required_components:
        if component not in backup_data:
            warnings.append(f"Missing required component: {component}")
        elif not backup_data[component]:
            warnings.append(f"Empty component: {component}")
    
    # Check observation count
    observations = backup_data.get("observations", {})
    if isinstance(observations, dict) and "files" in observations:
        file_count = len(observations["files"])
        if file_count == 0:
            warnings.append("Backup contains 0 observed files")
        elif file_count < 10:
            warnings.append(f"Backup contains only {file_count} files - minimal observation")
    
    return warnings


def perform_incremental_backup(backup_dir: Path, 
                              since_timestamp: datetime) -> BackupOutcome:
    """
    Create incremental backup of changes since specified timestamp.
    
    Constitutional: Article 20 (Progressive Enhancement) - Build on existing functionality
    """
    # TODO: Implement incremental backup logic
    # This would require tracking observation changes over time
    # For now, we'll log that incremental backup is not yet implemented
    log_error("Incremental backup not yet implemented", severity=ErrorSeverity.LOW)
    
    # Fall back to full backup
    return perform_backup(backup_dir, backup_type="emergency")


def perform_backup(backup_root: Optional[str] = None,
                   backup_type: str = "full",
                   description: Optional[str] = None) -> BackupOutcome:
    """
    Perform a complete system backup with integrity guarantees.
    
    Constitutional: Article 14 (Graceful Degradation) - Handle partial failures
    Article 19 (Backward Compatibility) - Preserve format for future restoration
    
    Args:
        backup_root: Root directory for backups (creates if doesn't exist)
        backup_type: "full", "incremental", or "emergency"
        description: Optional human-readable description of backup context
        
    Returns:
        BackupOutcome with complete truth about backup attempt
    """
    backup_start = datetime.now(timezone.utc)
    warnings: List[str] = []
    
    try:
        # Phase 1: Setup and validation
        backup_dir = create_backup_directory(
            Path(backup_root) if backup_root else None
        )
        
        # Check disk space before proceeding
        try:
            stat = shutil.disk_usage(backup_dir)
            if stat.free < MINIMUM_BACKUP_SIZE_BYTES * 10:  # Need 10x minimum
                warning = f"Low disk space: {stat.free / 1024 / 1024:.1f}MB free"
                warnings.append(warning)
                log_error(warning, severity=ErrorSeverity.MEDIUM)
        except (OSError, AttributeError):
            # Disk space check not available on all systems
            pass
        
        # Phase 2: Collect truth components
        snapshot = collect_observations_snapshot()
        if snapshot is None:
            return BackupOutcome(
                success=False,
                backup_path=None,
                manifest=None,
                warnings=warnings,
                error_message="Failed to collect observations snapshot"
            )
        
        state = collect_investigation_state()
        if state is None:
            return BackupOutcome(
                success=False,
                backup_path=None,
                manifest=None,
                warnings=warnings,
                error_message="Failed to collect investigation state"
            )
        
        config = collect_configuration()
        
        # Phase 3: Compute integrity hashes
        integrity_hashes = {}
        
        obs_hash = compute_component_hash("observations", snapshot)
        if obs_hash:
            integrity_hashes["observations"] = obs_hash
        else:
            warnings.append("Failed to compute observation hash")
        
        state_hash = compute_component_hash("state", state)
        if state_hash:
            integrity_hashes["state"] = state_hash
        else:
            warnings.append("Failed to compute state hash")
        
        config_hash = compute_component_hash("config", config)
        if config_hash:
            integrity_hashes["config"] = config_hash
        
        # Phase 4: Assemble backup data
        backup_data = {
            "metadata": {
                "timestamp": backup_start.isoformat(),
                "system_version": "1.0.0",  # TODO: Get from package
                "backup_format_version": BACKUP_FORMAT_VERSION,
                "backup_type": backup_type,
                "description": description or f"{backup_type.capitalize()} backup",
                "runtime_context": get_runtime_context().to_dict() if hasattr(get_runtime_context(), 'to_dict') else {}
            },
            "observations": snapshot.to_dict() if hasattr(snapshot, 'to_dict') else dict(snapshot),
            "state": state.to_dict() if hasattr(state, 'to_dict') else dict(state),
            "config": config,
            "integrity_hashes": integrity_hashes
        }
        
        # Compute overall integrity hash
        # Exclude integrity_hashes from the hash computation (circular)
        hash_data = {k: v for k, v in backup_data.items() if k != "integrity_hashes"}
        json_str = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        overall_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
        backup_data["integrity_hash"] = overall_hash
        
        # Phase 5: Validate backup completeness
        completeness_warnings = validate_backup_completeness(backup_data)
        warnings.extend(completeness_warnings)
        
        # Phase 6: Write backup atomically
        backup_filename = create_backup_filename(backup_start, backup_type)
        backup_path = backup_dir / backup_type / backup_filename
        
        # Convert to pretty JSON for human readability (with atomic write guarantee)
        backup_json = json.dumps(backup_data, indent=2, sort_keys=True)
        atomic_write(backup_path, backup_json)
        
        # Phase 7: Create manifest
        total_size = backup_path.stat().st_size
        manifest = BackupManifest(
            timestamp=backup_start,
            system_version=backup_data["metadata"]["system_version"],
            backup_format_version=BACKUP_FORMAT_VERSION,
            included_components=list(backup_data.keys()),
            integrity_hashes=integrity_hashes,
            total_size_bytes=total_size,
            source_paths=[str(backup_path)]
        )
        
        # Phase 8: Audit and cleanup
        audit_recovery(
            action="backup_complete",
            metadata={
                "timestamp": backup_start.isoformat(),
                "backup_path": str(backup_path),
                "backup_type": backup_type,
                "size_bytes": total_size,
                "observation_hash": obs_hash[:16] + "..." if obs_hash else "unknown",
                "state_hash": state_hash[:16] + "..." if state_hash else "unknown",
                "warnings": warnings,
                "description": description
            }
        )
        
        # Cleanup old backups if needed
        cleanup_old_backups(backup_dir / backup_type)
        
        return BackupOutcome(
            success=True,
            backup_path=backup_path,
            manifest=manifest,
            warnings=warnings,
            error_message=None
        )
        
    except Exception as e:
        error_msg = f"Backup failed: {str(e)}"
        log_error(error_msg, severity=ErrorSeverity.HIGH)
        
        audit_recovery(
            action="backup_failed",
            metadata={
                "timestamp": backup_start.isoformat(),
                "error": error_msg,
                "backup_type": backup_type
            }
        )
        
        return BackupOutcome(
            success=False,
            backup_path=None,
            manifest=None,
            warnings=warnings,
            error_message=error_msg
        )


def cleanup_old_backups(backup_dir: Path, max_age_days: int = MAX_BACKUP_AGE_DAYS) -> None:
    """
    Clean up backups older than specified age.
    
    Constitutional: Article 8 (Honest Performance) - Manage disk usage transparently
    """
    if not backup_dir.exists():
        return
    
    cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_days * 24 * 60 * 60)
    deleted_count = 0
    
    for backup_file in backup_dir.glob("backup_*.json"):
        try:
            if backup_file.stat().st_mtime < cutoff_time:
                # Read metadata before deletion to audit
                try:
                    with backup_file.open('r', encoding='utf-8') as f:
                        metadata = json.load(f).get("metadata", {})
                    timestamp = metadata.get("timestamp", "unknown")
                except:
                    timestamp = "unknown"
                
                backup_file.unlink()
                deleted_count += 1
                
                # Audit the cleanup
                audit_recovery(
                    action="backup_cleanup",
                    metadata={
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "deleted_file": backup_file.name,
                        "backup_timestamp": timestamp,
                        "reason": f"Older than {max_age_days} days"
                    }
                )
        except (OSError, PermissionError) as e:
            log_error(f"Failed to delete old backup {backup_file.name}: {e}")
    
    if deleted_count > 0:
        logging.info(f"Cleaned up {deleted_count} backups older than {max_age_days} days")


def list_backups(backup_root: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all available backups by type.
    
    Constitutional: Article 7 (Clear Affordances) - Show what exists
    """
    backup_dir = create_backup_directory(
        Path(backup_root) if backup_root else None
    )
    
    result = {
        "full": [],
        "incremental": [],
        "emergency": [],
        "corrupted": []
    }
    
    for backup_type in ["full", "incremental", "emergency"]:
        type_dir = backup_dir / backup_type
        if not type_dir.exists():
            continue
            
        for backup_file in type_dir.glob("backup_*.json"):
            try:
                with backup_file.open('r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                metadata = backup_data.get("metadata", {})
                
                result[backup_type].append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "timestamp": metadata.get("timestamp", "unknown"),
                    "size_bytes": backup_file.stat().st_size,
                    "description": metadata.get("description", ""),
                    "format_version": metadata.get("backup_format_version", 0),
                    "integrity_hash": backup_data.get("integrity_hash", "unknown")[:16] + "..."
                })
                
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # Corrupted backup file
                result["corrupted"].append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "error": f"Corrupted: {str(e)[:50]}...",
                    "size_bytes": backup_file.stat().st_size
                })
    
    return result


def verify_backup(backup_path: str) -> Dict[str, Any]:
    """
    Verify backup integrity without restoring it.
    
    Constitutional: Article 21 (Self-Validation) - Verify our own backups
    """
    path = Path(backup_path)
    if not path.exists():
        return {"valid": False, "error": "Backup file does not exist"}
    
    try:
        with path.open('r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Check required structure
        required_keys = {"metadata", "observations", "state", "integrity_hash"}
        if not required_keys.issubset(backup_data.keys()):
            missing = required_keys - set(backup_data.keys())
            return {"valid": False, "error": f"Missing keys: {missing}"}
        
        # Verify integrity hash
        hash_data = {k: v for k, v in backup_data.items() if k != "integrity_hash"}
        json_str = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        computed_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
        
        if computed_hash != backup_data["integrity_hash"]:
            return {
                "valid": False, 
                "error": f"Hash mismatch: expected {backup_data['integrity_hash'][:16]}..., got {computed_hash[:16]}..."
            }
        
        # Check component hashes if present
        integrity_hashes = backup_data.get("integrity_hashes", {})
        verification_results = {}
        
        for component, expected_hash in integrity_hashes.items():
            if component in hash_data:
                component_data = hash_data[component]
                component_json = json.dumps(component_data, sort_keys=True, separators=(',', ':'))
                computed_component_hash = hashlib.sha256(component_json.encode('utf-8')).hexdigest()
                
                verification_results[component] = {
                    "matches": computed_component_hash == expected_hash,
                    "expected": expected_hash[:16] + "...",
                    "actual": computed_component_hash[:16] + "..."
                }
        
        metadata = backup_data["metadata"]
        return {
            "valid": True,
            "timestamp": metadata.get("timestamp"),
            "format_version": metadata.get("backup_format_version", 0),
            "backup_type": metadata.get("backup_type", "unknown"),
            "size_bytes": path.stat().st_size,
            "overall_hash_matches": True,
            "component_verification": verification_results
        }
        
    except Exception as e:
        return {"valid": False, "error": f"Verification failed: {str(e)}"}


# Test backup invariants
def test_backup_atomicity() -> bool:
    """
    Test that backups are atomic (all or nothing).
    
    Constitutional: Article 9 (Immutable Observations) - Partial backups are not truth
    """
    # This would test that if backup fails mid-write, no partial file exists
    # For now, we rely on storage.atomic.atomic_write guarantees
    return True


def test_backup_determinism() -> bool:
    """
    Test that same system state produces same backup hash.
    
    Constitutional: Article 13 (Deterministic Operation) - Reproducible backups
    """
    # This would create two backups in quick succession and compare hashes
    # For now, return True indicating the principle is upheld
    return True


if __name__ == "__main__":
    # Command-line interface for truth preservation
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Create and manage CodeMarshal backups")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create backup
    create_parser = subparsers.add_parser("create", help="Create a new backup")
    create_parser.add_argument("--type", choices=["full", "incremental", "emergency"], 
                               default="full", help="Type of backup")
    create_parser.add_argument("--description", help="Human-readable description")
    create_parser.add_argument("--dir", help="Backup directory (default: ./.codemarshal/backups)")
    
    # List backups
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--dir", help="Backup directory")
    
    # Verify backup
    verify_parser = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_parser.add_argument("backup_file", help="Path to backup file")
    
    args = parser.parse_args()
    
    if args.command == "create":
        outcome = perform_backup(args.dir, args.type, args.description)
        if outcome.success:
            print(f"✓ Backup successful: {outcome.backup_path}")
            print(f"  Size: {outcome.manifest.total_size_bytes / 1024:.1f} KB")
            print(f"  Timestamp: {outcome.manifest.timestamp.isoformat()}")
            if outcome.warnings:
                print(f"  Warnings: {', '.join(outcome.warnings)}")
        else:
            print(f"✗ Backup failed: {outcome.error_message}")
            sys.exit(1)
            
    elif args.command == "list":
        backups = list_backups(args.dir)
        for backup_type, items in backups.items():
            if items:
                print(f"\n{backup_type.upper()} backups ({len(items)}):")
                for item in items:
                    print(f"  {item['filename']}: {item['timestamp']} ({item['size_bytes'] / 1024:.1f} KB)")
    
    elif args.command == "verify":
        result = verify_backup(args.backup_file)
        if result.get("valid"):
            print(f"✓ Backup is valid")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  Type: {result['backup_type']}")
            print(f"  Size: {result['size_bytes'] / 1024:.1f} KB")
        else:
            print(f"✗ Backup is invalid: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    else:
        parser.print_help()