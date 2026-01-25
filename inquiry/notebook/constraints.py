"""
constraints.py - Constitutional enforcement of one-way reference from note → evidence.

Validates note anchors point to existing observations.
Raises errors on any attempted mutation of snapshots, anchors, or pattern outputs.
Prevents accidental contamination of Layer 1 evidence by subjective human thought.
"""

from observations.record.integrity import check_integrity
from observations.record.snapshot import Snapshot

from .entries import NoteEntry


class ConstraintViolationError(Exception):
    """Raised when a constitutional constraint is violated."""

    pass


class EvidenceMutationError(ConstraintViolationError):
    """Raised when attempting to mutate evidence."""

    pass


class AnchorValidationError(ConstraintViolationError):
    """Raised when anchor validation fails."""

    pass


class ConstraintsValidator:
    """
    Enforces one-way reference from human thinking (notes) to evidence (observations).

    Production guarantees:
    - Prevents any accidental contamination of Layer 1 evidence by subjective human thought
    - Enforces separation of truth vs interpretation
    - Validates all references point to existing, immutable evidence
    """

    def __init__(self, known_snapshots: set[Snapshot] | None = None) -> None:
        """
        Initialize validator with known snapshots.

        Args:
            known_snapshots: Set of valid snapshots that can be referenced
        """
        self._known_snapshots: set[Snapshot] = known_snapshots or set()
        self._validated_anchors: set[str] = set()

    def register_snapshot(self, snapshot: Snapshot) -> None:
        """
        Register a snapshot as valid evidence that can be referenced.

        Args:
            snapshot: Snapshot to register

        Raises:
            TypeError: If not a Snapshot instance
        """
        if not isinstance(snapshot, Snapshot):
            raise TypeError(f"Expected Snapshot, got {type(snapshot).__name__}")

        self._known_snapshots.add(snapshot)

    def validate_note_anchors(self, note: NoteEntry) -> list[str]:
        """
        Validate all anchors in a note point to existing, immutable evidence.

        Args:
            note: NoteEntry to validate

        Returns:
            List of anchor IDs that were validated

        Raises:
            AnchorValidationError: If any anchor cannot be validated
            EvidenceMutationError: If any evidence appears modified
        """
        if not isinstance(note, NoteEntry):
            raise TypeError(f"Expected NoteEntry, got {type(note).__name__}")

        validated_anchor_ids: list[str] = []

        for anchor in note.anchors:
            # Get anchor ID for tracking
            anchor_id = self._get_anchor_id(anchor)

            # Check if we've already validated this anchor
            if anchor_id in self._validated_anchors:
                validated_anchor_ids.append(anchor_id)
                continue

            # Validate the anchor points to known evidence
            self._validate_anchor_reference(anchor)

            # Check evidence integrity
            self._validate_evidence_integrity(anchor)

            # Mark as validated
            self._validated_anchors.add(anchor_id)
            validated_anchor_ids.append(anchor_id)

        return validated_anchor_ids

    def _get_anchor_id(self, anchor) -> str:
        """
        Get a stable identifier for an anchor.

        Args:
            anchor: Anchor object

        Returns:
            String identifier

        Raises:
            AnchorValidationError: If anchor doesn't have a valid ID
        """
        anchor_id = getattr(anchor, "id", None)
        if anchor_id is None:
            anchor_id = getattr(anchor, "path", None)

        if anchor_id is None:
            raise AnchorValidationError(
                f"Anchor of type {type(anchor).__name__} has no identifiable attribute"
            )

        return str(anchor_id)

    def _validate_anchor_reference(self, anchor) -> None:
        """
        Validate an anchor references known evidence.

        Args:
            anchor: Anchor to validate

        Raises:
            AnchorValidationError: If anchor doesn't reference valid evidence
        """
        # Try to get the snapshot from the anchor
        snapshot = getattr(anchor, "snapshot", None)

        # If anchor has a snapshot attribute, validate it
        if snapshot is not None:
            if not isinstance(snapshot, Snapshot):
                raise AnchorValidationError(
                    f"Anchor references non-Snapshot object: {type(snapshot).__name__}"
                )

            if snapshot not in self._known_snapshots:
                raise AnchorValidationError(
                    f"Anchor references unknown snapshot: {snapshot}"
                )

            # Check that anchor is within snapshot bounds if applicable
            if hasattr(anchor, "line_number"):
                self._validate_anchor_position(anchor, snapshot)
        else:
            # Anchor must have some way to be validated
            # For now, we require all anchors to reference a snapshot
            raise AnchorValidationError(
                f"Anchor of type {type(anchor).__name__} doesn't reference a snapshot"
            )

    def _validate_anchor_position(self, anchor, snapshot: Snapshot) -> None:
        """
        Validate anchor position is within snapshot bounds.

        Args:
            anchor: Anchor with line_number attribute
            snapshot: Snapshot to check against

        Raises:
            AnchorValidationError: If anchor position is invalid
        """
        line_number = getattr(anchor, "line_number", None)
        if line_number is not None:
            # Check if snapshot has line count info
            if hasattr(snapshot, "line_count"):
                if line_number < 0 or line_number >= snapshot.line_count:
                    raise AnchorValidationError(
                        f"Anchor line {line_number} out of bounds "
                        f"(snapshot has {snapshot.line_count} lines)"
                    )

    def _validate_evidence_integrity(self, anchor) -> None:
        """
        Validate that referenced evidence has not been mutated.

        Args:
            anchor: Anchor to validate

        Raises:
            EvidenceMutationError: If evidence integrity check fails
        """
        snapshot = getattr(anchor, "snapshot", None)
        if snapshot is not None:
            try:
                # Use the imported integrity check function
                is_valid = check_integrity(snapshot)
                if not is_valid:
                    raise EvidenceMutationError(
                        f"Snapshot integrity check failed for anchor: {anchor}"
                    )
            except Exception as e:
                raise EvidenceMutationError(
                    f"Failed to validate snapshot integrity: {e}"
                ) from e

    def validate_note_creation(
        self, content: str, anchors: list, author_id: str, session_id: str
    ) -> None:
        """
        Validate all constraints for note creation.

        Args:
            content: Note content
            anchors: List of anchors
            author_id: Author identifier
            session_id: Session identifier

        Raises:
            ConstraintViolationError: If any constraint is violated
        """
        # Content must not be empty
        if not content or not isinstance(content, str):
            raise ConstraintViolationError("Note content must be non-empty string")

        # Must have at least one anchor
        if not anchors:
            raise ConstraintViolationError("Note must have at least one anchor")

        # Author and session must be provided
        if not author_id or not isinstance(author_id, str):
            raise ConstraintViolationError("Author ID must be non-empty string")

        if not session_id or not isinstance(session_id, str):
            raise ConstraintViolationError("Session ID must be non-empty string")

        # Validate each anchor
        for anchor in anchors:
            self._validate_anchor_reference(anchor)
            self._validate_evidence_integrity(anchor)

    def validate_note_update(
        self, old_note: NoteEntry, new_content: str, new_anchors: list | None = None
    ) -> None:
        """
        Validate constraints for note update.

        Args:
            old_note: Existing note being updated
            new_content: New content
            new_anchors: Optional new anchors (if provided)

        Raises:
            ConstraintViolationError: If any constraint is violated
        """
        if not isinstance(old_note, NoteEntry):
            raise TypeError(f"Expected NoteEntry, got {type(old_note).__name__}")

        # Content must not be empty
        if not new_content or not isinstance(new_content, str):
            raise ConstraintViolationError("Note content must be non-empty string")

        # If new anchors provided, validate them
        if new_anchors is not None:
            if not new_anchors:
                raise ConstraintViolationError("Note must have at least one anchor")

            for anchor in new_anchors:
                self._validate_anchor_reference(anchor)
                self._validate_evidence_integrity(anchor)

    def check_for_cross_contamination(self, note: NoteEntry) -> bool:
        """
        Check if a note shows signs of evidence contamination.

        Args:
            note: Note to check

        Returns:
            True if contamination detected, False otherwise

        Note:
            This is a safety check, not a validation. It looks for patterns
            that suggest human thinking is being mistaken for evidence.
        """
        contamination_patterns = [
            # Patterns where note might be trying to state facts
            r"evidence shows",
            r"the code proves",
            r"this demonstrates",
            r"it is clear that",
            r"the system must",
            # Absolute statements about code behavior
            r"always\s+",
            r"never\s+",
            r"must\s+",
            r"cannot\s+",
            r"will\s+",
            # Inference patterns
            r"therefore",
            r"thus",
            r"consequently",
            r"as a result",
        ]

        content_lower = note.content.lower()
        for pattern in contamination_patterns:
            if pattern in content_lower:
                return True

        return False

    def get_validation_report(self) -> dict:
        """
        Generate a report of validation state.

        Returns:
            Dictionary with validation statistics
        """
        return {
            "known_snapshots": len(self._known_snapshots),
            "validated_anchors": len(self._validated_anchors),
            "validation_status": "active",
        }

    def clear_validated_anchors(self) -> None:
        """Clear cache of validated anchors (for testing)."""
        self._validated_anchors.clear()

    def remove_snapshot(self, snapshot: Snapshot) -> bool:
        """
        Remove a snapshot from known snapshots.

        Args:
            snapshot: Snapshot to remove

        Returns:
            True if removed, False if not found
        """
        if snapshot in self._known_snapshots:
            self._known_snapshots.remove(snapshot)
            return True
        return False
