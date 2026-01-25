"""
observations/record/anchors.py

Stable reference points for snapshots.

Anchors answer: "What do multiple snapshots agree is the same thing?"
Paths change. Files move. Names lie. Anchors persist.

This module defines stable identifiers:
- Content hashes (what something is)
- Structural hashes (how something is organized)
- Semantic-neutral fingerprints (identity without location)

Production principle: Anchors turn snapshots into a chain of custody.
"""

import hashlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
)
from uuid import UUID

# Import for type hints only
if TYPE_CHECKING:
    from observations.record.snapshot import Snapshot

# ============================================================================
# ANCHOR TYPES
# ============================================================================


class AnchorType(str, Enum):
    """Types of anchors for different entities."""

    FILE = "file"  # Individual file
    DIRECTORY = "directory"  # Directory structure
    MODULE = "module"  # Python module/package
    ARTIFACT = "artifact"  # Build artifact or generated file
    TEXT_BLOCK = "text_block"  # Specific block of text within a file

    @classmethod
    def from_path(cls, path: str | Path) -> "AnchorType":
        """Determine anchor type from path."""
        path_obj = Path(path)

        if path_obj.is_dir():
            return cls.DIRECTORY
        elif path_obj.is_file():
            # Check if it's a Python module
            if path_obj.suffix == ".py":
                return cls.MODULE
            # Check for common artifact patterns
            artifact_patterns = [
                r"\.pyc$",
                r"\.so$",
                r"\.pyd$",
                r"__pycache__",
                r"\.egg$",
                r"\.whl$",
                r"build/",
                r"dist/",
                r"\.git/",
            ]
            path_str = str(path_obj)
            for pattern in artifact_patterns:
                if re.search(pattern, path_str):
                    return cls.ARTIFACT
            return cls.FILE
        else:
            # Doesn't exist or special file
            return cls.FILE  # Default


class ContentFingerprintMethod(str, Enum):
    """Methods for generating content fingerprints."""

    FULL_CONTENT_SHA256 = "full_content_sha256"
    LINE_HASH_MERKLE = "line_hash_merkle"
    STRUCTURAL_SKELETON = "structural_skeleton"
    IMPORT_SIGNATURE = "import_signature"
    AST_HASH = "ast_hash"  # Abstract Syntax Tree hash (semantic-neutral)

    @property
    def description(self) -> str:
        """Human-readable description of the method."""
        descriptions = {
            self.FULL_CONTENT_SHA256: "SHA-256 hash of entire file content",
            self.LINE_HASH_MERKLE: "Merkle tree of individual line hashes",
            self.STRUCTURAL_SKELETON: "Hash of structural elements (ignoring content)",
            self.IMPORT_SIGNATURE: "Hash of import statements and signatures",
            self.AST_HASH: "Hash of AST with normalized identifiers",
        }
        return descriptions[self]

    @classmethod
    def default_for_type(cls, anchor_type: AnchorType) -> "ContentFingerprintMethod":
        """Get default fingerprint method for an anchor type."""
        defaults = {
            AnchorType.FILE: cls.FULL_CONTENT_SHA256,
            AnchorType.DIRECTORY: cls.STRUCTURAL_SKELETON,
            AnchorType.MODULE: cls.AST_HASH,  # For code, AST provides best semantic-neutral identity
            AnchorType.ARTIFACT: cls.FULL_CONTENT_SHA256,
            AnchorType.TEXT_BLOCK: cls.LINE_HASH_MERKLE,
        }
        return defaults.get(anchor_type, cls.FULL_CONTENT_SHA256)


# ============================================================================
# CORE ANCHOR CLASSES
# ============================================================================


@dataclass(frozen=True)
class AnchorMetadata:
    """Metadata about how an anchor was generated."""

    generated_at: datetime
    method: ContentFingerprintMethod
    algorithm: str  # Hash algorithm used
    parameters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        method: ContentFingerprintMethod,
        algorithm: str = "sha256",
        parameters: dict[str, Any] | None = None,
    ) -> "AnchorMetadata":
        """Create metadata with current timestamp."""
        return cls(
            generated_at=datetime.now(UTC),
            method=method,
            algorithm=algorithm,
            parameters=parameters or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "method": self.method.value,
            "algorithm": self.algorithm,
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnchorMetadata":
        """Create from dictionary."""
        return cls(
            generated_at=datetime.fromisoformat(data["generated_at"]),
            method=ContentFingerprintMethod(data["method"]),
            algorithm=data["algorithm"],
            parameters=data.get("parameters", {}),
        )


@dataclass(frozen=True)
class Anchor:
    """
    Base class for all anchors.

    An anchor is a stable identifier for an entity that persists
    across snapshots, even when location or superficial details change.
    """

    # Core identification
    identifier: str  # Unique, deterministic identifier
    anchor_type: AnchorType

    # Content fingerprint
    content_fingerprint: str  # Hash/fingerprint of content/structure
    fingerprint_method: ContentFingerprintMethod

    # Metadata
    metadata: AnchorMetadata

    # Context
    original_path: str | None = None  # Path at observation time (for reference only)
    relative_path: str | None = None  # Relative path from source root

    # Versioning
    version: int = 1  # Anchor format version

    # Extended fingerprints (for cross-method verification)
    auxiliary_fingerprints: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate anchor after creation."""
        # Validate identifier is not empty
        if not self.identifier:
            raise ValueError("Anchor identifier cannot be empty")

        # Validate fingerprint is not empty
        if not self.content_fingerprint:
            raise ValueError("Content fingerprint cannot be empty")

        # Validate identifier follows pattern: type:hash
        if ":" not in self.identifier:
            raise ValueError(f"Invalid identifier format: {self.identifier}")

        # Validate timestamp is timezone-aware
        if self.metadata.generated_at.tzinfo is None:
            raise ValueError("Metadata timestamp must be timezone-aware")

    @property
    def is_file(self) -> bool:
        """Check if this is a file anchor."""
        return self.anchor_type == AnchorType.FILE

    @property
    def is_directory(self) -> bool:
        """Check if this is a directory anchor."""
        return self.anchor_type == AnchorType.DIRECTORY

    @property
    def is_module(self) -> bool:
        """Check if this is a module anchor."""
        return self.anchor_type == AnchorType.MODULE

    @property
    def is_artifact(self) -> bool:
        """Check if this is an artifact anchor."""
        return self.anchor_type == AnchorType.ARTIFACT

    def to_dict(self) -> dict[str, Any]:
        """Convert anchor to JSON-serializable dictionary."""
        return {
            "identifier": self.identifier,
            "anchor_type": self.anchor_type.value,
            "content_fingerprint": self.content_fingerprint,
            "fingerprint_method": self.fingerprint_method.value,
            "original_path": self.original_path,
            "relative_path": self.relative_path,
            "metadata": self.metadata.to_dict(),
            "version": self.version,
            "auxiliary_fingerprints": self.auxiliary_fingerprints,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Anchor":
        """Create anchor from dictionary."""
        return cls(
            identifier=data["identifier"],
            anchor_type=AnchorType(data["anchor_type"]),
            content_fingerprint=data["content_fingerprint"],
            fingerprint_method=ContentFingerprintMethod(data["fingerprint_method"]),
            original_path=data.get("original_path"),
            relative_path=data.get("relative_path"),
            metadata=AnchorMetadata.from_dict(data["metadata"]),
            version=data.get("version", 1),
            auxiliary_fingerprints=data.get("auxiliary_fingerprints", {}),
        )

    def __eq__(self, other: Any) -> bool:
        """Anchors are equal if their identifiers match."""
        if not isinstance(other, Anchor):
            return False
        return self.identifier == other.identifier

    def __hash__(self) -> int:
        """Hash based on identifier."""
        return hash(self.identifier)

    def __str__(self) -> str:
        """Human-readable string representation."""
        path_display = self.relative_path or self.original_path or "unknown"
        return (
            f"{self.anchor_type.value}:{self.content_fingerprint[:16]} ({path_display})"
        )

    def summary(self) -> str:
        """Get detailed summary."""
        lines = [
            f"Anchor: {self.identifier}",
            f"Type: {self.anchor_type.value}",
            f"Fingerprint: {self.content_fingerprint[:32]}...",
            f"Method: {self.fingerprint_method.value}",
            f"Generated: {self.metadata.generated_at.isoformat()[:19]}Z",
        ]

        if self.original_path:
            lines.append(f"Original: {self.original_path}")

        if self.relative_path:
            lines.append(f"Relative: {self.relative_path}")

        if self.auxiliary_fingerprints:
            lines.append("Auxiliary fingerprints:")
            for method, fp in self.auxiliary_fingerprints.items():
                lines.append(f"  {method}: {fp[:16]}...")

        return "\n".join(lines)


# ============================================================================
# ANCHOR GENERATORS
# ============================================================================


class AnchorGenerator(ABC):
    """Abstract base class for anchor generators."""

    @abstractmethod
    def generate(self, path: str | Path, **kwargs: Any) -> Anchor:
        """Generate an anchor for the given path."""
        pass

    @property
    @abstractmethod
    def method(self) -> ContentFingerprintMethod:
        """Get the fingerprint method used by this generator."""
        pass


class FileContentAnchorGenerator(AnchorGenerator):
    """Generate anchors based on full file content hash."""

    def __init__(self, algorithm: str = "sha256", chunk_size: int = 8192):
        self._algorithm = algorithm
        self._chunk_size = chunk_size

    @property
    def method(self) -> ContentFingerprintMethod:
        return ContentFingerprintMethod.FULL_CONTENT_SHA256

    def generate(self, path: str | Path, **kwargs: Any) -> Anchor:
        """Generate anchor by hashing entire file content."""
        path_obj = Path(path)

        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Compute hash
        hasher = hashlib.new(self._algorithm)

        try:
            with open(path_obj, "rb") as f:
                while chunk := f.read(self._chunk_size):
                    hasher.update(chunk)
        except OSError as e:
            raise ValueError(f"Cannot read file {path}: {e}") from e

        content_hash = hasher.hexdigest()

        # Create identifier
        identifier = f"file:{self._algorithm}:{content_hash}"

        # Get relative path if base path provided
        relative_path = None
        if "base_path" in kwargs:
            try:
                relative_path = str(Path(path).relative_to(kwargs["base_path"]))
            except ValueError:
                # Path is not relative to base
                pass

        return Anchor(
            identifier=identifier,
            anchor_type=AnchorType.FILE,
            content_fingerprint=content_hash,
            fingerprint_method=self.method,
            original_path=str(path_obj.absolute()),
            relative_path=relative_path,
            metadata=AnchorMetadata.create(
                method=self.method,
                algorithm=self._algorithm,
                parameters={"chunk_size": self._chunk_size},
            ),
        )


class LineHashMerkleAnchorGenerator(AnchorGenerator):
    """Generate anchors using Merkle tree of line hashes."""

    def __init__(self, algorithm: str = "sha256", normalize_whitespace: bool = True):
        self._algorithm = algorithm
        self._normalize_whitespace = normalize_whitespace

    @property
    def method(self) -> ContentFingerprintMethod:
        return ContentFingerprintMethod.LINE_HASH_MERKLE

    def generate(self, path: str | Path, **kwargs: Any) -> Anchor:
        """Generate anchor using Merkle tree of lines."""
        path_obj = Path(path)

        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Read and process lines
        try:
            with open(path_obj, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except (OSError, UnicodeError) as e:
            raise ValueError(f"Cannot read file {path}: {e}") from e

        # Normalize lines if requested
        if self._normalize_whitespace:
            lines = [line.rstrip() for line in lines]

        # Compute hash for each line
        line_hashes = []
        hasher = hashlib.new(self._algorithm)

        for line in lines:
            hasher.update(line.encode("utf-8"))
            line_hashes.append(hasher.hexdigest())
            hasher = hashlib.new(self._algorithm)  # Reset for next line

        # Build Merkle tree
        if not line_hashes:
            # Empty file - hash of empty string
            root_hash = hashlib.new(self._algorithm).hexdigest()
        else:
            root_hash = self._build_merkle_tree(line_hashes)

        # Create identifier
        identifier = f"merkle:{self._algorithm}:{root_hash}"

        # Get relative path
        relative_path = None
        if "base_path" in kwargs:
            try:
                relative_path = str(Path(path).relative_to(kwargs["base_path"]))
            except ValueError:
                pass

        # Also compute full content hash as auxiliary fingerprint
        full_content_hasher = hashlib.new(self._algorithm)
        with open(path_obj, "rb") as f:
            while chunk := f.read(8192):
                full_content_hasher.update(chunk)

        return Anchor(
            identifier=identifier,
            anchor_type=AnchorType.FILE,
            content_fingerprint=root_hash,
            fingerprint_method=self.method,
            original_path=str(path_obj.absolute()),
            relative_path=relative_path,
            metadata=AnchorMetadata.create(
                method=self.method,
                algorithm=self._algorithm,
                parameters={
                    "normalize_whitespace": self._normalize_whitespace,
                    "line_count": len(lines),
                },
            ),
            auxiliary_fingerprints={"full_content": full_content_hasher.hexdigest()},
        )

    def _build_merkle_tree(self, hashes: list[str]) -> str:
        """Build a Merkle tree from leaf hashes."""
        if not hashes:
            return hashlib.new(self._algorithm).digest().hex()

        current_level = hashes

        while len(current_level) > 1:
            next_level = []

            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Combine two hashes
                    combined = current_level[i] + current_level[i + 1]
                    hash_val = hashlib.new(
                        self._algorithm, combined.encode()
                    ).hexdigest()
                else:
                    # Odd number - duplicate last hash
                    combined = current_level[i] + current_level[i]
                    hash_val = hashlib.new(
                        self._algorithm, combined.encode()
                    ).hexdigest()

                next_level.append(hash_val)

            current_level = next_level

        return current_level[0]


class DirectoryStructureAnchorGenerator(AnchorGenerator):
    """Generate anchors for directory structures."""

    def __init__(
        self,
        algorithm: str = "sha256",
        exclude_patterns: list[str] | None = None,
        max_depth: int | None = 10,
    ):
        self._algorithm = algorithm
        self._exclude_patterns = exclude_patterns or [
            r"^\.git$",
            r"^__pycache__$",
            r"^\.pytest_cache$",
            r"^node_modules$",
            r"^\.venv$",
            r"^venv$",
            r"^env$",
            r"^\.idea$",
            r"^\.vscode$",
            r"^\.DS_Store$",
        ]
        self._max_depth = max_depth
        self._file_generator = FileContentAnchorGenerator(algorithm)

    @property
    def method(self) -> ContentFingerprintMethod:
        return ContentFingerprintMethod.STRUCTURAL_SKELETON

    def generate(self, path: str | Path, **kwargs: Any) -> Anchor:
        """Generate anchor for directory structure."""
        path_obj = Path(path)

        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        # Build structural representation
        structure = self._capture_structure(path_obj, depth=0)

        # Create canonical JSON representation
        structure_json = json.dumps(structure, sort_keys=True, separators=(",", ":"))

        # Hash the structure
        hasher = hashlib.new(self._algorithm)
        hasher.update(structure_json.encode("utf-8"))
        structure_hash = hasher.hexdigest()

        # Create identifier
        identifier = f"dir:{self._algorithm}:{structure_hash}"

        # Get relative path
        relative_path = None
        if "base_path" in kwargs:
            try:
                relative_path = str(Path(path).relative_to(kwargs["base_path"]))
            except ValueError:
                pass

        return Anchor(
            identifier=identifier,
            anchor_type=AnchorType.DIRECTORY,
            content_fingerprint=structure_hash,
            fingerprint_method=self.method,
            original_path=str(path_obj.absolute()),
            relative_path=relative_path,
            metadata=AnchorMetadata.create(
                method=self.method,
                algorithm=self._algorithm,
                parameters={
                    "exclude_patterns": self._exclude_patterns,
                    "max_depth": self._max_depth,
                },
            ),
        )

    def _capture_structure(self, directory: Path, depth: int) -> dict[str, Any]:
        """Recursively capture directory structure."""
        if self._max_depth is not None and depth >= self._max_depth:
            return {"name": directory.name, "type": "directory", "truncated": True}

        result = {"name": directory.name, "type": "directory", "contents": []}

        try:
            items = sorted(directory.iterdir(), key=lambda p: p.name.lower())

            for item in items:
                # Check if item should be excluded
                if self._should_exclude(item):
                    continue

                if item.is_dir():
                    # Recursively capture subdirectory
                    subdir_structure = self._capture_structure(item, depth + 1)
                    result["contents"].append(subdir_structure)
                elif item.is_file():
                    # Capture file with basic metadata
                    stat = item.stat()
                    file_info = {
                        "name": item.name,
                        "type": "file",
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "extension": item.suffix.lower(),
                    }
                    result["contents"].append(file_info)
                # Note: symlinks and special files are ignored

        except (OSError, PermissionError) as e:
            result["error"] = str(e)

        return result

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        for pattern in self._exclude_patterns:
            if re.match(pattern, path.name):
                return True
        return False


class PythonASTAnchorGenerator(AnchorGenerator):
    """Generate anchors for Python modules using AST."""

    def __init__(
        self,
        algorithm: str = "sha256",
        normalize_identifiers: bool = True,
        ignore_comments: bool = True,
        ignore_docstrings: bool = True,
    ):
        self._algorithm = algorithm
        self._normalize_identifiers = normalize_identifiers
        self._ignore_comments = ignore_comments
        self._ignore_docstrings = ignore_docstrings

    @property
    def method(self) -> ContentFingerprintMethod:
        return ContentFingerprintMethod.AST_HASH

    def generate(self, path: str | Path, **kwargs: Any) -> Anchor:
        """Generate anchor using Python AST."""
        path_obj = Path(path)

        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

        if path_obj.suffix != ".py":
            raise ValueError(f"Not a Python file: {path}")

        try:
            import ast
        except ImportError as e:
            raise RuntimeError("AST module not available") from e

        # Read file
        try:
            source = path_obj.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeError) as e:
            raise ValueError(f"Cannot read file {path}: {e}") from e

        # Parse AST
        try:
            tree = ast.parse(source, filename=path_obj.name)
        except SyntaxError:
            # Invalid Python - use simplified representation
            ast_hash = self._hash_fallback(source)
        else:
            # Normalize AST
            normalized = self._normalize_ast(tree)
            # Convert to string representation
            ast_str = ast.dump(normalized, annotate_fields=False)
            # Hash the AST string
            hasher = hashlib.new(self._algorithm)
            hasher.update(ast_str.encode("utf-8"))
            ast_hash = hasher.hexdigest()

        # Create identifier
        identifier = f"python:{self._algorithm}:{ast_hash}"

        # Get relative path
        relative_path = None
        if "base_path" in kwargs:
            try:
                relative_path = str(Path(path).relative_to(kwargs["base_path"]))
            except ValueError:
                pass

        # Also compute line-based Merkle hash as auxiliary
        line_generator = LineHashMerkleAnchorGenerator(self._algorithm)
        try:
            line_anchor = line_generator.generate(path, **kwargs)
            auxiliary_fingerprints = {"line_merkle": line_anchor.content_fingerprint}
        except Exception:
            auxiliary_fingerprints = {}

        return Anchor(
            identifier=identifier,
            anchor_type=AnchorType.MODULE,
            content_fingerprint=ast_hash,
            fingerprint_method=self.method,
            original_path=str(path_obj.absolute()),
            relative_path=relative_path,
            metadata=AnchorMetadata.create(
                method=self.method,
                algorithm=self._algorithm,
                parameters={
                    "normalize_identifiers": self._normalize_identifiers,
                    "ignore_comments": self._ignore_comments,
                    "ignore_docstrings": self._ignore_docstrings,
                },
            ),
            auxiliary_fingerprints=auxiliary_fingerprints,
        )

    def _normalize_ast(self, node: Any) -> Any:
        """Normalize AST by removing variable content."""
        import ast

        if isinstance(node, ast.Module):
            # Process body
            node.body = [self._normalize_ast(child) for child in node.body]
            return node

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Normalize name to generic identifier
            node.name = (
                f"func_{hash(node.name) & 0xFFFF:04x}"
                if self._normalize_identifiers
                else node.name
            )
            node.body = [self._normalize_ast(child) for child in node.body]
            if self._ignore_docstrings and ast.get_docstring(node):
                # Remove docstring if present
                if node.body and isinstance(node.body[0], ast.Expr):
                    node.body = node.body[1:]
            return node

        elif isinstance(node, ast.Name):
            if self._normalize_identifiers:
                node.id = f"id_{hash(node.id) & 0xFFFF:04x}"
            return node

        elif isinstance(node, ast.arg):
            if self._normalize_identifiers:
                node.arg = f"arg_{hash(node.arg) & 0xFFFF:04x}"
            return node

        elif isinstance(node, ast.Attribute):
            node.value = self._normalize_ast(node.value)
            if self._normalize_identifiers:
                node.attr = f"attr_{hash(node.attr) & 0xFFFF:04x}"
            return node

        elif isinstance(node, ast.Str):
            # Replace string literals with placeholder
            if self._ignore_docstrings and isinstance(
                node.parent, getattr(ast, "Expr", type(None))
            ):
                # This might be a docstring
                return ast.Pass()  # Placeholder
            return ast.Str(s="<string_literal>")

        elif isinstance(node, ast.Num):
            # Replace numbers with placeholder
            return ast.Num(n=0)

        elif isinstance(node, ast.Constant):
            # Python 3.8+ constant node
            if isinstance(node.value, str):
                return ast.Constant(value="<string_literal>")
            elif isinstance(node.value, (int, float, complex)):
                return ast.Constant(value=0)
            else:
                return ast.Constant(value=None)

        elif isinstance(node, ast.List):
            node.elts = [self._normalize_ast(child) for child in node.elts]
            return node

        elif isinstance(node, ast.Dict):
            node.keys = [self._normalize_ast(child) for child in node.keys]
            node.values = [self._normalize_ast(child) for child in node.values]
            return node

        # For other nodes, recursively process children
        for field_name, field_value in ast.iter_fields(node):
            if isinstance(field_value, list):
                setattr(
                    node,
                    field_name,
                    [self._normalize_ast(child) for child in field_value],
                )
            elif isinstance(field_value, ast.AST):
                setattr(node, field_name, self._normalize_ast(field_value))

        return node

    def _hash_fallback(self, source: str) -> str:
        """Fallback hash for non-parsable Python files."""
        # Remove comments and normalize whitespace
        lines = source.split("\n")
        cleaned = []

        for line in lines:
            # Remove inline comments
            if "#" in line:
                line = line.split("#")[0]
            line = line.strip()
            if line:
                cleaned.append(line)

        cleaned_source = "\n".join(cleaned)

        hasher = hashlib.new(self._algorithm)
        hasher.update(cleaned_source.encode("utf-8"))
        return hasher.hexdigest()


# ============================================================================
# ANCHOR REGISTRY AND FACTORY
# ============================================================================


class AnchorFactory:
    """Factory for creating anchors with appropriate generators."""

    _generators: dict[ContentFingerprintMethod, AnchorGenerator] = {}

    @classmethod
    def register_generator(
        cls, method: ContentFingerprintMethod, generator: AnchorGenerator
    ) -> None:
        """Register a generator for a fingerprint method."""
        cls._generators[method] = generator

    @classmethod
    def get_generator(cls, method: ContentFingerprintMethod) -> AnchorGenerator:
        """Get generator for a method."""
        if method not in cls._generators:
            # Create default generators
            defaults = {
                ContentFingerprintMethod.FULL_CONTENT_SHA256: FileContentAnchorGenerator(),
                ContentFingerprintMethod.LINE_HASH_MERKLE: LineHashMerkleAnchorGenerator(),
                ContentFingerprintMethod.STRUCTURAL_SKELETON: DirectoryStructureAnchorGenerator(),
                ContentFingerprintMethod.AST_HASH: PythonASTAnchorGenerator(),
                ContentFingerprintMethod.IMPORT_SIGNATURE: FileContentAnchorGenerator(),  # TODO: Implement
            }
            if method in defaults:
                cls._generators[method] = defaults[method]
            else:
                raise ValueError(f"No generator for method: {method}")

        return cls._generators[method]

    @classmethod
    def create_anchor(
        cls,
        path: str | Path,
        method: ContentFingerprintMethod | None = None,
        **kwargs: Any,
    ) -> Anchor:
        """
        Create anchor for a path.

        Args:
            path: Path to file or directory
            method: Fingerprint method to use (default: based on type)
            **kwargs: Additional arguments for generator

        Returns:
            Anchor for the path
        """
        path_obj = Path(path)

        # Determine anchor type
        anchor_type = AnchorType.from_path(path_obj)

        # Determine method if not specified
        if method is None:
            method = ContentFingerprintMethod.default_for_type(anchor_type)

        # Get generator and create anchor
        generator = cls.get_generator(method)
        return generator.generate(path_obj, **kwargs)

    @classmethod
    def create_anchors_for_snapshot(
        cls, snapshot: "Snapshot", method: ContentFingerprintMethod | None = None
    ) -> list[Anchor]:
        """
        Create anchors for all files in a snapshot.

        Args:
            snapshot: Snapshot to create anchors for
            method: Fingerprint method to use (default: based on type)

        Returns:
            List of anchors
        """
        anchors: list[Anchor] = []
        Path(snapshot.source_path)

        # We need to extract file paths from snapshot observations
        # For now, this is a placeholder - will be implemented when we have
        # observation data structure

        # TODO: Extract file paths from snapshot observations
        # This will depend on the observation structure

        return anchors


# ============================================================================
# ANCHOR SET OPERATIONS
# ============================================================================


@dataclass(frozen=True)
class AnchorSet:
    """A set of anchors with operations for comparison."""

    anchors: frozenset[Anchor]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_list(cls, anchors: list[Anchor]) -> "AnchorSet":
        """Create AnchorSet from list of anchors."""
        return cls(anchors=frozenset(anchors))

    def to_list(self) -> list[Anchor]:
        """Convert to sorted list of anchors."""
        return sorted(self.anchors, key=lambda a: a.identifier)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "anchors": [anchor.to_dict() for anchor in self.to_list()],
            "created_at": self.created_at.isoformat(),
            "count": len(self.anchors),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnchorSet":
        """Create AnchorSet from dictionary."""
        anchors = [Anchor.from_dict(anchor_dict) for anchor_dict in data["anchors"]]
        created_at = datetime.fromisoformat(data["created_at"])
        return cls(anchors=frozenset(anchors), created_at=created_at)

    @property
    def count(self) -> int:
        """Number of anchors in set."""
        return len(self.anchors)

    @property
    def by_type(self) -> dict[AnchorType, list[Anchor]]:
        """Group anchors by type."""
        groups: dict[AnchorType, list[Anchor]] = {}
        for anchor in self.anchors:
            groups.setdefault(anchor.anchor_type, []).append(anchor)
        return groups

    def get_anchor(self, identifier: str) -> Anchor | None:
        """Get anchor by identifier."""
        for anchor in self.anchors:
            if anchor.identifier == identifier:
                return anchor
        return None

    def find_anchors_by_path(
        self, path: str | Path, exact: bool = True
    ) -> list[Anchor]:
        """Find anchors by original or relative path."""
        path_str = str(path)
        results = []

        for anchor in self.anchors:
            if exact:
                if anchor.original_path == path_str or anchor.relative_path == path_str:
                    results.append(anchor)
            else:
                if (anchor.original_path and path_str in anchor.original_path) or (
                    anchor.relative_path and path_str in anchor.relative_path
                ):
                    results.append(anchor)

        return results

    def compare(self, other: "AnchorSet") -> "AnchorComparison":
        """Compare this anchor set with another."""
        return AnchorComparison(self, other)


@dataclass(frozen=True)
class AnchorComparison:
    """Result of comparing two anchor sets."""

    set_a: AnchorSet
    set_b: AnchorSet

    # Pre-computed sets for efficiency
    _anchors_a: frozenset[str] = field(init=False)
    _anchors_b: frozenset[str] = field(init=False)

    def __post_init__(self) -> None:
        """Pre-compute identifier sets."""
        # Use object.__setattr__ because dataclass is frozen
        object.__setattr__(
            self, "_anchors_a", frozenset(a.identifier for a in self.set_a.anchors)
        )
        object.__setattr__(
            self, "_anchors_b", frozenset(a.identifier for a in self.set_b.anchors)
        )

    @property
    def common_anchors(self) -> frozenset[Anchor]:
        """Anchors present in both sets."""
        common_ids = self._anchors_a & self._anchors_b
        return frozenset(a for a in self.set_a.anchors if a.identifier in common_ids)

    @property
    def unique_to_a(self) -> frozenset[Anchor]:
        """Anchors only in set A."""
        unique_ids = self._anchors_a - self._anchors_b
        return frozenset(a for a in self.set_a.anchors if a.identifier in unique_ids)

    @property
    def unique_to_b(self) -> frozenset[Anchor]:
        """Anchors only in set B."""
        unique_ids = self._anchors_b - self._anchors_a
        return frozenset(a for a in self.set_b.anchors if a.identifier in unique_ids)

    @property
    def similarity(self) -> float:
        """Jaccard similarity between anchor sets."""
        if not self._anchors_a and not self._anchors_b:
            return 1.0  # Both empty

        intersection = len(self._anchors_a & self._anchors_b)
        union = len(self._anchors_a | self._anchors_b)

        return intersection / union if union > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert comparison to dictionary."""
        return {
            "set_a_count": self.set_a.count,
            "set_b_count": self.set_b.count,
            "common_count": len(self.common_anchors),
            "unique_to_a_count": len(self.unique_to_a),
            "unique_to_b_count": len(self.unique_to_b),
            "similarity": self.similarity,
            "common_anchors": [
                a.to_dict()
                for a in sorted(self.common_anchors, key=lambda x: x.identifier)
            ],
            "unique_to_a": [
                a.to_dict()
                for a in sorted(self.unique_to_a, key=lambda x: x.identifier)
            ],
            "unique_to_b": [
                a.to_dict()
                for a in sorted(self.unique_to_b, key=lambda x: x.identifier)
            ],
        }

    def summary(self) -> str:
        """Human-readable summary of comparison."""
        lines = [
            "Anchor Comparison:",
            f"  Set A: {self.set_a.count} anchors",
            f"  Set B: {self.set_b.count} anchors",
            f"  Common: {len(self.common_anchors)} anchors",
            f"  Unique to A: {len(self.unique_to_a)} anchors",
            f"  Unique to B: {len(self.unique_to_b)} anchors",
            f"  Similarity: {self.similarity:.3f}",
        ]

        # Show breakdown by type for common anchors
        common_by_type: dict[AnchorType, int] = {}
        for anchor in self.common_anchors:
            common_by_type[anchor.anchor_type] = (
                common_by_type.get(anchor.anchor_type, 0) + 1
            )

        if common_by_type:
            lines.append("  Common by type:")
            for anchor_type, count in sorted(common_by_type.items()):
                lines.append(f"    {anchor_type.value}: {count}")

        return "\n".join(lines)


# ============================================================================
# PUBLIC API
# ============================================================================


def create_anchor(
    path: str | Path, method: ContentFingerprintMethod | None = None, **kwargs: Any
) -> Anchor:
    """
    Create an anchor for a file or directory.

    Args:
        path: Path to file or directory
        method: Fingerprint method to use (default: auto-detect)
        **kwargs: Additional arguments for generator

    Returns:
        Anchor for the path
    """
    return AnchorFactory.create_anchor(path, method, **kwargs)


def compare_anchor_sets(set_a: AnchorSet, set_b: AnchorSet) -> AnchorComparison:
    """
    Compare two anchor sets.

    Args:
        set_a: First anchor set
        set_b: Second anchor set

    Returns:
        Comparison results
    """
    return set_a.compare(set_b)


def verify_anchor_consistency(anchor: Anchor) -> tuple[bool, str | None]:
    """
    Verify that an anchor is internally consistent.

    Args:
        anchor: Anchor to verify

    Returns:
        Tuple of (is_consistent: bool, reason: Optional[str])
    """
    try:
        # Recreate identifier to verify format
        if ":" not in anchor.identifier:
            return False, "Identifier missing colon separator"

        # Verify fingerprint method matches
        if not isinstance(anchor.fingerprint_method, ContentFingerprintMethod):
            return False, "Invalid fingerprint method"

        # Verify metadata
        if anchor.metadata.generated_at.tzinfo is None:
            return False, "Metadata timestamp is timezone-naive"

        return True, None

    except Exception as e:
        return False, f"Verification error: {str(e)}"


def compute_anchors_for_snapshot(snapshot: "Snapshot") -> list[Anchor]:
    """
    Compute anchors for all files in a snapshot.

    This is the main function to call after creating a snapshot.

    Args:
        snapshot: Snapshot to compute anchors for

    Returns:
        List of anchors for the snapshot
    """
    # TODO: Implement based on snapshot observation data
    # For now, return empty list
    return []


# ============================================================================
# INITIALIZATION
# ============================================================================

# Register default generators
AnchorFactory.register_generator(
    ContentFingerprintMethod.FULL_CONTENT_SHA256, FileContentAnchorGenerator()
)

AnchorFactory.register_generator(
    ContentFingerprintMethod.LINE_HASH_MERKLE, LineHashMerkleAnchorGenerator()
)

AnchorFactory.register_generator(
    ContentFingerprintMethod.STRUCTURAL_SKELETON, DirectoryStructureAnchorGenerator()
)

AnchorFactory.register_generator(
    ContentFingerprintMethod.AST_HASH, PythonASTAnchorGenerator()
)

# ============================================================================
# UTILITIES
# ============================================================================


def get_anchor(storage_path: str, snapshot_id: UUID, anchor_id: str) -> Anchor | None:
    """
    Retrieve an anchor from a stored snapshot.

    Args:
        storage_path: Path to observation storage
        snapshot_id: ID of snapshot
        anchor_id: ID of anchor to find

    Returns:
        Anchor object or None if not found
    """
    try:
        base_path = Path(storage_path)
        # Try standard locations
        candidates = [
            base_path / "snapshots" / f"{snapshot_id}.json",
            base_path / f"{snapshot_id}.json",
        ]

        target_file = None
        for candidate in candidates:
            if candidate.exists():
                target_file = candidate
                break

        if not target_file:
            return None

        # Load snapshot (just needed parts)
        with open(target_file, encoding="utf-8") as f:
            data = json.load(f)

        if "anchors" not in data:
            return None

        # Find anchor
        for anchor_dict in data["anchors"]:
            if anchor_dict.get("identifier") == anchor_id:
                return Anchor.from_dict(anchor_dict)

        return None

    except Exception:
        return None


def validate_anchor_reference(anchor: Anchor, snapshot_id: UUID) -> bool:
    """
    Validate that an anchor correctly references a snapshot.

    Since Anchor doesn't currently store snapshot_id, this is a placeholder
    for future consistency checks (e.g. verifying anchor validity against
    snapshot integrity).
    """
    if not isinstance(anchor, Anchor):
        return False
    # In future: check if anchor.snapshot_ref == snapshot_id
    return True


# Alias for compatibility
ObservationAnchor = Anchor

__all__ = [
    "Anchor",
    "ObservationAnchor",
    "AnchorType",
    "get_anchor",
    "validate_anchor_reference",
]
