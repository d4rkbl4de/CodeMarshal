"""
inquiry/answers/thinking_engine.py

Thinking Engine for CodeMarshal Query System
============================================

This module generates recommendations, suggestions, and thoughtful analysis
based on observations. Unlike other analyzers, this module can provide
opinionated guidance about what to investigate next.

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 3: Explicit Limitations (marks recommendations as suggestions only)
- Article 9: Immutable Observations (read-only analysis)
- Article 17: Uncertainty Indicators (confidence levels on suggestions)
- Article 20: Human Primacy (recommendations serve human judgment, not replace it)

This module IS:
- A recommendation engine for investigation next steps
- A risk identifier based on observed patterns
- A thoughtful analyzer providing guidance
- An opinionated assistant (within strict limits)

This module IS NOT:
- An AI decision maker (human always decides)
- A code reviewer (does not judge quality)
- An automatic fixer (does not suggest specific changes)
- A substitute for human judgment

ALLOWED IMPORTS:
- typing modules (type hints only)
- No external AI/ML libraries

PROHIBITED IMPORTS:
- Any neural networks or LLMs
- Automated decision systems
- Code generation libraries

QUESTION TYPES HANDLED:
- "What should I investigate next?"
- "What are the risks?"
- "What concerns you about this code?"
- "Suggest next steps"

RECOMMENDATION TYPES:
1. Next Steps - Prioritized investigation suggestions
2. Risk Assessment - Potential problems and mitigations
3. General Analysis - Overall observations and thoughts

PRIORITY LEVELS:
- High: Boundary violations, architectural issues
- Medium: High coupling, complexity concerns
- Low: Minor patterns, informational only

CONFIDENCE INDICATORS:
All recommendations include:
- Priority level (High/Medium/Low)
- Reasoning (why this matters)
- Suggested action (what to do)
- Confidence marker (how certain)

LIMITATION DECLARATIONS:
- Recommendations are suggestions only
- Human must make final decisions
- System cannot judge code quality
- No specific refactoring instructions
- No automatic fix generation
"""

from typing import Any


class ThinkingEngine:
    """
    Generate thoughtful analysis and suggestions based on observations.

    The ThinkingEngine is unique among analyzers because it provides
    opinionated recommendations rather than just facts. It analyzes
    patterns in observations and suggests what a human investigator
    might want to focus on next.

    RECOMMENDATION PHILOSOPHY:

    This engine provides suggestions, not mandates. All recommendations:
    1. Are clearly marked as suggestions
    2. Include reasoning for the suggestion
    3. Provide actionable next steps
    4. Acknowledge uncertainty where appropriate
    5. Never override human judgment

    RECOMMENDATION CATEGORIES:

    1. Next Steps
       Based on findings, suggests what to investigate next
       - High priority: Critical issues (boundary violations)
       - Medium priority: Concerns (high coupling)
       - Low priority: Informational (orphan files)

    2. Risk Assessment
       Identifies potential risks in the codebase
       - Architectural risks (boundary violations)
       - Maintainability risks (high coupling)
       - Stability risks (circular dependencies)
       Each includes impact and mitigation suggestions

    3. General Analysis
       Provides overall assessment and recommendations
       - Statistics summary
       - Pattern interpretation
       - General suggestions

    SEVERITY CLASSIFICATION:

    - High: Requires immediate attention
      Examples: Boundary violations affecting architecture

    - Medium: Should be addressed soon
      Examples: High coupling that may cause maintenance issues

    - Low: Informational, address when convenient
      Examples: Minor patterns, style observations

    CONFIDENCE LEVELS:

    Recommendations include implicit confidence:
    - "Investigate X" (high confidence)
    - "Consider reviewing Y" (medium confidence)
    - "You might want to look at Z" (low confidence)

    LIMITATION DECLARATIONS:

    This engine explicitly does NOT:
    - Make decisions for the user
    - Judge code as "good" or "bad"
    - Suggest specific code changes
    - Guarantee that recommendations are correct
    - Replace human architectural judgment

    THREAD SAFETY:
    Stateless class - safe for concurrent use.

    PERFORMANCE:
    - Time: O(n) where n = observations
    - Space: O(k) where k = recommendations
    - Single-pass analysis

    EXAMPLES:
        >>> engine = ThinkingEngine()
        >>> observations = [...]
        >>> result = engine.analyze(observations, "What should I investigate?")
        >>> print(result)
        Suggested Next Steps:
        ...
    """

    # Class constants
    _SECTION_SEPARATOR_LENGTH: int = 60
    """Length of ASCII separator lines."""

    _HIGH_COUPLING_THRESHOLD: int = 15
    """Imports count considered high coupling."""

    _ORPHAN_THRESHOLD: int = 5
    """Number of orphan files to trigger recommendation."""

    def __init__(self) -> None:
        """Initialize the ThinkingEngine."""
        pass

    def analyze(self, observations: list[dict[str, Any]], question: str) -> str:
        """
        Analyze observations and generate thoughtful answers.

        QUESTION ROUTING:
        - "investigate" or "next" → Next steps suggestions
        - "risk" or "concern" → Risk assessment
        - Default → General analysis

        Args:
            observations: List of observations to analyze.
            question: Natural language question.

        Returns:
            str: Recommendations, risk assessment, or analysis.
        """
        question_lower = question.lower()

        if "investigate" in question_lower or "next" in question_lower:
            return self._suggest_next_steps(observations)
        elif "risk" in question_lower or "concern" in question_lower:
            return self._identify_risks(observations)
        else:
            return self._general_analysis(observations)

    def _suggest_next_steps(self, observations: list[dict[str, Any]]) -> str:
        """
        Suggest what to investigate next based on observations.

        Analyzes findings and generates prioritized recommendations
        for further investigation.

        Args:
            observations: Observations to analyze.

        Returns:
            str: Prioritized list of suggestions.
        """
        suggestions: list[dict[str, Any]] = []

        # Check for boundary violations
        boundary_violations = 0
        for obs in observations:
            if obs.get("type") == "boundary_sight":
                boundary_violations += len(obs.get("crossings", []))
            if obs.get("type") == "import_sight":
                boundary_violations += len(obs.get("boundary_violations", []))

        if boundary_violations > 0:
            suggestions.append(
                {
                    "priority": "High",
                    "suggestion": f"Investigate {boundary_violations} boundary violations",
                    "reason": "Architectural boundaries are being crossed",
                    "action": "codemarshal query <id> --question='Show boundary violations' --question-type=anomalies",
                }
            )

        # Check for high coupling
        high_coupling_files = []
        for obs in observations:
            if obs.get("type") == "import_sight":
                statements = obs.get("statements", [])
                if len(statements) > self._HIGH_COUPLING_THRESHOLD:
                    high_coupling_files.append(
                        {"file": obs.get("file", ""), "imports": len(statements)}
                    )

        if high_coupling_files:
            suggestions.append(
                {
                    "priority": "Medium",
                    "suggestion": f"Review {len(high_coupling_files)} files with high import counts",
                    "reason": "High coupling may indicate design issues",
                    "files": ", ".join(f["file"] for f in high_coupling_files[:3]),
                }
            )

        # Check for orphan files
        files_with_imports: set[str] = set()
        all_files: set[str] = set()

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

        orphan_files = all_files - files_with_imports
        if len(orphan_files) > self._ORPHAN_THRESHOLD:
            suggestions.append(
                {
                    "priority": "Low",
                    "suggestion": f"Review {len(orphan_files)} files with no imports",
                    "reason": "May be unused code or entry points",
                }
            )

        # Handle no suggestions
        if not suggestions:
            return """Suggested Next Steps:
========================

The codebase appears well-structured based on current observations.

Consider investigating:
1. Specific modules of interest with:
   codemarshal query <id> --question="What does [module] do?" --question-type=purpose

2. Dependency patterns with:
   codemarshal query <id> --question="Show import relationships" --question-type=connections

3. Code quality metrics with pattern queries
"""

        # Build formatted output
        lines: list[str] = [
            "Suggested Next Steps:",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        for i, sugg in enumerate(suggestions, 1):
            lines.append(f"\n{i}. [{sugg['priority']}] {sugg['suggestion']}")
            lines.append(f"   Reason: {sugg['reason']}")

            if "action" in sugg:
                lines.append(f"   Action: {sugg['action']}")
            if "files" in sugg:
                lines.append("   Files to review:")
                for f in sugg["files"]:
                    lines.append(f"     • {f}")

        lines.append("\n" + "=" * self._SECTION_SEPARATOR_LENGTH)
        lines.append("\nTo investigate further, use:")
        lines.append(
            "  codemarshal query <investigation_id> --question='...' --question-type=<type>"
        )

        return "\n".join(lines)

    def _identify_risks(self, observations: list[dict[str, Any]]) -> str:
        """
        Identify potential risks in the codebase.

        Analyzes observations for patterns that may indicate risks
        to architecture, maintainability, or stability.

        Args:
            observations: Observations to analyze.

        Returns:
            str: Risk assessment with severity and mitigations.
        """
        risks: list[dict[str, Any]] = []

        # Risk 1: Boundary violations
        boundary_count = 0
        for obs in observations:
            if obs.get("type") == "boundary_sight":
                boundary_count += len(obs.get("crossings", []))
            if obs.get("type") == "import_sight":
                boundary_count += len(obs.get("boundary_violations", []))

        if boundary_count > 0:
            risks.append(
                {
                    "level": "High",
                    "risk": "Architectural boundary violations",
                    "count": boundary_count,
                    "impact": "Code may be tightly coupled across layers",
                    "mitigation": "Review and refactor cross-boundary imports",
                }
            )

        # Risk 2: High coupling
        high_coupling_count = 0
        for obs in observations:
            if obs.get("type") == "import_sight":
                if len(obs.get("statements", [])) > self._HIGH_COUPLING_THRESHOLD:
                    high_coupling_count += 1

        if high_coupling_count > 0:
            risks.append(
                {
                    "level": "Medium",
                    "risk": "High coupling detected",
                    "count": high_coupling_count,
                    "impact": "Modules may be difficult to test and maintain",
                    "mitigation": "Consider breaking down large modules",
                }
            )

        # Risk 3: Relative imports
        relative_import_count = 0
        for obs in observations:
            if obs.get("type") == "import_sight":
                for stmt in obs.get("statements", []):
                    if isinstance(stmt, dict):
                        module = stmt.get("module", "")
                        if ".." in module or module.startswith("."):
                            relative_import_count += 1

        if relative_import_count > 0:
            risks.append(
                {
                    "level": "Low",
                    "risk": "Relative imports present",
                    "count": relative_import_count,
                    "impact": "May cause import issues when moving files",
                    "mitigation": "Consider using absolute imports",
                }
            )

        # Handle no risks
        if not risks:
            return """Risk Assessment:
================

No significant risks detected in the current observations.

The codebase appears to be:
• Well-structured architecturally
• Following import best practices
• Maintaining reasonable coupling levels

Continue monitoring as the codebase evolves.
"""

        # Build formatted output
        lines: list[str] = ["Risk Assessment:", "=" * self._SECTION_SEPARATOR_LENGTH]

        for i, risk in enumerate(risks, 1):
            lines.append(f"\n{i}. [{risk['level']}] {risk['risk']}")
            lines.append(f"   Occurrences: {risk['count']}")
            lines.append(f"   Impact: {risk['impact']}")
            lines.append(f"   Mitigation: {risk['mitigation']}")

        return "\n".join(lines)

    def _general_analysis(self, observations: list[dict[str, Any]]) -> str:
        """
        Provide general thoughtful analysis.

        Generates overall assessment of the codebase based on
        statistics and patterns.

        Args:
            observations: Observations to analyze.

        Returns:
            str: General analysis with observations and recommendations.
        """
        # Gather statistics
        stats: dict[str, int] = {
            "total_observations": len(observations),
            "files": 0,
            "imports": 0,
            "exports": 0,
            "violations": 0,
        }

        for obs in observations:
            obs_type = obs.get("type", "")
            if obs_type == "file_sight":
                result = obs.get("result", {})
                stats["files"] += len(result.get("modules", []))
            elif obs_type == "import_sight":
                stats["imports"] += len(obs.get("statements", []))
            elif obs_type == "export_sight":
                result = obs.get("result", {})
                stats["exports"] += len(result.get("exports", []))
            elif obs_type == "boundary_sight":
                stats["violations"] += len(obs.get("crossings", []))

        # Build output
        lines: list[str] = [
            "Thoughtful Analysis:",
            "=" * self._SECTION_SEPARATOR_LENGTH,
            f"Based on {stats['total_observations']} observations:",
            "",
            f"• Analyzed {stats['files']} files",
            f"• Found {stats['imports']} import statements",
            f"• Identified {stats['exports']} public exports",
            f"• Detected {stats['violations']} boundary violations",
            "",
        ]

        # Add interpretation
        if stats["violations"] == 0:
            lines.append("✓ The codebase maintains good architectural boundaries.")
        else:
            lines.append(
                f"⚠ {stats['violations']} boundary violations suggest potential refactoring needs."
            )

        if stats["files"] > 0:
            avg_imports = stats["imports"] / max(stats["files"], 1)
            if avg_imports < 5:
                lines.append(
                    "✓ Low average imports per file indicates good modularity."
                )
            elif avg_imports > 10:
                lines.append("⚠ High average imports may indicate tight coupling.")

        lines.append("")
        lines.append("Recommendations:")
        lines.append("• Review boundary violations if any")
        lines.append("• Consider the module dependency graph")
        lines.append("• Examine files with high import counts")

        return "\n".join(lines)

    def _calculate_health_score(self, stats: dict[str, int]) -> int:
        """
        Calculate a simple health score for the codebase.

        Score is based on:
        - Boundary violations (negative)
        - File count (neutral)
        - Import/export ratio

        Args:
            stats: Statistics dictionary

        Returns:
            int: Health score (0-100)
        """
        score = 100

        # Deduct for boundary violations
        score -= stats.get("violations", 0) * 10

        # Deduct for high coupling
        if stats["files"] > 0:
            avg_imports = stats["imports"] / stats["files"]
            if avg_imports > 10:
                score -= 10
            elif avg_imports > 20:
                score -= 20

        return max(0, min(100, score))


# Module exports
__all__ = ["ThinkingEngine"]
"""Exported symbols from this module."""

__version__ = "1.0.0"
"""Module version following semantic versioning."""

__modified__ = "2026-02-05"
"""Last modification date."""

__author__ = "CodeMarshal Team"
"""Module author attribution."""
