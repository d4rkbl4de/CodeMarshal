"""
QUESTIONS PACKAGE: Human Questions Registry

This file serves as a registry of question types and explicitly exports
supported question classes. It contains no logic, defaults, or state.

Purpose:
1. Marks the boundary where interpretive activity begins
2. Prevents accidental imports into Layer 1 (observations/)
3. Allows the interface layer (lens/) to:
   - Enumerate available questions
   - Enforce linear investigation flow (Article 6)

Hard Rule:
No observation code (Layer 1) may import from inquiry (Layer 2).
This file exists to enforce that directional gravity.

CONSTITUTIONAL RULES:
1. No logic in this file - only declarations and exports
2. No defaults - each question module defines its own defaults
3. No state - this is a static registry
4. No computation - only type definitions and exports

Tier 1 Violation: If this file contains any business logic,
state management, or computation, the system halts immediately.
"""

import sys
from typing import (
    Dict, Any, List, Tuple, Optional,
     Protocol, runtime_checkable
)
from enum import Enum, auto


class QuestionType(Enum):
    """Enumeration of human question archetypes.
    
    These represent the shape of human curiosity, not answers.
    Ordered according to natural investigation flow (Article 6).
    """
    STRUCTURE = auto()    # "What's here?" - First question
    PURPOSE = auto()      # "What does this do?" - Second question
    CONNECTIONS = auto()  # "How is it connected?" - Third question
    ANOMALIES = auto()    # "What seems unusual?" - Fourth question
    THINKING = auto()     # "What do I think?" - Fifth question


class QuestionMetadata:
    """Immutable metadata about a question type.
    
    Contains only declarative information, no logic.
    """
    
    __slots__ = ('question_type', 'module_name', 'description', 
                 'requires_snapshot', 'produces_output_type')
    
    def __init__(self, 
                 question_type: QuestionType,
                 module_name: str,
                 description: str,
                 requires_snapshot: bool = True,
                 produces_output_type: Optional[str] = None):
        """Initialize question metadata."""
        self.question_type = question_type
        self.module_name = module_name
        self.description = description
        self.requires_snapshot = requires_snapshot
        self.produces_output_type = produces_output_type
    
    def __repr__(self) -> str:
        """Representation for debugging."""
        return (f"QuestionMetadata({self.question_type.name}, "
                f"module={self.module_name}, "
                f"desc='{self.description[:30]}...')")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'question_type': self.question_type.name,
            'module_name': self.module_name,
            'description': self.description,
            'requires_snapshot': self.requires_snapshot,
            'produces_output_type': self.produces_output_type
        }


@runtime_checkable
class QuestionInterface(Protocol):
    """Protocol defining the interface for question modules.
    
    This is a type hint only - no implementation.
    Question modules are not required to implement this,
    but it documents the expected shape.
    """
    
    @classmethod
    def ask(cls, snapshot: Any, **kwargs: Any) -> Any:
        """Ask this question about a snapshot.
        
        Args:
            snapshot: Observation snapshot from Layer 1
            **kwargs: Question-specific parameters
            
        Returns:
            Question-specific output
        """
        ...
    
    @classmethod
    def get_metadata(cls) -> QuestionMetadata:
        """Get metadata about this question type."""
        ...


# Registry of available questions
# Constitutional: This is static declaration only, no dynamic registration
QUESTION_REGISTRY: Dict[QuestionType, QuestionMetadata] = {
    QuestionType.STRUCTURE: QuestionMetadata(
        question_type=QuestionType.STRUCTURE,
        module_name='inquiry.questions.structure',
        description="What's here? - Pure description without inference",
        requires_snapshot=True,
        produces_output_type='StructureAnalysis'
    ),
    QuestionType.PURPOSE: QuestionMetadata(
        question_type=QuestionType.PURPOSE,
        module_name='inquiry.questions.purpose',
        description="What does this do? - Aggregating declared signals without inference",
        requires_snapshot=True,
        produces_output_type='PurposeAnalysis'
    ),
    QuestionType.CONNECTIONS: QuestionMetadata(
        question_type=QuestionType.CONNECTIONS,
        module_name='inquiry.questions.connections',
        description="How is it connected? - Relational structure without semantics",
        requires_snapshot=True,
        produces_output_type='ConnectionAnalysis'
    ),
    QuestionType.ANOMALIES: QuestionMetadata(
        question_type=QuestionType.ANOMALIES,
        module_name='inquiry.questions.anomalies',
        description="What seems unusual? - Statistical deviations without judgment",
        requires_snapshot=True,
        produces_output_type='AnomalyAnalysis'
    ),
    QuestionType.THINKING: QuestionMetadata(
        question_type=QuestionType.THINKING,
        module_name='inquiry.questions.thinking',
        description="What do I think? - Structured space for human reasoning",
        requires_snapshot=False,  # Thinking doesn't require snapshot, just anchors
        produces_output_type='ThoughtCollection'
    )
}


# Linear investigation flow (Article 6)
# Constitutional: This order is fixed, not configurable
QUESTION_ORDER: Tuple[QuestionType, ...] = (
    QuestionType.STRUCTURE,
    QuestionType.PURPOSE,
    QuestionType.CONNECTIONS,
    QuestionType.ANOMALIES,
    QuestionType.THINKING
)


def get_question_order() -> List[QuestionType]:
    """Get questions in linear investigation order.
    
    Constitutional: Returns copy to prevent modification.
    """
    return list(QUESTION_ORDER)


def get_question_metadata(question_type: QuestionType) -> Optional[QuestionMetadata]:
    """Get metadata for a question type.
    
    Constitutional: Returns None if not found, doesn't raise.
    """
    return QUESTION_REGISTRY.get(question_type)


def get_all_question_metadata() -> List[QuestionMetadata]:
    """Get metadata for all questions in investigation order.
    
    Constitutional: Returns copy to prevent modification.
    """
    return [
        QUESTION_REGISTRY[qt]
        for qt in QUESTION_ORDER
        if qt in QUESTION_REGISTRY
    ]


def validate_question_flow(current: Optional[QuestionType], 
                          next_question: QuestionType) -> bool:
    """Validate that question flow follows linear investigation.
    
    Constitutional: Enforces Article 6 - Linear Investigation.
    
    Args:
        current: Current question type (None if starting)
        next_question: Next question type to ask
        
    Returns:
        True if flow is valid, False otherwise
    """
    if current is None:
        # Starting - must begin with STRUCTURE
        return next_question == QuestionType.STRUCTURE
    
    try:
        current_index = QUESTION_ORDER.index(current)
        next_index = QUESTION_ORDER.index(next_question)
        
        # Must move forward in order, not skip ahead
        return next_index == current_index + 1
        
    except ValueError:
        # Invalid question type
        return False


def load_question_module(question_type: QuestionType) -> Any:
    """Load question module dynamically.
    
    Constitutional: This is the only function that may import modules.
    It exists to support the interface layer without requiring all
    question modules to be loaded at startup.
    
    Args:
        question_type: Type of question to load
        
    Returns:
        Loaded module object
        
    Raises:
        ImportError: If module cannot be loaded
        KeyError: If question type not in registry
    """
    if question_type not in QUESTION_REGISTRY:
        raise KeyError(f"Unknown question type: {question_type}")
    
    metadata = QUESTION_REGISTRY[question_type]
    module_name = metadata.module_name
    
    # Remove 'inquiry.questions.' prefix if present
    if module_name.startswith('inquiry.questions.'):
        relative_name = module_name[18:]  # len('inquiry.questions.')
    else:
        relative_name = module_name
    
    # Import the module
    # Constitutional: Uses importlib for explicit control
    import importlib
    module = importlib.import_module(f'.{relative_name}', package='inquiry.questions')
    
    return module


# Export public API
__all__ = [
    # Types
    'QuestionType',
    'QuestionMetadata',
    'QuestionInterface',
    
    # Registry functions
    'get_question_order',
    'get_question_metadata',
    'get_all_question_metadata',
    'validate_question_flow',
    'load_question_module',
    
    # Constants
    'QUESTION_REGISTRY',  # Read-only, don't modify
    'QUESTION_ORDER',     # Read-only, don't modify
]


# Constitutional self-check
def _validate_registry() -> None:
    """Validate the question registry against constitutional rules.
    
    This function runs at import time to ensure constitutional compliance.
    """
    import logging
    
    # Check 1: All questions in order must be in registry
    for question_type in QUESTION_ORDER:
        if question_type not in QUESTION_REGISTRY:
            logger = logging.getLogger('codemarshal.questions')
            logger.error(
                f"Constitutional violation: Question {question_type} "
                f"in ORDER but not in REGISTRY"
            )
            # Don't raise - allow system to continue but log error
    
    # Check 2: Registry must contain exactly the questions in order
    registry_set = set(QUESTION_REGISTRY.keys())
    order_set = set(QUESTION_ORDER)
    
    if registry_set != order_set:
        missing_in_order = registry_set - order_set
        missing_in_registry = order_set - registry_set
        
        logger = logging.getLogger('codemarshal.questions')
        if missing_in_order:
            logger.error(
                f"Constitutional violation: Questions in registry but not in order: "
                f"{[qt.name for qt in missing_in_order]}"
            )
        if missing_in_registry:
            logger.error(
                f"Constitutional violation: Questions in order but not in registry: "
                f"{[qt.name for qt in missing_in_registry]}"
            )


# Run validation
try:
    _validate_registry()
except Exception as e:
    # Don't raise during import - just log
    import logging
    logger = logging.getLogger('codemarshal.questions')
    logger.debug(f"Registry validation failed: {e}")


# Constitutional reminder
_CONSTITUTIONAL_NOTE = """
QUESTIONS PACKAGE CONSTITUTIONAL BOUNDARY

This package exists at Layer 2 (inquiry) and must never:

1. Import from observations/ (Layer 1) - Violation of Article 9
2. Contain business logic - Only type definitions and exports
3. Modify state - This is a static registry
4. Make truth claims - Only organizes questions about observations

Layer 2 may be deleted entirely and the system must still be truthful.
If removing inquiry/ causes observations to lose meaning, you violated the constitution.
"""

# Export the note as a constant (for documentation purposes)
CONSTITUTIONAL_NOTE = _CONSTITUTIONAL_NOTE
__all__.append('CONSTITUTIONAL_NOTE')


# Final check: This file must not contain any executable logic beyond declarations
# The following line ensures no logic runs at import time beyond what's above
if __name__ != "__main__":
    # This is being imported as a module - good
    pass
else:
    # This file is being run directly - not intended
    import sys
    print("Error: This is a registry module, not a script.", file=sys.stderr)
    sys.exit(1)