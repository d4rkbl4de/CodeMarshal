"""
timeline.py - Chronological reasoning for notebook entries.

Maintains immutable historical record of note edits for audit and reasoning.
Provides chronological views of notes without analysis or reordering.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from .entries import NoteEntry


class Timeline:
    """
    Records the temporal order of notes for audit and reasoning.
    
    Rules:
    - Cannot reorder or filter notes for analysis purposes
    - Cannot collapse events into higher-level assumptions
    - Must maintain immutable historical record
    """
    
    def __init__(self) -> None:
        """Initialize empty timeline."""
        self._notes_by_time: List[NoteEntry] = []
        self._edit_history: List[Tuple[datetime, str, UUID, Optional[str]]] = []  # (timestamp, action, note_id, old_content)
    
    def add_note(self, note: NoteEntry) -> None:
        """
        Record a new note in the timeline.
        
        Args:
            note: The note to record
            
        Raises:
            ValueError: If note already exists in timeline
        """
        # Check for duplicates based on id
        existing_ids = {n.id for n in self._notes_by_time}
        if note.id in existing_ids:
            raise ValueError(f"Note with id {note.id} already exists in timeline")
        
        self._notes_by_time.append(note)
        self._edit_history.append((
            note.created_at,
            "created",
            note.id,
            None  # No old content for creation
        ))
    
    def record_edit(self, note_id: UUID, old_content: str, edit_time: datetime) -> None:
        """
        Record an edit to an existing note.
        
        Args:
            note_id: ID of the edited note
            old_content: Previous content before edit
            edit_time: When the edit occurred
            
        Raises:
            ValueError: If note_id not found in timeline
        """
        # Verify note exists
        note_exists = any(n.id == note_id for n in self._notes_by_time)
        if not note_exists:
            raise ValueError(f"Note with id {note_id} not found in timeline")
        
        self._edit_history.append((
            edit_time,
            "updated",
            note_id,
            old_content
        ))
    
    def get_notes_by_time(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> List[NoteEntry]:
        """
        Get notes within a time range, optionally filtered by session.
        
        Args:
            start_time: Earliest creation time (inclusive)
            end_time: Latest creation time (inclusive)
            session_id: Optional session filter
            
        Returns:
            List of notes sorted by creation time (ascending)
            
        Note:
            Returns all notes if no time constraints provided
            Never reorders or filters for analysis - only basic time/session filtering
        """
        filtered_notes = self._notes_by_time.copy()  # Shallow copy for safety
        
        # Apply session filter if specified
        if session_id is not None:
            filtered_notes = [n for n in filtered_notes if n.session_id == session_id]
        
        # Apply time filters
        if start_time is not None:
            filtered_notes = [n for n in filtered_notes if n.created_at >= start_time]
        
        if end_time is not None:
            filtered_notes = [n for n in filtered_notes if n.created_at <= end_time]
        
        # Return in chronological order (they're already in insertion order)
        return sorted(filtered_notes, key=lambda n: n.created_at)
    
    def replay_session(self, session_id: str) -> List[Tuple[datetime, str, NoteEntry, Optional[str]]]:
        """
        Replay all events for a session in chronological order.
        
        Args:
            session_id: Session to replay
            
        Returns:
            List of (timestamp, action, note, old_content) tuples
            old_content is None for creation events, contains previous content for edits
        """
        # Get all notes for this session
        session_notes = {n.id: n for n in self._notes_by_time if n.session_id == session_id}
        
        # Get all events for these notes, sorted chronologically
        session_events: List[Tuple[datetime, str, NoteEntry, Optional[str]]] = []
        for timestamp, action, note_id, old_content in self._edit_history:
            if note_id in session_notes:
                session_events.append((
                    timestamp,
                    action,
                    session_notes[note_id],
                    old_content
                ))
        
        return sorted(session_events, key=lambda x: x[0])  # Sort by timestamp
    
    def get_note_history(self, note_id: UUID) -> List[Tuple[datetime, str, Optional[str]]]:
        """
        Get complete edit history for a specific note.
        
        Args:
            note_id: Note to get history for
            
        Returns:
            List of (timestamp, action, old_content) for the note
            Sorted chronologically
        """
        note_history: List[Tuple[datetime, str, Optional[str]]] = []
        for timestamp, action, event_note_id, old_content in self._edit_history:
            if event_note_id == note_id:
                note_history.append((timestamp, action, old_content))
        
        return sorted(note_history, key=lambda x: x[0])
    
    def get_recent_notes(self, count: int = 10) -> List[NoteEntry]:
        """
        Get most recently created notes.
        
        Args:
            count: Maximum number of notes to return
            
        Returns:
            Most recent notes by creation time
            
        Note:
            This is for UI display only, not analysis
        """
        return sorted(self._notes_by_time, key=lambda n: n.created_at, reverse=True)[:count]
    
    def clear(self) -> None:
        """Clear all timeline data (for testing and session reset)."""
        self._notes_by_time.clear()
        self._edit_history.clear()
    
    def __len__(self) -> int:
        """Number of notes in timeline."""
        return len(self._notes_by_time)
    
    def __contains__(self, note_id: UUID) -> bool:
        """Check if a note exists in timeline."""
        return any(n.id == note_id for n in self._notes_by_time)