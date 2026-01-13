"""
organization.py - Tags and search for notebook organization.

Organizes notes using human-applied metadata like tags.
Provides search capabilities without inference or auto-classification.
"""

import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

from .entries import NoteEntry


class TagManager:
    """
    Manages tags and search functionality for notebook entries.
    
    Rules:
    - Cannot auto-classify or create patterns from notes
    - Tags are advisory only; system logic must ignore them
    - No inference allowed - only exact matching
    """
    
    def __init__(self) -> None:
        """Initialize empty tag manager with no tags or indices."""
        # tag -> set of note IDs
        self._tag_to_notes: Dict[str, Set[UUID]] = defaultdict(set)
        
        # note ID -> set of tags
        self._note_to_tags: Dict[UUID, Set[str]] = defaultdict(set)
        
        # Index for keyword search (note ID -> content)
        self._content_index: Dict[UUID, str] = {}
        
        # Index for anchor search (anchor ID -> set of note IDs)
        self._anchor_index: Dict[str, Set[UUID]] = defaultdict(set)
    
    def add_tag(self, note: NoteEntry, tag: str) -> None:
        """
        Add a tag to a note.
        
        Args:
            note: The note to tag
            tag: Tag to add (must be non-empty)
            
        Raises:
            TypeError: If note is not a NoteEntry
            ValueError: If tag is empty or contains invalid characters
            RuntimeError: If note not in index (must be indexed first)
        """
        if not isinstance(note, NoteEntry):
            raise TypeError(f"Expected NoteEntry, got {type(note).__name__}")
        
        if not tag or not isinstance(tag, str):
            raise ValueError("Tag must be non-empty string")
        
        # Validate tag format: letters, numbers, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
            raise ValueError(f"Tag '{tag}' contains invalid characters. Use letters, numbers, hyphens, underscores")
        
        if note.id not in self._content_index:
            raise RuntimeError(f"Note {note.id} must be indexed before adding tags")
        
        # Add to both indices
        self._tag_to_notes[tag].add(note.id)
        self._note_to_tags[note.id].add(tag)
    
    def remove_tag(self, note: NoteEntry, tag: str) -> None:
        """
        Remove a tag from a note.
        
        Args:
            note: The note to untag
            tag: Tag to remove
            
        Raises:
            ValueError: If note doesn't have this tag
        """
        if note.id not in self._note_to_tags:
            raise ValueError(f"Note {note.id} not in tag manager")
        
        if tag not in self._note_to_tags[note.id]:
            raise ValueError(f"Note {note.id} doesn't have tag '{tag}'")
        
        # Remove from both indices
        self._note_to_tags[note.id].remove(tag)
        self._tag_to_notes[tag].remove(note.id)
        
        # Clean up empty sets
        if not self._note_to_tags[note.id]:
            del self._note_to_tags[note.id]
        
        if not self._tag_to_notes[tag]:
            del self._tag_to_notes[tag]
    
    def get_tags_for_note(self, note: NoteEntry) -> List[str]:
        """
        Get all tags for a note.
        
        Args:
            note: The note to query
            
        Returns:
            List of tags sorted alphabetically
        """
        if note.id not in self._note_to_tags:
            return []
        return sorted(self._note_to_tags[note.id])
    
    def get_notes_by_tag(self, tag: str) -> List[NoteEntry]:
        """
        Get all notes with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of notes with this tag
            
        Note:
            Returns empty list if tag doesn't exist
        """
        if tag not in self._tag_to_notes:
            return []
        
        # Note: We cannot return NoteEntry objects directly because we only store IDs
        # In practice, this would be used with a NoteStore that can look up notes by ID
        # For now, return empty list - actual implementation would resolve IDs to notes
        return []
    
    def index_note(self, note: NoteEntry) -> None:
        """
        Index a note for search capabilities.
        
        Args:
            note: The note to index
            
        Raises:
            TypeError: If note is not a NoteEntry
        """
        if not isinstance(note, NoteEntry):
            raise TypeError(f"Expected NoteEntry, got {type(note).__name__}")
        
        # Index content
        self._content_index[note.id] = note.content
        
        # Index anchors
        for anchor in note.anchors:
            anchor_id = getattr(anchor, 'id', None) or str(id(anchor))
            self._anchor_index[anchor_id].add(note.id)
    
    def remove_from_index(self, note_id: UUID) -> None:
        """
        Remove a note from all indices.
        
        Args:
            note_id: ID of note to remove
        """
        # Remove from content index
        if note_id in self._content_index:
            del self._content_index[note_id]
        
        # Remove from anchor index
        for anchor_id in list(self._anchor_index.keys()):
            if note_id in self._anchor_index[anchor_id]:
                self._anchor_index[anchor_id].remove(note_id)
                if not self._anchor_index[anchor_id]:
                    del self._anchor_index[anchor_id]
        
        # Remove from tag indices
        if note_id in self._note_to_tags:
            tags = list(self._note_to_tags[note_id])
            for tag in tags:
                self._tag_to_notes[tag].remove(note_id)
                if not self._tag_to_notes[tag]:
                    del self._tag_to_notes[tag]
            del self._note_to_tags[note_id]
    
    def search_by_keyword(
        self,
        keyword: str,
        notes: Optional[List[NoteEntry]] = None
    ) -> List[NoteEntry]:
        """
        Search for notes containing a keyword.
        
        Args:
            keyword: String to search for (case-sensitive)
            notes: Optional list of notes to search within
            
        Returns:
            List of notes containing the keyword
            
        Note:
            Exact substring match only - no stemming, no fuzzy matching
            Case-sensitive by default to avoid inference
        """
        if not keyword:
            return []
        
        results: List[NoteEntry] = []
        
        if notes is None:
            # Search all indexed notes
            # Note: In practice we need a NoteStore to resolve IDs
            # For now, return empty list
            return []
        
        # Search within provided notes
        for note in notes:
            if keyword in note.content:
                results.append(note)
        
        return results
    
    def search_by_anchor(
        self,
        anchor_id: str,
        notes: Optional[List[NoteEntry]] = None
    ) -> List[NoteEntry]:
        """
        Search for notes referencing a specific anchor.
        
        Args:
            anchor_id: Anchor identifier to search for
            notes: Optional list of notes to search within
            
        Returns:
            List of notes referencing this anchor
        """
        results: List[NoteEntry] = []
        
        if notes is None:
            # Use index if available
            if anchor_id in self._anchor_index:
                # Need NoteStore to resolve IDs
                return []
            return []
        
        # Search within provided notes
        for note in notes:
            # Check if any anchor matches
            for anchor in note.anchors:
                current_anchor_id = getattr(anchor, 'id', None) or str(id(anchor))
                if current_anchor_id == anchor_id:
                    results.append(note)
                    break
        
        return results
    
    def get_all_tags(self) -> List[str]:
        """
        Get all tags in use.
        
        Returns:
            List of tags sorted alphabetically
        """
        return sorted(self._tag_to_notes.keys())
    
    def get_tag_stats(self) -> Dict[str, int]:
        """
        Get statistics for tags (number of notes per tag).
        
        Returns:
            Dictionary mapping tag to count of notes
        
        Note:
            For display purposes only - no analysis
        """
        return {tag: len(notes) for tag, notes in self._tag_to_notes.items()}
    
    def clear(self) -> None:
        """Clear all indices (for testing and session reset)."""
        self._tag_to_notes.clear()
        self._note_to_tags.clear()
        self._content_index.clear()
        self._anchor_index.clear()
    
    def get_notes_without_tags(self, notes: List[NoteEntry]) -> List[NoteEntry]:
        """
        Get notes that have no tags.
        
        Args:
            notes: List of notes to check
            
        Returns:
            Notes without any tags
        """
        return [note for note in notes if note.id not in self._note_to_tags]
    
    def __contains__(self, tag: str) -> bool:
        """Check if a tag exists."""
        return tag in self._tag_to_notes
    
    def __len__(self) -> int:
        """Number of tags in manager."""
        return len(self._tag_to_notes)