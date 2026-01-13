from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass, field

from .entries import NoteEntry, NotebookManager
from observations.record.anchors import ObservationAnchor, Anchor

# Type aliases
Note = NoteEntry
NoteCollection = NotebookManager
NoteAnchor = ObservationAnchor

class Thought(NoteEntry):
    """A thought recorded in the investigation."""
    
    def __init__(
        self,
        content: str,
        anchors: List[ObservationAnchor],
        context_path: List[str],
        id: Optional[str] = None,
        note_id: Optional[UUID] = None,
        author_id: str = "system",
        session_id: str = "session",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        # NoteEntry expects UUID for note_id, but we might have string from usage.
        # We pass it through.
        real_id = note_id
        if real_id is None and id is not None:
            real_id = id
            
        super().__init__(
            content=content,
            anchors=anchors,
            author_id=author_id,
            session_id=session_id,
            note_id=real_id,
            created_at=created_at,
            updated_at=updated_at
        )
        self.context_path = context_path
        self.metadata = metadata or {}
        
    @property
    def author(self) -> Optional[str]:
        return self.author_id

class ReasoningStep(Thought):
    """An explicit step in a reasoning chain."""
    pass

class Assumption(Thought):
    """An assumption made during investigation."""
    pass

class OpenQuestion(Thought):
    """An open question to be answered."""
    pass

class BlindSpot(Thought):
    """A known blind spot or missing information."""
    pass
