"""
observations/record - IMMUTABLE RECORDING

Single responsibility: Convert raw observational outputs into stable, 
tamper-evident, referencable snapshots of reality.

This layer:
- Does not interpret
- Does not judge  
- Does not decide
- Commits to what was observed

Core production rules (non-negotiable):
1. Immutability is enforced, not promised
2. Every snapshot is addressable
3. Every snapshot is verifiable
4. No snapshot is overwritten
5. Corruption must be detectable, not merely avoided

If any of these are violated, this is not a record system — 
it's a cache pretending to be serious.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type-only imports to satisfy mypy without runtime circular dependencies
    from .snapshot import Snapshot, SnapshotMetadata, SnapshotPayload, ObservationGroup, ObservationCategory
    from .anchors import Anchor, AnchorSet, AnchorComparison, ContentFingerprintMethod, AnchorType
    from .version import SnapshotVersion, VersionFormat, SemanticVersion, TimestampVersion
    from .integrity import IntegrityRoot, HashAlgorithm, CorruptionReport, CorruptionType

# ============================================================================
# PUBLIC API
# ============================================================================

# Re-export from snapshot module
from .snapshot import (
    Snapshot,
    SnapshotMetadata,
    SnapshotPayload,
    ObservationGroup,
    ObservationCategory,
    create_empty_snapshot,
    validate_snapshot_for_storage,
    get_canonical_hash_input,
    SnapshotBuilder,
)

# Import from utils
from .utils import (
    create_snapshot,
    load_snapshot,
    validate_snapshot,
)

# Re-export from anchors module
from .anchors import (
    Anchor,
    AnchorSet,
    AnchorComparison,
    AnchorType,
    ContentFingerprintMethod,
    create_anchor,
    compare_anchor_sets,
    verify_anchor_consistency,
    compute_anchors_for_snapshot,
)

# Re-export from version module
from .version import (
    SnapshotVersion,
    VersionFormat,
    SemanticVersion,
    TimestampVersion,
    get_current_version,
    validate_snapshot_version,
    check_compatibility,
    upgrade_snapshot,
    serialize_version,
    deserialize_version,
)

# Re-export from integrity module
from .integrity import (
    IntegrityRoot,
    HashAlgorithm,
    CorruptionReport,
    CorruptionType,
    compute_integrity_root,
    verify_integrity,
    audit_snapshot,
    create_integrity_for_testing,
    get_default_algorithm,
    compare_hashes,
)

# ============================================================================
# PACKAGE METADATA
# ============================================================================

__version__ = "1.0.0"
__author__ = "CodeMarshal Team"
__email__ = "code@codemarshal.dev"

__all__ = [
    # Snapshot types
    "Snapshot",
    "SnapshotMetadata", 
    "SnapshotPayload",
    "ObservationGroup",
    "ObservationCategory",
    
    # Snapshot functions
    "create_empty_snapshot",
    "validate_snapshot_for_storage",
    "get_canonical_hash_input",
    "SnapshotBuilder",
    
    # Utilities
    "create_snapshot",
    "load_snapshot",
    "validate_snapshot",
    
    # Anchor types
    "Anchor",
    "AnchorSet", 
    "AnchorComparison",
    "AnchorType",
    "ContentFingerprintMethod",
    
    # Anchor functions
    "create_anchor",
    "compare_anchor_sets", 
    "verify_anchor_consistency",
    "compute_anchors_for_snapshot",
    
    # Version types
    "SnapshotVersion",
    "VersionFormat",
    "SemanticVersion", 
    "TimestampVersion",
    
    # Version functions
    "get_current_version",
    "validate_snapshot_version",
    "check_compatibility", 
    "upgrade_snapshot",
    "serialize_version",
    "deserialize_version",
    
    # Integrity types
    "IntegrityRoot",
    "HashAlgorithm", 
    "CorruptionReport",
    "CorruptionType",
    
    # Integrity functions
    "compute_integrity_root",
    "verify_integrity",
    "audit_snapshot",
    "create_integrity_for_testing",
    "get_default_algorithm",
    "compare_hashes",
]

# ============================================================================
# PACKAGE DOCUMENTATION
# ============================================================================

__doc__ = """RECORD PACKAGE: IMMUTABLE TRUTH PRESERVATION

Purpose
-------
Convert raw observational outputs into stable, tamper-evident, 
referencable snapshots of reality.

Philosophy
----------
This layer still:
❌ does not interpret
❌ does not judge  
❌ does not decide

But unlike eyes, it commits.

Core Production Rules (Non-Negotiable)
--------------------------------------
1. Immutability is enforced, not promised
2. Every snapshot is addressable
3. Every snapshot is verifiable
4. No snapshot is overwritten
5. Corruption must be detectable, not merely avoided

If any of these are violated, this is not a record system — 
it's a cache pretending to be serious.

Module Overview
---------------
snapshot.py: Complete observation snapshot - the forensic unit of truth
anchors.py: Stable reference points - identity without location
version.py: Snapshot format versioning and compatibility management
integrity.py: Tamper alarm system - hash trees and corruption detection

Usage Example
-------------
```python
from observations.record import Snapshot, create_anchor, compute_integrity_root

# Create a snapshot from observations
snapshot = Snapshot.create(...)

# Add stable anchors
anchors = [create_anchor(path) for path in observed_paths]
snapshot_with_anchors = snapshot.with_anchors(anchors)

# Compute integrity root
integrity_root = compute_integrity_root(snapshot_with_anchors)
complete_snapshot = snapshot_with_anchors.with_integrity(integrity_root)

# Verify integrity
is_valid, reason = verify_integrity(complete_snapshot)
if not is_valid:
    raise ValueError(f"Corruption detected: {reason}")

# Serialize for storage
json_str = complete_snapshot.to_json(indent=2) """