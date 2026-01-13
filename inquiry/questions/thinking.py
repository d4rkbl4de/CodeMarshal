"""
THINKING: HUMAN REASONING SPACE

This module provides structured space for human reasoning.
It binds thoughts to observation anchors and pattern outputs.
The system does not think for you; it preserves how you think.

CONSTITUTIONAL RULES:
1. Never analyze code
2. Never generate insights
3. Never summarize patterns
4. All thoughts must be anchored to specific observations
5. All thoughts must be traceable to their origin

Tier 1 Violation: If this module produces any code analysis, 
the system halts immediately.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, ClassVar, TypeVar, Generic
from dataclasses import dataclass, field, asdict
import json

# Type variables for generic anchoring
T = TypeVar('T', bound='ObservationAnchor')


@dataclass(frozen=True)
class ObservationAnchor:
    """Immutable reference to a specific observation.
    
    Anchors ensure thoughts are tethered to observable reality.
    An anchor without a valid reference is a constitutional violation.
    """
    observation_id: str
    source_path: str
    observation_type: str
    snapshot_version: str
    hash_digest: str  # Ensures thought points to specific observation state
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObservationAnchor':
        """Create anchor from dictionary representation."""
        return cls(
            observation_id=data['observation_id'],
            source_path=data['source_path'],
            observation_type=data['observation_type'],
            snapshot_version=data['snapshot_version'],
            hash_digest=data['hash_digest']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def validate(self) -> bool:
        """Validate anchor points to a real observation.
        
        This is a placeholder - in production, this would
        verify the observation exists in the current snapshot.
        """
        # Basic validation
        required_fields = [
            self.observation_id,
            self.source_path, 
            self.observation_type,
            self.snapshot_version,
            self.hash_digest
        ]
        return all(field and isinstance(field, str) for field in required_fields)


@dataclass
class Thought(Generic[T]):
    """A single human thought anchored to reality.
    
    Thoughts are mutable by humans but immutable once recorded.
    Every thought must be anchored to at least one observation.
    """
    
    # Required fields (constitutional)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    anchor: T  # Generic anchor type
    content: str
    
    # Optional metadata
    tags: set[str] = field(default_factory=set)
    connections: set[str] = field(default_factory=set)  # IDs of related thoughts
    confidence: Optional[float] = field(default=None)  # Human's confidence, not system's
    
    # System tracking
    modified_at: Optional[datetime] = field(default=None)
    version: int = field(default=1)
    
    # Constitutional guardrails
    _SYSTEM_GENERATED: ClassVar[bool] = False  # Never True for this class
    
    def __post_init__(self) -> None:
        """Validate thought against constitutional rules."""
        self._validate_anchor()
        self._validate_content()
        
        # Ensure tags are lowercase for consistency
        self.tags = {tag.lower().strip() for tag in self.tags if tag}
        
        # Remove self-referential connections
        self.connections.discard(self.id)
    
    def _validate_anchor(self) -> None:
        """Ensure thought is properly anchored.
        
        Tier 1 Violation: Unanchored thoughts are prohibited.
        """
        if not self.anchor:
            raise ConstitutionalViolation(
                "Thought must be anchored to an observation. "
                "Floating thoughts are prohibited by Article 10."
            )
        
        if not isinstance(self.anchor, ObservationAnchor):
            raise ConstitutionalViolation(
                f"Anchor must be ObservationAnchor, got {type(self.anchor)}"
            )
        
        if not self.anchor.validate():
            raise ConstitutionalViolation(
                f"Invalid anchor: {self.anchor}. "
                "Thoughts must point to real observations."
            )
    
    def _validate_content(self) -> None:
        """Validate thought content.
        
        Constitutional Rule: No code analysis in thoughts.
        """
        content_lower = self.content.lower()
        
        # Check for code analysis patterns
        analysis_patterns = [
            'this function should',
            'the code needs to',
            'refactor this to',
            'this is poorly',
            'this could be improved',
            'bug in line',
            'error handling is',
            'performance issue',
            'memory leak',
            'security vulnerability'
        ]
        
        for pattern in analysis_patterns:
            if pattern in content_lower:
                raise ConstitutionalViolation(
                    f"Thought contains code analysis: '{pattern}'. "
                    "Thoughts must be about understanding, not fixing. "
                    "Violates Article 2: Human Primacy."
                )
        
        # Check for system-generated language
        system_patterns = [
            'based on the pattern',
            'the system detects',
            'analysis shows',
            'statistically significant',
            'algorithmically determined'
        ]
        
        for pattern in system_patterns:
            if pattern in content_lower:
                raise ConstitutionalViolation(
                    f"Thought mimics system output: '{pattern}'. "
                    "Thoughts must be explicitly human. "
                    "Violates Article 2: Human Primacy."
                )
    
    def update(self, new_content: str, new_tags: Optional[set[str]] = None) -> 'Thought[T]':
        """Create updated version of thought.
        
        Thoughts are immutable in storage, but humans can create
        new versions. Original thought remains unchanged.
        """
        updated = Thought(
            id=self.id,  # Same ID for version tracking
            created_at=self.created_at,
            anchor=self.anchor,
            content=new_content,
            tags=new_tags if new_tags is not None else self.tags.copy(),
            connections=self.connections.copy(),
            confidence=self.confidence,
            modified_at=datetime.now(timezone.utc),
            version=self.version + 1
        )
        return updated
    
    def connect_to(self, other_thought_id: str) -> None:
        """Connect this thought to another thought."""
        if other_thought_id != self.id:
            self.connections.add(other_thought_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thought to serializable dictionary."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'anchor': self.anchor.to_dict(),
            'content': self.content,
            'tags': list(self.tags),
            'connections': list(self.connections),
            'confidence': self.confidence,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'version': self.version,
            '_type': 'human_thought'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Thought[T]':
        """Create thought from dictionary representation."""
        # Handle datetime strings
        created_at = datetime.fromisoformat(data['created_at'])
        modified_at = (
            datetime.fromisoformat(data['modified_at']) 
            if data.get('modified_at') 
            else None
        )
        
        # Create anchor
        anchor = ObservationAnchor.from_dict(data['anchor'])
        
        return cls(
            id=data['id'],
            created_at=created_at,
            anchor=anchor,
            content=data['content'],
            tags=set(data.get('tags', [])),
            connections=set(data.get('connections', [])),
            confidence=data.get('confidence'),
            modified_at=modified_at,
            version=data.get('version', 1)
        )
    
    def __str__(self) -> str:
        """Human-readable representation."""
        anchor_info = f"{self.anchor.observation_type} at {self.anchor.source_path}"
        timestamp = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        
        return (
            f"Thought [{self.id[:8]}...] ({timestamp})\n"
            f"Anchor: {anchor_info}\n"
            f"Content: {self.content}\n"
            f"Tags: {', '.join(sorted(self.tags)) if self.tags else '(none)'}\n"
            f"Connections: {len(self.connections)} related thoughts"
        )


class ThoughtCollection:
    """Collection of related thoughts with integrity guarantees."""
    
    def __init__(self, title: str, description: Optional[str] = None):
        self.id: str = str(uuid.uuid4())
        self.title: str = title
        self.description: Optional[str] = description
        self.created_at: datetime = datetime.now(timezone.utc)
        self.thoughts: Dict[str, Thought] = {}
        self.thought_order: list[str] = []  # Preserve chronological order
        
        # Indexes for fast lookup
        self._anchor_index: Dict[str, list[str]] = {}  # anchor_id -> thought_ids
        self._tag_index: Dict[str, set[str]] = {}  # tag -> thought_ids
    
    def add_thought(self, thought: Thought) -> None:
        """Add thought to collection with integrity checks."""
        # Constitutional check: Ensure no duplicate IDs
        if thought.id in self.thoughts:
            raise ConstitutionalViolation(
                f"Thought {thought.id} already exists in collection. "
                "Each thought must have unique identity."
            )
        
        # Constitutional check: All thoughts must be anchored
        if not thought.anchor:
            raise ConstitutionalViolation(
                f"Thought {thought.id} has no anchor. "
                "All thoughts must be anchored to observations (Article 10)."
            )
        
        # Store thought
        self.thoughts[thought.id] = thought
        self.thought_order.append(thought.id)
        
        # Update indexes
        anchor_key = f"{thought.anchor.source_path}:{thought.anchor.observation_id}"
        self._anchor_index.setdefault(anchor_key, []).append(thought.id)
        
        for tag in thought.tags:
            self._tag_index.setdefault(tag, set()).add(thought.id)
    
    def get_thoughts_by_anchor(self, anchor: ObservationAnchor) -> list[Thought]:
        """Get all thoughts anchored to a specific observation."""
        anchor_key = f"{anchor.source_path}:{anchor.observation_id}"
        thought_ids = self._anchor_index.get(anchor_key, [])
        return [self.thoughts[thought_id] for thought_id in thought_ids]
    
    def get_thoughts_by_tag(self, tag: str) -> list[Thought]:
        """Get all thoughts with a specific tag."""
        thought_ids = self._tag_index.get(tag.lower(), set())
        return [self.thoughts[thought_id] for thought_id in thought_ids]
    
    def get_chronological(self) -> list[Thought]:
        """Get all thoughts in chronological order."""
        return [self.thoughts[thought_id] for thought_id in self.thought_order]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert collection to serializable dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'thoughts': [thought.to_dict() for thought in self.get_chronological()],
            'thought_count': len(self.thoughts),
            '_type': 'thought_collection'
        }
    
    def save(self, filepath: str) -> None:
        """Save collection to file."""
        data = self.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filepath: str) -> 'ThoughtCollection':
        """Load collection from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        collection = cls(
            title=data['title'],
            description=data.get('description')
        )
        collection.id = data['id']
        collection.created_at = datetime.fromisoformat(data['created_at'])
        
        for thought_data in data['thoughts']:
            thought = Thought.from_dict(thought_data)
            collection.thoughts[thought.id] = thought
            collection.thought_order.append(thought.id)
            
            # Rebuild indexes
            anchor_key = f"{thought.anchor.source_path}:{thought.anchor.observation_id}"
            collection._anchor_index.setdefault(anchor_key, []).append(thought.id)
            
            for tag in thought.tags:
                collection._tag_index.setdefault(tag, set()).add(thought.id)
        
        return collection


class ConstitutionalViolation(Exception):
    """Exception raised when constitutional rules are violated.
    
    Tier 1 violations must halt the system immediately.
    """
    
    def __init__(self, message: str, tier: int = 1):
        super().__init__(message)
        self.tier = tier
        self.message = message
        
        # Log the violation for audit trail
        self._log_violation()
    
    def _log_violation(self) -> None:
        """Log constitutional violation for audit purposes."""
        import logging
        logger = logging.getLogger('codemarshal.constitution')
        logger.error(
            f"Constitutional Violation (Tier {self.tier}): {self.message}"
        )


# Example usage function (for testing only)
def create_example_thought() -> Thought[ObservationAnchor]:
    """Create an example thought for demonstration.
    
    This function is for testing only and should not be used in production.
    """
    # Create a mock anchor
    anchor = ObservationAnchor(
        observation_id="obs_12345",
        source_path="/path/to/module.py",
        observation_type="function_definition",
        snapshot_version="2024.1.0",
        hash_digest="sha256:abc123..."
    )
    
    # Create a constitutional thought
    thought = Thought(
        anchor=anchor,
        content="This function appears to handle user authentication. "
                "I notice it checks multiple conditions before proceeding. "
                "Uncertain about the session timeout logic.",
        tags={"authentication", "security", "uncertain"},
        confidence=0.7  # Human's confidence in their understanding
    )
    
    return thought


# Export public API
__all__ = [
    'ObservationAnchor',
    'Thought',
    'ThoughtCollection',
    'ConstitutionalViolation'
]