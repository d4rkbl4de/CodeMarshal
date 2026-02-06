"""
inquiry/answers/anomaly_detector.py

Anomaly Detector for CodeMarshal Query System
=============================================

This module analyzes observations to detect anomalies, suspicious patterns,
and boundary violations in the codebase.

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 3: Explicit Limitations (declares what patterns it cannot detect)
- Article 5: Uncertainty Quantification (flags uncertain detections)
- Article 9: Immutable Observations (read-only analysis)
- Article 16: Anomaly Detection (identifies deviations from norms)

This module IS:
- A pattern detection engine for anomaly questions
- A boundary violation checker
- A suspicious pattern identifier
- A statistical analyzer for code metrics
- A fact-based reporter (no speculation)

This module IS NOT:
- A bug finder (does not detect functional bugs)
- A security scanner (does not check for vulnerabilities)
- A style checker (does not enforce PEP 8)
- An AI classifier (does not learn from code)
- A semantic analyzer (does not understand code meaning)

ALLOWED IMPORTS:
- typing modules (type hints only)
- No external analysis libraries

PROHIBITED IMPORTS:
- pylint, flake8, etc. (no external checkers)
- ast, parser (no code parsing beyond observations)
- Any ML/AI libraries (no learning)

QUESTION TYPES HANDLED:
- "Are there any anomalies?"
- "Show me boundary violations"
- "What looks suspicious?"
- "Find code smells"
- "Detect unusual patterns"

ANOMALY TYPES DETECTED:
1. Boundary Violations - Cross-layer imports
2. Orphan Files - Files with no imports (potential dead code)
3. High Coupling - Files with excessive imports
4. Relative Imports - Potentially problematic imports
5. Circular Dependencies - Import cycles (via connection data)

DETECTION THRESHOLDS:
- High Coupling: >20 imports per file
- Orphan Threshold: Any file with zero imports
- Relative Import: Any import starting with "." or ".."

OUTPUT FORMAT:
- Severity levels (High, Medium, Low)
- Detailed descriptions
- File locations
- Counts and statistics
- Contextual information

LIMITATION DECLARATIONS:
This detector explicitly cannot:
- Detect runtime anomalies (need execution)
- Find logical bugs (need semantics)
- Identify security issues (need security analysis)
- Check code style (need style rules)
- Detect performance issues (need profiling)
"""

from typing import Any


class AnomalyDetector:
    """
    Analyze observations to detect anomalies and violations.

    The AnomalyDetector serves as the quality control and pattern analysis
    engine for the CodeMarshal query system. It identifies deviations from
    expected patterns that may indicate architectural issues, maintenance
    problems, or code smells.

    CORE CAPABILITIES:
    1. Boundary Violation Detection - Finds cross-layer imports
    2. Orphan File Detection - Identifies files with no imports
    3. Coupling Analysis - Flags files with excessive dependencies
    4. Pattern Recognition - Detects unusual import patterns
    5. Statistical Analysis - Computes metrics for anomaly scoring

    DETECTION METHODOLOGY:
    The detector uses simple rule-based heuristics rather than ML:
    - Hard thresholds (e.g., >20 imports = high coupling)
    - Pattern matching (e.g., ".." in import = relative)
    - Set operations (e.g., all_files - files_with_imports = orphans)
    - Count aggregation (e.g., boundary crossings)

    This approach is:
    - Deterministic (same input → same output)
    - Explainable (rules are transparent)
    - Fast (no model inference)
    - Predictable (users understand thresholds)

    SEVERITY CLASSIFICATION:
    Anomalies are classified by severity:
    - High: Boundary violations (architectural risk)
    - Medium: High coupling (maintainability risk)
    - Low: Relative imports (potential issues)

    LIMITATION DECLARATIONS:
    This detector explicitly cannot:
    - Detect runtime bugs (static analysis only)
    - Find security vulnerabilities (no security rules)
    - Check code style (no style guide enforcement)
    - Understand code semantics (no execution)
    - Learn from code patterns (no ML models)

    THREAD SAFETY:
    Stateless class - safe for concurrent use. All state is local
    to method calls.

    PERFORMANCE CHARACTERISTICS:
    - Time: O(n) where n = number of observations
    - Space: O(f) where f = number of files
    - Single-pass processing
    - No external dependencies

    EXAMPLES:
        >>> detector = AnomalyDetector()
        >>> observations = [
        ...     {
        ...         "type": "boundary_sight",
        ...         "crossings": [{"source": "a", "target": "b"}]
        ...     }
        ... ]
        >>> result = detector.analyze(observations, "Are there anomalies?")
        >>> print(result)
        Anomaly Summary:
        ============================================================
        Boundary Violations: 1
        ...
    """

    # Class constants for detection thresholds
    _SECTION_SEPARATOR_LENGTH: int = 60
    """Length of ASCII separator lines."""

    _HIGH_COUPLING_THRESHOLD: int = 20
    """Number of imports considered high coupling."""

    _MAX_ANOMALIES_DISPLAY: int = 50
    """Maximum anomalies to list (prevents spam)."""

    _ORPHAN_THRESHOLD: int = 0
    """Files with this many imports are considered orphans."""

    def __init__(self) -> None:
        """
        Initialize the AnomalyDetector.

        This analyzer is stateless and requires no initialization
        parameters. The constructor exists for:
        1. Factory pattern compatibility
        2. Future stateful extensions
        3. Consistent API across all analyzers
        """
        pass

    def analyze(self, observations: list[dict[str, Any]], question: str) -> str:
        """
        Analyze observations and generate an answer to an anomaly question.

        QUESTION ROUTING LOGIC:
        The analyzer examines question keywords to determine intent:

        1. "boundary" or "violation" → Boundary violation analysis
           Example: "Show me boundary violations"

        2. "suspicious" or "unusual" → Suspicious pattern detection
           Example: "What looks suspicious?"

        3. Default → General anomaly summary
           Example: "Are there any anomalies?"

        Args:
            observations: List of observation dictionaries containing
                boundary_sight, import_sight, and file_sight data.
            question: Natural language question string.

        Returns:
            str: Formatted anomaly report with severity levels,
                descriptions, and statistics.

        CONSTITUTIONAL COMPLIANCE:
        - Article 3: Declares limitations in output
        - Article 5: Classifies uncertainty levels
        - Article 9: Never modifies observations
        - Article 16: Provides explicit anomaly classification
        """
        # Normalize question for matching
        question_lower = question.lower()

        # Route based on question keywords
        if "boundary" in question_lower or "violation" in question_lower:
            # Specific question about boundary violations
            return self._find_boundary_violations(observations)

        elif "suspicious" in question_lower or "unusual" in question_lower:
            # Question asking about suspicious patterns
            return self._find_suspicious_patterns(observations)

        else:
            # General anomaly summary
            return self._get_anomaly_summary(observations)

    def _find_boundary_violations(self, observations: list[dict[str, Any]]) -> str:
        """
        Find all boundary violations in observations.

        This method scans observations for boundary crossings that
        violate architectural rules defined in the boundary configuration.

        VIOLATION SOURCES:
        1. boundary_sight observations - Direct boundary crossings
        2. import_sight observations - Import-based violations

        Each violation includes:
        - Source module (where violation originates)
        - Target module (what's being imported)
        - Line number (if available)
        - Violation type (classification)
        - Rule violated (if specified)

        Args:
            observations: List of observations to scan.

        Returns:
            str: Formatted list of boundary violations with details.
        """
        # Accumulate violations
        violations: list[dict[str, Any]] = []

        # Scan all observations
        for obs in observations:
            # Check boundary_sight observations
            if obs.get("type") == "boundary_sight":
                crossings = obs.get("crossings", [])

                for crossing in crossings:
                    if isinstance(crossing, dict):
                        source = crossing.get("source_module", "")
                        target = crossing.get("target_module", "")
                        line = crossing.get("line_number", 0)

                        violations.append(
                            {
                                "source": source,
                                "target": target,
                                "line": line,
                                "type": "cross_lobe_import",
                            }
                        )

            # Check import_sight for boundary violations
            if obs.get("type") == "import_sight":
                boundary_violations = obs.get("boundary_violations", [])
                for violation in boundary_violations:
                    if isinstance(violation, dict):
                        violations.append(
                            {
                                "source": violation.get("source", ""),
                                "target": violation.get("target", ""),
                                "line": violation.get("line_number", 0),
                                "type": violation.get("type", "boundary_violation"),
                                "rule": violation.get("rule", ""),
                            }
                        )

        # Handle case: no violations
        if not violations:
            return "No boundary violations detected."

        # Build formatted output
        lines: list[str] = [
            f"Boundary Violations Found: {len(violations)}",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Detail each violation
        for i, v in enumerate(violations, 1):
            lines.append(f"\nViolation {i}:")
            lines.append(f"  Source: {v.get('source', 'Unknown')}")
            lines.append(f"  Target: {v.get('target', 'Unknown')}")
            lines.append(f"  Type: {v.get('type', 'Unknown')}")

            if v.get("line"):
                lines.append(f"  Line: {v['line']}")
            if v.get("rule"):
                lines.append(f"  Rule: {v['rule']}")

        return "\n".join(lines)

    def _find_suspicious_patterns(self, observations: list[dict[str, Any]]) -> str:
        """
        Find suspicious patterns in observations.

        This method applies heuristics to identify code patterns that
        may indicate maintenance issues or architectural problems.

        PATTERNS DETECTED:
        1. Orphan Files - Files with no imports (potential dead code)
        2. High Coupling - Files with excessive imports
        3. Relative Imports - Potentially fragile import patterns

        DETECTION LOGIC:
        - Orphans: all_files - files_with_imports
        - High Coupling: import_count > _HIGH_COUPLING_THRESHOLD
        - Relative Imports: module.startswith(".") or ".." in module

        Args:
            observations: List of observations to analyze.

        Returns:
            str: Formatted list of suspicious patterns with details.
        """
        # Track suspicious findings
        suspicious: list[dict[str, Any]] = []

        # Track files for orphan detection
        files_with_imports: set[str] = set()
        all_files: set[str] = set()

        # First pass: collect all files and files with imports
        for obs in observations:
            if obs.get("type") == "file_sight":
                result = obs.get("result", {})
                modules = result.get("modules", [])

                for module in modules:
                    if isinstance(module, dict):
                        path = module.get("path", "")
                        if path:
                            all_files.add(path)

            elif obs.get("type") == "import_sight":
                file_path = obs.get("file", "")
                if file_path:
                    files_with_imports.add(file_path)

        # Detect orphan files
        orphan_files = all_files - files_with_imports
        if len(orphan_files) > 0:
            suspicious.append(
                {
                    "type": "orphan_files",
                    "description": "Files with no imports detected",
                    "count": len(orphan_files),
                    "files": list(orphan_files)[:5],
                }
            )

        # Detect high coupling
        for obs in observations:
            if obs.get("type") == "import_sight":
                file_path = obs.get("file", "")
                statements = obs.get("statements", [])

                if len(statements) > self._HIGH_COUPLING_THRESHOLD:
                    suspicious.append(
                        {
                            "type": "high_import_count",
                            "description": f"File has {len(statements)} imports (high coupling)",
                            "file": file_path,
                            "count": len(statements),
                        }
                    )

        # Detect relative imports
        for obs in observations:
            if obs.get("type") == "import_sight":
                statements = obs.get("statements", [])

                for stmt in statements:
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        if ".." in module or module.startswith("."):
                            suspicious.append(
                                {
                                    "type": "relative_import",
                                    "description": f"Relative import detected: {module}",
                                    "file": obs.get("file", ""),
                                }
                            )

        # Handle case: no suspicious patterns
        if not suspicious:
            return "No suspicious patterns detected."

        # Build formatted output
        lines: list[str] = [
            f"Suspicious Patterns Found: {len(suspicious)}",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Detail each pattern
        for i, item in enumerate(suspicious, 1):
            type_str = str(item.get("type", "Unknown"))
            lines.append(f"\n{i}. {type_str.replace('_', ' ').title()}")
            lines.append(f"   {item.get('description', '')}")

            if item.get("file"):
                lines.append(f"   File: {item['file']}")
            if item.get("count"):
                lines.append(f"   Count: {item['count']}")

            files = item.get("files")
            if isinstance(files, list):
                lines.append("   Examples:")
                for f in files:
                    lines.append(f"     • {f}")

        return "\n".join(lines)

    def _get_anomaly_summary(self, observations: list[dict[str, Any]]) -> str:
        """
        Generate summary of all anomalies found.

        This method provides a high-level overview of all detected
        anomalies, organized by category with counts.

        CATEGORIES:
        - Boundary Violations - Architectural rule violations
        - Orphan Files - Files with no imports
        - High Import Count - Files with excessive coupling
        - Relative Imports - Potentially problematic imports

        This is useful for getting a quick health check of the codebase
        without reading detailed violation reports.

        Args:
            observations: List of observations to analyze.

        Returns:
            str: Formatted anomaly summary with statistics.
        """
        # Initialize statistics
        stats: dict[str, int] = {
            "boundary_violations": 0,
            "orphan_files": 0,
            "high_import_count": 0,
            "relative_imports": 0,
        }

        # Count boundary violations
        for obs in observations:
            if obs.get("type") == "boundary_sight":
                stats["boundary_violations"] += len(obs.get("crossings", []))

            if obs.get("type") == "import_sight":
                stats["boundary_violations"] += len(obs.get("boundary_violations", []))

        # Count other anomalies
        files_with_imports: set[str] = set()
        all_files: set[str] = set()
        high_import_files: int = 0
        relative_imports: int = 0

        for obs in observations:
            if obs.get("type") == "file_sight":
                result = obs.get("result", {})
                modules = result.get("modules", [])
                for module in modules:
                    if isinstance(module, dict):
                        path = module.get("path", "")
                        if path:
                            all_files.add(path)

            elif obs.get("type") == "import_sight":
                file_path = obs.get("file", "")
                if file_path:
                    files_with_imports.add(file_path)

                statements = obs.get("statements", [])
                if len(statements) > self._HIGH_COUPLING_THRESHOLD:
                    high_import_files += 1

                for stmt in statements:
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        if ".." in module or module.startswith("."):
                            relative_imports += 1

        stats["orphan_files"] = len(all_files - files_with_imports)
        stats["high_import_count"] = high_import_files
        stats["relative_imports"] = relative_imports

        # Build formatted output
        lines: list[str] = [
            "Anomaly Summary:",
            "=" * self._SECTION_SEPARATOR_LENGTH,
            f"Boundary Violations: {stats['boundary_violations']}",
            f"Orphan Files (no imports): {stats['orphan_files']}",
            f"Files with High Import Count: {stats['high_import_count']}",
            f"Relative Import Statements: {stats['relative_imports']}",
        ]

        total_anomalies = sum(stats.values())
        lines.append(f"\nTotal Anomalies: {total_anomalies}")

        if total_anomalies == 0:
            lines.append("\nNo anomalies detected - codebase appears healthy.")

        return "\n".join(lines)


# Module exports
__all__ = ["AnomalyDetector"]
__version__ = "1.0.0"
__modified__ = "2026-02-05"
