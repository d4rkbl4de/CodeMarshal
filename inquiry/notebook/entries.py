"""
entries.py - Notes anchored to observations.

Represents individual thoughts anchored to immutable evidence.
Notes are mutable, observations are immutable.
Every note references valid ObservationAnchor instances.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from observations.record.anchors import ObservationAnchor


class NoteEntry:
    """
    Individual thought anchored to immutable evidence.
    
    Rules:
    - Cannot modify observations
    - Cannot infer patterns
    - Cannot auto-tag
    - Must reference valid ObservationAnchor instances
    """
    
    def __init__(
        self,
        content: str,
        anchors: List[ObservationAnchor],
        author_id: str,
        session_id: str,
        note_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> None:
        """
        Initialize a new note entry.
        
        Args:
            content: Note content (human thinking)
            anchors: List of ObservationAnchor instances this note references
            author_id: Identifier of the human author
            session_id: Investigation session identifier
            note_id: Optional UUID (auto-generated if None)
            created_at: Optional creation timestamp (auto-set if None)
            updated_at: Optional update timestamp (auto-set if None)
            
        Raises:
            TypeError: If anchors contains non-ObservationAnchor objects
            ValueError: If content is empty or anchors list is empty
        """
        if not content or not isinstance(content, str):
            raise ValueError("Content must be non-empty string")
        
        if not anchors:
            raise ValueError("Must have at least one anchor")
        
        for anchor in anchors:
            if not isinstance(anchor, ObservationAnchor):
                raise TypeError(f"Expected ObservationAnchor, got {type(anchor).__name__}")
        
        self._id = note_id if note_id is not None else uuid4()
        self._content = content
        self._anchors = anchors.copy()  # Copy to prevent external mutation
        self._author_id = author_id
        self._session_id = session_id
        
        now = datetime.now(timezone.utc)
        self._created_at = created_at if created_at is not None else now
        self._updated_at = updated_at if updated_at is not None else now
        
        # Validate created_at <= updated_at
        if self._created_at > self._updated_at:
            raise ValueError("created_at cannot be after updated_at")
    
    @property
    def id(self) -> UUID:
        """Get note ID (immutable)."""
        return self._id
    
    @property
    def content(self) -> str:
        """Get note content."""
        return self._content
    
    @property
    def anchors(self) -> List[ObservationAnchor]:
        """Get copy of anchors list (prevent mutation)."""
        return self._anchors.copy()
    
    @property
    def author_id(self) -> str:
        """Get author ID (immutable)."""
        return self._author_id
    
    @property
    def session_id(self) -> str:
        """Get session ID (immutable)."""
        return self._session_id
    
    @property
    def created_at(self) -> datetime:
        """Get creation timestamp (immutable)."""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get last update timestamp."""
        return self._updated_at
    
    def update_content(
        self,
        new_content: str,
        new_anchors: Optional[List[ObservationAnchor]] = None,
        update_time: Optional[datetime] = None
    ) -> str:
        """
        Update note content and optionally anchors.
        
        Args:
            new_content: Updated content (must be non-empty)
            new_anchors: Optional new list of anchors (preserves existing if None)
            update_time: Optional update timestamp (uses current UTC if None)
            
        Returns:
            Previous content (for history tracking)
            
        Raises:
            ValueError: If new_content is empty
            TypeError: If new_anchors contains non-ObservationAnchor objects
        """
        if not new_content or not isinstance(new_content, str):
            raise ValueError("Content must be non-empty string")
        
        old_content = self._content
        self._content = new_content
        
        if new_anchors is not None:
            if not new_anchors:
                raise ValueError("Must have at least one anchor")
            
            for anchor in new_anchors:
                if not isinstance(anchor, ObservationAnchor):
                    raise TypeError(f"Expected ObservationAnchor, got {type(anchor).__name__}")
            
            self._anchors = new_anchors.copy()
        
        self._updated_at = update_time if update_time is not None else datetime.now(timezone.utc)
        
        # Validate update time is not before creation
        if self._updated_at < self._created_at:
            raise ValueError("updated_at cannot be before created_at")
        
        return old_content
    
    def add_anchor(self, anchor: ObservationAnchor) -> None:
        """
        Add a new anchor to the note.
        
        Args:
            anchor: ObservationAnchor to add
            
        Raises:
            TypeError: If anchor is not an ObservationAnchor
        """
        if not isinstance(anchor, ObservationAnchor):
            raise TypeError(f"Expected ObservationAnchor, got {type(anchor).__name__}")
        
        # Don't add duplicates
        if anchor not in self._anchors:
            self._anchors.append(anchor)
            self._updated_at = datetime.now(timezone.utc)
    
    def remove_anchor(self, anchor: ObservationAnchor) -> bool:
        """
        Remove an anchor from the note.
        
        Args:
            anchor: ObservationAnchor to remove
            
        Returns:
            True if anchor was removed, False if not found
            
        Raises:
            ValueError: If removal would leave note with no anchors
        """
        if anchor in self._anchors:
            # Check if this is the last anchor
            if len(self._anchors) <= 1:
                raise ValueError("Note must have at least one anchor")
            
            self._anchors.remove(anchor)
            self._updated_at = datetime.now(timezone.utc)
            return True
        
        return False
    
    def has_anchor(self, anchor: ObservationAnchor) -> bool:
        """Check if note has a specific anchor."""
        return anchor in self._anchors
    
    def __eq__(self, other: object) -> bool:
        """Compare notes by ID."""
        if not isinstance(other, NoteEntry):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash note by ID."""
        return hash(self._id)
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"NoteEntry(id={self._id}, author={self._author_id}, anchors={len(self._anchors)})"


class NotebookManager:
    """
    Manages a collection of NoteEntry objects.
    
    Provides CRUD operations with validation.
    Ensures notes reference valid anchors.
    """
    
    def __init__(self) -> None:
        """Initialize empty notebook."""
        self._notes: dict[UUID, NoteEntry] = {}
    
    def create_note(
        self,
        content: str,
        anchors: List[ObservationAnchor],
        author_id: str,
        session_id: str
    ) -> NoteEntry:
        """
        Create and store a new note.
        
        Args:
            content: Note content
            anchors: List of ObservationAnchor instances
            author_id: Author identifier
            session_id: Session identifier
            
        Returns:
            Created NoteEntry
            
        Raises:
            ValueError: If content empty or anchors empty
            TypeError: If anchors invalid
        """
        note = NoteEntry(
            content=content,
            anchors=anchors,
            author_id=author_id,
            session_id=session_id
        )
        
        if note.id in self._notes:
            # This should never happen with UUID, but guard anyway
            raise RuntimeError(f"Note with ID {note.id} already exists")
        
        self._notes[note.id] = note
        return note
    
    def get_note(self, note_id: UUID) -> Optional[NoteEntry]:
        """
        Get a note by ID.
        
        Args:
            note_id: Note UUID
            
        Returns:
            NoteEntry if found, None otherwise
        """
        return self._notes.get(note_id)
    
    def update_note(
        self,
        note_id: UUID,
        new_content: str,
        new_anchors: Optional[List[ObservationAnchor]] = None
    ) -> Optional[str]:
        """
        Update note content and optionally anchors.
        
        Args:
            note_id: Note UUID
            new_content: New content
            new_anchors: Optional new anchors list
            
        Returns:
            Old content if update successful, None if note not found
            
        Raises:
            ValueError: If new_content empty
            TypeError: If new_anchors invalid
        """
        note = self._notes.get(note_id)
        if note is None:
            return None
        
        old_content = note.update_content(new_content, new_anchors)
        return old_content
    
    def delete_note(self, note_id: UUID) -> bool:
        """
        Delete a note by ID.
        
        Args:
            note_id: Note UUID
            
        Returns:
            True if deleted, False if not found
        """
        if note_id in self._notes:
            del self._notes[note_id]
            return True
        return False
    
    def get_notes_by_author(self, author_id: str) -> List[NoteEntry]:
        """Get all notes by a specific author."""
        return [note for note in self._notes.values() if note.author_id == author_id]
    
    def get_notes_by_session(self, session_id: str) -> List[NoteEntry]:
        """Get all notes from a specific session."""
        return [note for note in self._notes.values() if note.session_id == session_id]
    
    def get_notes_by_anchor(self, anchor: ObservationAnchor) -> List[NoteEntry]:
        """Get all notes that reference a specific anchor."""
        return [note for note in self._notes.values() if note.has_anchor(anchor)]
    
    def get_all_notes(self) -> List[NoteEntry]:
        """Get all notes in chronological order."""
        return sorted(self._notes.values(), key=lambda n: n.created_at)
    
    def clear(self) -> None:
        """Remove all notes (for testing and session reset)."""
        self._notes.clear()
    
    def __contains__(self, note_id: UUID) -> bool:
        """Check if note exists."""
        return note_id in self._notes
    
    def __len__(self) -> int:
        """Number of notes."""
        return len(self._notes)
    
    def __iter__(self):
        """Iterate over notes in chronological order."""
        return iter(self.get_all_notes())