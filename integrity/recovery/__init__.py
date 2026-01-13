"""
integrity/recovery/__init__.py

TRUTH RECOVERY GATEWAY - TIER 14 (GRACEFUL DEGRADATION)

Purpose: Single import point for all recovery operations with integrity guarantees.
Principle: Recovery should be accessible, auditable, and deterministic.
Constitutional: Article 14 (Graceful Degradation), Article 21 (Self-Validation)
"""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Import recovery modules with explicit type hints
from .backup import (
    perform_backup,
    BackupOutcome,
    BackupManifest,
    list_backups,
    verify_backup,
    cleanup_old_backups,
    create_backup_directory,
    collect_observations_snapshot,
    collect_investigation_state,
    collect_configuration,
    compute_component_hash,
    test_backup_atomicity,
    test_backup_determinism
)

from .restore import (
    perform_restore,
    RestorationOutcome,
    validate_backup_file,
    compute_current_observation_hash,
    create_restoration_checkpoint,
    list_available_backups,
    get_backup_info,
    test_restoration_determinism,
    test_restoration_rollback_safety
)

from .audit import (
    log_audit_event,
    AuditEvent,
    AuditChain,
    AuditSummary,
    create_audit_directory,
    compute_event_hash,
    verify_audit_chain,
    query_audit_events,
    create_audit_summary,
    export_audit_trail,
    cleanup_old_audit_logs,
    audit_recovery,
    audit_observation,
    audit_system,
    test_audit_immutability,
    test_audit_chain_integrity
)

# Re-export all public functions and types
__all__ = [
    # Backup functions
    "perform_backup",
    "BackupOutcome",
    "BackupManifest",
    "list_backups",
    "verify_backup",
    "cleanup_old_backups",
    "create_backup_directory",
    "collect_observations_snapshot",
    "collect_investigation_state",
    "collect_configuration",
    "compute_component_hash",
    "test_backup_atomicity",
    "test_backup_determinism",
    
    # Restore functions
    "perform_restore",
    "RestorationOutcome",
    "validate_backup_file",
    "compute_current_observation_hash",
    "create_restoration_checkpoint",
    "list_available_backups",
    "get_backup_info",
    "test_restoration_determinism",
    "test_restoration_rollback_safety",
    
    # Audit functions
    "log_audit_event",
    "AuditEvent",
    "AuditChain",
    "AuditSummary",
    "create_audit_directory",
    "compute_event_hash",
    "verify_audit_chain",
    "query_audit_events",
    "create_audit_summary",
    "export_audit_trail",
    "cleanup_old_audit_logs",
    "audit_recovery",
    "audit_observation",
    "audit_system",
    "test_audit_immutability",
    "test_audit_chain_integrity",
    
    # Convenience functions
    "run_full_recovery_cycle",
    "validate_recovery_system",
    "get_recovery_status"
]


# Convenience functions for common recovery patterns
def run_full_recovery_cycle(
    backup_dir: Optional[str] = None,
    audit_dir: Optional[str] = None
) -> Tuple[BackupOutcome, Dict[str, Any]]:
    """
    Run a complete backup-verify-audit cycle.
    
    Constitutional: Article 8 (Honest Performance) - Complete operation with verification
    
    Args:
        backup_dir: Directory for backups (default: ./.codemarshal/backups)
        audit_dir: Directory for audit logs (default: ./.codemarshal/audit_logs)
        
    Returns:
        Tuple of (backup_outcome, verification_results)
    """
    from datetime import datetime, timezone
    
    cycle_start = datetime.now(timezone.utc)
    
    # Step 1: Create backup
    backup_outcome = perform_backup(
        backup_root=backup_dir,
        backup_type="full",
        description=f"Recovery cycle backup at {cycle_start.isoformat()}"
    )
    
    verification_results = {
        "cycle_start": cycle_start.isoformat(),
        "backup_success": backup_outcome.success,
        "verification_steps": []
    }
    
    if backup_outcome.success and backup_outcome.backup_path:
        # Step 2: Verify backup
        verify_result = verify_backup(str(backup_outcome.backup_path))
        verification_results["backup_verification"] = verify_result
        verification_results["verification_steps"].append("backup_verified")
        
        # Step 3: Audit the backup
        audit_event = audit_recovery(
            action="recovery_cycle_complete",
            metadata={
                "cycle_start": cycle_start.isoformat(),
                "backup_path": str(backup_outcome.backup_path),
                "backup_success": backup_outcome.success,
                "verification_result": verify_result.get("valid", False),
                "manifest": backup_outcome.manifest._asdict() if backup_outcome.manifest else None
            }
        )
        verification_results["audit_event_id"] = audit_event.event_id
        verification_results["verification_steps"].append("audit_logged")
    
    # Step 4: Validate audit chain
    if audit_dir:
        audit_root = Path(audit_dir)
        audit_summary = create_audit_summary(audit_root)
        verification_results["audit_summary"] = audit_summary._asdict()
        verification_results["verification_steps"].append("audit_validated")
    
    cycle_end = datetime.now(timezone.utc)
    verification_results["cycle_end"] = cycle_end.isoformat()
    verification_results["duration_seconds"] = (cycle_end - cycle_start).total_seconds()
    
    return backup_outcome, verification_results


def validate_recovery_system(
    test_backup: bool = True,
    test_restore: bool = True,
    test_audit: bool = True
) -> Dict[str, Any]:
    """
    Validate the entire recovery system through self-tests.
    
    Constitutional: Article 21 (Self-Validation) - System must verify itself
    
    Args:
        test_backup: Run backup system tests
        test_restore: Run restore system tests
        test_audit: Run audit system tests
        
    Returns:
        Dictionary with test results
    """
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "tests_run": [],
        "tests_passed": [],
        "tests_failed": [],
        "overall_valid": True
    }
    
    # Backup system tests
    if test_backup:
        validation_results["tests_run"].append("backup_atomicity")
        if test_backup_atomicity():
            validation_results["tests_passed"].append("backup_atomicity")
        else:
            validation_results["tests_failed"].append("backup_atomicity")
            validation_results["overall_valid"] = False
        
        validation_results["tests_run"].append("backup_determinism")
        if test_backup_determinism():
            validation_results["tests_passed"].append("backup_determinism")
        else:
            validation_results["tests_failed"].append("backup_determinism")
            validation_results["overall_valid"] = False
    
    # Restore system tests
    if test_restore:
        validation_results["tests_run"].append("restore_determinism")
        if test_restoration_determinism():
            validation_results["tests_passed"].append("restore_determinism")
        else:
            validation_results["tests_failed"].append("restore_determinism")
            validation_results["overall_valid"] = False
        
        validation_results["tests_run"].append("restore_rollback_safety")
        if test_restoration_rollback_safety():
            validation_results["tests_passed"].append("restore_rollback_safety")
        else:
            validation_results["tests_failed"].append("restore_rollback_safety")
            validation_results["overall_valid"] = False
    
    # Audit system tests
    if test_audit:
        validation_results["tests_run"].append("audit_immutability")
        if test_audit_immutability():
            validation_results["tests_passed"].append("audit_immutability")
        else:
            validation_results["tests_failed"].append("audit_immutability")
            validation_results["overall_valid"] = False
        
        validation_results["tests_run"].append("audit_chain_integrity")
        if test_audit_chain_integrity():
            validation_results["tests_passed"].append("audit_chain_integrity")
        else:
            validation_results["tests_failed"].append("audit_chain_integrity")
            validation_results["overall_valid"] = False
    
    # Log the validation results
    audit_recovery(
        action="recovery_system_validation",
        metadata={
            "timestamp": validation_results["timestamp"],
            "tests_run": len(validation_results["tests_run"]),
            "tests_passed": len(validation_results["tests_passed"]),
            "tests_failed": len(validation_results["tests_failed"]),
            "overall_valid": validation_results["overall_valid"]
        }
    )
    
    return validation_results


def get_recovery_status(
    backup_dir: Optional[str] = None,
    audit_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get comprehensive status of recovery system.
    
    Constitutional: Article 7 (Clear Affordances) - Show system state clearly
    
    Args:
        backup_dir: Backup directory to check
        audit_dir: Audit directory to check
        
    Returns:
        Dictionary with system status
    """
    from datetime import datetime, timezone
    
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {},
        "health": "unknown"
    }
    
    # Check backup system
    try:
        backup_root = create_backup_directory(Path(backup_dir) if backup_dir else None)
        backups = list_backups(str(backup_root))
        
        backup_counts = {k: len(v) for k, v in backups.items()}
        total_backups = sum(backup_counts.values())
        
        status["components"]["backup"] = {
            "available": True,
            "backup_counts": backup_counts,
            "total_backups": total_backups,
            "directory": str(backup_root)
        }
    except Exception as e:
        status["components"]["backup"] = {
            "available": False,
            "error": str(e)
        }
    
    # Check audit system
    try:
        audit_root = create_audit_directory(Path(audit_dir) if audit_dir else None)
        audit_summary = create_audit_summary(audit_root)
        
        status["components"]["audit"] = {
            "available": True,
            "total_events": audit_summary.total_events,
            "chain_integrity": audit_summary.valid_chain,
            "broken_links": audit_summary.broken_links,
            "time_range_days": audit_summary.time_range_days,
            "directory": str(audit_root)
        }
    except Exception as e:
        status["components"]["audit"] = {
            "available": False,
            "error": str(e)
        }
    
    # Determine overall health
    components_available = all(
        comp["available"] for comp in status["components"].values()
    )
    
    if not components_available:
        status["health"] = "degraded"
    elif status.get("components", {}).get("audit", {}).get("chain_integrity", True) == False:
        status["health"] = "compromised"
    elif status.get("components", {}).get("backup", {}).get("total_backups", 0) == 0:
        status["health"] = "unprepared"
    else:
        status["health"] = "healthy"
    
    return status


# Module-level recovery system initialization
def _initialize_recovery_system() -> None:
    """
    Initialize recovery system on module import.
    
    Constitutional: Article 14 (Graceful Degradation) - Initialize but don't fail hard
    """
    try:
        # Create necessary directories
        backup_dir = create_backup_directory()
        audit_dir = create_audit_directory()
        
        # Log system initialization
        audit_recovery(
            action="recovery_system_initialized",
            metadata={
                "backup_directory": str(backup_dir),
                "audit_directory": str(audit_dir),
                "module_version": "1.0.0",
                "initialization_time": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        # Don't raise on initialization failure - system should still work
        # Just log the error
        from integrity.monitoring.errors import log_error, ErrorSeverity
        log_error(f"Recovery system initialization failed: {e}", severity=ErrorSeverity.MEDIUM)


# Initialize on module import
_initialize_recovery_system()


# Export version information
__version__ = "1.0.0"
__author__ = "CodeMarshal Recovery System"
__description__ = "Truth-preserving recovery system for CodeMarshal"
__constitutional_compliance__ = [
    "Article 1: Observation Purity",
    "Article 9: Immutable Observations", 
    "Article 13: Deterministic Operation",
    "Article 14: Graceful Degradation",
    "Article 15: Session Integrity",
    "Article 19: Backward Truth Compatibility",
    "Article 21: Self-Validation"
]