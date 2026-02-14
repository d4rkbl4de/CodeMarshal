"""
observations/record/integrity.py

Tamper alarm system for snapshots.

This module provides:
- Canonical hashing rules
- Hash tree / Merkle-style root computation
- Integrity verification functions

Production principle: Corruption that is detected is survivable.
Corruption that is hidden becomes institutionalized.

This module must be boring, strict, and merciless.
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

# Type-only imports to avoid circular dependencies
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from observations.record.snapshot import Snapshot

# ============================================================================
# HASHING ALGORITHMS
# ============================================================================


class HashAlgorithm(StrEnum):
    """Supported hash algorithms."""

    SHA256 = "sha256"  # Default - cryptographically strong, widely used
    SHA512 = "sha512"  # For higher security requirements
    BLAKE2B = "blake2b"  # Fast, parallelizable, cryptographically strong
    BLAKE2S = "blake2s"  # Smaller output, still strong

    @classmethod
    def default(cls) -> "HashAlgorithm":
        """Get the default hash algorithm."""
        return cls.SHA256

    def create_hasher(self) -> Any:
        """Create a hasher instance for this algorithm."""
        if self == HashAlgorithm.SHA256:
            return hashlib.sha256()
        elif self == HashAlgorithm.SHA512:
            return hashlib.sha512()
        elif self == HashAlgorithm.BLAKE2B:
            return hashlib.blake2b()
        elif self == HashAlgorithm.BLAKE2S:
            return hashlib.blake2s()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self}")

    @property
    def digest_size(self) -> int:
        """Size of the hash digest in bytes."""
        if self == HashAlgorithm.SHA256:
            return 32
        elif self == HashAlgorithm.SHA512:
            return 64
        elif self == HashAlgorithm.BLAKE2B:
            return 64
        elif self == HashAlgorithm.BLAKE2S:
            return 32
        else:
            raise ValueError(f"Unsupported hash algorithm: {self}")


# ============================================================================
# CORE HASHING UTILITIES
# ============================================================================


def compute_hash(
    data: bytes, algorithm: HashAlgorithm = HashAlgorithm.default()
) -> str:
    """
    Compute hash of binary data.

    Args:
        data: Binary data to hash
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal string representation of hash
    """
    hasher = algorithm.create_hasher()
    hasher.update(data)
    return hasher.hexdigest()


def compute_string_hash(
    text: str, algorithm: HashAlgorithm = HashAlgorithm.default()
) -> str:
    """
    Compute hash of a UTF-8 string.

    Args:
        text: String to hash (encoded as UTF-8)
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal string representation of hash
    """
    return compute_hash(text.encode("utf-8"), algorithm)


def compute_dict_hash(
    data: dict[str, Any], algorithm: HashAlgorithm = HashAlgorithm.default()
) -> str:
    """
    Compute hash of a dictionary using canonical JSON serialization.

    Args:
        data: Dictionary to hash
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal string representation of hash
    """
    # Use canonical JSON serialization (no whitespace, sorted keys)
    json_str = json.dumps(data, separators=(",", ":"), sort_keys=True)
    return compute_string_hash(json_str, algorithm)


def compute_list_hash(
    items: list[Any], algorithm: HashAlgorithm = HashAlgorithm.default()
) -> str:
    """
    Compute hash of a list using canonical JSON serialization.

    Args:
        items: List to hash
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal string representation of hash
    """
    return compute_dict_hash({"items": items}, algorithm)


def combine_hashes(
    hash1: str, hash2: str, algorithm: HashAlgorithm = HashAlgorithm.default()
) -> str:
    """
    Combine two hashes in a deterministic way.

    This is used for building hash trees. The order matters: hash1 then hash2.

    Args:
        hash1: First hash (hex string)
        hash2: Second hash (hex string)
        algorithm: Hash algorithm to use

    Returns:
        Combined hash
    """
    # Convert hex strings to bytes
    try:
        bytes1 = bytes.fromhex(hash1)
        bytes2 = bytes.fromhex(hash2)
    except ValueError as e:
        raise ValueError(f"Invalid hex string in hash: {e}") from e

    # Ensure hashes are using the same algorithm (rough check by length)
    expected_len = algorithm.digest_size * 2  # hex chars = bytes * 2
    if len(hash1) != expected_len or len(hash2) != expected_len:
        raise ValueError(
            f"Hash length mismatch for algorithm {algorithm}: "
            f"expected {expected_len} chars, got {len(hash1)} and {len(hash2)}"
        )

    # Concatenate and hash
    combined = bytes1 + bytes2
    return compute_hash(combined, algorithm)


# ============================================================================
# HASH TREE (MERKLE TREE) IMPLEMENTATION
# ============================================================================


@dataclass(frozen=True)
class HashTreeNode:
    """A node in a Merkle tree."""

    hash_value: str
    algorithm: HashAlgorithm
    left: Optional["HashTreeNode"] = None
    right: Optional["HashTreeNode"] = None
    data_hash: str | None = None  # Hash of actual data (for leaves)

    def __post_init__(self) -> None:
        """Validate node consistency."""
        # Validate hash length
        expected_len = self.algorithm.digest_size * 2
        if len(self.hash_value) != expected_len:
            raise ValueError(
                f"Hash length mismatch: expected {expected_len} chars, "
                f"got {len(self.hash_value)} for algorithm {self.algorithm}"
            )

        # Validate leaf vs internal node
        if self.left is None and self.right is None:
            # Leaf node should have data_hash
            if self.data_hash is None:
                raise ValueError("Leaf node must have data_hash")
            if self.hash_value != self.data_hash:
                raise ValueError("Leaf node hash must equal data_hash")
        else:
            # Internal node should have both children
            if self.left is None or self.right is None:
                raise ValueError("Internal node must have both children")
            # Internal node shouldn't have data_hash
            if self.data_hash is not None:
                raise ValueError("Internal node should not have data_hash")

            # Verify hash is correct combination of children
            expected_hash = combine_hashes(
                self.left.hash_value, self.right.hash_value, self.algorithm
            )
            if self.hash_value != expected_hash:
                raise ValueError("Internal node hash doesn't match children")

    @classmethod
    def create_leaf(cls, data_hash: str, algorithm: HashAlgorithm) -> "HashTreeNode":
        """Create a leaf node."""
        return cls(hash_value=data_hash, algorithm=algorithm, data_hash=data_hash)

    @classmethod
    def create_internal(
        cls, left: "HashTreeNode", right: "HashTreeNode", algorithm: HashAlgorithm
    ) -> "HashTreeNode":
        """Create an internal node from two children."""
        # Ensure both children use same algorithm
        if left.algorithm != algorithm or right.algorithm != algorithm:
            raise ValueError("Children must use same algorithm as parent")

        hash_value = combine_hashes(left.hash_value, right.hash_value, algorithm)

        return cls(hash_value=hash_value, algorithm=algorithm, left=left, right=right)

    def verify(self) -> bool:
        """Verify the entire subtree."""
        try:
            self.__post_init__()  # This will validate the node
            # Recursively verify children
            if self.left is not None:
                if not self.left.verify():
                    return False
            if self.right is not None:
                if not self.right.verify():
                    return False
            return True
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert node to serializable dictionary."""
        result = {"hash": self.hash_value, "algorithm": self.algorithm.value}

        if self.left is not None and self.right is not None:
            result["left"] = self.left.to_dict()
            result["right"] = self.right.to_dict()

        if self.data_hash is not None:
            result["data_hash"] = self.data_hash

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HashTreeNode":
        """Create node from dictionary."""
        algorithm = HashAlgorithm(data["algorithm"])

        left = None
        right = None
        data_hash = None

        if "left" in data and "right" in data:
            left = cls.from_dict(data["left"])
            right = cls.from_dict(data["right"])
        else:
            data_hash = data.get("data_hash")

        return cls(
            hash_value=data["hash"],
            algorithm=algorithm,
            left=left,
            right=right,
            data_hash=data_hash,
        )


class HashTree:
    """Merkle tree for efficient integrity verification of large datasets."""

    def __init__(
        self,
        items: list[Any],
        algorithm: HashAlgorithm = HashAlgorithm.default(),
        hash_func: Callable[[Any, HashAlgorithm], str] | None = None,
    ):
        """
        Build a Merkle tree from items.

        Args:
            items: List of items to hash
            algorithm: Hash algorithm to use
            hash_func: Function to compute hash of an item (default: compute_dict_hash)
        """
        self.algorithm = algorithm
        self.hash_func = hash_func or compute_dict_hash

        if not items:
            self.root = None
            self.leaf_count = 0
            return

        # Create leaf nodes
        leaves = []
        for item in items:
            item_hash = self.hash_func(item, self.algorithm)
            leaf = HashTreeNode.create_leaf(item_hash, self.algorithm)
            leaves.append(leaf)

        self.leaf_count = len(leaves)
        self.root = self._build_tree(leaves)

    def _build_tree(self, nodes: list[HashTreeNode]) -> HashTreeNode:
        """Recursively build tree from nodes."""
        if len(nodes) == 1:
            return nodes[0]

        # Pair nodes and combine
        paired = []
        for i in range(0, len(nodes), 2):
            if i + 1 < len(nodes):
                paired.append(
                    HashTreeNode.create_internal(nodes[i], nodes[i + 1], self.algorithm)
                )
            else:
                # Odd number of nodes: duplicate last node
                paired.append(
                    HashTreeNode.create_internal(nodes[i], nodes[i], self.algorithm)
                )

        return self._build_tree(paired)

    @property
    def root_hash(self) -> str | None:
        """Get the root hash of the tree."""
        return self.root.hash_value if self.root else None

    def verify_item(self, item: Any, index: int) -> tuple[bool, list[str] | None]:
        """
        Verify an item exists in the tree and get proof path.

        Args:
            item: Item to verify
            index: Index of item in original list

        Returns:
            Tuple of (is_valid: bool, proof_path: Optional[List[str]])
        """
        if self.root is None:
            return False, None

        if index < 0 or index >= self.leaf_count:
            return False, None

        # Compute item hash
        item_hash = self.hash_func(item, self.algorithm)

        # Navigate tree to build proof
        proof = []
        node = self.root
        leaf_index = index
        leaf_count = self.leaf_count

        while node.left is not None and node.right is not None:
            # Determine which side our leaf is on
            # At each level, half the leaves are on each side
            half = (leaf_count + 1) // 2  # Ceiling division

            if leaf_index < half:
                # Leaf is in left subtree
                proof.append(("right", node.right.hash_value))
                node = node.left
                leaf_count = half
            else:
                # Leaf is in right subtree
                proof.append(("left", node.left.hash_value))
                node = node.right
                leaf_index -= half
                leaf_count = leaf_count - half

        # At leaf: verify hash
        if node.hash_value != item_hash:
            return False, None

        # Reconstruct from proof
        current_hash = item_hash
        for side, sibling_hash in reversed(proof):
            if side == "left":
                current_hash = combine_hashes(
                    sibling_hash, current_hash, self.algorithm
                )
            else:
                current_hash = combine_hashes(
                    current_hash, sibling_hash, self.algorithm
                )

        return current_hash == self.root_hash, [h for _, h in proof]

    def verify_proof(self, item_hash: str, index: int, proof: list[str]) -> bool:
        """
        Verify a Merkle proof.

        Args:
            item_hash: Hash of the item
            index: Index of the item
            proof: List of sibling hashes from leaf to root

        Returns:
            True if proof is valid
        """
        if self.root is None:
            return False

        current_hash = item_hash
        leaf_index = index
        leaf_count = self.leaf_count

        for sibling_hash in proof:
            # Determine if sibling is left or right based on index
            half = (leaf_count + 1) // 2

            if leaf_index < half:
                # Sibling is on the right
                current_hash = combine_hashes(
                    current_hash, sibling_hash, self.algorithm
                )
                leaf_count = half
            else:
                # Sibling is on the left
                current_hash = combine_hashes(
                    sibling_hash, current_hash, self.algorithm
                )
                leaf_index -= half
                leaf_count = leaf_count - half

        return current_hash == self.root_hash

    def to_dict(self) -> dict[str, Any]:
        """Convert tree to serializable dictionary."""
        return {
            "algorithm": self.algorithm.value,
            "leaf_count": self.leaf_count,
            "root": self.root.to_dict() if self.root else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HashTree":
        """Create tree from dictionary."""
        tree = cls([], HashAlgorithm(data["algorithm"]))
        tree.leaf_count = data["leaf_count"]
        if data["root"]:
            tree.root = HashTreeNode.from_dict(data["root"])
        return tree

    def verify_tree(self) -> bool:
        """Verify the entire tree structure."""
        if self.root is None:
            return self.leaf_count == 0

        return self.root.verify()


# ============================================================================
# INTEGRITY ROOT STRUCTURE
# ============================================================================


@dataclass(frozen=True)
class IntegrityRoot:
    """
    Complete integrity information for a snapshot.

    This is a hash tree root that covers:
    - Snapshot metadata
    - Observations payload
    - Anchors
    """

    # Root hash
    root_hash: str

    # Hash algorithm used
    algorithm: HashAlgorithm

    # Component hashes (for partial verification)
    metadata_hash: str
    payload_hash: str
    anchors_hash: str | None = None

    # Timestamp of computation
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Hash tree structure (optional, for advanced verification)
    hash_tree: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate integrity root."""
        # Validate hash lengths
        expected_len = self.algorithm.digest_size * 2

        hashes_to_check = [
            ("root_hash", self.root_hash),
            ("metadata_hash", self.metadata_hash),
            ("payload_hash", self.payload_hash),
        ]

        if self.anchors_hash:
            hashes_to_check.append(("anchors_hash", self.anchors_hash))

        for name, hash_value in hashes_to_check:
            if len(hash_value) != expected_len:
                raise ValueError(
                    f"{name} length mismatch for algorithm {self.algorithm}: "
                    f"expected {expected_len} chars, got {len(hash_value)}"
                )

        # Validate computed_at is timezone-aware
        if self.computed_at.tzinfo is None:
            raise ValueError("computed_at must be timezone-aware")

    def verify_consistency(self) -> bool:
        """Verify that component hashes combine to root hash."""
        if self.anchors_hash:
            # Combine metadata, payload, and anchors
            combined = combine_hashes(
                self.metadata_hash, self.payload_hash, self.algorithm
            )
            final = combine_hashes(combined, self.anchors_hash, self.algorithm)
        else:
            # Just metadata and payload
            final = combine_hashes(
                self.metadata_hash, self.payload_hash, self.algorithm
            )

        return final == self.root_hash

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        result = {
            "root_hash": self.root_hash,
            "algorithm": self.algorithm.value,
            "metadata_hash": self.metadata_hash,
            "payload_hash": self.payload_hash,
            "computed_at": self.computed_at.isoformat(),
        }

        if self.anchors_hash:
            result["anchors_hash"] = self.anchors_hash

        if self.hash_tree:
            result["hash_tree"] = self.hash_tree

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntegrityRoot":
        """Create from dictionary."""
        # Parse datetime
        computed_at = datetime.fromisoformat(data["computed_at"])

        # Parse algorithm
        algorithm = HashAlgorithm(data["algorithm"])

        return cls(
            root_hash=data["root_hash"],
            algorithm=algorithm,
            metadata_hash=data["metadata_hash"],
            payload_hash=data["payload_hash"],
            anchors_hash=data.get("anchors_hash"),
            computed_at=computed_at,
            hash_tree=data.get("hash_tree"),
        )

    def summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            f"Integrity Root: {self.root_hash[:16]}...",
            f"Algorithm: {self.algorithm.value}",
            f"Computed: {self.computed_at.isoformat()[:19]}Z",
            f"Metadata: {self.metadata_hash[:16]}...",
            f"Payload: {self.payload_hash[:16]}...",
        ]

        if self.anchors_hash:
            lines.append(f"Anchors: {self.anchors_hash[:16]}...")
        else:
            lines.append("Anchors: (none)")

        lines.append(f"Consistent: {'✓' if self.verify_consistency() else '✗'}")

        return "\n".join(lines)


# ============================================================================
# SNAPSHOT INTEGRITY COMPUTATION
# ============================================================================


def compute_snapshot_integrity(snapshot: "Snapshot") -> IntegrityRoot:
    """
    Compute integrity root for a snapshot.

    This is the main function that should be called to compute integrity
    for a complete snapshot (with anchors).

    Args:
        snapshot: Complete snapshot with anchors

    Returns:
        IntegrityRoot for the snapshot

    Raises:
        ValueError: If snapshot doesn't have anchors
        RuntimeError: If integrity cannot be computed
    """
    from observations.record.snapshot import Snapshot

    if not isinstance(snapshot, Snapshot):
        raise TypeError(f"Expected Snapshot, got {type(snapshot)}")

    if not snapshot.has_anchors():
        raise ValueError("Cannot compute integrity for snapshot without anchors")

    # Get canonical JSON for hashing
    canonical_dict = snapshot.to_dict(canonical=True)

    # Extract components for hashing
    metadata = canonical_dict["metadata"]
    payload = canonical_dict["payload"]
    anchors = canonical_dict.get("anchors", [])

    # Compute component hashes
    algorithm = HashAlgorithm.default()

    metadata_hash = compute_dict_hash(metadata, algorithm)
    payload_hash = compute_dict_hash(payload, algorithm)
    anchors_hash = compute_list_hash(anchors, algorithm) if anchors else None

    # Compute root hash
    if anchors_hash:
        # Combine metadata + payload, then with anchors
        combined = combine_hashes(metadata_hash, payload_hash, algorithm)
        root_hash = combine_hashes(combined, anchors_hash, algorithm)
    else:
        # Just metadata + payload
        root_hash = combine_hashes(metadata_hash, payload_hash, algorithm)

    # Build hash tree for detailed verification
    components = [
        {"type": "metadata", "data": metadata},
        {"type": "payload", "data": payload},
    ]

    if anchors:
        components.append({"type": "anchors", "data": anchors})

    hash_tree_obj = HashTree(components, algorithm)
    hash_tree_dict = hash_tree_obj.to_dict()

    return IntegrityRoot(
        root_hash=root_hash,
        algorithm=algorithm,
        metadata_hash=metadata_hash,
        payload_hash=payload_hash,
        anchors_hash=anchors_hash,
        hash_tree=hash_tree_dict,
    )


def verify_snapshot_integrity(snapshot: "Snapshot") -> tuple[bool, str | None]:
    """
    Verify integrity of a snapshot.

    Args:
        snapshot: Snapshot to verify

    Returns:
        Tuple of (is_valid: bool, reason: Optional[str])

        If is_valid is False, reason contains explanation.
    """
    from observations.record.snapshot import Snapshot

    if not isinstance(snapshot, Snapshot):
        return False, f"Expected Snapshot, got {type(snapshot)}"

    if not snapshot.has_integrity():
        return False, "Snapshot has no integrity root"

    integrity_root = snapshot.integrity_root

    try:
        # Verify integrity root structure
        if not integrity_root.verify_consistency():
            return False, "Integrity root is internally inconsistent"

        # Recompute hashes from snapshot
        canonical_dict = snapshot.to_dict(canonical=True)

        metadata = canonical_dict["metadata"]
        payload = canonical_dict["payload"]
        anchors = canonical_dict.get("anchors", [])

        algorithm = integrity_root.algorithm

        metadata_hash = compute_dict_hash(metadata, algorithm)
        payload_hash = compute_dict_hash(payload, algorithm)
        anchors_hash = compute_list_hash(anchors, algorithm) if anchors else None

        # Compare hashes
        if metadata_hash != integrity_root.metadata_hash:
            return False, "Metadata hash mismatch"

        if payload_hash != integrity_root.payload_hash:
            return False, "Payload hash mismatch"

        if anchors_hash != integrity_root.anchors_hash:
            if anchors_hash is None and integrity_root.anchors_hash is None:
                pass  # Both None is OK
            else:
                return False, "Anchors hash mismatch"

        # Verify root hash
        if anchors_hash:
            combined = combine_hashes(metadata_hash, payload_hash, algorithm)
            expected_root = combine_hashes(combined, anchors_hash, algorithm)
        else:
            expected_root = combine_hashes(metadata_hash, payload_hash, algorithm)

        if expected_root != integrity_root.root_hash:
            return False, "Root hash mismatch"

        return True, None

    except Exception as e:
        return False, f"Verification error: {str(e)}"


def verify_snapshot_against_root(
    snapshot: "Snapshot", expected_root: IntegrityRoot
) -> tuple[bool, str | None]:
    """
    Verify snapshot against a specific integrity root.

    Useful for checking if a snapshot matches a previously computed root.

    Args:
        snapshot: Snapshot to verify
        expected_root: Expected integrity root

    Returns:
        Tuple of (is_valid: bool, reason: Optional[str])
    """
    # First verify snapshot's own integrity
    is_valid, reason = verify_snapshot_integrity(snapshot)
    if not is_valid:
        return False, f"Snapshot integrity invalid: {reason}"

    # Compare with expected root
    if snapshot.integrity_root != expected_root:
        return False, "Integrity root doesn't match expected"

    return True, None


# ============================================================================
# CORRUPTION DETECTION
# ============================================================================


class CorruptionType(StrEnum):
    """Types of corruption that can be detected."""

    HASH_MISMATCH = "hash_mismatch"
    STRUCTURE_INVALID = "structure_invalid"
    MISSING_COMPONENT = "missing_component"
    VERSION_MISMATCH = "version_mismatch"
    TIMESTAMP_ANOMALY = "timestamp_anomaly"
    ALGORITHM_UNSUPPORTED = "algorithm_unsupported"

    def description(self) -> str:
        """Human-readable description."""
        descriptions = {
            self.HASH_MISMATCH: "Hash value doesn't match computed hash",
            self.STRUCTURE_INVALID: "Data structure is invalid or malformed",
            self.MISSING_COMPONENT: "Required component is missing",
            self.VERSION_MISMATCH: "Version doesn't match expected format",
            self.TIMESTAMP_ANOMALY: "Timestamp is invalid or suspicious",
            self.ALGORITHM_UNSUPPORTED: "Hash algorithm is not supported",
        }
        return descriptions[self]


@dataclass(frozen=True)
class CorruptionReport:
    """Report of detected corruption."""

    corruption_type: CorruptionType
    component: str  # Which component is corrupted
    expected: str | None = None  # Expected value (if applicable)
    actual: str | None = None  # Actual value (if applicable)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "corruption_type": self.corruption_type.value,
            "component": self.component,
            "expected": self.expected,
            "actual": self.actual,
            "detected_at": self.detected_at.isoformat(),
            "description": self.corruption_type.description(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CorruptionReport":
        """Create from dictionary."""
        return cls(
            corruption_type=CorruptionType(data["corruption_type"]),
            component=data["component"],
            expected=data.get("expected"),
            actual=data.get("actual"),
            detected_at=datetime.fromisoformat(data["detected_at"]),
        )

    def __str__(self) -> str:
        lines = [
            f"Corruption detected in {self.component}:",
            f"  Type: {self.corruption_type.value}",
            f"  Description: {self.corruption_type.description()}",
            f"  Detected: {self.detected_at.isoformat()[:19]}Z",
        ]

        if self.expected:
            lines.append(f"  Expected: {self.expected}")
        if self.actual:
            lines.append(f"  Actual: {self.actual}")

        return "\n".join(lines)


def detect_corruption(snapshot_dict: dict[str, Any]) -> list[CorruptionReport]:
    """
    Detect any corruption in a snapshot dictionary.

    This is a comprehensive check that goes beyond hash verification.

    Args:
        snapshot_dict: Snapshot dictionary (as loaded from storage)

    Returns:
        List of corruption reports (empty if no corruption)
    """
    reports: list[CorruptionReport] = []

    # Check required fields
    required_fields = ["version", "metadata", "payload"]
    for required_field in required_fields:
        if required_field not in snapshot_dict:
            reports.append(
                CorruptionReport(
                    corruption_type=CorruptionType.MISSING_COMPONENT,
                    component="snapshot",
                    expected=required_field,
                    actual=None,
                )
            )

    if reports:  # Can't check further if structure is broken
        return reports

    # Check metadata structure
    metadata = snapshot_dict.get("metadata", {})
    metadata_required = ["snapshot_id", "created_at", "source_path"]
    for metadata_field in metadata_required:
        if metadata_field not in metadata:
            reports.append(
                CorruptionReport(
                    corruption_type=CorruptionType.MISSING_COMPONENT,
                    component="metadata",
                    expected=metadata_field,
                    actual=None,
                )
            )

    # Check timestamp format
    created_at = metadata.get("created_at")
    if created_at:
        try:
            if isinstance(created_at, str):
                dt = datetime.fromisoformat(created_at)
                if dt.tzinfo is None:
                    reports.append(
                        CorruptionReport(
                            corruption_type=CorruptionType.TIMESTAMP_ANOMALY,
                            component="metadata.created_at",
                            expected="timezone-aware datetime",
                            actual="timezone-naive",
                        )
                    )
        except ValueError:
            reports.append(
                CorruptionReport(
                    corruption_type=CorruptionType.STRUCTURE_INVALID,
                    component="metadata.created_at",
                    expected="ISO format datetime string",
                    actual=str(created_at)[:50],
                )
            )

    # Check payload structure
    payload = snapshot_dict.get("payload", {})
    if "groups" not in payload:
        reports.append(
            CorruptionReport(
                corruption_type=CorruptionType.MISSING_COMPONENT,
                component="payload",
                expected="groups",
                actual=None,
            )
        )
    elif not isinstance(payload["groups"], list):
        reports.append(
            CorruptionReport(
                corruption_type=CorruptionType.STRUCTURE_INVALID,
                component="payload.groups",
                expected="list",
                actual=str(type(payload["groups"])),
            )
        )

    # Check integrity field if present
    if "integrity" in snapshot_dict:
        integrity = snapshot_dict["integrity"]

        # Check required integrity fields
        integrity_required = ["root_hash", "algorithm", "metadata_hash", "payload_hash"]
        for field in integrity_required:
            if field not in integrity:
                reports.append(
                    CorruptionReport(
                        corruption_type=CorruptionType.MISSING_COMPONENT,
                        component="integrity",
                        expected=field,
                        actual=None,
                    )
                )

        # Check algorithm is supported
        if "algorithm" in integrity:
            try:
                HashAlgorithm(integrity["algorithm"])
            except ValueError:
                reports.append(
                    CorruptionReport(
                        corruption_type=CorruptionType.ALGORITHM_UNSUPPORTED,
                        component="integrity.algorithm",
                        expected="supported hash algorithm",
                        actual=integrity["algorithm"],
                    )
                )

    return reports


# ============================================================================
# PUBLIC API
# ============================================================================


def compute_integrity_root(snapshot: "Snapshot") -> IntegrityRoot:
    """
    Compute integrity root for a complete snapshot.

    This is the primary function for external use.

    Args:
        snapshot: Complete snapshot (must have anchors)

    Returns:
        IntegrityRoot for the snapshot
    """
    return compute_snapshot_integrity(snapshot)


def verify_integrity(snapshot: "Snapshot") -> tuple[bool, str | None]:
    """
    Verify integrity of a snapshot.

    This is the primary verification function for external use.

    Args:
        snapshot: Snapshot to verify

    Returns:
        Tuple of (is_valid: bool, reason: Optional[str])
    """
    return verify_snapshot_integrity(snapshot)


def audit_snapshot(snapshot_dict: dict[str, Any]) -> list[CorruptionReport]:
    """
    Comprehensive audit of a snapshot dictionary.

    Use this when loading snapshots from storage to detect any issues.

    Args:
        snapshot_dict: Snapshot dictionary (as loaded from JSON)

    Returns:
        List of corruption reports (empty if clean)
    """
    return detect_corruption(snapshot_dict)


def create_integrity_for_testing(
    metadata_hash: str,
    payload_hash: str,
    anchors_hash: str | None = None,
    algorithm: HashAlgorithm = HashAlgorithm.default(),
) -> IntegrityRoot:
    """
    Create an integrity root for testing purposes.

    This allows creating expected integrity roots without a full snapshot.
    """
    if anchors_hash:
        combined = combine_hashes(metadata_hash, payload_hash, algorithm)
        root_hash = combine_hashes(combined, anchors_hash, algorithm)
    else:
        root_hash = combine_hashes(metadata_hash, payload_hash, algorithm)

    return IntegrityRoot(
        root_hash=root_hash,
        algorithm=algorithm,
        metadata_hash=metadata_hash,
        payload_hash=payload_hash,
        anchors_hash=anchors_hash,
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_default_algorithm() -> HashAlgorithm:
    """Get the default hash algorithm."""
    return HashAlgorithm.default()


def is_valid_hash(hash_str: str, algorithm: HashAlgorithm | None = None) -> bool:
    """
    Check if a string is a valid hash for an algorithm.

    Args:
        hash_str: String to check
        algorithm: Algorithm to check against (default: checks all)

    Returns:
        True if valid
    """
    if algorithm:
        expected_len = algorithm.digest_size * 2
        if len(hash_str) != expected_len:
            return False

        # Check hex characters
        try:
            bytes.fromhex(hash_str)
            return True
        except ValueError:
            return False
    else:
        # Check against all algorithms
        for algo in HashAlgorithm:
            if is_valid_hash(hash_str, algo):
                return True
        return False


def compare_hashes(hash1: str, hash2: str) -> bool:
    """
    Compare two hashes in constant time to avoid timing attacks.

    Args:
        hash1: First hash
        hash2: Second hash

    Returns:
        True if equal
    """
    # Use secrets.compare_digest for constant-time comparison
    # This prevents timing attacks that could reveal hash values
    import secrets

    return secrets.compare_digest(hash1, hash2)


def check_integrity(obj: Any) -> bool:
    """
    Check integrity of a snapshot or other object.

    Args:
        obj: Object to check (typically Snapshot)

    Returns:
        True if valid, False if corrupted
    """
    if hasattr(obj, "is_valid"):
        return bool(obj.is_valid)

    # Validation method that raises exception
    if hasattr(obj, "validate"):
        try:
            obj.validate()
            return True
        except Exception:
            return False

    # Default to True if no validation method
    return True


__all__ = [
    "HashAlgorithm",
    "compute_hash",
    "compute_string_hash",
    "is_valid_hash",
    "compare_hashes",
    "check_integrity",
]
