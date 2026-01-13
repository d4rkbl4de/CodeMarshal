"""
Prohibitions Package Initialization
===================================

Exposes enforcement functions for constitutional constraints in truth-critical modules.
This package provides the guardians against integrity violations without performing
observation or computation itself.

Design Principle: Only provide access to enforcement routines; no side effects.
"""

from typing import List, Dict, Any

# Import prohibition enforcement functions from individual modules
# We use try/except to allow independent development of modules
try:
    from .no_network import enforce_no_network, validate_no_network_access, install_network_guard
    NO_NETWORK_AVAILABLE = True
except ImportError:
    NO_NETWORK_AVAILABLE = False
    # Create stubs for missing functions
    def enforce_no_network() -> List[Dict[str, str]]:
        """Stub function when no_network module is not available."""
        return [{
            "violation": "module_missing",
            "module": "integrity.prohibitions.no_network",
            "details": "No network prohibition module is not available",
            "timestamp": "1900-01-01T00:00:00Z"
        }]
    
    def validate_no_network_access() -> bool:
        """Stub function when no_network module is not available."""
        return False
        
    def install_network_guard() -> Any:
        """Stub function when no_network module is not available."""
        raise ImportError("No network prohibition module is not available")

try:
    from .no_runtime_imports import enforce_no_runtime_imports, validate_import_staticness, install_import_hook
    NO_RUNTIME_IMPORTS_AVAILABLE = True
except ImportError:
    NO_RUNTIME_IMPORTS_AVAILABLE = False
    # Create stubs for missing functions
    def enforce_no_runtime_imports() -> List[Dict[str, str]]:
        """Stub function when no_runtime_imports module is not available."""
        return [{
            "violation": "module_missing",
            "module": "integrity.prohibitions.no_runtime_imports",
            "details": "No runtime imports prohibition module is not available",
            "timestamp": "1900-01-01T00:00:00Z"
        }]
    
    def validate_import_staticness() -> bool:
        """Stub function when no_runtime_imports module is not available."""
        return False
        
    def install_import_hook() -> None:
        """Stub function when no_runtime_imports module is not available."""
        raise ImportError("No runtime imports prohibition module is not available")

try:
    from .no_mutation import enforce_no_mutation, validate_no_mutation, install_mutation_guard
    NO_MUTATION_AVAILABLE = True
except ImportError:
    NO_MUTATION_AVAILABLE = False
    # Create stubs for missing functions
    def enforce_no_mutation() -> List[Dict[str, str]]:
        """Stub function when no_mutation module is not available."""
        return [{
            "violation": "module_missing",
            "module": "integrity.prohibitions.no_mutation",
            "details": "No mutation prohibition module is not available",
            "timestamp": "1900-01-01T00:00:00Z"
        }]
    
    def validate_no_mutation() -> bool:
        """Stub function when no_mutation module is not available."""
        return False
        
    def install_mutation_guard() -> Any:
        """Stub function when no_mutation module is not available."""
        raise ImportError("No mutation prohibition module is not available")


# Module availability tracking
MODULE_AVAILABILITY = {
    "no_network": NO_NETWORK_AVAILABLE,
    "no_runtime_imports": NO_RUNTIME_IMPORTS_AVAILABLE,
    "no_mutation": NO_MUTATION_AVAILABLE,
}


def get_available_prohibitions() -> List[str]:
    """
    Get list of available prohibition enforcement modules.
    
    Returns:
        List of module names that are available.
    """
    return [name for name, available in MODULE_AVAILABILITY.items() if available]


def get_missing_prohibitions() -> List[str]:
    """
    Get list of missing prohibition enforcement modules.
    
    Returns:
        List of module names that are not available.
    """
    return [name for name, available in MODULE_AVAILABILITY.items() if not available]


def validate_all_prohibitions() -> Dict[str, Dict[str, Any]]:
    """
    Run all available prohibition validations.
    
    Returns:
        Dictionary with validation results for each available prohibition.
        Structure:
        {
            "no_network": {
                "available": bool,
                "passed": bool,
                "violations": List[Dict],
                "error": Optional[str]
            },
            ...
        }
    """
    results = {}
    
    # Validate no network
    results["no_network"] = {
        "available": NO_NETWORK_AVAILABLE,
        "passed": False,
        "violations": [],
        "error": None
    }
    
    if NO_NETWORK_AVAILABLE:
        try:
            violations = enforce_no_network()
            results["no_network"]["violations"] = violations
            results["no_network"]["passed"] = len(violations) == 0
        except Exception as e:
            results["no_network"]["error"] = str(e)
    else:
        results["no_network"]["error"] = "Module not available"
        
    # Validate no runtime imports
    results["no_runtime_imports"] = {
        "available": NO_RUNTIME_IMPORTS_AVAILABLE,
        "passed": False,
        "violations": [],
        "error": None
    }
    
    if NO_RUNTIME_IMPORTS_AVAILABLE:
        try:
            violations = enforce_no_runtime_imports()
            results["no_runtime_imports"]["violations"] = violations
            results["no_runtime_imports"]["passed"] = len(violations) == 0
        except Exception as e:
            results["no_runtime_imports"]["error"] = str(e)
    else:
        results["no_runtime_imports"]["error"] = "Module not available"
        
    # Validate no mutation
    results["no_mutation"] = {
        "available": NO_MUTATION_AVAILABLE,
        "passed": False,
        "violations": [],
        "error": None
    }
    
    if NO_MUTATION_AVAILABLE:
        try:
            violations = enforce_no_mutation()
            results["no_mutation"]["violations"] = violations
            results["no_mutation"]["passed"] = len(violations) == 0
        except Exception as e:
            results["no_mutation"]["error"] = str(e)
    else:
        results["no_mutation"]["error"] = "Module not available"
        
    return results


def enforce_all_prohibitions() -> List[Dict[str, str]]:
    """
    Run all available prohibition enforcements and collect all violations.
    
    Returns:
        Combined list of all violations from all available prohibition checks.
    """
    all_violations: List[Dict[str, str]] = []
    
    if NO_NETWORK_AVAILABLE:
        try:
            network_violations = enforce_no_network()
            all_violations.extend(network_violations)
        except Exception:
            pass  # Skip if module fails
            
    if NO_RUNTIME_IMPORTS_AVAILABLE:
        try:
            import_violations = enforce_no_runtime_imports()
            all_violations.extend(import_violations)
        except Exception:
            pass  # Skip if module fails
            
    if NO_MUTATION_AVAILABLE:
        try:
            mutation_violations = enforce_no_mutation()
            all_violations.extend(mutation_violations)
        except Exception:
            pass  # Skip if module fails
            
    return all_violations


def install_all_guards() -> Dict[str, Any]:
    """
    Install all available runtime guards.
    
    Returns:
        Dictionary of installed guards for later removal.
        
    WARNING: This is invasive and should only be used in test environments.
    """
    guards = {}
    
    if NO_NETWORK_AVAILABLE:
        try:
            network_guard = install_network_guard()
            guards["network"] = network_guard
        except Exception as e:
            guards["network_error"] = str(e)
            
    if NO_RUNTIME_IMPORTS_AVAILABLE:
        try:
            install_import_hook()
            guards["import_hook"] = "installed"
        except Exception as e:
            guards["import_hook_error"] = str(e)
            
    if NO_MUTATION_AVAILABLE:
        try:
            mutation_guard = install_mutation_guard()
            guards["mutation"] = mutation_guard
        except Exception as e:
            guards["mutation_error"] = str(e)
            
    return guards


# Public interface
__all__ = [
    # Primary enforcement functions
    "enforce_no_network",
    "enforce_no_runtime_imports", 
    "enforce_no_mutation",
    
    # Validation functions
    "validate_no_network_access",
    "validate_import_staticness",
    "validate_no_mutation",
    
    # Guard installation functions
    "install_network_guard",
    "install_import_hook",
    "install_mutation_guard",
    
    # Combined operations
    "enforce_all_prohibitions",
    "validate_all_prohibitions",
    "install_all_guards",
    
    # Information functions
    "get_available_prohibitions",
    "get_missing_prohibitions",
    
    # Module availability flags
    "NO_NETWORK_AVAILABLE",
    "NO_RUNTIME_IMPORTS_AVAILABLE",
    "NO_MUTATION_AVAILABLE",
    "MODULE_AVAILABILITY",
]


# Module metadata
__version__ = "1.0.0"
__author__ = "CodeMarshal Integrity Team"
__description__ = "Truth-preserving prohibition enforcement for constitutional constraints"
__license__ = "Constitutional"


# Export all symbols for clean imports
__all_symbols__ = {
    "enforce": [
        "enforce_no_network",
        "enforce_no_runtime_imports",
        "enforce_no_mutation",
        "enforce_all_prohibitions",
    ],
    "validate": [
        "validate_no_network_access",
        "validate_import_staticness", 
        "validate_no_mutation",
        "validate_all_prohibitions",
    ],
    "guards": [
        "install_network_guard",
        "install_import_hook",
        "install_mutation_guard",
        "install_all_guards",
    ],
    "info": [
        "get_available_prohibitions",
        "get_missing_prohibitions",
    ],
    "metadata": [
        "NO_NETWORK_AVAILABLE",
        "NO_RUNTIME_IMPORTS_AVAILABLE",
        "NO_MUTATION_AVAILABLE",
        "MODULE_AVAILABILITY",
    ],
}


# Module docstring for help() and introspection
__doc__ = """
CodeMarshal Integrity Prohibitions Module
=========================================

This module provides enforcement mechanisms for constitutional constraints
in truth-critical parts of the CodeMarshal system.

Constitutional Constraints Enforced:
1. No Network Access (Tier 12: Local Operation)
2. No Runtime Imports (Tier 1: Observation Purity) 
3. No Mutation (Tier 9: Immutable Observations)

Usage Examples:
    >>> from integrity.prohibitions import enforce_all_prohibitions
    >>> violations = enforce_all_prohibitions()
    >>> if violations:
    ...     print(f"Found {len(violations)} constitutional violations")
    
    >>> from integrity.prohibitions import validate_all_prohibitions
    >>> results = validate_all_prohibitions()
    >>> for prohibition, result in results.items():
    ...     print(f"{prohibition}: {'PASS' if result['passed'] else 'FAIL'}")
    
    >>> # For test environments only:
    >>> from integrity.prohibitions import install_all_guards
    >>> guards = install_all_guards()
    >>> # ... run tests ...
    >>> # Guards are automatically cleaned up on test completion

Design Principles:
- No observation or computation in this module
- Only provide access to enforcement routines
- Graceful degradation when modules are missing
- Clear, typed interfaces for all functions
- Runtime guards only for test environments
"""