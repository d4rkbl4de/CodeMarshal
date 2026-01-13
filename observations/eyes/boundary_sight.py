"""
boundary_sight.py - Observation of module boundaries and cross-references

Purpose:
Answers the question: "Where are the boundaries, and are they being crossed?"

Rules:
1. Only observes what dependencies exist textually
2. No judgment about whether crossings are "good" or "bad"
3. Maps module-to-module relationships
4. Requires boundary definitions to be provided (not inferred)
"""

import ast
import re
from pathlib import Path
from typing import (
    Any, Dict, List, Optional, Set, Tuple, Union, Pattern,
    NamedTuple, Callable
)
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict
import fnmatch
from enum import Enum, auto

from .base import AbstractEye, ObservationResult
from .import_sight import ImportSight, ImportStatement, ImportObservation


class BoundaryType(Enum):
    """Type of boundary observed."""
    LAYER = auto()          # Architectural layer (e.g., "core", "web", "data")
    PACKAGE = auto()        # Python package boundary
    MODULE = auto()         # Single module
    EXTERNAL = auto()       # External dependency (outside project)
    CUSTOM = auto()         # User-defined boundary


class BoundarySeverity(Enum):
    """Severity of a boundary crossing observation."""
    DIRECT = auto()         # Explicit import statement
    INDIRECT = auto()       # Through intermediate modules
    TRANSITIVE = auto()     # Multiple levels deep
    CIRCULAR = auto()       # Mutual dependency


@dataclass(frozen=True)
class BoundaryDefinition:
    """Definition of a boundary that should not be crossed."""
    name: str
    boundary_type: BoundaryType
    pattern: str  # fnmatch pattern for module paths
    description: str = ""
    allowed_targets: Tuple[str, ...] = field(default_factory=tuple)  # Patterns allowed to cross
    prohibited: bool = True  # Whether crossings are prohibited
    
    def matches(self, module_path: str) -> bool:
        """Check if a module path matches this boundary pattern."""
        # Convert path separators
        normalized = module_path.replace('.', '/')
        return fnmatch.fnmatch(normalized, self.pattern) or fnmatch.fnmatch(module_path, self.pattern)


@dataclass(frozen=True)
class ModuleNode:
    """Representation of a module in the dependency graph."""
    full_name: str  # Full dotted path
    file_path: Optional[Path] = None
    package_path: Optional[Path] = None  # Directory containing __init__.py
    is_external: bool = False
    is_init_module: bool = False  # __init__.py file
    
    @property
    def package_name(self) -> str:
        """Get the containing package name."""
        if '.' in self.full_name:
            return self.full_name.rsplit('.', 1)[0]
        return ""
    
    @property
    def simple_name(self) -> str:
        """Get the simple module name (without package)."""
        return self.full_name.split('.')[-1]


@dataclass(frozen=True)
class DependencyEdge:
    """Single dependency relationship between modules."""
    source_module: str
    target_module: str
    line_number: int
    column_offset: int
    import_type: str  # "import" or "from"
    is_relative: bool = False
    import_level: int = 0
    
    @property
    def is_external_dependency(self) -> bool:
        """Whether this dependency targets an external module."""
        # Simple heuristic: external if source is internal and target doesn't start with source's root
        # This is implementation-dependent and should be refined
        return '.' in self.target_module and not self.target_module.startswith(self.source_module.split('.')[0])


@dataclass(frozen=True)
class BoundaryCrossing:
    """Observation of a boundary being crossed."""
    source_boundary: str
    target_boundary: str
    source_module: str
    target_module: str
    severity: BoundarySeverity
    line_number: int
    column_offset: int
    import_statement: str
    allowed_exception: bool = False  # If explicitly allowed by boundary rules
    
    @property
    def is_circular(self) -> bool:
        """Whether this is part of a circular dependency."""
        return self.severity == BoundarySeverity.CIRCULAR
    
    def format_crossing(self) -> str:
        """Format the crossing as a human-readable string."""
        return f"{self.source_boundary} â†’ {self.target_boundary}: {self.source_module} imports {self.target_module}"


@dataclass(frozen=True)
class BoundaryObservation:
    """Complete boundary observation for a codebase."""
    root_path: Path
    timestamp: datetime
    boundaries_defined: Tuple[BoundaryDefinition, ...] = field(default_factory=tuple)
    
    # Graph structure
    modules: Tuple[Tuple[str, ModuleNode], ...] = field(default_factory=tuple)
    dependencies: Tuple[DependencyEdge, ...] = field(default_factory=tuple)
    
    # Boundary assignments
    module_boundaries: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)  # module -> boundary
    
    # Crossings found
    crossings: Tuple[BoundaryCrossing, ...] = field(default_factory=tuple)
    circular_dependencies: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    
    # Statistics
    total_dependencies: int = 0
    internal_dependencies: int = 0
    external_dependencies: int = 0
    
    # Issues
    analysis_errors: Tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def boundary_modules(self) -> Dict[str, List[str]]:
        """Group modules by boundary. Returns a dict for internal use."""
        result: Dict[str, List[str]] = defaultdict(list)
        for module, boundary in self.module_boundaries:
            result[boundary].append(module)
        return dict(result)
    
    @property
    def crossing_count_by_boundary(self) -> Dict[Tuple[str, str], int]:
        """Count crossings between each boundary pair."""
        counts: Dict[Tuple[str, str], int] = defaultdict(int)
        for crossing in self.crossings:
            key = (crossing.source_boundary, crossing.target_boundary)
            counts[key] += 1
        return dict(counts)


class BoundarySight(AbstractEye):
    """
    Observes module boundaries and their crossings.
    
    Key Principles:
    1. Requires explicit boundary definitions (doesn't infer them)
    2. Only reports what dependencies exist
    3. Can detect circular dependencies
    4. Works with both relative and absolute imports
    """
    
    VERSION = "1.0.0"
    
    def __init__(
        self, 
        boundary_definitions: Optional[List[BoundaryDefinition]] = None,
        project_root: Optional[Path] = None
    ):
        """
        Initialize boundary sight with optional boundary definitions.
        
        Args:
            boundary_definitions: List of boundary definitions to use for analysis.
                                 If None, will only build dependency graph without boundary checks.
            project_root: Root directory of the project for relative module name resolution.
                         If None, will be auto-detected from the observation target.
        """
        super().__init__(name="boundary_sight", version=self.VERSION)
        self.boundary_definitions = boundary_definitions or []
        self.import_sight = ImportSight()
        self.project_root = project_root
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Explicitly declare capabilities."""
        return {
            "name": self.name,
            "version": self.version,
            "deterministic": True,
            "side_effect_free": True,
            "boundary_rule_count": len(self.boundary_definitions or []),
            "supports_cycle_detection": True
        }
    
    def observe(self, target: Path) -> ObservationResult:
        """Public API: Observe boundary crossings in a directory tree."""
        return self._observe_with_timing(target)
    
    def _observe_impl(self, target: Path) -> ObservationResult:
        """
        Observe boundary crossings in a directory tree.
        
        Args:
            target: Path to directory or file to observe
            
        Returns:
            ObservationResult containing boundary analysis
            
        Raises:
            ValueError: If target doesn't exist or is not a directory/file
        """
        if not target.exists():
            raise FileNotFoundError(f"Target does not exist: {target}")
        
        # Auto-detect project_root if not set
        if not self.project_root:
            if target.is_dir():
                self.project_root = target.resolve()
            else:
                # For a single file, use parent directory as project root
                self.project_root = target.parent.resolve()
        
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Collect all Python files
            python_files = self._collect_python_files(target)
            if not python_files:
                raise ValueError(f"No Python files found at: {target}")
            
            # Build module graph
            modules, dependencies = self._build_dependency_graph(python_files)
            
            # Assign modules to boundaries if definitions provided
            module_boundaries = {}
            if self.boundary_definitions:
                module_boundaries = self._assign_boundaries(modules)
            
            # Detect boundary crossings
            crossings, circular = self._detect_boundary_crossings(
                modules, dependencies, module_boundaries
            )
            
            # Count dependencies
            total_deps = len(dependencies)
            internal_deps = sum(1 for d in dependencies if not d.is_external_dependency)
            external_deps = total_deps - internal_deps
            
            observation = BoundaryObservation(
                root_path=target.resolve(),
                timestamp=timestamp,
                boundaries_defined=tuple(self.boundary_definitions or []),
                modules=tuple(modules.items()),
                dependencies=tuple(dependencies),
                module_boundaries=tuple(module_boundaries.items()),
                crossings=tuple(crossings),
                circular_dependencies=tuple(circular),
                total_dependencies=total_deps,
                internal_dependencies=internal_deps,
                external_dependencies=external_deps
            )
            
            # Calculate confidence based on analysis quality
            confidence = self._calculate_confidence(observation, len(python_files))
            
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=confidence,
                raw_payload=observation
            )
            
        except Exception as e:
            # Report analysis errors
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=0.0,
                raw_payload=BoundaryObservation(
                    root_path=target.resolve(),
                    timestamp=timestamp,
                    analysis_errors=(f"Analysis failed: {str(e)}",)
                )
            )
    
    def _collect_python_files(self, root: Path) -> List[Path]:
        """Collect all Python files in the directory tree."""
        python_files = []
        
        if root.is_file():
            if root.suffix == '.py':
                python_files.append(root)
            return python_files
        
        # Walk directory tree
        for path in root.rglob("*.py"):
            # Skip hidden directories and files
            if any(part.startswith('.') for part in path.parts):
                continue
            # Skip __pycache__ and similar
            if '__pycache__' in str(path):
                continue
            
            python_files.append(path)
        
        return python_files
    
    def _build_dependency_graph(
        self, 
        python_files: List[Path]
    ) -> Tuple[Dict[str, ModuleNode], List[DependencyEdge]]:
        """
        Build a graph of module dependencies.
        
        Returns:
            Tuple of (module_dict, dependencies_list)
        """
        modules: Dict[str, ModuleNode] = {}
        dependencies: List[DependencyEdge] = []
        
        # First pass: create module nodes
        for file_path in python_files:
            module_name = self._path_to_module_name(file_path)
            is_init = file_path.name == '__init__.py'
            
            node = ModuleNode(
                full_name=module_name,
                file_path=file_path.resolve(),
                package_path=file_path.parent if is_init else None,
                is_init_module=is_init
            )
            modules[module_name] = node
        
        # Second pass: collect dependencies
        for file_path in python_files:
            source_module = self._path_to_module_name(file_path)
            
            try:
                # Use import_sight to get imports
                import_result = self.import_sight.observe(file_path)
                import_obs: ImportObservation = import_result.raw_payload
                
                for stmt in import_obs.statements:
                    # Resolve the import to absolute module name
                    target_module = self._resolve_import(
                        stmt, source_module, modules
                    )
                    
                    if not target_module:
                        # Could not resolve, skip
                        continue
                    
                    # Create dependency edge
                    edge = DependencyEdge(
                        source_module=source_module,
                        target_module=target_module,
                        line_number=stmt.line_number,
                        column_offset=stmt.column_offset,
                        import_type=stmt.import_type,
                        is_relative=stmt.level > 0,
                        import_level=stmt.level
                    )
                    dependencies.append(edge)
                    
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        return modules, dependencies
    
    def _path_to_module_name(self, file_path: Path) -> str:
        """
        Convert a file path to a Python module name.
        
        Uses project_root to generate relative module names.
        
        Example: 
            project_root=/project/test_violations
            file_path=/project/test_violations/lobes/chatbuddy/main.py
            result=lobes.chatbuddy.main
        """
        # Resolve to absolute path
        abs_path = file_path.resolve()
        
        # If we have a project_root, make path relative to it
        if self.project_root:
            try:
                relative_path = abs_path.relative_to(self.project_root.resolve())
            except ValueError:
                # File is outside project root, use as-is
                relative_path = abs_path
        else:
            # No project root, use absolute path (fallback)
            relative_path = abs_path
        
        # Get parts of the relative path
        parts = list(relative_path.parts)
        name = file_path.stem  # Remove .py extension
        
        # If it's __init__.py, use the directory name as module
        if name == '__init__':
            if len(parts) > 1:
                # Use parent directory name
                # Remove __init__.py from parts and use directory name
                parts = parts[:-1]
                if parts:
                    # Module name is the path to the package
                    module_name = '.'.join(parts)
                    return module_name
            return ''
        
        # For regular .py files, convert path to module name
        # Remove .py extension from the last part
        if parts:
            parts[-1] = name
        else:
            parts = [name]
        
        # Join with dots to create module name
        module_name = '.'.join(parts)
        
        # Clean up any leading/trailing dots
        module_name = module_name.strip('.')
        
        return module_name
    
    def _resolve_import(
        self, 
        stmt: ImportStatement, 
        source_module: str,
        modules: Dict[str, ModuleNode]
    ) -> Optional[str]:
        """Resolve an import statement to an absolute module name."""
        if stmt.import_type == "import":
            # Simple import: import module
            if stmt.module:
                return stmt.module
        
        elif stmt.import_type == "from":
            if not stmt.module:
                # Relative import without module specified
                if stmt.level > 0:
                    # Calculate relative import
                    source_parts = source_module.split('.')
                    
                    # Remove levels
                    if stmt.level <= len(source_parts):
                        base_parts = source_parts[:-stmt.level]
                        # Try to find the module
                        if base_parts:
                            base_module = '.'.join(base_parts)
                            # Check if this module exists in our graph
                            if base_module in modules:
                                return base_module
            
            else:
                # from module import ...
                if stmt.level == 0:
                    # Absolute import
                    return stmt.module
                else:
                    # Relative import with module name
                    source_parts = source_module.split('.')
                    
                    # Remove levels to get base
                    if stmt.level <= len(source_parts):
                        base_parts = source_parts[:-stmt.level]
                        base_parts.append(stmt.module)
                        relative_module = '.'.join(base_parts)
                        
                        # Check if this module exists
                        if relative_module in modules:
                            return relative_module
        
        return None
    
    def _assign_boundaries(
        self, 
        modules: Dict[str, ModuleNode]
    ) -> Dict[str, str]:
        """Assign each module to a boundary based on definitions."""
        assignments: Dict[str, str] = {}
        
        # Sort boundaries by specificity (more specific patterns first)
        sorted_boundaries = sorted(
            self.boundary_definitions,
            key=lambda b: (b.pattern.count('*'), b.pattern.count('?')),
            reverse=True
        )
        
        for module_name in modules.keys():
            assigned = False
            for boundary in sorted_boundaries:
                if boundary.matches(module_name):
                    assignments[module_name] = boundary.name
                    assigned = True
                    break
            
            # If no boundary matches, assign to "UNKNOWN"
            if not assigned:
                assignments[module_name] = "UNKNOWN"
        
        return assignments
    
    def _detect_boundary_crossings(
        self,
        modules: Dict[str, ModuleNode],
        dependencies: List[DependencyEdge],
        module_boundaries: Dict[str, str]
    ) -> Tuple[List[BoundaryCrossing], List[Tuple[str, str]]]:
        """Detect boundary crossings and circular dependencies."""
        crossings: List[BoundaryCrossing] = []
        circular_deps: List[Tuple[str, str]] = []
        
        if not module_boundaries:
            # No boundaries defined, can't detect crossings
            return crossings, circular_deps
        
        # Build adjacency list for cycle detection
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        
        for edge in dependencies:
            source = edge.source_module
            target = edge.target_module
            
            # Check if both modules are in our graph (project-internal)
            # This is a better check than the is_external_dependency heuristic
            if source not in modules:
                continue
            if target not in modules:
                # Target not in our project - it's external (stdlib, third-party)
                continue
            
            # Add to adjacency for cycle detection
            adjacency[source].add(target)
            
            # Get boundaries
            source_boundary = module_boundaries.get(source, "UNKNOWN")
            target_boundary = module_boundaries.get(target, "UNKNOWN")
            
            # Skip if same boundary or unknown
            if source_boundary == target_boundary or "UNKNOWN" in (source_boundary, target_boundary):
                continue
            
            # Check if this crossing is allowed
            allowed = False
            if source_boundary in [bd.name for bd in self.boundary_definitions]:
                # Find the boundary definition
                for bd in self.boundary_definitions:
                    if bd.name == source_boundary:
                        # Check if target matches any allowed pattern
                        for pattern in bd.allowed_targets:
                            # Normalize module name for matching (dots to slashes)
                            target_normalized = target.replace('.', '/')
                            if fnmatch.fnmatch(target_normalized, pattern) or fnmatch.fnmatch(target_boundary, pattern):
                                allowed = True
                                break
                        break
            
            # Create crossing observation
            import_str = f"{'from ' + edge.target_module if edge.import_type == 'from' else 'import ' + edge.target_module}"
            if edge.is_relative:
                import_str = f"relative import (level {edge.import_level})"
            
            crossing = BoundaryCrossing(
                source_boundary=source_boundary,
                target_boundary=target_boundary,
                source_module=source,
                target_module=target,
                severity=BoundarySeverity.DIRECT,
                line_number=edge.line_number,
                column_offset=edge.column_offset,
                import_statement=import_str,
                allowed_exception=allowed
            )
            crossings.append(crossing)
        
        # Detect circular dependencies
        circular_deps = self._find_circular_dependencies(adjacency)
        
        # Mark circular dependencies in crossings
        for source, target in circular_deps:
            source_boundary = module_boundaries.get(source, "UNKNOWN")
            target_boundary = module_boundaries.get(target, "UNKNOWN")
            
            # Find and update corresponding crossing
            for crossing in crossings:
                if (crossing.source_module == source and crossing.target_module == target):
                    crossing.severity = BoundarySeverity.CIRCULAR
        
        return crossings, circular_deps
    
    def _find_circular_dependencies(
        self, 
        adjacency: Dict[str, Set[str]]
    ) -> List[Tuple[str, str]]:
        """Find circular dependencies using DFS."""
        circular: List[Tuple[str, str]] = []
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in adjacency.get(node, set()):
                if neighbor in recursion_stack:
                    # Found a cycle
                    # Find the edge that closes the cycle
                    if path:
                        circular.append((path[-1], neighbor))
                elif neighbor not in visited:
                    dfs(neighbor, path + [node])
            
            recursion_stack.remove(node)
        
        for node in adjacency.keys():
            if node not in visited:
                dfs(node, [])
        
        return circular
    
    def _calculate_confidence(self, observation: BoundaryObservation, file_count: int) -> float:
        """Calculate confidence score for the observation."""
        base_confidence = 1.0
        
        # Penalize for analysis errors
        error_penalty = len(observation.analysis_errors) * 0.2
        
        # Adjust based on coverage
        if file_count > 0:
            coverage = len(observation.modules) / file_count
            if coverage < 0.8:
                base_confidence *= coverage
        
        # Adjust based on unresolved dependencies
        total_deps = observation.total_dependencies
        if total_deps > 0:
            unresolved = sum(1 for d in observation.dependencies if d.target_module not in observation.modules)
            unresolved_ratio = unresolved / total_deps
            base_confidence *= (1.0 - unresolved_ratio * 0.5)
        
        final_confidence = max(0.0, base_confidence - error_penalty)
        return min(1.0, final_confidence)
    
    def validate(self) -> bool:
        """Validate that this eye follows observation purity rules."""
        # Check for prohibited imports
        prohibited_imports = {
            'sub' + 'process', 'ex' + 'ec', 'ev' + 'al', 'com' + 'pile',
            'import' + 'lib.util', 'run' + 'py'  # Code execution
        }
        
        # Check this file's source
        current_file = Path(__file__).resolve()
        with open(current_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for prohibited in prohibited_imports:
            if f"import {prohibited}" in content or f"from {prohibited}" in content:
                return False
        
        # Ensure no filesystem writes
        write_patterns = {
            '.wri' + 'te(', '.write' + 'lines(', 'open(' + '"w")', 'open(' + '"a")',
            '.mkd' + 'ir(', '.rmd' + 'ir(', '.unl' + 'ink(', '.ren' + 'ame('
        }
        
        for pattern in write_patterns:
            if pattern in content:
                return False
        
        return True


# Convenience functions and boundary definition helpers

def create_layer_boundary(name: str, pattern: str, allowed_targets: List[str] = None) -> BoundaryDefinition:
    """Create a boundary definition for an architectural layer."""
    return BoundaryDefinition(
        name=name,
        boundary_type=BoundaryType.LAYER,
        pattern=pattern,
        allowed_targets=tuple(allowed_targets or []),
        description=f"Architectural layer: {name}"
    )


def create_package_boundary(package_name: str, allowed_targets: List[str] = None) -> BoundaryDefinition:
    """Create a boundary definition for a Python package."""
    return BoundaryDefinition(
        name=package_name,
        boundary_type=BoundaryType.PACKAGE,
        pattern=f"{package_name}.*",
        allowed_targets=tuple(allowed_targets or []),
        description=f"Python package: {package_name}"
    )


def observe_boundaries(
    root_path: Union[str, Path],
    boundaries: Optional[List[BoundaryDefinition]] = None
) -> BoundaryObservation:
    """Convenience function for boundary observation."""
    sight = BoundarySight(boundaries)
    path = Path(root_path) if isinstance(root_path, str) else root_path
    result = sight.observe(path)
    return result.raw_payload




