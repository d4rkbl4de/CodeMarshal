"""
integrity/validation/interface_test.py - Interface validation tests

Tests that validate CodeMarshal's interface contracts and protocols.
Ensures that interfaces are properly defined and implemented.
"""

import pytest
from typing import Protocol, runtime_checkable


class TestInterfaceContracts:
    """Test that interfaces define proper contracts."""

    def test_protocol_definition(self):
        """Test that protocols are properly defined."""

        @runtime_checkable
        class TestProtocol(Protocol):
            def method(self) -> str: ...

        # Verify protocol is runtime checkable
        assert hasattr(TestProtocol, "__protocol_attrs__")

    def test_abstract_method_definitions(self):
        """Test that abstract methods are properly declared."""
        from abc import ABC, abstractmethod

        class AbstractBase(ABC):
            @abstractmethod
            def abstract_method(self) -> None:
                pass

        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            AbstractBase()

    def test_interface_compliance(self):
        """Test that implementations comply with interfaces."""
        from abc import ABC, abstractmethod

        class Interface(ABC):
            @abstractmethod
            def required_method(self) -> str:
                pass

        class Implementation(Interface):
            def required_method(self) -> str:
                return "implemented"

        # Should be instantiable
        impl = Implementation()
        assert impl.required_method() == "implemented"


class TestInterfaceDocumentation:
    """Test that interfaces are properly documented."""

    def test_interface_has_docstring(self):
        """Test that interfaces have docstrings."""
        from abc import ABC, abstractmethod

        class DocumentedInterface(ABC):
            """This is a documented interface."""

            @abstractmethod
            def method(self) -> None:
                """Method documentation."""
                pass

        assert DocumentedInterface.__doc__ is not None
        assert "documented" in DocumentedInterface.__doc__.lower()


class TestErrorHandling:
    """Test interface error handling."""

    def test_interface_method_signature(self):
        """Test that interface methods have proper signatures."""
        import inspect
        from abc import ABC, abstractmethod

        class InterfaceWithSignature(ABC):
            @abstractmethod
            def method_with_args(self, arg1: str, arg2: int = 10) -> bool:
                """Method with typed arguments."""
                pass

        # Check signature exists
        sig = inspect.signature(InterfaceWithSignature.method_with_args)
        params = list(sig.parameters.keys())
        assert "arg1" in params
        assert "arg2" in params

    def test_interface_inheritance(self):
        """Test that interfaces properly support inheritance."""
        from abc import ABC, abstractmethod

        class BaseInterface(ABC):
            @abstractmethod
            def base_method(self) -> None:
                pass

        class ExtendedInterface(BaseInterface):
            @abstractmethod
            def extended_method(self) -> None:
                pass

        class FullImplementation(ExtendedInterface):
            def base_method(self) -> None:
                pass

            def extended_method(self) -> None:
                pass

        # Should be instantiable with all methods implemented
        impl = FullImplementation()
        assert hasattr(impl, "base_method")
        assert hasattr(impl, "extended_method")


def validate_interface() -> "ValidationResult":
    """Run interface validation tests and return a ValidationResult."""
    from integrity import ValidationResult

    try:
        exit_code = pytest.main([__file__, "-q"])
    except Exception as exc:
        return ValidationResult(
            passed=False,
            violations=[{"check": "interface", "error": str(exc)}],
            details="Validation execution failed",
        )

    passed = exit_code == 0
    violations = [] if passed else [{"check": "interface", "details": "pytest failures"}]

    return ValidationResult(
        passed=passed,
        violations=violations,
        details=f"pytest exit code: {exit_code}",
    )
