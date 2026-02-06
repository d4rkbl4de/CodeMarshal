"""
inquiry/answers/connection_mapper.py

Connection Mapper for CodeMarshal Query System
==============================================

This module analyzes import/export observations to answer questions about
codebase dependencies, import relationships, and connection patterns.

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 1: Truth Preservation (only reports observed imports)
- Article 3: Explicit Limitations (declares static analysis limits)
- Article 9: Immutable Observations (read-only processing)
- Article 12: Linear Investigation (sequential dependency tracking)

This module IS:
- A dependency analysis engine for connection questions
- A graph builder for import relationships
- A cycle detector for circular dependencies
- A fact-based reporter (no speculation)

This module IS NOT:
- A runtime tracer (does not execute code)
- A dynamic analyzer (cannot see runtime imports)
- A recommendation engine (does not suggest refactorings)
- A semantic analyzer (does not understand import purposes)

ALLOWED IMPORTS:
- pathlib.Path (path manipulation)
- typing modules (type hints)
- No external graph libraries (maintains zero dependencies)

PROHIBITED IMPORTS:
- networkx or similar graph libraries (builds graphs manually)
- runtime introspection tools
- dynamic import analyzers
- Any inference engines

QUESTION TYPES HANDLED:
- "What depends on X?" (reverse dependencies)
- "What does X import?" (forward dependencies)
- "Show circular dependencies" (cycle detection)
- "Show import relationships" (dependency graph)
- "What imports Y?" (dependent finding)

ALGORITHMS IMPLEMENTED:
1. Simple substring matching for dependency extraction
2. Depth-First Search (DFS) for cycle detection
3. Graph adjacency list representation
4. Multi-pass statistics accumulation

PERFORMANCE NOTES:
- Cycle detection is O(V + E) where V = files, E = imports
- Graph building is O(n) where n = observations
- Memory usage is O(V + E) for graph storage
- No caching (processes fresh each time)

OUTPUT FORMAT:
- ASCII-formatted text
- Section separators for clarity
- Bullet lists for dependencies
- Arrow notation for cycles (A → B → C)
- Statistical summaries
"""

from typing import Any


class ConnectionMapper:
    """
    Analyze import/export observations to answer connection questions.

    The ConnectionMapper serves as the dependency analysis engine for the
    CodeMarshal query system. It builds a mental model of how codebase
    components connect to each other through import statements.

    CORE CAPABILITIES:
    1. Forward dependency tracking: What does module X import?
    2. Reverse dependency tracking: What imports module X?
    3. Circular dependency detection: Find import cycles
    4. Graph summarization: Overall dependency statistics

    GRAPH REPRESENTATION:
    This class builds dependency graphs using adjacency lists (dictionaries
    mapping source to sets of targets). This is memory-efficient and allows
    O(1) edge lookup while maintaining O(V + E) space complexity.

    LIMITATION DECLARATIONS:
    This mapper explicitly cannot:
    - Resolve dynamic imports (exec, __import__, importlib)
    - Handle conditional imports (imports inside if statements)
    - See runtime-only dependencies
    - Understand the semantics of imports (only the existence)
    - Track star imports with precision (from X import *)
    - Resolve relative imports without context

    CYCLE DETECTION ALGORITHM:
    Uses Depth-First Search (DFS) with three color states:
    - White: Unvisited
    - Gray: Currently being processed (in recursion stack)
    - Black: Finished processing

    A cycle is detected when we encounter a gray node (back edge).

    PERFORMANCE CHARACTERISTICS:
    - Graph Building: O(n) where n = number of observations
    - Cycle Detection: O(V + E) standard DFS complexity
    - Dependency Lookup: O(1) with adjacency list
    - Memory: O(V + E) for graph storage

    THREAD SAFETY:
    Stateless class - safe for concurrent use. Each analyze() call
    builds independent graph structures.

    EXAMPLES:
        >>> mapper = ConnectionMapper()
        >>> observations = [
        ...     {
        ...         "type": "import_sight",
        ...         "file": "main.py",
        ...         "statements": [{"module": "os"}]
        ...     }
        ... ]
        >>> result = mapper.analyze(observations, "What does main import?")
        >>> print(result)
        Imports in 'main': 1
        ============================================================
          • os
    """

    # Class constants for formatting and limits
    _SECTION_SEPARATOR_LENGTH: int = 60
    """Length of ASCII separator lines in output."""

    _MAX_DEPENDENTS_DISPLAY: int = 100
    """Maximum number of dependents to list (prevents output spam)."""

    _MAX_CYCLES_DISPLAY: int = 20
    """Maximum number of circular dependency cycles to display."""

    _HIGH_COUPLING_THRESHOLD: int = 20
    """Number of imports considered "high coupling" for warnings."""

    def __init__(self) -> None:
        """
        Initialize the ConnectionMapper.

        This analyzer is stateless and requires no initialization
        parameters. The constructor exists for:
        1. Factory pattern compatibility
        2. Future stateful extensions
        3. Consistent API across all analyzers

        The mapper builds fresh graph structures for each analyze()
        call, ensuring no data leakage between investigations.
        """
        # No state initialization needed
        # Reserved for future extensions
        pass

    def analyze(self, observations: list[dict[str, Any]], question: str) -> str:
        """
        Analyze observations and generate an answer to a connection question.

        QUESTION ROUTING LOGIC:
        The analyzer examines question keywords to determine intent:

        1. "depend" + "what depend" → Reverse dependency lookup
           Example: "What depends on core.engine?"

        2. "import" + "what" → Forward dependency lookup
           Example: "What does main.py import?"

        3. "circular" → Cycle detection
           Example: "Show circular dependencies"

        4. Default → General dependency graph summary
           Example: "Show me the dependencies"

        DEPENDENCY EXTRACTION:
        Dependencies are extracted from import_sight observations,
        which contain structured import statement data.

        Args:
            observations: List of observation dictionaries containing
                import_sight data with file paths and import statements.
            question: Natural language question string analyzed for
                keywords to determine query type.

        Returns:
            str: Formatted answer with dependency information.
                Format varies by question type but includes:
                - Clear headers
                - ASCII separators
                - Bullet lists or arrow chains
                - Statistical summaries

        CONSTITUTIONAL COMPLIANCE:
        - Article 1: Only reports actually observed imports
        - Article 3: Declares limitations (no dynamic imports)
        - Article 9: Never modifies observations
        - Article 12: Builds graph linearly from observations

        Example:
            >>> mapper = ConnectionMapper()
            >>> obs = [{"type": "import_sight", "file": "a.py",
            ...         "statements": [{"module": "b"}]}]
            >>> mapper.analyze(obs, "What depends on b?")
            'Modules that depend on 'b': 1\n...'
        """
        # Normalize question for case-insensitive matching
        question_lower = question.lower()

        # Route based on question keywords
        # Check more specific patterns first

        if "depend" in question_lower and "what depend" in question_lower:
            # Question asks what depends on a target
            # Examples:
            # - "What depends on core.engine?"
            # - "What modules depend on utils?"
            # - "Show me what depends on bridge"
            target = self._extract_target_module(question)
            if target:
                return self._find_dependents(observations, target)
            else:
                return "Could not determine target module from question."

        elif "import" in question_lower and "what" in question_lower:
            # Question asks what something imports
            # Examples:
            # - "What does main.py import?"
            # - "What modules does core import?"
            # - "What are the imports of bridge/cli?"
            target = self._extract_target_module(question)
            if target:
                return self._find_imports_of_module(observations, target)
            else:
                # No specific target, show summary of all imports
                return self._get_all_imports_summary(observations)

        elif "circular" in question_lower:
            # Question asks about circular dependencies
            # Examples:
            # - "Show circular dependencies"
            # - "Find import cycles"
            # - "Are there any circular imports?"
            return self._find_circular_dependencies(observations)

        else:
            # Default: provide general dependency graph summary
            # This is useful for general questions like:
            # - "Show me the dependencies"
            # - "What imports exist?"
            # - "Describe the dependency graph"
            return self._get_dependency_graph_summary(observations)

    def _extract_target_module(self, question: str) -> str | None:
        """
        Extract module name from question text.

        This method uses simple pattern matching to identify the target
        module that a question refers to. It looks for common patterns
        in dependency questions.

        PATTERNS RECOGNIZED:
        - "depends on X" → X is the target
        - "depend on X" → X is the target
        - "import X" → X is the target
        - "imports X" → X is the target
        - "from X import" → X is the target

        EXTRACTION LOGIC:
        1. Convert to lowercase for case-insensitive matching
        2. Check each pattern in order
        3. Split on pattern and take right side
        4. Strip whitespace and punctuation
        5. Return cleaned module name

        LIMITATION:
        This is a heuristic approach. Complex questions with multiple
        modules may not be parsed correctly. The system returns None
        when uncertain, triggering fallback behavior.

        Args:
            question: Natural language question string.

        Returns:
            Optional[str]: Extracted module name or None if cannot
                determine target from question.

        Examples:
            >>> mapper._extract_target_module("What depends on core.engine?")
            'core.engine'
            >>> mapper._extract_target_module("What does main import?")
            'main'
            >>> mapper._extract_target_module("Show all dependencies")
            None
        """
        # Normalize to lowercase
        question_lower = question.lower()

        # Define patterns to check
        # Order matters: check more specific patterns first
        patterns: list[str] = [
            "depends on ",
            "depend on ",
            "imports ",
            "import ",
            "does ",
        ]

        # Try each pattern
        for pattern in patterns:
            if pattern in question_lower:
                # Split on pattern and take the part after it
                parts = question_lower.split(pattern)
                if len(parts) > 1:
                    # Extract target module name
                    target = parts[1].strip()

                    # Remove trailing punctuation
                    target = target.rstrip("?.!;:,").strip()

                    # Remove common suffixes
                    target = target.replace(" import", "").strip()
                    target = target.replace(" depend", "").strip()

                    # Return cleaned target
                    return target if target else None

        # Could not extract target
        return None

    def _find_dependents(
        self, observations: list[dict[str, Any]], target_module: str
    ) -> str:
        """
        Find all modules that import the target module.

        This method performs reverse dependency analysis: given a target
        module, it finds all other modules that import it. This is useful
        for understanding the impact of changes to a module.

        MATCHING LOGIC:
        A file is considered dependent if:
        1. It has an import_sight observation
        2. Any import statement references the target
        3. Match is substring-based ("core" matches "core.engine")

        The substring matching allows finding dependencies even when
        the exact module path isn't known. However, this may produce
        false positives (e.g., "core" matches "core_utils").

        Args:
            observations: List of observations to search.
            target_module: Module name to find dependents for.

        Returns:
            str: Formatted list of dependent modules.

        Example:
            Target: "core.engine"
            Result:
                Modules that depend on 'core.engine': 3
                ============================================================
                  • main.py
                  • bridge/cli.py
                  • tests/test_engine.py
        """
        # Track dependents (files that import the target)
        dependents: list[str] = []

        # Scan all observations for import references
        for obs in observations:
            if obs.get("type") == "import_sight":
                statements = obs.get("statements", [])
                file_path = obs.get("file", "")

                # Check each import statement
                for stmt in statements:
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        names = stmt.get("names", [])

                        # Check if this import references the target
                        # Use substring matching for flexibility
                        if target_module in module or target_module in str(names):
                            # Found a dependency
                            if file_path and file_path not in dependents:
                                dependents.append(file_path)
                            break  # Only count each file once

        # Handle case: no dependents found
        if not dependents:
            return f"No modules found that depend on: {target_module}"

        # Build formatted output
        lines: list[str] = [
            f"Modules that depend on '{target_module}': {len(dependents)}",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Add each dependent with bullet point
        for dep in sorted(dependents)[: self._MAX_DEPENDENTS_DISPLAY]:
            lines.append(f"  • {dep}")

        # Note if list was truncated
        if len(dependents) > self._MAX_DEPENDENTS_DISPLAY:
            remaining = len(dependents) - self._MAX_DEPENDENTS_DISPLAY
            lines.append(f"  ... and {remaining} more")

        return "\n".join(lines)

    def _find_imports_of_module(
        self, observations: list[dict[str, Any]], target_module: str
    ) -> str:
        """
        Find what a specific module imports.

        This method performs forward dependency analysis: given a target
        module, it finds all modules that the target imports. This helps
        understand what a module depends on.

        MATCHING LOGIC:
        An import is attributed to the target if:
        1. The observation's file path contains the target name
        2. OR the target name (with dots→slashes) is in the file path

        This handles both:
        - Direct matches: target="main" matches "main.py"
        - Module paths: target="core.engine" matches "core/engine.py"

        Args:
            observations: List of observations to search.
            target_module: Module name to find imports for.

        Returns:
            str: Formatted list of imports.

        Example:
            Target: "main"
            Result:
                Imports in 'main': 5
                ============================================================
                  • os
                  • sys
                  • core.engine (Engine, Runtime)
                  • bridge.cli
                  • config.loader
        """
        # Track imports found
        imports_found: list[str] = []

        # Convert module path notation for matching
        # "core.engine" → "core/engine"
        target_path = target_module.replace(".", "/")

        # Scan observations
        for obs in observations:
            if obs.get("type") == "import_sight":
                file_path = obs.get("file", "")

                # Check if this observation is for the target module
                if target_module in file_path or target_path in file_path:
                    statements = obs.get("statements", [])

                    # Extract imports from statements
                    for stmt in statements:
                        if isinstance(stmt, dict):
                            module = stmt.get("module", "")
                            names = stmt.get("names", [])

                            if module:
                                # Format with imported names if present
                                import_str = module
                                if names:
                                    import_str += f" ({', '.join(names)})"
                                imports_found.append(import_str)

        # Handle case: no imports found
        if not imports_found:
            return f"No imports found for module: {target_module}"

        # Build formatted output
        lines: list[str] = [
            f"Imports in '{target_module}': {len(imports_found)}",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Add each import (deduplicated and sorted)
        for imp in sorted(set(imports_found)):
            lines.append(f"  • {imp}")

        return "\n".join(lines)

    def _get_all_imports_summary(self, observations: list[dict[str, Any]]) -> str:
        """
        Generate summary of all imports found in observations.

        This method provides a high-level overview of all import
        relationships in the codebase, organized by file.

        STATISTICS PROVIDED:
        - Total import statements across all files
        - Number of files with imports
        - Most commonly imported modules (top 10)

        USE CASES:
        - Getting a quick overview of dependencies
        - Identifying commonly used modules
        - Understanding import patterns

        Args:
            observations: List of observations containing import_sight data.

        Returns:
            str: Formatted summary with import statistics.
        """
        # Build import map: file -> list of imported modules
        all_imports: dict[str, list[str]] = {}
        total_imports: int = 0

        for obs in observations:
            if obs.get("type") == "import_sight":
                statements = obs.get("statements", [])
                file_path = obs.get("file", "")

                if file_path not in all_imports:
                    all_imports[file_path] = []

                for stmt in statements:
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        if module:
                            all_imports[file_path].append(module)
                            total_imports += 1

        # Calculate import frequencies
        import_counts: dict[str, int] = {}
        for imports in all_imports.values():
            for imp in imports:
                import_counts[imp] = import_counts.get(imp, 0) + 1

        # Build formatted output
        lines: list[str] = [
            f"Import Summary: {total_imports} imports across {len(all_imports)} files",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Show most imported modules
        if import_counts:
            lines.append("\nMost Imported Modules:")
            sorted_imports = sorted(
                import_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
            for module, count in sorted_imports:
                lines.append(f"  • {module}: {count} imports")

        return "\n".join(lines)

    def _find_circular_dependencies(self, observations: list[dict[str, Any]]) -> str:
        """
        Detect circular import dependencies using DFS.

        This method builds a dependency graph from observations and
        performs cycle detection using Depth-First Search (DFS).

        ALGORITHM:
        1. Build adjacency list graph from import observations
        2. Initialize DFS tracking (visited, recursion stack)
        3. For each unvisited node:
           a. Mark as visiting (gray)
           b. Visit all neighbors
           c. If neighbor is gray, cycle detected
           d. Mark as visited (black)
        4. Report all found cycles

        COMPLEXITY:
        - Time: O(V + E) standard DFS
        - Space: O(V) for recursion stack and tracking

        LIMITATION:
        This only detects direct import cycles. Runtime import cycles
        (e.g., inside function calls) cannot be detected statically.

        Args:
            observations: List of observations to analyze.

        Returns:
            str: Formatted list of circular dependencies or message
                indicating no cycles found.
        """
        # Build dependency graph as adjacency list
        graph: dict[str, set[str]] = {}

        for obs in observations:
            if obs.get("type") == "import_sight":
                file_path = obs.get("file", "")
                statements = obs.get("statements", [])

                if file_path not in graph:
                    graph[file_path] = set()

                for stmt in statements:
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        if module:
                            # Convert module to potential file path
                            potential_path = module.replace(".", "/") + ".py"
                            graph[file_path].add(potential_path)

        # Find cycles using DFS
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> None:
            """Depth-first search helper for cycle detection."""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)

            rec_stack.remove(node)

        # Run DFS from all unvisited nodes
        for node in graph:
            if node not in visited:
                dfs(node, [node])

        # Handle case: no cycles found
        if not cycles:
            return "No circular dependencies detected."

        # Build formatted output
        lines: list[str] = [
            f"Circular Dependencies Found: {len(cycles)}",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Show each cycle with arrow notation
        for i, cycle in enumerate(cycles[: self._MAX_CYCLES_DISPLAY], 1):
            lines.append(f"\nCycle {i}:")
            for j, node in enumerate(cycle):
                if j < len(cycle) - 1:
                    lines.append(f"  {node} →")
                else:
                    lines.append(f"  {node}")

        # Note if truncated
        if len(cycles) > self._MAX_CYCLES_DISPLAY:
            remaining = len(cycles) - self._MAX_CYCLES_DISPLAY
            lines.append(f"\n... and {remaining} more cycles")

        return "\n".join(lines)

    def _get_dependency_graph_summary(self, observations: list[dict[str, Any]]) -> str:
        """
        Generate a summary of the dependency graph.

        Provides high-level statistics about the dependency structure
        without listing individual dependencies.

        STATISTICS:
        - Files with imports
        - Total import statements
        - Unique imported modules
        - Top imported modules

        Args:
            observations: List of observations to analyze.

        Returns:
            str: Formatted dependency graph summary.
        """
        # Initialize statistics
        stats: dict[str, Any] = {
            "total_imports": 0,
            "unique_modules": set(),
            "files_with_imports": 0,
        }

        # Accumulate statistics
        for obs in observations:
            if obs.get("type") == "import_sight":
                stats["files_with_imports"] += 1
                statements = obs.get("statements", [])

                for stmt in statements:
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        if module:
                            stats["total_imports"] += 1
                            stats["unique_modules"].add(module)

        # Build formatted output
        lines: list[str] = [
            "Dependency Graph Summary:",
            "=" * self._SECTION_SEPARATOR_LENGTH,
            f"Files with imports: {stats['files_with_imports']}",
            f"Total import statements: {stats['total_imports']}",
            f"Unique imported modules: {len(stats['unique_modules'])}",
        ]

        # Show top modules
        if stats["unique_modules"]:
            lines.append("\nTop imported modules:")
            # Count occurrences
            module_counts: dict[str, int] = {}
            for obs in observations:
                if obs.get("type") == "import_sight":
                    for stmt in obs.get("statements", []):
                        if isinstance(stmt, dict):
                            module = stmt.get("module", "")
                            if module:
                                module_counts[module] = module_counts.get(module, 0) + 1

            sorted_modules = sorted(
                module_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
            for module, count in sorted_modules:
                lines.append(f"  • {module}: {count} imports")

        return "\n".join(lines)

    def _build_dependency_graph(
        self, observations: list[dict[str, Any]]
    ) -> dict[str, set[str]]:
        """
        Build a dependency graph from observations.

        Helper method that constructs an adjacency list representation
        of the dependency graph for reuse by multiple analysis methods.

        Args:
            observations: List of observations to process.

        Returns:
            Dict mapping source files to sets of target modules.

        Note: Currently unused but available for future extensions
        that need graph operations.
        """
        graph: dict[str, set[str]] = {}

        for obs in observations:
            if obs.get("type") == "import_sight":
                file_path = obs.get("file", "")
                statements = obs.get("statements", [])

                if file_path not in graph:
                    graph[file_path] = set()

                for stmt in statements:
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        if module:
                            graph[file_path].add(module)

        return graph


# Module exports
__all__ = ["ConnectionMapper"]
__version__ = "1.0.0"
__modified__ = "2026-02-05"
