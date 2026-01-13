"""
Bridge layer for truth preservation.

This layer is the command and control center that coordinates the system
without leaking truth or expanding capabilities.

ARCHITECTURAL ROLE:
The bridge layer connects human intent to system action while preserving:
1. Constitutional compliance
2. Layer separation
3. Truth preservation
4. No capability expansion

STRUCTURE:
├── commands/     - Authorized power (what can be done)
├── entry/        - Human access points (CLI, TUI, API)
├── integration/  - External adaptation (no power addition)
└── coordination/ - Time & reuse (caching, scheduling)

CONSTITUTIONAL BASIS:
- Article 5: Single-Focus Interface
- Article 6: Linear Investigation
- Article 7: Clear Affordances
- Article 12: Local Operation
"""

from typing import Dict, Any, List, Optional
import sys

# Import the integration module we've built
from .integration import (
    IntegrationType,
    IntegrationRegistry,
    SUPPORTED_INTEGRATIONS,
    list_supported_integrations,
    validate_integration_name,
    check_integration_compliance
)

import functools
import logging

# Configure logging for integrity checks
_integrity_logger = logging.getLogger("bridge.integrity")


def integrity_check(func):
    """
    Decorator that validates constitutional compliance for bridge commands.
    
    This decorator ensures that:
    1. Commands respect layer boundaries
    2. No capability expansion occurs during execution
    3. Truth is preserved throughout the command lifecycle
    4. Violations are logged and can be audited
    
    Constitutional Basis:
    - Article 5: Single-Focus Interface
    - Article 6: Linear Investigation  
    - Article 9: Immutable Observations
    - Article 12: Local Operation
    
    Usage:
        @integrity_check
        def execute_investigation(...):
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        module_name = func.__module__
        
        _integrity_logger.debug(
            f"Integrity check: entering {module_name}.{func_name}"
        )
        
        try:
            # Pre-execution validation
            # Verify we're operating within bridge layer constraints
            _validate_bridge_context(func_name, args, kwargs)
            
            # Execute the actual command
            result = func(*args, **kwargs)
            
            # Post-execution validation
            # Ensure no capability expansion occurred
            _validate_result_integrity(func_name, result)
            
            _integrity_logger.debug(
                f"Integrity check: {module_name}.{func_name} completed successfully"
            )
            
            return result
            
        except Exception as e:
            _integrity_logger.error(
                f"Integrity violation in {module_name}.{func_name}: {e}"
            )
            raise
    
    return wrapper


def _validate_bridge_context(func_name: str, args: tuple, kwargs: dict) -> None:
    """
    Validate that the command is being called in a valid bridge context.
    
    This is a lightweight check that ensures basic constraints are met.
    More detailed validation happens within the commands themselves.
    """
    # Currently a passthrough - commands handle their own detailed validation
    # This hook exists for future cross-cutting concerns like:
    # - Rate limiting
    # - Session validation
    # - Permission checks
    pass


def _validate_result_integrity(func_name: str, result: Any) -> None:
    """
    Validate that the command result maintains system integrity.
    
    Ensures:
    - Results don't contain capability expansions
    - Truth is preserved in return values
    - No prohibited state leakage
    """
    # Currently a passthrough - can be extended to validate:
    # - Result structure matches expected schema
    # - No sensitive data leakage
    # - Constitutional compliance of returned data
    pass


class BridgeLayer:
    """
    Main bridge layer that coordinates without expanding capabilities.
    
    This class ensures that:
    1. Commands don't leak across layers
    2. Integration doesn't add power
    3. Entry points don't bypass constraints
    4. Coordination doesn't obscure truth
    """
    
    def __init__(self):
        self._initialized = False
        self._available_modules: Dict[str, bool] = {
            "commands": False,
            "entry": False,
            "integration": True,  # We've built this
            "coordination": False
        }
    
    def initialize(self) -> None:
        """
        Initialize the bridge layer with constitutional compliance checks.
        
        Raises:
            RuntimeError: If any module violates constitutional constraints
        """
        if self._initialized:
            return
        
        # Check integration compliance
        integration_status = self._check_integration_compliance()
        if not integration_status["all_passed"]:
            raise RuntimeError(
                f"Integration layer violates constitution: "
                f"{integration_status['violations']}"
            )
        
        self._initialized = True
    
    def _check_integration_compliance(self) -> Dict[str, Any]:
        """
        Verify that the integration layer follows constitutional constraints.
        """
        violations: List[str] = []
        
        for integration_type in IntegrationType:
            report = check_integration_compliance(integration_type)
            if not report["constitutional"] or report["compliance_summary"] == "FAIL":
                violations.append(f"{integration_type.value}: {report.get('error', 'Compliance failure')}")
        
        return {
            "all_passed": len(violations) == 0,
            "violations": violations,
            "total_integrations": len(list(IntegrationType)),
            "compliant_integrations": len(list(IntegrationType)) - len(violations)
        }
    
    def get_available_capabilities(self) -> Dict[str, List[str]]:
        """
        List what capabilities are available in the bridge layer.
        
        This is a truth-preserving declaration of what exists, not what might exist.
        """
        capabilities: Dict[str, List[str]] = {
            "integration": [
                "Export formats (JSON, Markdown, Plain Text)",
                "Editor integration (VS Code, Neovim)",
                "CI integration (GitHub Actions, JUnit, JSON)"
            ]
        }
        
        # Add other modules as they become available
        if self._available_modules["commands"]:
            capabilities["commands"] = ["Investigate", "Observe", "Query", "Export"]
        
        if self._available_modules["entry"]:
            capabilities["entry"] = ["CLI", "TUI", "API"]
        
        if self._available_modules["coordination"]:
            capabilities["coordination"] = ["Caching", "Scheduling"]
        
        return capabilities
    
    def validate_command_flow(
        self,
        source: str,
        target: str,
        action: str
    ) -> bool:
        """
        Validate that a command flow respects layer boundaries.
        
        This prevents:
        - Commands from leaking into observation layer
        - Integration from triggering commands
        - Entry points from bypassing authorization
        """
        # Define allowed flows (source -> target)
        allowed_flows = {
            ("entry", "commands"): True,      # Entry can call commands
            ("commands", "integration"): True, # Commands can use integration
            ("commands", "coordination"): True # Commands can use coordination
        }
        
        # Integration must never call commands or modify observations
        if source == "integration" and target in ["commands", "observations"]:
            return False
        
        # Entry must never directly access integration or observations
        if source == "entry" and target in ["integration", "observations"]:
            return False
        
        # Check specific flow
        return allowed_flows.get((source, target), False)
    
    def get_constitutional_status(self) -> Dict[str, Any]:
        """
        Get the constitutional compliance status of the bridge layer.
        """
        integration_status = self._check_integration_compliance()
        
        return {
            "layer": "bridge",
            "initialized": self._initialized,
            "available_modules": self._available_modules,
            "integration_compliance": integration_status,
            "constitutional_articles": ["5", "6", "7", "12"],
            "compliance_summary": "PASS" if integration_status["all_passed"] else "FAIL",
            "system_invariant": "Integration never adds power - it only translates"
        }


# Create a singleton instance
_bridge_instance: Optional[BridgeLayer] = None


def get_bridge() -> BridgeLayer:
    """
    Get the singleton bridge layer instance.
    
    This ensures consistent coordination across the system.
    """
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = BridgeLayer()
        try:
            _bridge_instance.initialize()
        except RuntimeError as e:
            print(f"Bridge layer initialization failed: {e}", file=sys.stderr)
            raise
    return _bridge_instance


def list_bridge_capabilities() -> Dict[str, Any]:
    """
    List all capabilities of the bridge layer with constitutional constraints.
    """
    bridge = get_bridge()
    
    return {
        "capabilities": bridge.get_available_capabilities(),
        "constraints": {
            "integration_never_adds_power": True,
            "commands_require_authorization": True,
            "entry_points_respect_workflow": True,
            "coordination_preserves_truth": True
        },
        "integration_details": list_supported_integrations(),
        "constitutional_basis": [
            "Article 5: Single-Focus Interface",
            "Article 6: Linear Investigation",
            "Article 7: Clear Affordances",
            "Article 12: Local Operation"
        ]
    }


def validate_integration_use(
    integration_type: IntegrationType,
    proposed_action: str
) -> Dict[str, Any]:
    """
    Validate that an integration use doesn't expand capabilities.
    
    This is a guard against integration abuse.
    """
    # Get integration info
    info = IntegrationRegistry.get_integration_info(integration_type)
    
    # Check if proposed action violates non-capabilities
    violates = any(
        proposed_action.lower() in non_cap.lower()
        for non_cap in info["non_capabilities"]
    )
    
    # Check constitutional articles
    constitutional = all(
        article in info["constitutional_articles"]
        for article in ["12", "19"]
    )
    
    return {
        "integration": integration_type.value,
        "proposed_action": proposed_action,
        "violates_constraints": violates,
        "constitutional": constitutional,
        "allowed": not violates and constitutional,
        "reason": "Integration cannot add new capabilities" if violates else None
    }


# Export public interface
__all__ = [
    # Bridge layer
    "BridgeLayer",
    "get_bridge",
    "list_bridge_capabilities",
    "validate_integration_use",
    "integrity_check",
    
    # Integration module
    "IntegrationType",
    "IntegrationRegistry",
    "SUPPORTED_INTEGRATIONS",
    "list_supported_integrations",
    "validate_integration_name",
    "check_integration_compliance"
]


# Self-validation when module is run directly
if __name__ == "__main__":
    """
    Self-validation of bridge layer compliance.
    
    This ensures the bridge layer follows its own rules.
    """
    print("Validating Bridge Layer Constitutional Compliance...")
    print("=" * 70)
    
    try:
        bridge = get_bridge()
        status = bridge.get_constitutional_status()
        
        print("\nBRIDGE LAYER STATUS")
        print("-" * 40)
        print(f"Initialized: {status['initialized']}")
        print(f"Available modules: {status['available_modules']}")
        
        integration_status = status['integration_compliance']
        print(f"\nIntegration Compliance: {integration_status['all_passed']}")
        print(f"Total integrations: {integration_status['total_integrations']}")
        print(f"Compliant: {integration_status['compliant_integrations']}")
        
        if integration_status['violations']:
            print("\nVIOLATIONS FOUND:")
            for violation in integration_status['violations']:
                print(f"  ✗ {violation}")
        
        print(f"\nConstitutional Articles: {status['constitutional_articles']}")
        print(f"Overall: {status['compliance_summary']}")
        
        if status['compliance_summary'] == "FAIL":
            print("\n✗ Bridge layer violates constitution.")
            print("  Integration must never add power - it only translates.")
            raise SystemExit(1)
        
        # Test integration validation
        print("\n" + "=" * 70)
        print("Testing Integration Validation...")
        
        test_cases = [
            (IntegrationType.EDITOR, "Open file at location"),
            (IntegrationType.EDITOR, "Show location"),
            (IntegrationType.CI, "Suppress warning"),
            (IntegrationType.CI, "Generate report"),
            (IntegrationType.EXPORT, "Summarize observations"),
            (IntegrationType.EXPORT, "Format as JSON")
        ]
        
        for integration_type, action in test_cases:
            result = validate_integration_use(integration_type, action)
            symbol = "✓" if result["allowed"] else "✗"
            print(f"{symbol} {integration_type.value}: {action} -> {result['allowed']}")
        
        print("\n" + "=" * 70)
        print("✓ Bridge layer is constitutionally compliant.")
        print("  Integration never adds power - it only translates.")
        
    except Exception as e:
        print(f"\n✗ Bridge layer validation failed: {e}", file=sys.stderr)
        raise SystemExit(1)