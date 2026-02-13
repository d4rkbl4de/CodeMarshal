"""
Storage schema definitions for CodeMarshal.

This module defines the shape of persisted truth - the difference between
"data" and "evidence". Every stored artifact must declare its schema version,
content hash, and creation context.

CONSTITUTIONAL RULES:
1. Schemas are explicit, not inferred
2. Validation is strict, not forgiving
3. No auto-correction of malformed data
4. No migration logic (see migration.py for controlled evolution)
5. Schemas must be interpretable years later without code archaeology
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import (
    Any,
    Literal,
    cast,
)


class SchemaVersion(StrEnum):
    """Version identifiers for stored schemas.

    Increment only when making backward-incompatible changes.
    Each version must have explicit migration in storage/migration.py.
    """

    V1 = "v1.0.0"
    V2 = "v2.0.0"
    V2_1 = "v2.1.0"


def normalize_schema_version(raw_value: Any) -> SchemaVersion:
    """Normalize schema version to SchemaVersion enum."""
    if isinstance(raw_value, SchemaVersion):
        return raw_value

    if isinstance(raw_value, int):
        if raw_value == 1:
            return SchemaVersion.V1
        if raw_value == 2:
            return SchemaVersion.V2
        if raw_value == 210:
            return SchemaVersion.V2_1

    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized.startswith("v"):
            normalized = normalized[1:]
        normalized = normalized.replace("_", ".")

        if normalized in {"1", "1.0", "1.0.0"}:
            return SchemaVersion.V1
        if normalized in {"2", "2.0", "2.0.0"}:
            return SchemaVersion.V2
        if normalized in {"2.1", "2.1.0"}:
            return SchemaVersion.V2_1

    raise ValueError(f"Invalid schema_version: {raw_value}")


class EvidenceType(StrEnum):
    """Types of evidence that can be stored."""

    FILE_OBSERVATION = "file_observation"
    DIRECTORY_OBSERVATION = "directory_observation"
    IMPORT_OBSERVATION = "import_observation"
    EXPORT_OBSERVATION = "export_observation"
    BOUNDARY_OBSERVATION = "boundary_observation"
    ENCODING_OBSERVATION = "encoding_observation"
    ANCHOR = "anchor"
    SNAPSHOT = "snapshot"
    NOTEBOOK_ENTRY = "notebook_entry"


class IntegrityStatus(StrEnum):
    """Integrity status of stored evidence."""

    VALID = "valid"
    CORRUPTED = "corrupted"
    TAMPERED = "tampered"
    UNVERIFIABLE = "unverifiable"


class HashAlgorithm(StrEnum):
    """Supported hash algorithms for content verification."""

    SHA256 = "sha256"
    BLAKE2B = "blake2b"


@dataclass(frozen=True)
class ContentHash:
    """Immutable content hash with algorithm specification."""

    algorithm: HashAlgorithm
    digest: str  # Hex-encoded digest

    def verify(self, content: bytes) -> bool:
        """Verify content matches this hash."""
        if self.algorithm == HashAlgorithm.SHA256:
            computed = hashlib.sha256(content).hexdigest()
        elif self.algorithm == HashAlgorithm.BLAKE2B:
            computed = hashlib.blake2b(content).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.algorithm}")

        return self.digest == computed

    @classmethod
    def compute(
        cls, content: bytes, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> ContentHash:
        """Compute hash of content."""
        if algorithm == HashAlgorithm.SHA256:
            digest = hashlib.sha256(content).hexdigest()
        elif algorithm == HashAlgorithm.BLAKE2B:
            digest = hashlib.blake2b(content).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        return cls(algorithm=algorithm, digest=digest)


@dataclass(frozen=True)
class StorageContext:
    """Creation context for stored evidence."""

    tool_version: str
    command_line: str
    working_directory: str  # Stored as string for portability
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    environment: dict[str, str] = field(default_factory=dict)  # type: ignore

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "tool_version": self.tool_version,
            "command_line": self.command_line,
            "working_directory": self.working_directory,
            "created_at": self.created_at.isoformat(),
            "environment": self.environment,
        }


@dataclass(frozen=True)
class EvidenceMetadata:
    """Common metadata for all evidence types."""

    evidence_id: str  # UUID or deterministic ID
    evidence_type: EvidenceType
    schema_version: SchemaVersion
    content_hash: ContentHash
    context: StorageContext
    integrity_status: IntegrityStatus = IntegrityStatus.VALID

    def verify_integrity(self, content: bytes) -> bool:
        """Verify content integrity."""
        if self.integrity_status != IntegrityStatus.VALID:
            return False

        return self.content_hash.verify(content)

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "schema_version": self.schema_version.value,
            "content_hash": {
                "algorithm": self.content_hash.algorithm.value,
                "digest": self.content_hash.digest,
            },
            "context": self.context.to_serializable(),
            "integrity_status": self.integrity_status.value,
        }


# === FILE OBSERVATION SCHEMA ===


@dataclass(frozen=True)
class FileObservation:
    """Observation of a single file."""

    metadata: EvidenceMetadata
    path: str  # Stored as string for portability
    size_bytes: int
    encoding: str | None = None  # None means "could not determine"
    is_binary: bool = False
    is_symlink: bool = False
    symlink_target: str | None = None  # Stored as string

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "file",
                "path": self.path,
                "size_bytes": self.size_bytes,
                "encoding": self.encoding,
                "is_binary": self.is_binary,
                "is_symlink": self.is_symlink,
                "symlink_target": self.symlink_target,
            }
        )
        return base


# === DIRECTORY OBSERVATION SCHEMA ===


@dataclass(frozen=True)
class DirectoryObservation:
    """Observation of a directory structure."""

    metadata: EvidenceMetadata
    path: str  # Stored as string
    child_files: frozenset[str]  # Stored as strings
    child_directories: frozenset[str]  # Stored as strings
    total_size_bytes: int
    depth: int

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "directory",
                "path": self.path,
                "child_files": sorted(self.child_files),
                "child_directories": sorted(self.child_directories),
                "total_size_bytes": self.total_size_bytes,
                "depth": self.depth,
            }
        )
        return base


# === IMPORT OBSERVATION SCHEMA ===


@dataclass(frozen=True)
class ImportStatement:
    """Single import statement observation."""

    module_path: str  # Stored as string
    line_number: int
    column_start: int
    column_end: int
    imported_module: str  # The module being imported
    import_level: int = 0  # 0 for absolute, >0 for relative
    alias: str | None = None  # "import x as y"
    is_from_import: bool = False
    imported_names: frozenset[str] = field(default_factory=frozenset)  # type: ignore

    def to_serializable(self) -> dict[str, Any]:
        return {
            "module_path": self.module_path,
            "line_number": self.line_number,
            "column_start": self.column_start,
            "column_end": self.column_end,
            "imported_module": self.imported_module,
            "import_level": self.import_level,
            "alias": self.alias,
            "is_from_import": self.is_from_import,
            "imported_names": sorted(self.imported_names),
        }


@dataclass(frozen=True)
class ImportObservation:
    """Collection of import statements from a codebase."""

    metadata: EvidenceMetadata
    imports: frozenset[ImportStatement]
    module_count: int
    total_import_statements: int

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "imports",
                "imports": [
                    imp.to_serializable()
                    for imp in sorted(
                        self.imports,
                        key=lambda x: (x.module_path, x.line_number, x.column_start),
                    )
                ],
                "module_count": self.module_count,
                "total_import_statements": self.total_import_statements,
            }
        )
        return base


# === EXPORT OBSERVATION SCHEMA ===


@dataclass(frozen=True)
class ExportDefinition:
    """Single export definition (function, class, variable)."""

    module_path: str  # Stored as string
    line_number: int
    column_start: int
    column_end: int
    name: str
    export_type: Literal["function", "class", "variable", "constant"]
    signature: str | None = None  # For functions and methods
    docstring: str | None = None
    is_public: bool = True  # Not prefixed with _

    def to_serializable(self) -> dict[str, Any]:
        return {
            "module_path": self.module_path,
            "line_number": self.line_number,
            "column_start": self.column_start,
            "column_end": self.column_end,
            "name": self.name,
            "export_type": self.export_type,
            "signature": self.signature,
            "docstring": self.docstring,
            "is_public": self.is_public,
        }


@dataclass(frozen=True)
class ExportObservation:
    """Collection of export definitions from a codebase."""

    metadata: EvidenceMetadata
    exports: frozenset[ExportDefinition]
    module_count: int
    total_exports: int

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "exports",
                "exports": [
                    exp.to_serializable()
                    for exp in sorted(
                        self.exports,
                        key=lambda x: (x.module_path, x.line_number, x.column_start),
                    )
                ],
                "module_count": self.module_count,
                "total_exports": self.total_exports,
            }
        )
        return base


# === BOUNDARY OBSERVATION SCHEMA ===


@dataclass(frozen=True)
class ModuleBoundary:
    """Boundary definition for a module or package."""

    path: str  # Stored as string
    boundary_type: Literal["module", "package", "namespace"]
    exports: frozenset[str]  # Names exported from this boundary
    dependencies: frozenset[str]  # Other boundaries this depends on (as strings)

    def to_serializable(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "boundary_type": self.boundary_type,
            "exports": sorted(self.exports),
            "dependencies": sorted(self.dependencies),
        }


@dataclass(frozen=True)
class BoundaryObservation:
    """Collection of module boundaries and their relationships."""

    metadata: EvidenceMetadata
    boundaries: frozenset[ModuleBoundary]
    boundary_violations: frozenset[tuple[str, str]]  # (from_path, to_path) as strings

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "boundaries",
                "boundaries": [
                    b.to_serializable()
                    for b in sorted(self.boundaries, key=lambda x: x.path)
                ],
                "boundary_violations": [
                    [from_path, to_path]
                    for from_path, to_path in sorted(self.boundary_violations)
                ],
            }
        )
        return base


# === ENCODING OBSERVATION SCHEMA ===


@dataclass(frozen=True)
class FileEncoding:
    """Detected encoding of a file."""

    path: str  # Stored as string
    encoding: str | None  # None means "could not determine"
    confidence: float  # 0.0 to 1.0
    has_bom: bool = False
    line_endings: Literal["lf", "crlf", "cr", "mixed", "unknown"] = "unknown"

    def to_serializable(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "encoding": self.encoding,
            "confidence": self.confidence,
            "has_bom": self.has_bom,
            "line_endings": self.line_endings,
        }


@dataclass(frozen=True)
class EncodingObservation:
    """Collection of file encoding observations."""

    metadata: EvidenceMetadata
    encodings: frozenset[FileEncoding]
    total_files: int
    undetectable_count: int

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "encodings",
                "encodings": [
                    enc.to_serializable()
                    for enc in sorted(self.encodings, key=lambda x: x.path)
                ],
                "total_files": self.total_files,
                "undetectable_count": self.undetectable_count,
            }
        )
        return base


# === ANCHOR SCHEMA ===


@dataclass(frozen=True)
class Anchor:
    """Stable reference point in an investigation."""

    metadata: EvidenceMetadata
    anchor_id: str
    description: str
    anchored_to: EvidenceType
    anchored_evidence_id: str
    tags: frozenset[str] = field(default_factory=frozenset)  # type: ignore

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "anchor",
                "anchor_id": self.anchor_id,
                "description": self.description,
                "anchored_to": self.anchored_to.value,
                "anchored_evidence_id": self.anchored_evidence_id,
                "tags": sorted(self.tags),
            }
        )
        return base


# === SNAPSHOT SCHEMA ===


@dataclass(frozen=True)
class Snapshot:
    """Complete observation snapshot of a codebase."""

    metadata: EvidenceMetadata
    snapshot_id: str
    evidence_references: dict[EvidenceType, list[str]]  # Evidence IDs by type
    root_path: str  # Stored as string
    total_size_bytes: int
    file_count: int
    directory_count: int
    module_count: int

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "snapshot",
                "snapshot_id": self.snapshot_id,
                "evidence_references": {
                    evidence_type.value: evidence_ids
                    for evidence_type, evidence_ids in self.evidence_references.items()
                },
                "root_path": self.root_path,
                "total_size_bytes": self.total_size_bytes,
                "file_count": self.file_count,
                "directory_count": self.directory_count,
                "module_count": self.module_count,
            }
        )
        return base


# === NOTEBOOK ENTRY SCHEMA ===


@dataclass(frozen=True)
class NotebookEntry:
    """Human thinking anchored to observations."""

    metadata: EvidenceMetadata
    entry_id: str
    title: str
    content: str
    anchored_evidence_ids: frozenset[str]  # Evidence this thinking references
    tags: frozenset[str] = field(default_factory=frozenset)  # type: ignore
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def schema_version(cls) -> SchemaVersion:
        return SchemaVersion.V2_1

    def to_serializable(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        base = self.metadata.to_serializable()
        base.update(
            {
                "observation_type": "notebook_entry",
                "entry_id": self.entry_id,
                "title": self.title,
                "content": self.content,
                "anchored_evidence_ids": sorted(self.anchored_evidence_ids),
                "tags": sorted(self.tags),
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            }
        )
        return base


# === TYPE ALIASES FOR EASIER IMPORT ===

StoredEvidence = (
    FileObservation
    | DirectoryObservation
    | ImportObservation
    | ExportObservation
    | BoundaryObservation
    | EncodingObservation
    | Anchor
    | Snapshot
    | NotebookEntry
)


# === VALIDATION FUNCTIONS ===


def validate_evidence_structure(raw_data: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate raw data against evidence structure requirements.

    Returns (is_valid, error_message)
    """
    # Check required top-level fields
    required_fields = {
        "evidence_id",
        "evidence_type",
        "schema_version",
        "content_hash",
        "context",
    }

    # raw_data is Dict[str, Any], so keys are strings
    raw_keys_set: set[str] = set(raw_data.keys())

    missing = required_fields - raw_keys_set
    if missing:
        return False, f"Missing required fields: {sorted(missing)}"

    # Validate evidence_type
    try:
        EvidenceType(raw_data["evidence_type"])
    except ValueError:
        return False, f"Invalid evidence_type: {raw_data['evidence_type']}"

    # Validate schema_version
    try:
        normalize_schema_version(raw_data["schema_version"])
    except ValueError:
        return False, f"Invalid schema_version: {raw_data['schema_version']}"

    # Validate content_hash structure
    hash_data = raw_data.get("content_hash")
    if not isinstance(hash_data, dict):
        return False, "content_hash must be a dictionary"

    # Type narrowing: after isinstance check, cast to Dict[str, Any]
    hash_dict = cast(dict[str, Any], hash_data)

    hash_required = {"algorithm", "digest"}
    hash_keys_set: set[str] = set(hash_dict.keys())
    hash_missing = hash_required - hash_keys_set
    if hash_missing:
        return False, f"Missing content_hash fields: {sorted(hash_missing)}"

    try:
        HashAlgorithm(hash_dict["algorithm"])
    except ValueError:
        return False, f"Invalid hash algorithm: {hash_dict['algorithm']}"

    # Validate context structure
    context_data = raw_data.get("context")
    if not isinstance(context_data, dict):
        return False, "context must be a dictionary"

    # Type narrowing: after isinstance check, cast to Dict[str, Any]
    context_dict = cast(dict[str, Any], context_data)

    context_required = {
        "tool_version",
        "command_line",
        "working_directory",
        "created_at",
    }
    context_keys_set: set[str] = set(context_dict.keys())
    context_missing = context_required - context_keys_set
    if context_missing:
        return False, f"Missing context fields: {sorted(context_missing)}"

    return True, None


def compute_evidence_hash(evidence_data: dict[str, Any]) -> str:
    """Compute content hash for evidence data (excluding the hash itself)."""
    # Remove the hash field if present
    data_to_hash = dict(evidence_data)
    data_to_hash.pop("content_hash", None)

    # Sort keys for deterministic serialization
    serialized = json.dumps(data_to_hash, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_evidence_integrity(
    evidence_data: dict[str, Any],
) -> tuple[IntegrityStatus, str | None]:
    """Verify integrity of evidence data.

    Returns (integrity_status, error_message)
    """
    # Validate structure first
    is_valid, error = validate_evidence_structure(evidence_data)
    if not is_valid:
        return IntegrityStatus.CORRUPTED, error

    # Check hash
    stored_hash = evidence_data["content_hash"]["digest"]
    computed_hash = compute_evidence_hash(evidence_data)

    if stored_hash != computed_hash:
        return IntegrityStatus.TAMPERED, "Content hash mismatch"

    return IntegrityStatus.VALID, None


# === SERIALIZATION UTILITIES ===


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for evidence types."""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, Enum):
            return o.value
        elif isinstance(o, (frozenset, set)):
            # Convert to list of strings for JSON serialization
            # Use cast to help type inference
            typed_set = cast("set[Any]", o)
            return sorted([str(item) for item in typed_set])
        elif hasattr(o, "to_serializable"):
            return o.to_serializable()

        return super().default(o)


def serialize_evidence(evidence: StoredEvidence) -> bytes:
    """Serialize evidence to JSON bytes."""
    serializable = evidence.to_serializable()
    json_str = json.dumps(serializable, cls=JSONEncoder, indent=2, sort_keys=True)
    return json_str.encode("utf-8")


def deserialize_evidence(raw_bytes: bytes) -> tuple[StoredEvidence | None, str | None]:
    """Deserialize evidence from JSON bytes.

    Returns (evidence, error_message)
    """
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"

    # Verify integrity
    status, error = verify_evidence_integrity(data)
    if status != IntegrityStatus.VALID:
        return None, f"Integrity check failed: {error}"

    # Get evidence type (verify it's valid but we don't use it yet)
    try:
        EvidenceType(data["evidence_type"])
    except ValueError:
        return None, f"Unknown evidence type: {data['evidence_type']}"

    # Note: Full deserialization would reconstruct the appropriate dataclass
    # This is a placeholder - actual implementation would parse based on evidence_type
    return None, "Deserialization not fully implemented in schema module"


# === EXPORTED SYMBOLS ===

__all__ = [
    # Enums
    "SchemaVersion",
    "normalize_schema_version",
    "EvidenceType",
    "IntegrityStatus",
    "HashAlgorithm",
    # Core types
    "ContentHash",
    "StorageContext",
    "EvidenceMetadata",
    # Evidence schemas
    "FileObservation",
    "DirectoryObservation",
    "ImportObservation",
    "ExportObservation",
    "BoundaryObservation",
    "EncodingObservation",
    "Anchor",
    "Snapshot",
    "NotebookEntry",
    # Type aliases
    "StoredEvidence",
    # Validation functions
    "validate_evidence_structure",
    "compute_evidence_hash",
    "verify_evidence_integrity",
    # Serialization
    "serialize_evidence",
    "deserialize_evidence",
    "JSONEncoder",
]
