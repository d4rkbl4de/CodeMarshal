"""
PURPOSE: "What does this do?" - Aggregating Declared Signals Without Inference

This module answers the second legitimate human question about a codebase:
What observable signals suggest functionality, without inferring intent or business logic.

CONSTITUTIONAL RULES:
1. Never guess business logic
2. Never infer developer intention
3. Never collapse ambiguity
4. Only point to observable facts (entry points, exports, public interfaces)
5. Surface uncertainty aggressively
6. Use tentative language: "appears to", "may serve as", "suggests"

Tier 1 Violation: If this module makes any claim about what code "should" do,
what developers "intended", or what business purpose it serves, the system halts immediately.
"""

import collections
import json
import os
import pathlib
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from re import Pattern
from typing import (
    Any,
)

from observations.eyes.export_sight import ExportObservation

# Allowed Layer 1 imports (reality layer)
from observations.eyes.import_sight import ImportObservation
from observations.limitations.validation import ValidationLimitation

# Allowed Python stdlib


class FunctionalitySignal(Enum):
    """Observable signals of functionality without interpretation.

    Each signal must be directly observable in source code.
    No inferred meaning allowed.
    """

    ENTRY_POINT = auto()  # __name__ == "__main__" or main() function
    CLI_BINDING = auto()  # argparse, click, typer, sys.argv usage
    PUBLIC_API = auto()  # __all__ declaration or no leading underscore
    CLASS_CONSTRUCTOR = auto()  # __init__ method
    DECORATOR_USAGE = auto()  # @app.route, @click.command, etc.
    CONFIGURATION = auto()  # Config files, environment variables
    DATA_TRANSFORMATION = auto()  # Functions with "to_", "from_", "parse", "format"
    ERROR_HANDLING = auto()  # try/except, raise, assert
    ILLEGIBLE = auto()  # Cannot determine from observable signals
    UNCERTAIN = auto()  # Multiple possible signals


@dataclass(frozen=True)
class DeclaredSignal:
    """Immutable observation of a functionality signal in source code.

    Contains only what is textually present.
    No inference about what it "means" or "does".
    """

    source_path: pathlib.Path
    line_number: int
    signal_type: FunctionalitySignal
    raw_text: str  # The exact text from source code
    context_lines: tuple[str, ...]  # Surrounding lines for context

    # Associated exports/imports (if observable)
    associated_exports: tuple[str, ...] = field(default_factory=tuple)
    associated_imports: tuple[str, ...] = field(default_factory=tuple)

    # Uncertainty indicators
    confidence: float = 0.5  # Always low by default (epistemic humility)
    alternative_signals: tuple[FunctionalitySignal, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate signal doesn't contain inference."""
        # Constitutional: No interpretation in raw_text
        if "should" in self.raw_text.lower() or "must" in self.raw_text.lower():
            raise ConstitutionalViolation(
                "Signal text contains normative language. "
                "Only descriptive text allowed."
            )

        # Constitutional: Confidence must reflect uncertainty
        if self.confidence > 0.7:
            raise ConstitutionalViolation(
                f"Confidence {self.confidence} too high. "
                "Purpose signals must reflect uncertainty (max 0.7)."
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary without interpretation."""
        return {
            "source_path": str(self.source_path),
            "line_number": self.line_number,
            "signal_type": self.signal_type.name,
            "raw_text": self.raw_text,
            "context_lines": list(self.context_lines),
            "associated_exports": list(self.associated_exports),
            "associated_imports": list(self.associated_imports),
            "confidence": self.confidence,
            "alternative_signals": [s.name for s in self.alternative_signals],
            "_type": "declared_signal",
        }


@dataclass
class ModulePurpose:
    """Aggregated signals about a module's observable functionality.

    Constitutional: This is a framing, not a truth claim.
    All language must be tentative and evidence-based.
    """

    module_path: pathlib.Path
    signals: list[DeclaredSignal]
    primary_signal: FunctionalitySignal | None = None

    # Observational context
    has_main_guard: bool = False
    has_argparse: bool = False
    has_decorators: bool = False
    has_exports: bool = False
    has_config_parsing: bool = False

    # Limitations
    cannot_see: list[str] = field(default_factory=list)
    uncertain_about: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure purpose description remains tentative."""
        # Constitutional: Primary signal cannot be certain
        if self.primary_signal == FunctionalitySignal.ILLEGIBLE:
            self.primary_signal = None

        # Count signals for statistical context only
        signal_counts = collections.Counter(s.signal_type for s in self.signals)
        if signal_counts:
            most_common = signal_counts.most_common(1)[0][0]
            if most_common != FunctionalitySignal.UNCERTAIN:
                self.primary_signal = most_common

    def describe(self) -> str:
        """Generate tentative description based on observable signals.

        Constitutional: Must use tentative language.
        Must include uncertainty markers.
        """
        if not self.signals:
            return (
                "⚠️ No observable functionality signals found. Cannot determine purpose."
            )

        parts = []

        # Start with uncertainty
        parts.append("Based on observable signals, this module appears to:")

        # Add signal descriptions
        signal_descriptions = []

        for signal in self.signals:
            if signal.signal_type == FunctionalitySignal.ENTRY_POINT:
                signal_descriptions.append(
                    "• Serve as an entry point (if __name__ == '__main__')"
                )
            elif signal.signal_type == FunctionalitySignal.CLI_BINDING:
                signal_descriptions.append(
                    "• Provide CLI functionality (argparse/click usage)"
                )
            elif signal.signal_type == FunctionalitySignal.PUBLIC_API:
                signal_descriptions.append(
                    "• Expose a public API (__all__ or public names)"
                )
            elif signal.signal_type == FunctionalitySignal.CLASS_CONSTRUCTOR:
                signal_descriptions.append(
                    "• Define class constructors (__init__ methods)"
                )
            elif signal.signal_type == FunctionalitySignal.DECORATOR_USAGE:
                signal_descriptions.append("• Use decorators (observable @ patterns)")
            elif signal.signal_type == FunctionalitySignal.CONFIGURATION:
                signal_descriptions.append(
                    "• Handle configuration (config parsing patterns)"
                )
            elif signal.signal_type == FunctionalitySignal.DATA_TRANSFORMATION:
                signal_descriptions.append(
                    "• Transform data (to_/from_/parse/format patterns)"
                )
            elif signal.signal_type == FunctionalitySignal.ERROR_HANDLING:
                signal_descriptions.append(
                    "• Handle errors (try/except/raise patterns)"
                )

        # Add uncertainty notice
        if self.cannot_see:
            signal_descriptions.append(
                f"⚠️ Cannot see: {', '.join(self.cannot_see[:3])}"
            )
        if self.uncertain_about:
            signal_descriptions.append(
                f"⁉️ Uncertain about: {', '.join(self.uncertain_about[:3])}"
            )

        if signal_descriptions:
            parts.extend(signal_descriptions)
        else:
            parts.append("⚠️ Signals present but uncertain about their purpose.")

        # Add final disclaimer
        parts.append(
            "\nNote: This is a framing based on observable patterns, not a claim of intent."
        )

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary with tentative framing."""
        return {
            "module_path": str(self.module_path),
            "signals": [s.to_dict() for s in self.signals],
            "primary_signal": self.primary_signal.name if self.primary_signal else None,
            "has_main_guard": self.has_main_guard,
            "has_argparse": self.has_argparse,
            "has_decorators": self.has_decorators,
            "has_exports": self.has_exports,
            "has_config_parsing": self.has_config_parsing,
            "cannot_see": self.cannot_see,
            "uncertain_about": self.uncertain_about,
            "description": self.describe(),
            "_type": "module_purpose",
        }


@dataclass
class PurposeAnalysis:
    """Aggregated purpose signals across modules.

    Constitutional: This is not a system design document.
    It's a collection of observable patterns with uncertainty.
    """

    root_path: pathlib.Path
    module_purposes: dict[pathlib.Path, ModulePurpose]
    signal_frequency: dict[FunctionalitySignal, int]
    limitations: list[ValidationLimitation]

    # Cross-module patterns (observable only)
    common_exports: dict[str, int]  # export name -> frequency
    import_relationships: list[tuple[str, str, int]]  # importer -> imported -> count

    def get_modules_by_signal(
        self, signal_type: FunctionalitySignal
    ) -> list[pathlib.Path]:
        """Get modules exhibiting a specific signal."""
        return [
            path
            for path, purpose in self.module_purposes.items()
            if any(s.signal_type == signal_type for s in purpose.signals)
        ]

    def describe_ecosystem(self) -> str:
        """Generate tentative description of overall codebase patterns."""
        if not self.module_purposes:
            return "⚠️ No observable purpose signals found in codebase."

        # Count signals
        total_modules = len(self.module_purposes)
        entry_points = len(self.get_modules_by_signal(FunctionalitySignal.ENTRY_POINT))
        cli_modules = len(self.get_modules_by_signal(FunctionalitySignal.CLI_BINDING))
        api_modules = len(self.get_modules_by_signal(FunctionalitySignal.PUBLIC_API))

        parts = []
        parts.append("Based on observable signals across the codebase:")
        parts.append("")

        # Statistical observations only
        if entry_points > 0:
            parts.append(
                f"• {entry_points}/{total_modules} modules appear to be entry points"
            )
        if cli_modules > 0:
            parts.append(
                f"• {cli_modules}/{total_modules} modules appear to provide CLI functionality"
            )
        if api_modules > 0:
            parts.append(
                f"• {api_modules}/{total_modules} modules appear to expose public APIs"
            )

        # Common exports (observable fact)
        if self.common_exports:
            top_exports = sorted(
                self.common_exports.items(), key=lambda x: x[1], reverse=True
            )[:5]
            parts.append("")
            parts.append("Most frequently exported names:")
            for name, count in top_exports:
                parts.append(f"  - {name}: {count} modules")

        # Import relationships (observable fact)
        if self.import_relationships:
            parts.append("")
            parts.append("Common import patterns (importer → imported):")
            for importer, imported, count in sorted(
                self.import_relationships, key=lambda x: x[2], reverse=True
            )[:5]:
                parts.append(f"  - {importer} → {imported}: {count} times")

        parts.append("")
        parts.append(
            "⚠️ Note: These are statistical observations, not architectural claims."
        )

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary with uncertainty markers."""
        return {
            "root_path": str(self.root_path),
            "module_purposes": {
                str(path): purpose.to_dict()
                for path, purpose in self.module_purposes.items()
            },
            "signal_frequency": {
                signal.name: count for signal, count in self.signal_frequency.items()
            },
            "limitations": [
                limitation.to_dict()
                if hasattr(limitation, "to_dict")
                else str(limitation)
                for limitation in self.limitations
            ],
            "common_exports": self.common_exports,
            "import_relationships": [
                (importer, imported, count)
                for importer, imported, count in self.import_relationships
            ],
            "ecosystem_description": self.describe_ecosystem(),
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "_type": "purpose_analysis",
        }


class PurposeAnalyzer:
    """Analyzer that finds declared functionality signals without inference.

    This module exists to discipline language, not to be smart.
    Smart systems hallucinate purpose. Honest systems show evidence and hesitate.
    """

    # Observable patterns (must be directly visible in source)
    _ENTRY_POINT_PATTERNS: tuple[Pattern, ...] = (
        re.compile(r'if\s+__name__\s*==\s*["\']__main__["\']', re.IGNORECASE),
        re.compile(r"def\s+main\s*\(", re.IGNORECASE),
    )

    _CLI_PATTERNS: tuple[Pattern, ...] = (
        re.compile(r"argparse\.ArgumentParser", re.IGNORECASE),
        re.compile(r"click\.(command|group|option)", re.IGNORECASE),
        re.compile(r"typer\.Typer", re.IGNORECASE),
        re.compile(r"sys\.argv", re.IGNORECASE),
    )

    _DECORATOR_PATTERNS: tuple[Pattern, ...] = (
        re.compile(r"@app\.(route|get|post|put|delete)", re.IGNORECASE),
        re.compile(r"@click\.(command|group|option)", re.IGNORECASE),
        re.compile(r"@pytest\.(mark|fixture)", re.IGNORECASE),
    )

    _CONFIG_PATTERNS: tuple[Pattern, ...] = (
        re.compile(r"\.(json|yaml|yml|toml|ini|cfg|conf)\b", re.IGNORECASE),
        re.compile(r"os\.(getenv|environ)", re.IGNORECASE),
        re.compile(r"dotenv\.load_dotenv", re.IGNORECASE),
    )

    _TRANSFORM_PATTERNS: tuple[Pattern, ...] = (
        re.compile(r"\b(to_|from_|parse_|format_|convert_|transform_)", re.IGNORECASE),
        re.compile(r"\b(serialize|deserialize|encode|decode)\b", re.IGNORECASE),
    )

    def __init__(
        self,
        import_observations: list[ImportObservation],
        export_observations: list[ExportObservation],
    ):
        """Initialize with Layer 1 observations only."""
        self.import_observations = import_observations
        self.export_observations = export_observations
        self.limitations: list[ValidationLimitation] = []

        # Constitutional: Validate we only have observations
        for obs in import_observations:
            if not isinstance(obs, ImportObservation):
                raise ConstitutionalViolation(
                    f"Expected ImportObservation, got {type(obs)}"
                )

        for obs in export_observations:
            if not isinstance(obs, ExportObservation):
                raise ConstitutionalViolation(
                    f"Expected ExportObservation, got {type(obs)}"
                )

    def analyze_module(
        self, source_path: pathlib.Path, source_code: str
    ) -> ModulePurpose:
        """Analyze a single module for observable purpose signals.

        Constitutional: Only look at what's textually present.
        Never infer what isn't there.
        """
        signals: list[DeclaredSignal] = []
        cannot_see: list[str] = []
        uncertain_about: list[str] = []

        try:
            lines = source_code.splitlines()

            # Look for entry point patterns
            for i, line in enumerate(lines):
                context = self._get_context(lines, i)

                for pattern in self._ENTRY_POINT_PATTERNS:
                    if pattern.search(line):
                        signals.append(
                            DeclaredSignal(
                                source_path=source_path,
                                line_number=i + 1,
                                signal_type=FunctionalitySignal.ENTRY_POINT,
                                raw_text=line.strip(),
                                context_lines=context,
                                confidence=0.6,  # Moderate confidence
                            )
                        )

                # CLI patterns
                for pattern in self._CLI_PATTERNS:
                    if pattern.search(line):
                        signals.append(
                            DeclaredSignal(
                                source_path=source_path,
                                line_number=i + 1,
                                signal_type=FunctionalitySignal.CLI_BINDING,
                                raw_text=line.strip(),
                                context_lines=context,
                                confidence=0.5,  # Low confidence (could be imported but not used)
                            )
                        )

                # Decorator patterns
                for pattern in self._DECORATOR_PATTERNS:
                    if pattern.search(line):
                        signals.append(
                            DeclaredSignal(
                                source_path=source_path,
                                line_number=i + 1,
                                signal_type=FunctionalitySignal.DECORATOR_USAGE,
                                raw_text=line.strip(),
                                context_lines=context,
                                confidence=0.4,  # Very low confidence
                            )
                        )

            # Look for __all__ declarations
            if "__all__" in source_code:
                # Find the __all__ line
                for i, line in enumerate(lines):
                    if "__all__" in line:
                        context = self._get_context(lines, i)
                        signals.append(
                            DeclaredSignal(
                                source_path=source_path,
                                line_number=i + 1,
                                signal_type=FunctionalitySignal.PUBLIC_API,
                                raw_text=line.strip(),
                                context_lines=context,
                                confidence=0.7,  # Higher confidence (explicit declaration)
                            )
                        )
                        break

            # Look for class definitions with __init__
            if "class " in source_code and "__init__" in source_code:
                # Simple pattern matching (not full AST)
                for i, line in enumerate(lines):
                    if "class " in line:
                        # Look for __init__ in next 20 lines
                        for j in range(i + 1, min(i + 20, len(lines))):
                            if "__init__" in lines[j]:
                                context = self._get_context(lines, j)
                                signals.append(
                                    DeclaredSignal(
                                        source_path=source_path,
                                        line_number=j + 1,
                                        signal_type=FunctionalitySignal.CLASS_CONSTRUCTOR,
                                        raw_text=lines[j].strip(),
                                        context_lines=context,
                                        confidence=0.5,
                                    )
                                )
                                break

            # Record what we cannot see
            if not signals:
                cannot_see.append("clear functionality signals")
                uncertain_about.append("module's primary purpose")

        except Exception as e:
            # Constitutional: Record failures as limitations, not silence them
            self.limitations.append(
                ValidationLimitation(
                    source_path=str(source_path),
                    limitation_type="analysis_failure",
                    description=f"Could not analyze module: {str(e)}",
                    severity="medium",
                )
            )

        return ModulePurpose(
            module_path=source_path,
            signals=signals,
            cannot_see=cannot_see,
            uncertain_about=uncertain_about,
            has_main_guard=any(
                s.signal_type == FunctionalitySignal.ENTRY_POINT for s in signals
            ),
            has_argparse=any(
                s.signal_type == FunctionalitySignal.CLI_BINDING for s in signals
            ),
            has_decorators=any(
                s.signal_type == FunctionalitySignal.DECORATOR_USAGE for s in signals
            ),
            has_exports=any(
                s.signal_type == FunctionalitySignal.PUBLIC_API for s in signals
            ),
        )

    def analyze_codebase(
        self, source_files: dict[pathlib.Path, str]
    ) -> PurposeAnalysis:
        """Analyze all source files for purpose signals."""
        module_purposes: dict[pathlib.Path, ModulePurpose] = {}
        signal_counts: collections.defaultdict[FunctionalitySignal, int] = (
            collections.defaultdict(int)
        )

        # Analyze each module
        for source_path, source_code in source_files.items():
            purpose = self.analyze_module(source_path, source_code)
            module_purposes[source_path] = purpose

            # Count signals
            for signal in purpose.signals:
                signal_counts[signal.signal_type] += 1

        # Analyze export patterns (observable fact)
        common_exports = self._analyze_export_patterns()

        # Analyze import relationships (observable fact)
        import_relationships = self._analyze_import_relationships()

        return PurposeAnalysis(
            root_path=self._get_common_root(module_purposes.keys()),
            module_purposes=module_purposes,
            signal_frequency=dict(signal_counts),
            limitations=self.limitations,
            common_exports=common_exports,
            import_relationships=import_relationships,
        )

    def _get_context(
        self, lines: list[str], line_num: int, context_size: int = 2
    ) -> tuple[str, ...]:
        """Get context around a line without interpretation."""
        start = max(0, line_num - context_size)
        end = min(len(lines), line_num + context_size + 1)
        return tuple(lines[start:end])

    def _analyze_export_patterns(self) -> dict[str, int]:
        """Count how often each export appears (observable fact)."""
        exports: Counter[str] = collections.Counter()

        for obs in self.export_observations:
            if hasattr(obs, "exported_names"):
                for name in obs.exported_names:
                    exports[name] += 1

        return dict(exports)

    def _analyze_import_relationships(self) -> list[tuple[str, str, int]]:
        """Count import relationships (observable fact)."""
        relationships: collections.defaultdict[tuple[str, str], int] = (
            collections.defaultdict(int)
        )

        for obs in self.import_observations:
            if hasattr(obs, "source_module") and hasattr(obs, "imported_module"):
                key = (obs.source_module, obs.imported_module)
                relationships[key] += 1

        return [
            (importer, imported, count)
            for (importer, imported), count in relationships.items()
        ]

    def _get_common_root(self, paths: Iterator[pathlib.Path]) -> pathlib.Path:
        """Find common root path for analysis context."""
        path_list = list(paths)
        if not path_list:
            return pathlib.Path.cwd()

        # Start with first path
        common = path_list[0].parent

        for path in path_list[1:]:
            # Find common ancestor
            try:
                common = pathlib.Path(os.path.commonpath([common, path.parent]))
            except ValueError:
                # Paths have no common prefix
                return pathlib.Path.cwd()

        return common


class ConstitutionalViolation(Exception):
    """Exception raised when constitutional rules are violated."""

    def __init__(self, message: str, tier: int = 1):
        super().__init__(message)
        self.tier = tier
        self.message = message

        # Constitutional: Log violations
        self._log_violation()

    def _log_violation(self) -> None:
        """Log constitutional violation."""
        import logging

        logger = logging.getLogger("codemarshal.purpose")
        logger.error(f"Constitutional Violation (Tier {self.tier}): {self.message}")


# Utility functions for common purpose questions
def find_entry_points(analysis: PurposeAnalysis) -> list[dict[str, Any]]:
    """Find modules that appear to be entry points."""
    entry_modules = analysis.get_modules_by_signal(FunctionalitySignal.ENTRY_POINT)

    results = []
    for module_path in entry_modules:
        purpose = analysis.module_purposes[module_path]
        signals = [
            s
            for s in purpose.signals
            if s.signal_type == FunctionalitySignal.ENTRY_POINT
        ]

        for signal in signals:
            results.append(
                {
                    "module": str(module_path),
                    "line": signal.line_number,
                    "signal": signal.raw_text,
                    "confidence": signal.confidence,
                }
            )

    return results


def describe_module_purpose(
    analysis: PurposeAnalysis, module_path: pathlib.Path
) -> str | None:
    """Get tentative description of a module's purpose."""
    purpose = analysis.module_purposes.get(module_path)
    if purpose:
        return purpose.describe()
    return None


def export_purpose_report(analysis: PurposeAnalysis, output_path: pathlib.Path) -> None:
    """Export purpose analysis with uncertainty markers."""
    report = analysis.to_dict()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# Example usage (for testing only)
def analyze_example_purpose(source_dir: pathlib.Path) -> PurposeAnalysis:
    """Example function to demonstrate usage."""
    # This is a placeholder - in production, you'd have actual observations
    # For now, create dummy observations

    dummy_imports = []
    dummy_exports = []

    analyzer = PurposeAnalyzer(dummy_imports, dummy_exports)

    # Find Python files
    source_files = {}
    for py_file in source_dir.rglob("*.py"):
        try:
            source_files[py_file] = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

    return analyzer.analyze_codebase(source_files)


# Export public API
__all__ = [
    "FunctionalitySignal",
    "DeclaredSignal",
    "ModulePurpose",
    "PurposeAnalysis",
    "PurposeAnalyzer",
    "ConstitutionalViolation",
    "find_entry_points",
    "describe_module_purpose",
    "export_purpose_report",
]
