"""
inquiry/answers/purpose_extractor.py

Purpose Extractor for CodeMarshal Query System
=============================================

This module analyzes observations to extract and describe the purpose
of modules, files, and components in the codebase.

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 3: Explicit Limitations (declares semantic limits)
- Article 9: Immutable Observations (read-only analysis)
- Article 17: Uncertainty Indicators (marks inferred purposes)
- Article 19: Backward Compatibility (stable output format)

This module IS:
- A purpose descriptor for code components
- An export-based analyzer (looks at public APIs)
- A dependency-based inferencer (uses imports/exports)
- A fact-based reporter (limited inference)

This module IS NOT:
- A semantic analyzer (does not understand code meaning)
- A documentation parser (does not read docstrings)
- An AI interpreter (does not guess intent)
- A runtime analyzer (does not execute code)

ALLOWED IMPORTS:
- typing modules (type hints only)
- No external NLP or ML libraries

PROHIBITED IMPORTS:
- nltk, spacy, transformers (no NLP)
- ast, parser (no code parsing)
- inspect (no runtime introspection)

QUESTION TYPES HANDLED:
- "What does X do?"
- "What is the purpose of this module?"
- "Explain this component"
- "What is X's function?"

PURPOSE INFERENCE METHODS:
1. Export Analysis - Public functions/classes indicate purpose
2. Import Analysis - Dependencies suggest functionality
3. Naming Heuristics - Module names hint at purpose
4. Coupling Metrics - Import/export ratios show complexity

INFERENCE LIMITATIONS:
- Cannot understand semantic meaning
- Cannot parse docstrings or comments
- Cannot execute code to see behavior
- Relies on naming conventions
- May misinterpret generic names

OUTPUT FORMAT:
- Clear identification of target
- Export list (public API)
- Import list (dependencies)
- Inferred purpose statement
- Uncertainty markers where appropriate

UNCERTAINTY HANDLING:
When purpose cannot be confidently inferred:
- States "No detailed information found"
- Lists available data (exports, imports)
- Suggests manual review
- Does not fabricate descriptions
"""

from typing import Any


class PurposeExtractor:
    """
    Extract purpose information from code observations.

    The PurposeExtractor attempts to understand what code components do
    by analyzing their public interfaces (exports) and dependencies
    (imports). While it cannot truly understand semantic meaning, it
    provides evidence-based inferences about component purposes.

    INFERENCE METHODOLOGY:

    1. Export Analysis
       - Counts public functions/classes
       - Identifies module's public API
       - More exports = broader functionality

    2. Import Analysis
       - Examines what the module depends on
       - Suggests functionality through dependencies
       - High import count = complex/integration role

    3. Naming Heuristics
       - Module path suggests purpose
       - Examples: "core/engine" → core functionality
       - Examples: "utils/helpers" → utility functions

    4. Complexity Metrics
       - Export count indicates scope
       - Import count indicates coupling
       - Ratio suggests module type

    LIMITATION DECLARATIONS:
    This extractor explicitly cannot:
    - Understand semantic meaning of code
    - Parse docstrings or comments
    - Execute code to observe behavior
    - Infer purpose from implementation details
    - Guarantee accuracy of inferences

    PURPOSE STATEMENT GENERATION:
    Based on available evidence, generates statements like:
    - "This module provides: X, Y, Z" (based on exports)
    - "This appears to be a substantial module..." (many exports)
    - "It depends on N other modules" (import count)

    These are inferences, not facts, and are marked appropriately.

    THREAD SAFETY:
    Stateless class - safe for concurrent use.

    PERFORMANCE:
    - Time: O(n) where n = observations
    - Space: O(e + i) where e = exports, i = imports
    - Single-pass processing

    EXAMPLES:
        >>> extractor = PurposeExtractor()
        >>> observations = [
        ...     {
        ...         "type": "export_sight",
        ...         "file": "utils.py",
        ...         "result": {"exports": [{"name": "helper"}]}
        ...     }
        ... ]
        >>> result = extractor.analyze(observations, "What does utils do?")
        >>> print(result)
        Analysis of 'utils':
        ============================================================
        ...
    """

    # Class constants
    _SECTION_SEPARATOR_LENGTH: int = 60
    """Length of ASCII separator lines."""

    _MAX_EXPORTS_DISPLAY: int = 10
    """Maximum exports to list."""

    _MAX_IMPORTS_DISPLAY: int = 10
    """Maximum imports to list."""

    _SUBSTANTIAL_MODULE_THRESHOLD: int = 5
    """Exports count considered "substantial"."""

    def __init__(self) -> None:
        """Initialize the PurposeExtractor."""
        pass

    def analyze(self, observations: list[dict[str, Any]], question: str) -> str:
        """
        Analyze observations and generate an answer to a purpose question.

        QUESTION ROUTING:
        Attempts to extract a target module from the question.
        If target found → detailed analysis of that module
        If no target → general codebase purpose summary

        Args:
            observations: List of observations with export_sight
                and import_sight data.
            question: Natural language question.

        Returns:
            str: Purpose description with exports, imports, and
                inferred purpose statement.
        """
        # Try to extract target from question
        target = self._extract_target(question)

        if target:
            # Specific target requested
            return self._describe_target(observations, target)
        else:
            # General purpose summary
            return self._get_general_purpose(observations)

    def _extract_target(self, question: str) -> str | None:
        """
        Extract the target module/file from the question.

        PATTERNS:
        - "what does X do?"
        - "purpose of X"
        - "what is X"

        Args:
            question: Question string.

        Returns:
            Optional[str]: Extracted target or None.
        """
        question_lower = question.lower()

        patterns = [
            "what does ",
            "purpose of ",
            "what is ",
        ]

        for pattern in patterns:
            if pattern in question_lower:
                parts = question_lower.split(pattern)
                if len(parts) > 1:
                    target = parts[1].strip()
                    target = target.rstrip("?").strip()
                    target = target.rstrip(" do").strip()
                    return target

        return None

    def _describe_target(self, observations: list[dict[str, Any]], target: str) -> str:
        """
        Describe the purpose of a specific target.

        Gathers exports and imports for the target, then generates
        a purpose description based on available evidence.

        Args:
            observations: Observations to search.
            target: Target module name.

        Returns:
            str: Detailed purpose analysis.
        """
        # Collect exports and imports
        exports: list[str] = []
        imports: list[str] = []

        for obs in observations:
            obs_file = obs.get("file", "")

            # Check if this observation relates to target
            if target in obs_file or target.replace(".", "/") in obs_file:
                if obs.get("type") == "export_sight":
                    result = obs.get("result", {})
                    exports_data = result.get("exports", [])
                    for exp in exports_data:
                        if isinstance(exp, dict):
                            exports.append(exp.get("name", ""))

                elif obs.get("type") == "import_sight":
                    statements = obs.get("statements", [])
                    for stmt in statements:
                        if isinstance(stmt, dict):
                            module = stmt.get("module", "")
                            if module:
                                imports.append(module)

        # Build output
        lines: list[str] = [
            f"Analysis of '{target}':",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Show exports
        if exports:
            lines.append(f"\nExports ({len(exports)} items):")
            for exp in exports[: self._MAX_EXPORTS_DISPLAY]:
                lines.append(f"  • {exp}")
            if len(exports) > self._MAX_EXPORTS_DISPLAY:
                lines.append(
                    f"  ... and {len(exports) - self._MAX_EXPORTS_DISPLAY} more"
                )

        # Show imports
        if imports:
            lines.append(f"\nDependencies ({len(imports)} imports):")
            unique_imports = sorted(set(imports))
            for imp in unique_imports[: self._MAX_IMPORTS_DISPLAY]:
                lines.append(f"  • {imp}")
            if len(unique_imports) > self._MAX_IMPORTS_DISPLAY:
                lines.append(
                    f"  ... and {len(unique_imports) - self._MAX_IMPORTS_DISPLAY} more"
                )

        # Handle no data case
        if not exports and not imports:
            return f"No detailed information found for: {target}\n\nThis may be a data file or the target was not observed."

        # Generate inferred purpose
        if exports:
            lines.append("\nInferred Purpose:")
            if len(exports) > self._SUBSTANTIAL_MODULE_THRESHOLD:
                lines.append(
                    "  This appears to be a substantial module providing multiple functions/classes."
                )
            elif len(exports) > 0:
                lines.append(f"  This module provides: {', '.join(exports[:3])}")

            if imports:
                lines.append(f"  It depends on {len(set(imports))} other modules.")

        return "\n".join(lines)

    def _get_general_purpose(self, observations: list[dict[str, Any]]) -> str:
        """
        Generate general purpose summary of the codebase.

        Analyzes all exports and imports to characterize the overall
        codebase purpose and complexity.

        Args:
            observations: All observations.

        Returns:
            str: General codebase purpose summary.
        """
        # Initialize counters
        total_exports: int = 0
        total_imports: int = 0
        modules_with_exports: int = 0

        # Count exports and imports
        for obs in observations:
            if obs.get("type") == "export_sight":
                result = obs.get("result", {})
                exports = result.get("exports", [])
                total_exports += len(exports)
                if exports:
                    modules_with_exports += 1

            elif obs.get("type") == "import_sight":
                statements = obs.get("statements", [])
                total_imports += len(statements)

        # Build output
        lines: list[str] = [
            "Codebase Purpose Summary:",
            "=" * self._SECTION_SEPARATOR_LENGTH,
            f"Total Public Exports: {total_exports}",
            f"Modules with Exports: {modules_with_exports}",
            f"Total Import Statements: {total_imports}",
        ]

        # Calculate average
        if total_exports > 0:
            avg_exports = total_exports / max(modules_with_exports, 1)
            lines.append(f"Average Exports per Module: {avg_exports:.1f}")

        # Classify codebase size
        lines.append("\nThis appears to be a")
        if total_exports > 100:
            lines[-1] += " substantial codebase"
        elif total_exports > 50:
            lines[-1] += " medium-sized codebase"
        else:
            lines[-1] += " compact codebase"

        # Classify coupling
        if total_imports > total_exports * 2:
            lines[-1] += " with high internal coupling."
        elif total_imports > total_exports:
            lines[-1] += " with moderate internal coupling."
        else:
            lines[-1] += " with loose internal coupling."

        return "\n".join(lines)

    def _categorize_module_type(self, exports: list[str], imports: list[str]) -> str:
        """
        Categorize module type based on exports and imports.

        Uses heuristics to classify what type of module this might be:
        - Library/Utility: Many exports, few imports
        - Integration: Few exports, many imports
        - Core: Balanced exports and imports
        - Facade: Few exports, few imports

        Args:
            exports: List of exported names
            imports: List of imported modules

        Returns:
            str: Category description
        """
        export_count = len(exports)
        import_count = len(set(imports))

        if export_count > 10 and import_count < 5:
            return "Library/Utility module (provides many utilities with minimal dependencies)"
        elif export_count < 5 and import_count > 10:
            return "Integration module (orchestrates many dependencies)"
        elif export_count > 5 and import_count > 5:
            return "Core module (substantial functionality with moderate coupling)"
        else:
            return "Simple module (focused functionality)"

    def _analyze_export_patterns(self, exports: list[str]) -> dict[str, int]:
        """
        Analyze patterns in export names.

        Looks for naming patterns that might indicate module purpose:
        - Functions (verbs)
        - Classes (nouns)
        - Constants (UPPERCASE)
        - Mixed patterns

        Args:
            exports: List of exported names

        Returns:
            Dict with pattern counts
        """
        patterns = {
            "functions": 0,
            "classes": 0,
            "constants": 0,
            "unknown": 0,
        }

        for exp in exports:
            if exp.isupper():
                patterns["constants"] += 1
            elif exp[0].isupper():
                patterns["classes"] += 1
            elif exp[0].islower():
                patterns["functions"] += 1
            else:
                patterns["unknown"] += 1

        return patterns

    def _get_module_complexity_indicator(
        self, exports: list[str], imports: list[str]
    ) -> str:
        """
        Generate complexity indicator based on exports and imports.

        Provides a simple indicator of module complexity:
        - Simple: Low exports, low imports
        - Moderate: Medium counts
        - Complex: High counts

        Args:
            exports: List of exports
            imports: List of imports

        Returns:
            str: Complexity description
        """
        export_count = len(exports)
        import_count = len(set(imports))

        total_score = export_count + import_count

        if total_score < 10:
            return "Simple"
        elif total_score < 20:
            return "Moderate"
        else:
            return "Complex"

    def _format_export_name(self, name: str) -> str:
        """
        Format an export name for display.

        Adds context hints based on naming conventions:
        - Class names (PascalCase)
        - Functions (snake_case)
        - Constants (UPPERCASE)

        Args:
            name: Export name

        Returns:
            str: Formatted name with type hint
        """
        if not name:
            return name

        if name.isupper():
            return f"{name} (constant)"
        elif name[0].isupper():
            return f"{name} (class)"
        else:
            return f"{name} (function)"

    def _calculate_coupling_ratio(
        self, exports: list[str], imports: list[str]
    ) -> float:
        """
        Calculate coupling ratio for a module.

        Ratio = imports / exports
        Higher ratio = more coupled to other modules

        Args:
            exports: List of exports
            imports: List of imports

        Returns:
            float: Coupling ratio
        """
        export_count = max(len(exports), 1)  # Avoid division by zero
        import_count = len(set(imports))

        return import_count / export_count


# Module exports
__all__ = ["PurposeExtractor"]
"""List of symbols exported by this module."""

__version__ = "1.0.0"
"""Module version following semantic versioning."""

__modified__ = "2026-02-05"
"""Date of last modification."""

# Additional metadata for documentation generation
__author__ = "CodeMarshal Team"
"""Module author."""

__description__ = "Purpose extraction analyzer for CodeMarshal query system"
"""Module description."""
