"""
Integration layer for truth preservation.

This module declares the finite set of supported integrations.
Integration never adds power - it only translates already-authorized outcomes.

CONSTITUTIONAL BASIS:
- Article 12: Local Operation
- Article 19: Backward Truth Compatibility

SYSTEM-WIDE INVARIANT:
Integrations must never:
1. Introduce new actions
2. Bypass command authorization
3. Infer user intent
4. Enhance or reinterpret truth

If an integration makes the system feel more powerful than the core,
it is violating the constitution.
"""

from enum import Enum
from typing import Any, cast


class IntegrationType(Enum):
    """
    Finite set of supported integrations.

    Adding a new integration type requires:
    1. Constitutional review (Article 12, 19)
    2. Implementation in the corresponding module
    3. Registration in SUPPORTED_INTEGRATIONS
    4. Documentation in integration_types()
    """

    EDITOR = "editor"  # Human-context preservation
    CI = "ci"  # Truth in automation
    EXPORT = "export"  # Truth flattening, carefully


# Define a typed dict for integration info
IntegrationInfo = dict[str, Any]  # In full implementation, use TypedDict


# Finite registry of supported integrations
SUPPORTED_INTEGRATIONS: dict[IntegrationType, IntegrationInfo] = {
    IntegrationType.EDITOR: {
        "module": "bridge.integration.editor",
        "description": "Maps observations to editor locations without editor control",
        "capabilities": [
            "Show observation locations in editor",
            "Display annotations from notes",
            "Generate editor configuration",
        ],
        "non_capabilities": [
            "Cannot open files",
            "Cannot navigate",
            "Cannot trigger commands",
            "Cannot modify code",
        ],
        "constitutional_articles": ["12", "19"],
        "allowed_imports": [
            "observations.record.*",
            "inquiry.notebook.*",
            "lens.indicators.errors (severity only)",
            "bridge.commands.* (read-only metadata)",
        ],
    },
    IntegrationType.CI: {
        "module": "bridge.integration.ci",
        "description": "Exposes verification outputs suitable for CI environments",
        "capabilities": [
            "Generate deterministic CI outputs",
            "Signal uncertainty explicitly",
            "Provide integrity violation exits",
        ],
        "non_capabilities": [
            "Cannot suppress warnings",
            "Cannot retry flaky checks",
            "Cannot hide uncertainty",
            "Cannot make decisions",
        ],
        "constitutional_articles": ["8", "12", "19"],
        "allowed_imports": [
            "observations.record.integrity",
            "lens.indicators.errors (severity only)",
            "bridge.commands.* (read-only metadata)",
        ],
    },
    IntegrationType.EXPORT: {
        "module": "bridge.integration.export_formats",
        "description": "Defines export schemas for truth leaving the system",
        "capabilities": [
            "Export truth in structured formats",
            "Document context loss explicitly",
            "Preserve anchor references",
        ],
        "non_capabilities": [
            "Cannot summarize",
            "Cannot interpret",
            "Cannot compress",
            "Cannot enhance",
        ],
        "constitutional_articles": ["3", "19"],
        "allowed_imports": [
            "observations.record.*",
            "inquiry.notebook.*",
            "bridge.commands.* (read-only metadata)",
        ],
    },
}


class IntegrationRegistry:
    """
    Registry that enforces the finite set of integrations.

    This prevents:
    - Ad-hoc exporters
    - Undocumented editor hooks
    - Shadow CI adapters
    """

    @staticmethod
    def validate_integration(integration_type: IntegrationType) -> bool:
        """
        Validate that an integration is supported.

        Returns:
            True if integration is supported and constitutional

        Raises:
            ValueError: If integration is not in supported list
        """
        if integration_type not in SUPPORTED_INTEGRATIONS:
            raise ValueError(
                f"Integration '{integration_type}' is not supported. "
                f"Supported integrations: {list_supported_integrations()}"
            )

        # Verify integration follows constitutional constraints
        integration_info = SUPPORTED_INTEGRATIONS[integration_type]

        # Check for Article 12 compliance
        if "12" not in integration_info["constitutional_articles"]:
            raise ValueError(
                f"Integration '{integration_type}' violates Article 12: "
                "All integrations must work without network connectivity."
            )

        # Check for Article 19 compliance
        if "19" not in integration_info["constitutional_articles"]:
            raise ValueError(
                f"Integration '{integration_type}' violates Article 19: "
                "All integrations must maintain backward truth compatibility."
            )

        return True

    @staticmethod
    def get_integration_info(integration_type: IntegrationType) -> IntegrationInfo:
        """
        Get complete information about an integration.

        Returns:
            Dictionary with integration metadata and constraints

        Raises:
            ValueError: If integration is not supported
        """
        IntegrationRegistry.validate_integration(integration_type)
        return SUPPORTED_INTEGRATIONS[integration_type].copy()

    @staticmethod
    def list_allowed_imports(integration_type: IntegrationType) -> list[str]:
        """
        List imports allowed for this integration.

        This enforces import discipline and prevents capability expansion.
        """
        info = IntegrationRegistry.get_integration_info(integration_type)
        # Use cast to ensure mypy knows this is List[str]
        return cast(list[str], info["allowed_imports"])

    @staticmethod
    def verify_no_capability_expansion(
        integration_type: IntegrationType, proposed_capabilities: list[str]
    ) -> bool:
        """
        Verify that proposed capabilities don't expand beyond integration's role.

        Integration never adds power - it only translates.
        """
        info = IntegrationRegistry.get_integration_info(integration_type)
        existing_non_capabilities = cast(list[str], info["non_capabilities"])

        # Check if any proposed capability violates non-capabilities
        for capability in proposed_capabilities:
            for non_cap in existing_non_capabilities:
                if capability.lower() in non_cap.lower():
                    return False

        return True


def list_supported_integrations() -> list[dict[str, Any]]:
    """
    List all supported integrations with their constraints.

    This is the authoritative source for what integrations exist.
    """
    integrations: list[dict[str, Any]] = []

    for integration_type, info in SUPPORTED_INTEGRATIONS.items():
        integrations.append(
            {
                "type": integration_type.value,
                "description": info["description"],
                "module": info["module"],
                "capabilities": info["capabilities"],
                "non_capabilities": info["non_capabilities"],
                "constitutional_articles": info["constitutional_articles"],
                "import_rules": info["allowed_imports"],
            }
        )

    return integrations


def validate_integration_name(name: str) -> IntegrationType:
    """
    Validate and convert string to IntegrationType.

    Raises:
        ValueError: If name doesn't match any supported integration
    """
    try:
        return IntegrationType(name.lower())
    except ValueError:
        supported = [i.value for i in IntegrationType]
        raise ValueError(
            f"Unknown integration: '{name}'. Supported: {', '.join(supported)}"
        ) from None


def check_integration_compliance(integration_type: IntegrationType) -> dict[str, Any]:
    """
    Check if an integration complies with constitutional constraints.

    Returns a compliance report that can be used for validation.
    """
    try:
        IntegrationRegistry.validate_integration(integration_type)

        # Additional compliance checks
        info = SUPPORTED_INTEGRATIONS[integration_type]

        # Check that integration doesn't claim to add new actions
        non_capabilities = cast(list[str], info["non_capabilities"])
        has_no_new_actions = all(
            "cannot" in cap.lower() or "no" in cap.lower() for cap in non_capabilities
        )

        # Check that integration doesn't bypass command authorization
        allowed_imports = cast(list[str], info["allowed_imports"])
        respects_commands = any("bridge.commands" in imp for imp in allowed_imports)

        # Check that integration doesn't enhance truth
        description = info["description"]
        enhances_truth = any(
            word in description.lower()
            for word in ["enhance", "improve", "better", "summarize", "interpret"]
        )

        return {
            "integration": integration_type.value,
            "constitutional": True,
            "article_12": "12" in info["constitutional_articles"],
            "article_19": "19" in info["constitutional_articles"],
            "no_new_actions": has_no_new_actions,
            "respects_commands": respects_commands,
            "does_not_enhance_truth": not enhances_truth,
            "compliance_summary": "PASS"
            if all([has_no_new_actions, respects_commands, not enhances_truth])
            else "FAIL",
        }

    except ValueError as e:
        return {
            "integration": integration_type.value,
            "constitutional": False,
            "error": str(e),
            "compliance_summary": "FAIL",
        }


# Export public interface
__all__ = [
    "IntegrationType",
    "IntegrationRegistry",
    "SUPPORTED_INTEGRATIONS",
    "list_supported_integrations",
    "validate_integration_name",
    "check_integration_compliance",
]


# Constitutional enforcement
if __name__ == "__main__":
    """
    Self-validation of integration compliance.

    Run this module directly to validate all integrations follow the constitution.
    """
    print("Validating integration constitutional compliance...")
    print("=" * 70)

    all_passed = True
    for integration_type in IntegrationType:
        report = check_integration_compliance(integration_type)

        print(f"\n{integration_type.value.upper()} INTEGRATION")
        print("-" * 40)

        if report["constitutional"]:
            print("✓ Constitutional: PASS")
            print(f"✓ Article 12 (Local Operation): {report['article_12']}")
            print(f"✓ Article 19 (Backward Truth): {report['article_19']}")
            print(f"✓ No new actions: {report['no_new_actions']}")
            print(f"✓ Respects commands: {report['respects_commands']}")
            print(f"✓ Doesn't enhance truth: {report['does_not_enhance_truth']}")
            print(f"\nOverall: {report['compliance_summary']}")

            if report["compliance_summary"] == "FAIL":
                all_passed = False
        else:
            print("✗ Constitutional: FAIL")
            print(f"Error: {report['error']}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All integrations comply with the constitution.")
    else:
        print("✗ Some integrations violate the constitution.")
        print("  Integration cannot add power - it only translates.")
        print("  Integration must work locally and preserve backward compatibility.")
        raise SystemExit(1)
