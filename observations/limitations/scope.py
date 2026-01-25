from pathlib import Path
from typing import NamedTuple

from .declared import Limitation, get_active_limitations


class ScopeValidationResult(NamedTuple):
    is_valid: bool
    reason: str


def validate_observation_scope(
    eye_name: str, target: str | Path
) -> ScopeValidationResult:
    """
    Validate if a target is within the scope of an eye.

    Args:
        eye_name: Name of the eye
        target: Target path

    Returns:
        ScopeValidationResult
    """
    path = Path(target)

    # Basic validation logic
    if not path.exists():
        return ScopeValidationResult(False, "Target does not exist")

    # Check against known limitations
    # This is a simplified check. Real implementation would evaluating specific conditions.
    limitations = get_limitations_for_eye(eye_name)

    for lim in limitations:
        if lim.id == "binary-files" and eye_name == "encoding_sight":
            # Encoding sight handles binary files (sort of), or maybe it doesn't?
            # Actually encoding sight is for text encoding.
            pass

    return ScopeValidationResult(True, "")


def get_limitations_for_eye(eye_name: str) -> list[Limitation]:
    """
    Get limitations relevant to a specific eye.

    Args:
        eye_name: Name of the eye

    Returns:
        List of Limitation objects
    """
    all_lims = get_active_limitations()
    # Return all limitations for now as most are global
    # Ideally filter by scope or category if we had that mapping
    return list(all_lims)
