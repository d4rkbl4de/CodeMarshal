"""
Public storage contract for CodeMarshal.

Defines the public storage primitives and what is safe to touch.
This module answers: "What storage primitives exist, and which ones are safe to touch?"

CONSTITUTIONAL RULES:
1. Only export public, stable interfaces
2. No filesystem I/O in this module
3. No initialization or side effects
4. Import from sibling storage modules only
"""

# Explicit exports from storage modules
from .schema import (
    # Enums
    SchemaVersion,
    EvidenceType,
    IntegrityStatus,
    HashAlgorithm,
    
    # Core types
    ContentHash,
    StorageContext,
    EvidenceMetadata,
    
    # Evidence schemas
    FileObservation,
    DirectoryObservation,
    ImportObservation,
    ExportObservation,
    BoundaryObservation,
    EncodingObservation,
    Anchor,
    Snapshot,
    NotebookEntry,
    
    # Type aliases
    StoredEvidence,
    
    # Validation functions
    validate_evidence_structure,
    compute_evidence_hash,
    verify_evidence_integrity,
    
    # Serialization
    serialize_evidence,
    deserialize_evidence,
    JSONEncoder,
)

# Storage primitives that will be available when implemented
__all__ = [
    # From schema.py
    "SchemaVersion",
    "EvidenceType",
    "IntegrityStatus",
    "HashAlgorithm",
    "ContentHash",
    "StorageContext",
    "EvidenceMetadata",
    "FileObservation",
    "DirectoryObservation",
    "ImportObservation",
    "ExportObservation",
    "BoundaryObservation",
    "EncodingObservation",
    "Anchor",
    "Snapshot",
    "NotebookEntry",
    "StoredEvidence",
    "validate_evidence_structure",
    "compute_evidence_hash",
    "verify_evidence_integrity",
    "serialize_evidence",
    "deserialize_evidence",
    "JSONEncoder",
    
    # Placeholders for other modules (will be added when implemented)
    # "atomic_write",
    # "atomic_read",
    # "get_storage_path",
    # "detect_corruption",
    # "migrate_schema",
]


# === STORAGE ERROR HIERARCHY ===
# Note: These are defined here since they're part of the public contract,
# but specific error types will be defined in their respective modules.

class StorageError(Exception):
    """Base exception for all storage-related errors."""
    pass


class AtomicWriteError(StorageError):
    """Raised when atomic write operations fail."""
    pass


class SchemaError(StorageError):
    """Base exception for schema-related errors."""
    pass


class ValidationError(SchemaError):
    """Raised when validation fails."""
    pass


class VersionMismatchError(SchemaError):
    """Raised when schema version does not match."""
    pass


class HashMismatchError(SchemaError):
    """Raised when content hash does not match."""
    pass


class MissingRequiredFieldError(ValidationError):
    """Raised when a required field is missing."""
    pass


class TypeMismatchError(ValidationError):
    """Raised when a field has the wrong type."""
    pass


class ConstraintViolationError(ValidationError):
    """Raised when a constraint is violated."""
    pass


class LayoutError(StorageError):
    """Raised when storage layout operations fail."""
    pass


class CorruptionError(StorageError):
    """Raised when data corruption is detected."""
    pass


class MigrationError(StorageError):
    """Raised when migration operations fail."""
    pass


# === PUBLIC CONTRACT ===

def atomic_write(data: bytes, path: str) -> None:
    """Atomically write data to a file.
    
    This is a placeholder that will be implemented in atomic.py.
    """
    raise NotImplementedError("atomic_write will be implemented in storage.atomic")


def atomic_read(path: str) -> bytes:
    """Atomically read data from a file.
    
    This is a placeholder that will be implemented in atomic.py.
    """
    raise NotImplementedError("atomic_read will be implemented in storage.atomic")


def get_storage_path(investigation_id: str, evidence_type: str) -> str:
    """Get the storage path for an evidence type.
    
    This is a placeholder that will be implemented in layout.py.
    """
    raise NotImplementedError("get_storage_path will be implemented in storage.layout")


def detect_corruption(data: bytes, expected_hash: str) -> bool:
    """Detect if data has been corrupted.
    
    This is a placeholder that will be implemented in corruption.py.
    """
    raise NotImplementedError("detect_corruption will be implemented in storage.corruption")


def migrate_schema(old_data: bytes, from_version: SchemaVersion, to_version: SchemaVersion) -> bytes:
    """Migrate data from one schema version to another.
    
    This is a placeholder that will be implemented in migration.py.
    """
    raise NotImplementedError("migrate_schema will be implemented in storage.migration")


# Add error classes to exports
__all__.extend([
    "StorageError",
    "AtomicWriteError",
    "SchemaError",
    "ValidationError",
    "VersionMismatchError",
    "HashMismatchError",
    "MissingRequiredFieldError",
    "TypeMismatchError",
    "ConstraintViolationError",
    "LayoutError",
    "CorruptionError",
    "MigrationError",
    
    # Placeholder functions
    "atomic_write",
    "atomic_read",
    "get_storage_path",
    "detect_corruption",
    "migrate_schema",
])