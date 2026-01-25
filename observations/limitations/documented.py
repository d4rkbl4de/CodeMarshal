"""
DOCUMENTED LIMITATIONS - Human-Readable Explanations

Clear textual descriptions of each declared limitation.
For truth transfer to humans, not execution.
"""

from __future__ import annotations

import dataclasses
import textwrap

# Local import - allowed per specification
from .declared import LimitationCategory, LimitationScope


@dataclasses.dataclass(frozen=True, slots=True)
class LimitationDoc:
    """Human-readable documentation for a limitation."""

    limitation_id: str
    category: LimitationCategory
    scope: LimitationScope
    title: str  # Short, clear title
    explanation: str  # What this limitation means
    rationale: str  # Why this limitation exists
    implications: str  # How this affects interpretation
    mitigation_notes: str | None = None  # How humans can work around it

    def to_markdown(self) -> str:
        """Format as markdown for documentation."""
        lines = [
            f"## {self.title}",
            "",
            f"**ID:** `{self.limitation_id}`",
            f"**Category:** {self.category.value}",
            f"**Scope:** {self.scope.value}",
            "",
            "### Explanation",
            textwrap.fill(self.explanation, width=80),
            "",
            "### Rationale",
            textwrap.fill(self.rationale, width=80),
            "",
            "### Implications for Interpretation",
            textwrap.fill(self.implications, width=80),
        ]

        if self.mitigation_notes:
            lines.extend(
                [
                    "",
                    "### Mitigation Notes",
                    textwrap.fill(self.mitigation_notes, width=80),
                ]
            )

        return "\n".join(lines)


# Documentation registry - MUST stay synchronized with declared limitations
_LIMITATION_DOCS: dict[str, LimitationDoc] = {
    "dynamic-imports": LimitationDoc(
        limitation_id="dynamic-imports",
        category=LimitationCategory.STRUCTURAL,
        scope=LimitationScope.GLOBAL,
        title="Dynamic Imports Not Executed",
        explanation=(
            "CodeMarshal only observes static import statements. "
            "Dynamic imports using importlib, __import__(), exec(), or eval() "
            "are not executed during observation."
        ),
        rationale=(
            "Executing arbitrary code during static analysis is unsafe and "
            "non-deterministic. It could modify system state, access networks, "
            "or have side effects."
        ),
        implications=(
            "Modules loaded dynamically at runtime will not appear in import graphs. "
            "This creates blind spots in dependency analysis for codebases that "
            "heavily use plugin systems or runtime module loading."
        ),
        mitigation_notes=(
            "For complete analysis, statically declare all possible imports or "
            "use configuration files that can be observed separately."
        ),
    ),
    "generated-code": LimitationDoc(
        limitation_id="generated-code",
        category=LimitationCategory.STRUCTURAL,
        scope=LimitationScope.PER_FILE,
        title="Generated Code Not Materialized",
        explanation=(
            "Code generated at build time (protobuf, Thrift, Jinja templates, etc.) "
            "is not observed unless it already exists as source files."
        ),
        rationale=(
            "CodeMarshal observes the filesystem as-is. Requiring build steps "
            "would violate the principle of local-only, deterministic operation."
        ),
        implications=(
            "Dependencies on generated code may be missing from observations. "
            "The structure of generated classes/interfaces is invisible unless "
            "the generated files are committed to source control."
        ),
        mitigation_notes=(
            "Commit generated code to source control or run CodeMarshal after "
            "the build process completes."
        ),
    ),
    "network-modules": LimitationDoc(
        limitation_id="network-modules",
        category=LimitationCategory.INTENTIONAL,
        scope=LimitationScope.GLOBAL,
        title="Network-Loaded Modules Ignored",
        explanation=(
            "Modules downloaded from networks during import are not observed. "
            "Only locally available modules are analyzed."
        ),
        rationale=(
            "Network access violates the local-only operation principle and "
            "introduces non-determinism. Observations must be reproducible "
            "without external services."
        ),
        implications=(
            "Packages that dynamically fetch code will appear incomplete. "
            "This is a feature, not a bug - it ensures observations reflect "
            "only what is locally verifiable."
        ),
        mitigation_notes=(
            "Ensure all dependencies are locally installed before observation. "
            "Use virtual environments or containerization to capture complete "
            "dependency graphs."
        ),
    ),
    "runtime-behavior": LimitationDoc(
        limitation_id="runtime-behavior",
        category=LimitationCategory.STRUCTURAL,
        scope=LimitationScope.GLOBAL,
        title="Runtime-Only Behavior Excluded",
        explanation=(
            "Behavior that only manifests at runtime (conditional imports, "
            "dynamic attribute access, monkey patching) is not observed."
        ),
        rationale=(
            "Static analysis cannot predict execution flow. Attempting to do so "
            "would require interpretation and inference, violating observation purity."
        ),
        implications=(
            "The observed code structure may differ from runtime behavior. "
            "This is especially important for metaprogramming-heavy codebases "
            "and frameworks that modify behavior at runtime."
        ),
        mitigation_notes=(
            "Use CodeMarshal's anomaly detection to identify patterns that "
            "suggest runtime dynamism, but remember these are only signals, "
            "not observations of actual runtime behavior."
        ),
    ),
    "binary-files": LimitationDoc(
        limitation_id="binary-files",
        category=LimitationCategory.INTENTIONAL,
        scope=LimitationScope.PER_FILE,
        title="Binary Files Not Decoded",
        explanation=(
            "Binary files (.pyc, .so, .dll, images, etc.) are not decoded "
            "or analyzed. They are noted as present but their contents are opaque."
        ),
        rationale=(
            "Binary analysis requires specialized tools and often involves "
            "guessing or inference. CodeMarshal focuses on textual source code "
            "analysis for truth preservation."
        ),
        implications=(
            "Dependencies or logic embedded in binary files are invisible. "
            "This includes compiled extensions, serialized data, and embedded resources."
        ),
        mitigation_notes=(
            "For compiled extensions, analyze the source code instead. "
            "For data files, convert to text formats where possible."
        ),
    ),
    "symbolic-links-depth": LimitationDoc(
        limitation_id="symbolic-links-depth",
        category=LimitationCategory.CONDITIONAL,
        scope=LimitationScope.GLOBAL,
        title="Symbolic Links Followed to Limited Depth",
        explanation=(
            "Symbolic links are followed only to a configured maximum depth "
            "(default: 10). Longer chains are truncated."
        ),
        rationale=(
            "Infinite symlink loops would cause observation to hang. "
            "Depth limiting ensures termination while capturing most "
            "practical symlink usage."
        ),
        implications=(
            "Very deep or circular symlink structures may appear truncated "
            "or broken. File counts may be inaccurate for such structures."
        ),
        mitigation_notes=(
            "Increase the symlink_depth configuration if needed, but beware "
            "of infinite loops. Consider flattening complex symlink structures."
        ),
    ),
}


def get_limitation_docs() -> dict[str, LimitationDoc]:
    """Return all limitation documentation."""
    return _LIMITATION_DOCS.copy()


def get_doc_for_limitation(limitation_id: str) -> LimitationDoc | None:
    """Get documentation for a specific limitation."""
    return _LIMITATION_DOCS.get(limitation_id)


def generate_full_documentation() -> str:
    """Generate complete markdown documentation of all limitations."""
    docs = get_limitation_docs()

    header = textwrap.dedent("""
        # CodeMarshal Observational Limitations

        This document describes what CodeMarshal **cannot** and **will not** observe.
        These limitations are intentional and necessary for truth preservation.

        ## Categories

        - **Structural (cannot):** System capability limitations
        - **Intentional (will_not):** Design choices for truth preservation
        - **Conditional (not_with_current_config):** Could observe with different settings

        ## All Limitations

    """).strip()

    sections = [header]
    for doc in sorted(docs.values(), key=lambda d: d.limitation_id):
        sections.append(doc.to_markdown())
        sections.append("")  # Blank line between sections

    footer = textwrap.dedent("""
        ## Truth Preservation Note

        These limitations are not bugs - they are explicit declarations of
        observational boundaries. Knowing what we cannot see is essential
        for interpreting what we can see.

        CodeMarshal will never silently ignore these limitations or pretend
        to see beyond them. When a limitation affects an observation, it will
        be clearly indicated with ⚠️.
    """).strip()

    sections.append(footer)
    return "\n".join(sections)
