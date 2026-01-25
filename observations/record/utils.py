from pathlib import Path
from typing import Any

from observations.record.snapshot import (
    ObservationCategory,
    ObservationGroup,
    Snapshot,
    validate_snapshot_for_storage,
)


def create_snapshot(
    composite: Any, name: str | None = None, description: str = ""
) -> Snapshot:
    """
    Create a snapshot from a CompositeObservation.

    Args:
        composite: CompositeObservation objects
        name: Name for the snapshot
        description: Description

    Returns:
        Snapshot
    """
    # Mapping from eye name to category
    category_map = {
        "file_sight": ObservationCategory.STRUCTURE,
        "import_sight": ObservationCategory.CONTENT,
        "export_sight": ObservationCategory.CONTENT,
        "boundary_sight": ObservationCategory.BOUNDARY,
        "encoding_sight": ObservationCategory.ENCODING,
    }

    groups: list[ObservationGroup] = []

    # Group observations by eye
    observations_by_eye: dict[str, list[dict[str, Any]]] = {}

    # composite.observations is a tuple of ObservationResult
    for obs in composite.observations:
        # Check if successful
        if obs.confidence < 0.1 and not obs.raw_payload:
            continue

        # Get eye name from provenance if available
        eye_name = "unknown"
        if hasattr(obs, "provenance") and obs.provenance:
            eye_name = obs.provenance.observer_name

        # Convert raw_payload to dict if possible
        payload = obs.raw_payload
        if hasattr(payload, "to_dict"):
            payload_dict = payload.to_dict()
        elif hasattr(payload, "__dict__"):
            payload_dict = payload.__dict__
        else:
            payload_dict = {"value": payload}

        if eye_name not in observations_by_eye:
            observations_by_eye[eye_name] = []

        observations_by_eye[eye_name].append(payload_dict)

    # Create ObservationGroups
    for eye_name, obs_list in observations_by_eye.items():
        category = category_map.get(eye_name, ObservationCategory.CONTENT)

        group = ObservationGroup.from_eye_results(
            category=category, eye_name=eye_name, results=obs_list
        )
        groups.append(group)

    # Create snapshot
    # Calculate duration (mock or derive from composite timestamps)
    duration = 0.0
    if hasattr(composite, "timestamp"):
        # Just use 0 as we don't have start/end in composite usually
        pass

    return Snapshot.create(
        source_path=str(composite.target),
        observation_groups=groups,
        recording_duration=duration,
    )


def load_snapshot(path: str | Path) -> Snapshot:
    """Load a snapshot from a JSON file."""
    path = Path(path)
    return Snapshot.from_json(path.read_text(encoding="utf-8"))


def validate_snapshot(snapshot: Snapshot) -> tuple[bool, str | None]:
    """Validate a snapshot."""
    return validate_snapshot_for_storage(snapshot)
