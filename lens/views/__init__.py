"""
Lens Views - Authorized Perceptual Surfaces (Truth Layer 3)

Purpose: Declare the authorized perceptual surfaces of the system.
This prevents ad-hoc views, shortcut displays, and philosophy bypasses.

Article 5: Single-Focus Interface - Only one view visible at a time
Article 7: Clear Affordances - Explicitly declared views only
Article 16: Truth-Preserving Aesthetics - Views as truth-preserving lenses
"""

from __future__ import annotations

from typing import Type, Dict, List, Optional, Any, Tuple
from enum import Enum

# Import view classes from their respective modules
from .overview import OverviewView
from .examination import ExaminationView
from .connections import ConnectionsView
from .patterns import PatternsView
from .thinking import ThinkingView
from .help import HelpView


class ViewType(Enum):
    """Authorized view types in the system."""
    OVERVIEW = "overview"
    EXAMINATION = "examination"
    CONNECTIONS = "connections"
    PATTERNS = "patterns"
    THINKING = "thinking"
    HELP = "help"
    
    @property
    def display_name(self) -> str:
        """Human-readable view name."""
        return {
            ViewType.OVERVIEW: "Overview",
            ViewType.EXAMINATION: "Examination",
            ViewType.CONNECTIONS: "Connections",
            ViewType.PATTERNS: "Patterns",
            ViewType.THINKING: "Thinking",
            ViewType.HELP: "Help"
        }[self]
    
    @property
    def view_class(self) -> Type:
        """Get the view class for this view type."""
        return _VIEW_CLASSES[self]


# Map view types to their classes
_VIEW_CLASSES: Dict[ViewType, Type] = {
    ViewType.OVERVIEW: OverviewView,
    ViewType.EXAMINATION: ExaminationView,
    ViewType.CONNECTIONS: ConnectionsView,
    ViewType.PATTERNS: PatternsView,
    ViewType.THINKING: ThinkingView,
    ViewType.HELP: HelpView
}


class ViewRegistry:
    """
    Registry of all authorized views in the system.
    
    This ensures:
    1. No ad-hoc views can be created
    2. All views follow philosophy rules
    3. Views are properly instantiated
    """
    
    # Class-level registry
    _registered_views: Dict[ViewType, Type] = _VIEW_CLASSES.copy()
    
    @classmethod
    def get_view_class(cls, view_type: ViewType) -> Type:
        """
        Get the view class for a given view type.
        
        Args:
            view_type: The type of view to get
        
        Returns:
            The view class
        
        Raises:
            ValueError: If view_type is not registered
        """
        if view_type not in cls._registered_views:
            raise ValueError(f"View type '{view_type}' is not registered. "
                           f"Available views: {list(cls._registered_views.keys())}")
        
        return cls._registered_views[view_type]
    
    @classmethod
    def create_view(cls, view_type: ViewType, *args, **kwargs) -> Any:
        """
        Create an instance of a view.
        
        Args:
            view_type: The type of view to create
            *args: Positional arguments for view constructor
            **kwargs: Keyword arguments for view constructor
        
        Returns:
            View instance
        
        Raises:
            ValueError: If view_type is not registered
            TypeError: If view cannot be instantiated with given arguments
        """
        view_class = cls.get_view_class(view_type)
        
        try:
            return view_class(*args, **kwargs)
        except Exception as e:
            raise TypeError(f"Failed to create view '{view_type}': {e}")
    
    @classmethod
    def validate_view(cls, view: Any) -> bool:
        """
        Validate that an object is a registered view instance.
        
        Args:
            view: Object to validate
        
        Returns:
            True if valid view instance
        
        Note:
            This checks if the object's class is one of the registered view classes.
        """
        view_class = type(view)
        return any(view_class == registered_class 
                  for registered_class in cls._registered_views.values())
    
    @classmethod
    def list_views(cls) -> List[Dict[str, Any]]:
        """
        List all registered views with metadata.
        
        Returns:
            List of view metadata dictionaries
        """
        views_info = []
        
        for view_type, view_class in cls._registered_views.items():
            views_info.append({
                "type": view_type.value,
                "display_name": view_type.display_name,
                "class_name": view_class.__name__,
                "module": view_class.__module__,
                "description": view_class.__doc__.strip().split('\n')[0] if view_class.__doc__ else "No description"
            })
        
        return views_info
    
    @classmethod
    def get_view_dependencies(cls, view_type: ViewType) -> List[str]:
        """
        Get the import dependencies for a view.
        
        Args:
            view_type: The view type to check
        
        Returns:
            List of module dependencies
        
        Raises:
            ValueError: If view_type is not registered
        """
        view_class = cls.get_view_class(view_type)
        
        # Extract imports from view class module
        module = view_class.__module__
        
        # These are the allowed imports for views (per architecture)
        allowed_imports = [
            "lens.philosophy",
            "inquiry.session.context",
            "inquiry.notebook.models",
            "typing",
            "dataclasses",
            "datetime",
            "json",
            "textwrap",
            "enum",
            "collections",
            "pathlib"
        ]
        
        # In a real implementation, we would inspect the module's imports
        # For now, return the allowed imports as a demonstration
        return allowed_imports
    
    @classmethod
    def get_view_philosophy_rules(cls, view_type: ViewType) -> List[str]:
        """
        Get the philosophy rules that apply to a view.
        
        Args:
            view_type: The view type to check
        
        Returns:
            List of philosophy rule names
        
        Raises:
            ValueError: If view_type is not registered
        """
        # Map of view types to their primary philosophy rules
        view_rules = {
            ViewType.OVERVIEW: [
                "SingleFocusRule",
                "ProgressiveDisclosureRule",
                "ClarityRule",
                "NavigationRule"
            ],
            ViewType.EXAMINATION: [
                "SingleFocusRule",
                "ProgressiveDisclosureRule",
                "ClarityRule",
                "NavigationRule"
            ],
            ViewType.CONNECTIONS: [
                "SingleFocusRule",
                "ProgressiveDisclosureRule",
                "ClarityRule",
                "NavigationRule"
            ],
            ViewType.PATTERNS: [
                "SingleFocusRule",
                "ProgressiveDisclosureRule",
                "ClarityRule",
                "NavigationRule"
            ],
            ViewType.THINKING: [
                "SingleFocusRule",
                "ProgressiveDisclosureRule",
                "ClarityRule",
                "NavigationRule"
            ],
            ViewType.HELP: [
                "SingleFocusRule",
                "ProgressiveDisclosureRule",
                "ClarityRule",
                "NavigationRule"
            ]
        }
        
        return view_rules.get(view_type, [])
    
    @classmethod
    def check_view_compliance(cls, view_type: ViewType) -> Dict[str, Any]:
        """
        Check a view's compliance with architectural rules.
        
        Args:
            view_type: The view type to check
        
        Returns:
            Compliance report
        
        Raises:
            ValueError: If view_type is not registered
        """
        view_class = cls.get_view_class(view_type)
        
        report = {
            "view_type": view_type.value,
            "class_name": view_class.__name__,
            "module": view_class.__module__,
            "checks": {}
        }
        
        # Check 1: Class has required methods
        required_methods = ["render", "validate_integrity"]
        report["checks"]["required_methods"] = {
            "passed": all(hasattr(view_class, method) for method in required_methods),
            "missing": [method for method in required_methods if not hasattr(view_class, method)]
        }
        
        # Check 2: Render method returns Dict
        if hasattr(view_class, "render"):
            # Get the annotation of the render method's return type
            render_method = view_class.render
            if hasattr(render_method, "__annotations__"):
                return_annotation = render_method.__annotations__.get("return", None)
                report["checks"]["render_return_type"] = {
                    "passed": return_annotation == Dict[str, Any] or "Dict" in str(return_annotation),
                    "annotation": str(return_annotation)
                }
        
        # Check 3: Class is in lens.views module
        report["checks"]["correct_module"] = {
            "passed": view_class.__module__.startswith("lens.views"),
            "actual_module": view_class.__module__
        }
        
        # Check 4: Has proper documentation
        report["checks"]["has_documentation"] = {
            "passed": bool(view_class.__doc__),
            "doc_length": len(view_class.__doc__) if view_class.__doc__ else 0
        }
        
        # Overall compliance
        all_passed = all(check["passed"] for check in report["checks"].values())
        report["compliance"] = "PASS" if all_passed else "FAIL"
        
        return report


def get_view(view_type: str) -> Optional[Type]:
    """
    Get a view class by type string.
    
    Args:
        view_type: String representation of view type
    
    Returns:
        View class or None if not found
    """
    try:
        enum_type = ViewType(view_type.lower())
        return ViewRegistry.get_view_class(enum_type)
    except (ValueError, KeyError):
        return None


def list_all_views() -> List[str]:
    """
    List all available view types.
    
    Returns:
        List of view type strings
    """
    return [view_type.value for view_type in ViewType]


def validate_view_transition(current_view: Optional[ViewType], next_view: ViewType) -> Tuple[bool, str]:
    """
    Validate a transition between views.
    
    Args:
        current_view: Current view type (or None)
        next_view: Next view type
    
    Returns:
        Tuple of (is_valid, reason)
    
    Note:
        Implements Article 6: Linear Investigation
        Some views should only be accessible after others.
    """
    # Always allow HELP view (it's always accessible)
    if next_view == ViewType.HELP:
        return True, "Help is always accessible"
    
    # If no current view, only allow OVERVIEW or HELP
    if current_view is None:
        if next_view == ViewType.OVERVIEW:
            return True, "Overview is the entry point"
        else:
            return False, f"Must start with Overview, not {next_view.display_name}"
    
    # Define allowed transitions based on linear investigation flow
    allowed_transitions = {
        ViewType.OVERVIEW: [ViewType.EXAMINATION, ViewType.HELP],
        ViewType.EXAMINATION: [ViewType.CONNECTIONS, ViewType.PATTERNS, ViewType.HELP],
        ViewType.CONNECTIONS: [ViewType.PATTERNS, ViewType.THINKING, ViewType.HELP],
        ViewType.PATTERNS: [ViewType.THINKING, ViewType.HELP],
        ViewType.THINKING: [ViewType.OVERVIEW, ViewType.HELP],  # Can return to overview
        ViewType.HELP: list(ViewType)  # From help, can go to any view
    }
    
    # Check if transition is allowed
    if next_view in allowed_transitions.get(current_view, []):
        return True, f"Valid transition from {current_view.display_name} to {next_view.display_name}"
    else:
        return False, f"Cannot transition from {current_view.display_name} to {next_view.display_name}"


# Explicit exports
__all__ = [
    # View classes
    "OverviewView",
    "ExaminationView",
    "ConnectionsView",
    "PatternsView",
    "ThinkingView",
    "HelpView",
    
    # Enums
    "ViewType",
    
    # Registry and utilities
    "ViewRegistry",
    "get_view",
    "list_all_views",
    "validate_view_transition",
]

# Integrity check on import
def _verify_exports() -> None:
    """
    Verify that all exports are valid and properly typed.
    
    Raises:
        AssertionError: If exports are invalid
    """
    # Check that all items in __all__ exist
    for item in __all__:
        assert item in globals(), f"Export '{item}' not defined"
    
    # Check that all view classes are exported
    for view_type in ViewType:
        view_class = ViewRegistry.get_view_class(view_type)
        assert view_class.__name__ in __all__, f"View class {view_class.__name__} not exported"
    
    # Verify no ad-hoc exports
    exported_classes = [globals()[name] for name in __all__ if isinstance(globals().get(name), type)]
    for cls in exported_classes:
        if cls.__module__.startswith("lens.views."):
            assert cls.__name__ in __all__, f"View class {cls.__name__} from lens.views not exported"


# Run verification on import
_verify_exports()

# Clean up verification function from module namespace
del _verify_exports


# Test function (for development only)
def _test_views() -> None:
    """Test function to verify views are working correctly."""
    print("=== Testing Lens Views ===")
    
    # List all views
    print("\n1. Registered Views:")
    for view_info in ViewRegistry.list_views():
        print(f"  - {view_info['display_name']} ({view_info['type']})")
        print(f"    {view_info['description']}")
    
    # Check compliance
    print("\n2. Compliance Checks:")
    for view_type in ViewType:
        report = ViewRegistry.check_view_compliance(view_type)
        status = "✅" if report["compliance"] == "PASS" else "❌"
        print(f"  {status} {view_type.display_name}: {report['compliance']}")
    
    # Test transitions
    print("\n3. Valid Transitions:")
    test_transitions = [
        (None, ViewType.OVERVIEW),
        (ViewType.OVERVIEW, ViewType.EXAMINATION),
        (ViewType.EXAMINATION, ViewType.PATTERNS),
        (ViewType.PATTERNS, ViewType.THINKING),
        (ViewType.OVERVIEW, ViewType.HELP),
        (ViewType.HELP, ViewType.EXAMINATION),
    ]
    
    for from_view, to_view in test_transitions:
        valid, reason = validate_view_transition(from_view, to_view)
        status = "✅" if valid else "❌"
        from_name = from_view.display_name if from_view else "None"
        print(f"  {status} {from_name} → {to_view.display_name}: {reason}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    _test_views()