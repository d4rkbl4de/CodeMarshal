"""
Integrity Package Initialization
================================

The integrity system ensures CodeMarshal follows its own constitution and 
preserves truth throughout its operation.

This package provides:
1. Validation of constitutional compliance (Tier 1-4)
2. Monitoring for truth drift and performance issues
3. Prohibition enforcement (no network, no runtime imports, no mutation)
4. Recovery mechanisms for system corruption

Design Principle: The system must validate its own truth-preserving behavior.
"""

import sys
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timezone

# Type stubs for forward references
class ValidationResult:
    """Result of a validation check."""
    def __init__(
        self,
        passed: bool = False,
        violations: Optional[List[Dict[str, str]]] = None,
        details: Optional[str] = None
    ) -> None:
        self.passed = passed
        self.violations = violations or []
        self.details = details
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "violations": self.violations,
            "details": self.details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class MonitoringAlert:
    """Alert from monitoring system."""
    def __init__(
        self,
        alert_type: str,
        severity: str,
        message: str,
        location: Optional[Dict[str, str]] = None
    ) -> None:
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.location = location or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "timestamp": self.timestamp
        }


# Initialize subpackage availability flags
VALIDATION_AVAILABLE: bool = False
MONITORING_AVAILABLE: bool = False
PROHIBITIONS_AVAILABLE: bool = False
RECOVERY_AVAILABLE: bool = False

# Initialize function stubs
def _stub_validate_observations() -> ValidationResult:
    """Stub function when validation module is not available."""
    return ValidationResult(
        passed=False,
        details="Validation module not available"
    )


def _stub_validate_patterns() -> ValidationResult:
    """Stub function when patterns validation is not available."""
    return ValidationResult(
        passed=False,
        details="Patterns validation not available"
    )


def _stub_validate_interface() -> ValidationResult:
    """Stub function when interface validation is not available."""
    return ValidationResult(
        passed=False,
        details="Interface validation not available"
    )


def _stub_validate_integration() -> ValidationResult:
    """Stub function when integration validation is not available."""
    return ValidationResult(
        passed=False,
        details="Integration validation not available"
    )


def _stub_monitor_drift() -> List[MonitoringAlert]:
    """Stub function when drift monitoring is not available."""
    return [MonitoringAlert(
        alert_type="module_missing",
        severity="warning",
        message="Drift monitoring module not available"
    )]


def _stub_monitor_performance() -> List[MonitoringAlert]:
    """Stub function when performance monitoring is not available."""
    return [MonitoringAlert(
        alert_type="module_missing",
        severity="warning",
        message="Performance monitoring module not available"
    )]


def _stub_monitor_errors() -> List[MonitoringAlert]:
    """Stub function when error monitoring is not available."""
    return [MonitoringAlert(
        alert_type="module_missing",
        severity="warning",
        message="Error monitoring module not available"
    )]


def _stub_create_backup() -> bool:
    """Stub function when backup system is not available."""
    return False


def _stub_restore_backup() -> bool:
    """Stub function when restore system is not available."""
    return False


def _stub_run_audit() -> Dict[str, Any]:
    """Stub function when audit system is not available."""
    return {
        "status": "unavailable",
        "message": "Audit system not available",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Initialize public functions with stubs
validate_observations: Callable[[], ValidationResult] = _stub_validate_observations
validate_patterns: Callable[[], ValidationResult] = _stub_validate_patterns
validate_interface: Callable[[], ValidationResult] = _stub_validate_interface
validate_integration: Callable[[], ValidationResult] = _stub_validate_integration

monitor_drift: Callable[[], List[MonitoringAlert]] = _stub_monitor_drift
monitor_performance: Callable[[], List[MonitoringAlert]] = _stub_monitor_performance
monitor_errors: Callable[[], List[MonitoringAlert]] = _stub_monitor_errors

create_backup: Callable[[], bool] = _stub_create_backup
restore_backup: Callable[[], bool] = _stub_restore_backup
run_audit: Callable[[], Dict[str, Any]] = _stub_run_audit


# Try to import from validation subpackage
try:
    from .validation.observations_test import validate_observations as real_validate_observations
    validate_observations = real_validate_observations
    VALIDATION_AVAILABLE = True
except ImportError:
    pass
except Exception:
    pass


try:
    from .validation.patterns_test import validate_patterns as real_validate_patterns
    validate_patterns = real_validate_patterns
    VALIDATION_AVAILABLE = VALIDATION_AVAILABLE or True
except ImportError:
    pass
except Exception:
    pass


try:
    from .validation.interface_test import validate_interface as real_validate_interface
    validate_interface = real_validate_interface
    VALIDATION_AVAILABLE = VALIDATION_AVAILABLE or True
except ImportError:
    pass
except Exception:
    pass


try:
    from .validation.integration_test import validate_integration as real_validate_integration
    validate_integration = real_validate_integration
    VALIDATION_AVAILABLE = VALIDATION_AVAILABLE or True
except ImportError:
    pass
except Exception:
    pass


# Try to import from monitoring subpackage
try:
    from .monitoring.drift import monitor_drift as real_monitor_drift
    monitor_drift = real_monitor_drift
    MONITORING_AVAILABLE = True
except ImportError:
    pass
except Exception:
    pass


try:
    from .monitoring.performance import monitor_performance as real_monitor_performance
    monitor_performance = real_monitor_performance
    MONITORING_AVAILABLE = MONITORING_AVAILABLE or True
except ImportError:
    pass
except Exception:
    pass


try:
    from .monitoring.errors import monitor_errors as real_monitor_errors
    monitor_errors = real_monitor_errors
    MONITORING_AVAILABLE = MONITORING_AVAILABLE or True
except ImportError:
    pass
except Exception:
    pass


# Try to import from prohibitions subpackage
try:
    from .prohibitions import (
        enforce_all_prohibitions,
        validate_all_prohibitions,
        get_available_prohibitions,
        get_missing_prohibitions,
        NO_NETWORK_AVAILABLE,
        NO_RUNTIME_IMPORTS_AVAILABLE,
        NO_MUTATION_AVAILABLE,
        MODULE_AVAILABILITY as PROHIBITIONS_AVAILABILITY
    )
    PROHIBITIONS_AVAILABLE = True
except ImportError:
    # Create stub functions for prohibitions
    def enforce_all_prohibitions() -> List[Dict[str, str]]:
        return [{
            "violation": "module_missing",
            "module": "integrity.prohibitions",
            "details": "Prohibitions module not available",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    
    def validate_all_prohibitions() -> Dict[str, Dict[str, Any]]:
        return {
            "prohibitions": {
                "available": False,
                "passed": False,
                "violations": [],
                "error": "Module not available"
            }
        }
    
    def get_available_prohibitions() -> List[str]:
        return []
    
    def get_missing_prohibitions() -> List[str]:
        return ["no_network", "no_runtime_imports", "no_mutation"]
    
    NO_NETWORK_AVAILABLE = False
    NO_RUNTIME_IMPORTS_AVAILABLE = False
    NO_MUTATION_AVAILABLE = False
    PROHIBITIONS_AVAILABILITY = {
        "no_network": False,
        "no_runtime_imports": False,
        "no_mutation": False
    }
except Exception:
    # Re-raise the same stubs for any other error
    pass


# Try to import from recovery subpackage
try:
    from .recovery.backup import create_backup as real_create_backup
    create_backup = real_create_backup
    RECOVERY_AVAILABLE = True
except ImportError:
    pass
except Exception:
    pass


try:
    from .recovery.restore import restore_backup as real_restore_backup
    restore_backup = real_restore_backup
    RECOVERY_AVAILABLE = RECOVERY_AVAILABLE or True
except ImportError:
    pass
except Exception:
    pass


try:
    from .recovery.audit import run_audit as real_run_audit
    run_audit = real_run_audit
    RECOVERY_AVAILABLE = RECOVERY_AVAILABLE or True
except ImportError:
    pass
except Exception:
    pass


# Combined integrity functions
def run_full_integrity_check() -> Dict[str, Any]:
    """
    Run all integrity checks and return comprehensive results.
    
    Returns:
        Dictionary with results from all integrity subsystems.
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_passed": True,
        "subsystems": {}
    }
    
    # Run validation checks
    validation_results = {}
    
    try:
        obs_result = validate_observations()
        validation_results["observations"] = obs_result.to_dict()
        results["overall_passed"] = results["overall_passed"] and obs_result.passed
    except Exception as e:
        validation_results["observations"] = {
            "passed": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        results["overall_passed"] = False
    
    try:
        patterns_result = validate_patterns()
        validation_results["patterns"] = patterns_result.to_dict()
        results["overall_passed"] = results["overall_passed"] and patterns_result.passed
    except Exception as e:
        validation_results["patterns"] = {
            "passed": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        results["overall_passed"] = False
    
    try:
        interface_result = validate_interface()
        validation_results["interface"] = interface_result.to_dict()
        results["overall_passed"] = results["overall_passed"] and interface_result.passed
    except Exception as e:
        validation_results["interface"] = {
            "passed": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        results["overall_passed"] = False
    
    try:
        integration_result = validate_integration()
        validation_results["integration"] = integration_result.to_dict()
        results["overall_passed"] = results["overall_passed"] and integration_result.passed
    except Exception as e:
        validation_results["integration"] = {
            "passed": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        results["overall_passed"] = False
    
    results["subsystems"]["validation"] = {
        "available": VALIDATION_AVAILABLE,
        "results": validation_results
    }
    
    # Run monitoring checks
    monitoring_alerts = {}
    
    try:
        drift_alerts = monitor_drift()
        monitoring_alerts["drift"] = [alert.to_dict() for alert in drift_alerts]
        if drift_alerts:
            results["overall_passed"] = False
    except Exception as e:
        monitoring_alerts["drift"] = [{
            "alert_type": "error",
            "severity": "critical",
            "message": f"Drift monitoring failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
        results["overall_passed"] = False
    
    try:
        performance_alerts = monitor_performance()
        monitoring_alerts["performance"] = [alert.to_dict() for alert in performance_alerts]
        if performance_alerts:
            results["overall_passed"] = False
    except Exception as e:
        monitoring_alerts["performance"] = [{
            "alert_type": "error",
            "severity": "critical",
            "message": f"Performance monitoring failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
        results["overall_passed"] = False
    
    try:
        error_alerts = monitor_errors()
        monitoring_alerts["errors"] = [alert.to_dict() for alert in error_alerts]
        if error_alerts:
            results["overall_passed"] = False
    except Exception as e:
        monitoring_alerts["errors"] = [{
            "alert_type": "error",
            "severity": "critical",
            "message": f"Error monitoring failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
        results["overall_passed"] = False
    
    results["subsystems"]["monitoring"] = {
        "available": MONITORING_AVAILABLE,
        "alerts": monitoring_alerts
    }
    
    # Run prohibition checks
    try:
        prohibition_results = validate_all_prohibitions()
        results["subsystems"]["prohibitions"] = {
            "available": PROHIBITIONS_AVAILABLE,
            "results": prohibition_results
        }
        
        # Check if any prohibition failed
        for prohibition, result in prohibition_results.items():
            if result.get("available", False) and not result.get("passed", True):
                results["overall_passed"] = False
    except Exception as e:
        results["subsystems"]["prohibitions"] = {
            "available": PROHIBITIONS_AVAILABLE,
            "error": str(e),
            "results": {}
        }
        results["overall_passed"] = False
    
    # Run recovery audit
    try:
        audit_results = run_audit()
        results["subsystems"]["recovery"] = {
            "available": RECOVERY_AVAILABLE,
            "audit": audit_results
        }
        
        if audit_results.get("status") == "failed":
            results["overall_passed"] = False
    except Exception as e:
        results["subsystems"]["recovery"] = {
            "available": RECOVERY_AVAILABLE,
            "error": str(e),
            "audit": {}
        }
        results["overall_passed"] = False
    
    return results


def get_system_integrity_status() -> str:
    """
    Get a quick summary of system integrity status.
    
    Returns:
        One of: "healthy", "degraded", "critical", "unknown"
    """
    try:
        results = run_full_integrity_check()
        
        if not results["overall_passed"]:
            # Check severity
            critical_violations = 0
            warning_violations = 0
            
            # Check prohibitions
            prohibitions = results.get("subsystems", {}).get("prohibitions", {}).get("results", {})
            for prohibition, result in prohibitions.items():
                if not result.get("passed", True):
                    if prohibition in ["no_network", "no_mutation"]:
                        critical_violations += 1
                    else:
                        warning_violations += 1
            
            # Check monitoring alerts
            monitoring = results.get("subsystems", {}).get("monitoring", {}).get("alerts", {})
            for category, alerts in monitoring.items():
                for alert in alerts:
                    if alert.get("severity") == "critical":
                        critical_violations += 1
                    elif alert.get("severity") == "warning":
                        warning_violations += 1
            
            if critical_violations > 0:
                return "critical"
            elif warning_violations > 0:
                return "degraded"
            else:
                return "unknown"
        
        return "healthy"
        
    except Exception:
        return "unknown"


def log_integrity_violation(
    violation_type: str,
    location: Dict[str, str],
    details: str,
    severity: str = "warning"
) -> None:
    """
    Log an integrity violation to the monitoring system.
    
    This is a convenience function that routes violations to the appropriate
    monitoring subsystem.
    
    Args:
        violation_type: Type of violation (e.g., "network_access", "mutation")
        location: Dictionary with location details (module, function, line)
        details: Human-readable description of the violation
        severity: One of "info", "warning", "critical"
    """
    try:
        # Try to use the monitoring.errors module directly
        from .monitoring.errors import log_integrity_violation as monitor_log
        monitor_log(
            violation_type=violation_type,
            location=location,
            details=details,
            severity=severity
        )
    except ImportError:
        # Fall back to simple logging if monitoring is not available
        import logging
        logger = logging.getLogger(__name__)
        
        log_message = f"Integrity violation [{severity}]: {violation_type}"
        if location:
            log_message += f" at {location}"
        log_message += f" - {details}"
        
        if severity == "critical":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    except Exception as e:
        # Last resort: print to stderr
        import sys as sys_module
        print(f"Failed to log integrity violation: {e}", file=sys_module.stderr)


# Public interface
__all__ = [
    # Validation functions
    "validate_observations",
    "validate_patterns",
    "validate_interface",
    "validate_integration",
    
    # Monitoring functions
    "monitor_drift",
    "monitor_performance",
    "monitor_errors",
    
    # Prohibition functions (imported from prohibitions)
    "enforce_all_prohibitions",
    "validate_all_prohibitions",
    "get_available_prohibitions",
    "get_missing_prohibitions",
    
    # Recovery functions
    "create_backup",
    "restore_backup",
    "run_audit",
    
    # Combined operations
    "run_full_integrity_check",
    "get_system_integrity_status",
    "log_integrity_violation",
    
    # Availability flags
    "VALIDATION_AVAILABLE",
    "MONITORING_AVAILABLE",
    "PROHIBITIONS_AVAILABLE",
    "RECOVERY_AVAILABLE",
    
    # Prohibition availability (re-exported)
    "NO_NETWORK_AVAILABLE",
    "NO_RUNTIME_IMPORTS_AVAILABLE",
    "NO_MUTATION_AVAILABLE",
    "PROHIBITIONS_AVAILABILITY",
    
    # Helper classes
    "ValidationResult",
    "MonitoringAlert",
]


# Module metadata
__version__ = "1.0.0"
__author__ = "CodeMarshal Integrity Team"
__description__ = "Truth-preserving integrity system for constitutional compliance"
__license__ = "Constitutional"


if __name__ == "__main__":
    # Command-line interface for integrity checks
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="Run CodeMarshal integrity checks."
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick status check (healthy/degraded/critical)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full integrity check and output JSON"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run only validation checks"
    )
    parser.add_argument(
        "--monitor-only",
        action="store_true",
        help="Run only monitoring checks"
    )
    parser.add_argument(
        "--prohibitions-only",
        action="store_true",
        help="Run only prohibition checks"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        status = get_system_integrity_status()
        print(f"System integrity status: {status}")
        sys.exit(0 if status == "healthy" else 1)
        
    elif args.full:
        results = run_full_integrity_check()
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["overall_passed"] else 1)
        
    elif args.validate_only:
        # Run validation checks
        validation_results = {}
        for check_name in ["observations", "patterns", "interface", "integration"]:
            try:
                check_func = globals()[f"validate_{check_name}"]
                result = check_func()
                validation_results[check_name] = result.to_dict()
            except Exception as e:
                validation_results[check_name] = {
                    "passed": False,
                    "error": str(e)
                }
        
        print(json.dumps(validation_results, indent=2))
        all_passed = all(r.get("passed", False) for r in validation_results.values())
        sys.exit(0 if all_passed else 1)
        
    elif args.monitor_only:
        # Run monitoring checks
        monitoring_results = {}
        for check_name in ["drift", "performance", "errors"]:
            try:
                check_func = globals()[f"monitor_{check_name}"]
                alerts = check_func()
                monitoring_results[check_name] = [alert.to_dict() for alert in alerts]
            except Exception as e:
                monitoring_results[check_name] = [{
                    "error": str(e)
                }]
        
        print(json.dumps(monitoring_results, indent=2))
        has_alerts = any(len(alerts) > 0 for alerts in monitoring_results.values())
        sys.exit(0 if not has_alerts else 1)
        
    elif args.prohibitions_only:
        # Run prohibition checks
        try:
            results = validate_all_prohibitions()
            print(json.dumps(results, indent=2))
            all_passed = all(
                r.get("passed", True) 
                for r in results.values() 
                if r.get("available", False)
            )
            sys.exit(0 if all_passed else 1)
        except Exception as e:
            print(f"Error running prohibition checks: {e}")
            sys.exit(1)
            
    else:
        # Default: quick check
        status = get_system_integrity_status()
        print(f"System integrity status: {status}")
        if status != "healthy":
            print("\nFor detailed results, run: python -m integrity --full")
        sys.exit(0 if status == "healthy" else 1)