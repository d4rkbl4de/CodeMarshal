"""
Progressive Disclosure Constraint (Article 4 Enforcement)

This module defines the rule that complexity is revealed only when explicitly
requested by the human investigator. No information pushing, no adaptive
intelligence, no "helpful" guesses.

CRITICAL: This is NOT heuristics. This is a formal gating system that only
opens when human curiosity pulls. Violations are Tier-2 (immediate halt).
"""

from typing import Protocol, runtime_checkable, Optional, Dict, FrozenSet
from enum import Enum, auto
from dataclasses import dataclass, field


# ------------------------------------------------------------------------------
# QUESTION TYPES: WHAT HUMANS CAN ASK
# ------------------------------------------------------------------------------

# We import only the type definitions from inquiry.questions
# These protocols define the SHAPE of questions, not their implementation

@runtime_checkable
class HumanQuestion(Protocol):
    """Base protocol for all questions a human can ask."""
    
    @property
    def question_type(self) -> str:
        """Canonical identifier for the question kind."""
        ...
    
    @property
    def target_anchor(self) -> Optional[str]:
        """Specific observation or pattern being questioned, if any."""
        ...
    
    @property
    def is_follow_up(self) -> bool:
        """Whether this builds on a previous question (implies deeper disclosure)."""
        ...


@runtime_checkable
class StructureQuestion(HumanQuestion, Protocol):
    """Protocol for 'What's here?' questions."""
    
    @property
    def scope_boundary(self) -> str:
        """The directory or module boundary being examined."""
        ...


@runtime_checkable
class PurposeQuestion(HumanQuestion, Protocol):
    """Protocol for 'What does this do?' questions."""
    
    @property
    def focus_element(self) -> str:
        """The specific function, class, or module in question."""
        ...


@runtime_checkable
class ConnectionsQuestion(HumanQuestion, Protocol):
    """Protocol for 'How is it connected?' questions."""
    
    @property
    def from_element(self) -> str:
        """The starting point of connection exploration."""
        ...
    
    @property
    def connection_depth(self) -> int:
        """How many hops to explore (1 = direct, 2 = indirect)."""
        ...


@runtime_checkable
class AnomaliesQuestion(HumanQuestion, Protocol):
    """Protocol for 'What seems unusual?' questions."""
    
    @property
    def comparison_basis(self) -> Optional[str]:
        """What to compare against (e.g., 'project_norms', 'python_stdlib')."""
        ...


@runtime_checkable
class ThinkingQuestion(HumanQuestion, Protocol):
    """Protocol for 'What do I think?' questions."""
    
    @property
    def anchor_reference(self) -> str:
        """The observation or pattern being reflected upon."""
        ...


# ------------------------------------------------------------------------------
# DISCLOSURE STAGES: HOW MUCH CAN BE SEEN
# ------------------------------------------------------------------------------

class DisclosureStage(Enum):
    """
    Ordered stages of information revelation.
    
    Each stage requires explicit human action to reach.
    The system NEVER advances stages automatically.
    """
    
    # Stage 0: Nothing revealed (initial state)
    NOTHING = auto()
    
    # Stage 1: Minimal existence verification
    SURFACE = auto()      # e.g., "4 files exist", "module has 3 imports"
    
    # Stage 2: Basic composition and relationships
    EXPANDED = auto()     # e.g., "file has imports: X, Y, Z", "class has methods A, B"
    
    # Stage 3: Detailed internal structure
    DETAILED = auto()     # e.g., "function signature: def f(x: int) -> str", 
                         # "import statement: from a import b as c"
    
    # Stage 4: Exhaustive enumeration
    EXHAUSTIVE = auto()   # e.g., "all 247 characters of the docstring",
                         # "complete AST with byte offsets"
    
    # Stage 5: Analytical overlay (patterns, anomalies)
    ANALYTICAL = auto()   # e.g., "this module has unusually high fan-out",
                         # "these 3 files form a tight cluster"
    
    # Stage 6: Reflective synthesis (human thinking)
    REFLECTIVE = auto()   # e.g., "My notes on why this pattern matters",
                         # "Questions raised by this observation"
    
    def can_proceed_to(self, next_stage: 'DisclosureStage') -> bool:
        """
        Determine if moving from this stage to another is allowed.
        
        Rules:
        1. Can only move forward one stage at a time
        2. Cannot skip stages
        3. Cannot move backward (except via explicit reset)
        """
        if next_stage.value <= self.value:
            return False  # No backward movement
        
        if next_stage.value > self.value + 1:
            return False  # Cannot skip stages
        
        return True
    
    @property
    def requires_explicit_request(self) -> bool:
        """
        Whether this stage requires a clear human action to reach.
        
        All stages except NOTHING require explicit requests.
        """
        return self != DisclosureStage.NOTHING


# ------------------------------------------------------------------------------
# DISCLOSURE GATES: WHAT'S ALLOWED AT EACH STAGE
# ------------------------------------------------------------------------------

@dataclass(frozen=True)
class DisclosureGate:
    """
    A rule defining what content can be disclosed at a specific stage
    for a specific question type.
    
    This is immutable truth - gates are defined at system initialization.
    """
    
    question_type: str
    stage: DisclosureStage
    allowed_content_types: FrozenSet[str] = field(default_factory=lambda: frozenset[str]())
    required_explicit_action: str = field(default="")
    
    def allows_content(self, content_type: str) -> bool:
        """Check if a specific content type can be shown."""
        return content_type in self.allowed_content_types


# ------------------------------------------------------------------------------
# QUESTION → STAGE MAPPING: WHAT'S INITIALLY VISIBLE
# ------------------------------------------------------------------------------

class QuestionStageMapping:
    """
    Maps each question type to its initial disclosure stage.
    
    This defines the starting point - what you see when you first ask.
    All further disclosure requires explicit "show more" actions.
    """
    
    # Initial stages for each question type
    _INITIAL_STAGES: Dict[str, DisclosureStage] = {
        "structure": DisclosureStage.SURFACE,      # Start with file counts
        "purpose": DisclosureStage.EXPANDED,       # Start with basic signatures
        "connections": DisclosureStage.EXPANDED,   # Start with direct connections
        "anomalies": DisclosureStage.ANALYTICAL,   # Start with anomaly detection
        "thinking": DisclosureStage.REFLECTIVE,    # Start with existing notes
    }
    
    @classmethod
    def get_initial_stage(cls, question_type: str) -> DisclosureStage:
        """
        Get the starting disclosure stage for a question type.
        
        This is the MAXIMUM that can be shown without any follow-up requests.
        """
        try:
            return cls._INITIAL_STAGES[question_type]
        except KeyError:
            # Unknown question type gets minimal disclosure
            return DisclosureStage.SURFACE
    
    @classmethod
    def validate_question_type(cls, question_type: str) -> bool:
        """Check if a question type is recognized."""
        return question_type in cls._INITIAL_STAGES


# ------------------------------------------------------------------------------
# CORE RULE: PROGRESSIVE DISCLOSURE VALIDATOR
# ------------------------------------------------------------------------------

@dataclass
class ProgressiveDisclosureViolation(Exception):
    """Raised when interface attempts to show more than allowed for current stage."""
    
    question_type: str
    current_stage: DisclosureStage
    attempted_content_type: str
    allowed_content_types: FrozenSet[str]
    
    def __init__(
        self,
        question_type: str,
        current_stage: DisclosureStage,
        attempted_content_type: str,
        allowed_content_types: FrozenSet[str]
    ) -> None:
        self.question_type = question_type
        self.current_stage = current_stage
        self.attempted_content_type = attempted_content_type
        self.allowed_content_types = allowed_content_types
        
        msg = (
            f"Attempted to show '{attempted_content_type}' content for "
            f"'{question_type}' question at {current_stage.name} stage.\n"
            f"Allowed content types at this stage: {sorted(allowed_content_types)}\n"
            f"Article 4 violation: Complexity revealed without explicit request."
        )
        super().__init__(msg)


class ProgressiveDisclosureRule:
    """
    Enforces Article 4: Progressive Disclosure.
    
    This rule ensures that:
    1. Each question type starts at an appropriate initial disclosure level
    2. Only content appropriate for the current stage can be shown
    3. Advancement requires explicit human action
    4. Stages cannot be skipped
    
    The rule is defined declaratively via DisclosureGate objects.
    """
    
    # Define all disclosure gates (immutable system configuration)
    _GATES: Dict[str, Dict[DisclosureStage, DisclosureGate]] = {
        # Structure questions: "What's here?"
        "structure": {
            DisclosureStage.SURFACE: DisclosureGate(
                question_type="structure",
                stage=DisclosureStage.SURFACE,
                allowed_content_types=frozenset({
                    "file_count",
                    "directory_structure",
                    "module_boundaries",
                }),
                required_explicit_action="ask_structure_question",
            ),
            DisclosureStage.EXPANDED: DisclosureGate(
                question_type="structure",
                stage=DisclosureStage.EXPANDED,
                allowed_content_types=frozenset({
                    "file_types",
                    "import_statements",
                    "exported_names",
                    "module_hierarchy",
                }),
                required_explicit_action="expand_structure_details",
            ),
            DisclosureStage.DETAILED: DisclosureGate(
                question_type="structure",
                stage=DisclosureStage.DETAILED,
                allowed_content_types=frozenset({
                    "file_sizes",
                    "encoding_info",
                    "line_counts",
                    "import_details",  # source, alias, etc.
                }),
                required_explicit_action="show_detailed_structure",
            ),
            DisclosureStage.EXHAUSTIVE: DisclosureGate(
                question_type="structure",
                stage=DisclosureStage.EXHAUSTIVE,
                allowed_content_types=frozenset({
                    "byte_offsets",
                    "whitespace_analysis",
                    "exact_character_sequences",
                    "complete_ast",
                }),
                required_explicit_action="show_exhaustive_structure",
            ),
        },
        
        # Purpose questions: "What does this do?"
        "purpose": {
            DisclosureStage.EXPANDED: DisclosureGate(
                question_type="purpose",
                stage=DisclosureStage.EXPANDED,
                allowed_content_types=frozenset({
                    "function_signatures",
                    "class_declarations",
                    "docstring_summaries",
                    "decorator_names",
                }),
                required_explicit_action="ask_purpose_question",
            ),
            DisclosureStage.DETAILED: DisclosureGate(
                question_type="purpose",
                stage=DisclosureStage.DETAILED,
                allowed_content_types=frozenset({
                    "parameter_types",
                    "return_annotations",
                    "base_classes",
                    "method_signatures",
                }),
                required_explicit_action="expand_purpose_details",
            ),
            DisclosureStage.EXHAUSTIVE: DisclosureGate(
                question_type="purpose",
                stage=DisclosureStage.EXHAUSTIVE,
                allowed_content_types=frozenset({
                    "full_docstrings",
                    "type_comment_analysis",
                    "decorator_arguments",
                    "complete_signature_ast",
                }),
                required_explicit_action="show_exhaustive_purpose",
            ),
        },
        
        # Connections questions: "How is it connected?"
        "connections": {
            DisclosureStage.EXPANDED: DisclosureGate(
                question_type="connections",
                stage=DisclosureStage.EXPANDED,
                allowed_content_types=frozenset({
                    "direct_imports",
                    "immediate_dependents",
                    "module_adjacency",
                    "boundary_crossings",
                }),
                required_explicit_action="ask_connections_question",
            ),
            DisclosureStage.DETAILED: DisclosureGate(
                question_type="connections",
                stage=DisclosureStage.DETAILED,
                allowed_content_types=frozenset({
                    "indirect_imports",
                    "transitive_dependents",
                    "import_paths",
                    "circular_references",
                }),
                required_explicit_action="expand_connection_depth",
            ),
            DisclosureStage.EXHAUSTIVE: DisclosureGate(
                question_type="connections",
                stage=DisclosureStage.EXHAUSTIVE,
                allowed_content_types=frozenset({
                    "complete_dependency_graph",
                    "all_transitive_paths",
                    "import_frequency_counts",
                    "historical_connection_changes",
                }),
                required_explicit_action="show_exhaustive_connections",
            ),
        },
        
        # Anomalies questions: "What seems unusual?"
        "anomalies": {
            DisclosureStage.ANALYTICAL: DisclosureGate(
                question_type="anomalies",
                stage=DisclosureStage.ANALYTICAL,
                allowed_content_types=frozenset({
                    "pattern_violations",
                    "statistical_outliers",
                    "boundary_exceptions",
                    "unusual_imports",
                }),
                required_explicit_action="ask_anomalies_question",
            ),
            DisclosureStage.DETAILED: DisclosureGate(
                question_type="anomalies",
                stage=DisclosureStage.DETAILED,
                allowed_content_types=frozenset({
                    "anomaly_magnitude",
                    "comparison_baselines",
                    "historical_context",
                    "similar_anomalies",
                }),
                required_explicit_action="expand_anomaly_analysis",
            ),
            DisclosureStage.EXHAUSTIVE: DisclosureGate(
                question_type="anomalies",
                stage=DisclosureStage.EXHAUSTIVE,
                allowed_content_types=frozenset({
                    "full_statistical_analysis",
                    "all_detection_parameters",
                    "false_positive_rates",
                    "pattern_evolution_history",
                }),
                required_explicit_action="show_exhaustive_anomalies",
            ),
        },
        
        # Thinking questions: "What do I think?"
        "thinking": {
            DisclosureStage.REFLECTIVE: DisclosureGate(
                question_type="thinking",
                stage=DisclosureStage.REFLECTIVE,
                allowed_content_types=frozenset({
                    "existing_notes",
                    "anchor_references",
                    "note_timestamps",
                    "thinking_tags",
                }),
                required_explicit_action="ask_thinking_question",
            ),
            DisclosureStage.EXPANDED: DisclosureGate(
                question_type="thinking",
                stage=DisclosureStage.EXPANDED,
                allowed_content_types=frozenset({
                    "note_connections",
                    "thinking_patterns",
                    "question_evolution",
                    "insight_clusters",
                }),
                required_explicit_action="expand_thinking_context",
            ),
            DisclosureStage.EXHAUSTIVE: DisclosureGate(
                question_type="thinking",
                stage=DisclosureStage.EXHAUSTIVE,
                allowed_content_types=frozenset({
                    "complete_thinking_timeline",
                    "all_cross_references",
                    "thinking_metadata",
                    "exported_thoughts",
                }),
                required_explicit_action="show_exhaustive_thinking",
            ),
        },
    }
    
    def __init__(self) -> None:
        # Validate that all gates are properly ordered
        self._validate_gate_consistency()
    
    def _validate_gate_consistency(self) -> None:
        """Ensure gates form a proper progression for each question type."""
        for question_type, stages in self._GATES.items():
            # Get sorted stages for this question type
            sorted_stages = sorted(stages.keys(), key=lambda s: s.value)
            
            # Check that stages are consecutive
            for i in range(1, len(sorted_stages)):
                if not sorted_stages[i-1].can_proceed_to(sorted_stages[i]):
                    raise ValueError(
                        f"Invalid stage progression for {question_type}: "
                        f"{sorted_stages[i-1].name} → {sorted_stages[i].name}"
                    )
    
    def get_initial_stage(self, question_type: str) -> DisclosureStage:
        """Get the starting stage for a question type."""
        return QuestionStageMapping.get_initial_stage(question_type)
    
    def get_current_gate(
        self,
        question_type: str,
        current_stage: DisclosureStage
    ) -> Optional[DisclosureGate]:
        """
        Get the disclosure gate for the current stage.
        
        Returns None if the stage is not defined for this question type
        (which means no disclosure is allowed).
        """
        try:
            return self._GATES[question_type][current_stage]
        except KeyError:
            return None
    
    def get_next_gate(
        self,
        question_type: str,
        current_stage: DisclosureStage
    ) -> Optional[DisclosureGate]:
        """
        Get the next disclosure gate if human requests more detail.
        
        Returns None if no further disclosure is possible.
        """
        try:
            gates = self._GATES[question_type]
            # Find the next stage
            current_value = current_stage.value
            next_stage = None
            
            for stage in gates.keys():
                if stage.value == current_value + 1:
                    next_stage = stage
                    break
            
            return gates.get(next_stage) if next_stage else None
        except KeyError:
            return None
    
    def validate_disclosure(
        self,
        question_type: str,
        current_stage: DisclosureStage,
        content_type: str
    ) -> None:
        """
        Validate that showing specific content is allowed.
        
        Args:
            question_type: Type of question being asked
            current_stage: Current disclosure stage
            content_type: Type of content attempting to be shown
            
        Raises:
            ProgressiveDisclosureViolation: If content cannot be shown
        """
        gate = self.get_current_gate(question_type, current_stage)
        
        if gate is None:
            # No gate defined means no disclosure allowed at this stage
            allowed: FrozenSet[str] = frozenset()
        else:
            allowed = gate.allowed_content_types
        
        if content_type not in allowed:
            raise ProgressiveDisclosureViolation(
                question_type=question_type,
                current_stage=current_stage,
                attempted_content_type=content_type,
                allowed_content_types=allowed,
            )
    
    def can_advance_stage(
        self,
        question_type: str,
        current_stage: DisclosureStage
    ) -> bool:
        """Check if more detail can be revealed (human can ask for more)."""
        return self.get_next_gate(question_type, current_stage) is not None
    
    def get_required_action_to_advance(
        self,
        question_type: str,
        current_stage: DisclosureStage
    ) -> Optional[str]:
        """
        Get the explicit human action required to see more detail.
        
        Returns None if no further disclosure is possible.
        """
        next_gate = self.get_next_gate(question_type, current_stage)
        return next_gate.required_explicit_action if next_gate else None


# ------------------------------------------------------------------------------
# CONTENT PROTOCOL FOR VALIDATION
# ------------------------------------------------------------------------------

@runtime_checkable
class DisclosableContent(Protocol):
    """Content that can be progressively disclosed."""
    
    @property
    def content_type(self) -> str:
        """Canonical identifier for the content type."""
        ...
    
    @property
    def required_disclosure_stage(self) -> DisclosureStage:
        """Minimum stage at which this content can be shown."""
        ...


# ------------------------------------------------------------------------------
# VALIDATION UTILITIES (FOR INTERFACE IMPLEMENTERS)
# ------------------------------------------------------------------------------

def validate_content_for_stage(
    question_type: str,
    current_stage: DisclosureStage,
    content: DisclosableContent
) -> bool:
    """
    Helper for interfaces to validate content against disclosure rule.
    
    Returns True if content can be shown at current stage.
    Use this during interface rendering.
    
    Example:
        can_show = validate_content_for_stage(
            question_type="structure",
            current_stage=DisclosureStage.SURFACE,
            content=file_count_content
        )
    """
    rule = ProgressiveDisclosureRule()
    
    try:
        rule.validate_disclosure(question_type, current_stage, content.content_type)
        return True
    except ProgressiveDisclosureViolation:
        return False


def get_available_content_types(
    question_type: str,
    current_stage: DisclosureStage
) -> FrozenSet[str]:
    """
    Get all content types that can be shown at the current stage.
    
    Useful for interfaces to know what they're allowed to render.
    """
    rule = ProgressiveDisclosureRule()
    gate = rule.get_current_gate(question_type, current_stage)
    
    if gate:
        return gate.allowed_content_types
    return frozenset()


# ------------------------------------------------------------------------------
# TEST UTILITIES (FOR INTEGRITY GUARDIAN)
# ------------------------------------------------------------------------------

@dataclass
class MockDisclosableContent:
    """Minimal implementation for testing."""
    
    content_type: str
    required_disclosure_stage: DisclosureStage = DisclosureStage.SURFACE


@dataclass
class MockHumanQuestion:
    """Minimal implementation for testing."""
    
    question_type: str
    target_anchor: Optional[str] = None
    is_follow_up: bool = False


# ------------------------------------------------------------------------------
# EXPORTED CONTRACT
# ------------------------------------------------------------------------------

__all__ = [
    # Question Protocols
    'HumanQuestion',
    'StructureQuestion',
    'PurposeQuestion',
    'ConnectionsQuestion',
    'AnomaliesQuestion',
    'ThinkingQuestion',
    
    # Disclosure Stages
    'DisclosureStage',
    
    # Disclosure Gates
    'DisclosureGate',
    
    # Core Rule
    'ProgressiveDisclosureRule',
    'ProgressiveDisclosureViolation',
    
    # Content Protocol
    'DisclosableContent',
    
    # Utilities
    'validate_content_for_stage',
    'get_available_content_types',
    'QuestionStageMapping',
    
    # Test Utilities (exported for integrity tests only)
    'MockDisclosableContent',
    'MockHumanQuestion',
]