"""
BOUNDARY VIOLATION DETECTION

Checks imports and dependencies against constitutional boundaries.
Enforces Agent Nexus architectural rules.

Constitutional Rules:
1. No cross-lobe imports without explicit permission
2. Infrastructure access is controlled
3. Core modules have strict access rules
4. All violations are detected and reported
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Boundary:
    """Defines a constitutional boundary."""

    name: str
    path_patterns: list[str]  # Glob patterns for paths in this boundary
    allowed_imports: set[str] = field(default_factory=set)
    prohibited_imports: set[str] = field(default_factory=set)
    description: str = ""
    level: str = "package"  # package, module, layer


@dataclass(frozen=True)
class Violation:
    """Represents a boundary violation."""

    type: str
    source: str
    target: str
    source_boundary: str
    target_boundary: str
    rule: str
    line_number: int | None = None
    context: dict[str, Any] | None = None


class BoundaryMatcher:
    """Matches file paths to boundaries."""

    def __init__(self, boundaries: list[Boundary]):
        """
        Initialize with boundary definitions.

        Args:
            boundaries: List of boundary definitions
        """
        self.boundaries = boundaries
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self.compiled_patterns = []
        for boundary in self.boundaries:
            compiled = []
            for pattern in boundary.path_patterns:
                # Convert glob to regex
                regex_pattern = pattern.replace("*", ".*").replace("?", ".")
                compiled.append(re.compile(regex_pattern))
            self.compiled_patterns.append((boundary, compiled))

    def find_boundary(self, path: Path) -> Boundary | None:
        """
        Find which boundary a path belongs to.

        Args:
            path: File path to check

        Returns:
            Matching boundary or None
        """
        path_str = str(path)

        for boundary, patterns in self.compiled_patterns:
            for pattern in patterns:
                if pattern.match(path_str) or pattern.fullmatch(path_str):
                    return boundary

        return None


class BoundaryViolationChecker:
    """
    Checks for boundary violations in imports and dependencies.

    Features:
    - Pattern-based boundary matching
    - Import rule validation
    - Cross-lobe detection
    - Infrastructure access control
    """

    def __init__(self, boundaries: list[Boundary]):
        """
        Initialize with boundary definitions.

        Args:
            boundaries: Constitutional boundary definitions
        """
        self.matcher = BoundaryMatcher(boundaries)
        self.boundaries = {b.name: b for b in boundaries}

    def check_boundary_violation(
        self, source_path: Path, target_path: Path
    ) -> Violation | None:
        """
        Check if import crosses a prohibited boundary.

        Args:
            source_path: Path of importing file
            target_path: Path of imported module

        Returns:
            Violation if found, None otherwise
        """
        source_boundary = self.matcher.find_boundary(source_path)
        target_boundary = self.matcher.find_boundary(target_path)

        # If either is not in a boundary, no violation
        if not source_boundary or not target_boundary:
            return None

        # Check if target is in source's prohibited imports
        if target_boundary.name in source_boundary.prohibited_imports:
            return Violation(
                type="cross_boundary_import",
                source=str(source_path),
                target=str(target_path),
                source_boundary=source_boundary.name,
                target_boundary=target_boundary.name,
                rule=f"no_import_from_{target_boundary.name}",
            )

        # Check if target is NOT in source's allowed imports (if allowed is defined)
        if (
            source_boundary.allowed_imports
            and target_boundary.name not in source_boundary.allowed_imports
        ):
            return Violation(
                type="unauthorized_import",
                source=str(source_path),
                target=str(target_path),
                source_boundary=source_boundary.name,
                target_boundary=target_boundary.name,
                rule=f"only_import_from_{','.join(sorted(source_boundary.allowed_imports))}",
            )

        return None

    def check_import_statement(
        self, source_path: Path, import_statement: dict[str, Any]
    ) -> list[Violation]:
        """
        Check an import statement for boundary violations.

        Args:
            source_path: Path of file containing import
            import_statement: Parsed import statement

        Returns:
            List of violations found
        """
        violations = []

        # Handle different import types
        if import_statement.get("type") == "import":
            # import module
            module_name = import_statement.get("module", "")
            if module_name:
                target_path = self._resolve_module_path(module_name, source_path)
                violation = self.check_boundary_violation(source_path, target_path)
                if violation:
                    violations.append(violation)

        elif import_statement.get("type") == "from_import":
            # from module import name
            module_name = import_statement.get("module", "")
            if module_name:
                target_path = self._resolve_module_path(module_name, source_path)
                violation = self.check_boundary_violation(source_path, target_path)
                if violation:
                    violations.append(violation)

        return violations

    def check_file_imports(
        self, source_path: Path, import_statements: list[dict[str, Any]]
    ) -> list[Violation]:
        """
        Check all imports in a file for boundary violations.

        Args:
            source_path: Path of file to check
            import_statements: List of import statements

        Returns:
            List of violations found
        """
        all_violations = []

        for _i, stmt in enumerate(import_statements):
            violations = self.check_import_statement(source_path, stmt)
            for violation in violations:
                # Add line number if available
                if "line" in stmt:
                    violation = Violation(
                        type=violation.type,
                        source=violation.source,
                        target=violation.target,
                        source_boundary=violation.source_boundary,
                        target_boundary=violation.target_boundary,
                        rule=violation.rule,
                        line_number=stmt["line"],
                    )
                all_violations.append(violation)

        return all_violations

    def check_directory_imports(
        self, directory_path: Path, imports_by_file: dict[Path, list[dict[str, Any]]]
    ) -> dict[str, list[Violation]]:
        """
        Check all files in directory for boundary violations.

        Args:
            directory_path: Directory to check
            imports_by_file: Mapping of file paths to their imports

        Returns:
            Dictionary mapping file paths to violations
        """
        violations_by_file = {}

        for file_path, import_statements in imports_by_file.items():
            violations = self.check_file_imports(file_path, import_statements)
            if violations:
                violations_by_file[str(file_path)] = violations

        return violations_by_file

    def _resolve_module_path(self, module_name: str, source_path: Path) -> Path:
        """
        Resolve module name to a potential file path.

        This is a simplified resolver - in practice, you'd need
        to consider Python path, package structure, etc.

        Args:
            module_name: Name of imported module
            source_path: Path of importing file

        Returns:
            Resolved path (may not exist)
        """
        # Convert module name to path
        parts = module_name.split(".")

        # Try relative to source first
        for parent in source_path.parents:
            potential_path = parent
            for part in parts:
                potential_path = potential_path / part
            potential_path = potential_path / "__init__.py"

            if potential_path.exists():
                return potential_path

        # Fallback: assume it's a top-level module
        return Path(module_name.replace(".", "/")) / "__init__.py"

    def get_boundary_summary(self) -> dict[str, Any]:
        """
        Get summary of configured boundaries.

        Returns:
            Boundary configuration summary
        """
        return {
            "total_boundaries": len(self.boundaries),
            "boundaries": [
                {
                    "name": name,
                    "path_patterns": boundary.path_patterns,
                    "allowed_imports": list(boundary.allowed_imports),
                    "prohibited_imports": list(boundary.prohibited_imports),
                    "description": boundary.description,
                    "level": boundary.level,
                }
                for name, boundary in self.boundaries.items()
            ],
        }


# Convenience function for creating Agent Nexus boundaries
def create_agent_nexus_boundaries() -> list[Boundary]:
    """
    Create standard Agent Nexus boundary definitions.

    Returns:
        List of Agent Nexus boundaries
    """
    return [
        # Core boundary - most restricted
        Boundary(
            name="core",
            path_patterns=["*/core/*", "*/core.py"],
            allowed_imports=set(),  # Core cannot import from other boundaries
            prohibited_imports={"lobes", "infrastructure", "common"},
            description="Core system components with strict access controls",
            level="layer",
        ),
        # Infrastructure boundary - system services
        Boundary(
            name="infrastructure",
            path_patterns=["*/infrastructure/*", "*/infrastructure.py"],
            allowed_imports={"core"},  # Can only import from core
            prohibited_imports={"lobes"},
            description="Infrastructure services and utilities",
            level="layer",
        ),
        # Common boundary - shared utilities
        Boundary(
            name="common",
            path_patterns=["*/common/*", "*/common.py"],
            allowed_imports={"core", "infrastructure"},
            prohibited_imports={"lobes"},
            description="Common utilities shared across lobes",
            level="layer",
        ),
        # ChatBuddy lobe
        Boundary(
            name="chatbuddy",
            path_patterns=["*/lobes/chatbuddy/*"],
            allowed_imports={"core", "infrastructure", "common"},
            prohibited_imports={"insightmate", "dataminer", "analyzer"},
            description="ChatBuddy conversational AI lobe",
            level="package",
        ),
        # InsightMate lobe
        Boundary(
            name="insightmate",
            path_patterns=["*/lobes/insightmate/*"],
            allowed_imports={"core", "infrastructure", "common"},
            prohibited_imports={"chatbuddy", "dataminer", "analyzer"},
            description="InsightMate analysis AI lobe",
            level="package",
        ),
        # DataMiner lobe
        Boundary(
            name="dataminer",
            path_patterns=["*/lobes/dataminer/*"],
            allowed_imports={"core", "infrastructure", "common"},
            prohibited_imports={"chatbuddy", "insightmate", "analyzer"},
            description="DataMiner processing AI lobe",
            level="package",
        ),
        # Analyzer lobe
        Boundary(
            name="analyzer",
            path_patterns=["*/lobes/analyzer/*"],
            allowed_imports={"core", "infrastructure", "common"},
            prohibited_imports={"chatbuddy", "insightmate", "dataminer"},
            description="Analyzer validation AI lobe",
            level="package",
        ),
    ]


# Export public API
__all__ = [
    "Boundary",
    "Violation",
    "BoundaryMatcher",
    "BoundaryViolationChecker",
    "create_agent_nexus_boundaries",
]
