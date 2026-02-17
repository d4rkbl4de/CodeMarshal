"""
semantic_sight.py - Semantic code observation and indexing.

Purpose:
    Index code for semantic search by computing embeddings.
    Provides semantic context for investigation.

Constitutional Basis:
    - Article 1: Observation Purity (embeddings are observations)
    - Article 9: Immutable Observations (embeddings stored immutably)
    - Article 14: Graceful Degradation (fallback when models unavailable)

Features:
    - Code-aware semantic indexing
    - Function/class signature extraction
    - Incremental indexing
    - Embedding persistence
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore[assignment]
    NUMPY_AVAILABLE = False

from observations.eyes.base import AbstractEye, ObservationResult

# Try to import semantic search
try:
    from core.search.semantic_search import (
        SENTENCE_TRANSFORMERS_AVAILABLE,
        CodePreprocessor,
        SemanticSearchConfig,
        SemanticSearchEngine,
    )
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    CodePreprocessor = None
    SemanticSearchConfig = None
    SemanticSearchEngine = None


@dataclass
class SemanticIndex:
    """Semantic index for a code file."""

    file_path: Path
    chunks: list[tuple[int, str, np.ndarray]]  # (line, content, embedding)
    signatures: list[tuple[int, str, str]]  # (line, type, signature)
    indexed_at: datetime
    file_hash: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": str(self.file_path),
            "chunks": [
                {"line": line, "content": content[:100]}
                for line, content, _ in self.chunks
            ],
            "signatures": [
                {"line": line, "type": sig_type, "signature": sig}
                for line, sig_type, sig in self.signatures
            ],
            "indexed_at": self.indexed_at.isoformat(),
            "file_hash": self.file_hash,
            "num_embeddings": len(self.chunks),
        }


class SemanticSight(AbstractEye):
    """
    Semantic code observation using embeddings.

    Indexes code for semantic search and provides semantic context.
    """

    def __init__(
        self,
        config: SemanticSearchConfig | None = None,
        storage_path: Path | None = None,
    ):
        """
        Initialize semantic sight.

        Args:
            config: Semantic search configuration
            storage_path: Path to store embeddings
        """
        super().__init__()
        self.config = (
            config
            if config is not None
            else (SemanticSearchConfig() if SemanticSearchConfig is not None else None)
        )
        self.storage_path = storage_path
        self._engine: SemanticSearchEngine | None = None
        self._preprocessor = (
            CodePreprocessor() if CodePreprocessor is not None else None
        )
        self._indexed_files: dict[Path, SemanticIndex] = {}

        if (
            SENTENCE_TRANSFORMERS_AVAILABLE
            and NUMPY_AVAILABLE
            and self.config is not None
            and SemanticSearchEngine is not None
        ):
            try:
                self._engine = SemanticSearchEngine(self.config)
            except ImportError:
                pass

    def observe(self, target: Path) -> ObservationResult:
        """
        Observe code semantically by indexing it.

        Args:
            target: File or directory to index

        Returns:
            ObservationResult with semantic index data
        """
        if not self._is_available() or self._engine is None:
            return ObservationResult(
                raw_payload={
                    "error": self._unavailable_reason(),
                    "indexed": False,
                },
                path=target,
            )

        if target.is_file():
            index = self._index_file(target)
            return ObservationResult(
                raw_payload=index.to_dict() if index else {"indexed": False},
                path=target,
            )
        elif target.is_dir():
            indices = self._index_directory(target)
            return ObservationResult(
                raw_payload={
                    "indexed_files": len(indices),
                    "files": [idx.to_dict() for idx in indices[:10]],
                },
                path=target,
            )
        else:
            return ObservationResult(
                raw_payload={"error": "Path does not exist", "indexed": False},
                path=target,
            )

    def _index_file(self, file_path: Path) -> SemanticIndex | None:
        """Index a single file."""
        if self._engine is None or self._preprocessor is None:
            return None
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, IOError):
            return None

        # Compute file hash
        import hashlib

        file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Check if already indexed and unchanged
        if file_path in self._indexed_files:
            existing = self._indexed_files[file_path]
            if existing.file_hash == file_hash:
                return existing

        # Extract chunks with embeddings
        chunks_data = self._engine.index_file(file_path, content)

        chunks = []
        for chunk_id, embedding, start_line in chunks_data:
            # Get chunk content
            lines = content.splitlines()
            chunk_content = "\n".join(
                lines[start_line - 1 : start_line + 19]
            )  # 20 lines
            chunks.append((start_line, chunk_content, embedding))

        # Extract signatures
        signatures = self._preprocessor.extract_signatures(content)

        index = SemanticIndex(
            file_path=file_path,
            chunks=chunks,
            signatures=signatures,
            indexed_at=datetime.now(UTC),
            file_hash=file_hash,
        )

        self._indexed_files[file_path] = index
        return index

    def _index_directory(self, directory: Path) -> list[SemanticIndex]:
        """Index all code files in directory."""
        indices = []

        # Find all code files
        code_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"}

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in code_extensions:
                continue

            index = self._index_file(file_path)
            if index:
                indices.append(index)

        return indices

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search indexed code semantically.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of search results
        """
        if not self._engine or not self._indexed_files:
            return []

        # Prepare indexed files for search
        indexed_data = []
        for file_path, index in self._indexed_files.items():
            chunks = [
                (f"{file_path}:{line}", emb, line) for line, _, emb in index.chunks
            ]
            indexed_data.append((file_path, chunks))

        # Perform search
        results = self._engine.search(query, indexed_data)

        # Convert to dicts
        return [r.to_dict() for r in results[:top_k]]

    def find_similar(
        self,
        code_snippet: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find code similar to given snippet.

        Args:
            code_snippet: Code to find similar matches for
            top_k: Number of results

        Returns:
            List of similar code snippets
        """
        if not self._engine or not self._indexed_files:
            return []

        # Prepare indexed files
        indexed_data = [
            (
                file_path,
                [(f"{file_path}:{line}", emb, line) for line, _, emb in index.chunks],
            )
            for file_path, index in self._indexed_files.items()
        ]

        # Find similar
        results = self._engine.find_similar(code_snippet, indexed_data)

        return [r.to_dict() for r in results[:top_k]]

    def get_indexed_files(self) -> list[Path]:
        """Get list of indexed files."""
        return list(self._indexed_files.keys())

    def get_index_stats(self) -> dict[str, Any]:
        """Get indexing statistics."""
        total_embeddings = sum(len(idx.chunks) for idx in self._indexed_files.values())
        total_signatures = sum(
            len(idx.signatures) for idx in self._indexed_files.values()
        )

        return {
            "indexed_files": len(self._indexed_files),
            "total_embeddings": total_embeddings,
            "total_signatures": total_signatures,
            "cache_size": self._engine.get_cache_size() if self._engine else 0,
            "model_available": self._is_available(),
        }

    def clear_index(self) -> None:
        """Clear all indexed data."""
        self._indexed_files.clear()
        if self._engine:
            self._engine.clear_cache()

    def _is_available(self) -> bool:
        return (
            NUMPY_AVAILABLE
            and SENTENCE_TRANSFORMERS_AVAILABLE
            and SemanticSearchEngine is not None
            and SemanticSearchConfig is not None
            and CodePreprocessor is not None
        )

    def _unavailable_reason(self) -> str:
        reasons: list[str] = []
        if not NUMPY_AVAILABLE:
            reasons.append("numpy not available")
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            reasons.append("sentence-transformers not available")
        if SemanticSearchEngine is None:
            reasons.append("semantic search engine unavailable")
        if not reasons:
            reasons.append("semantic dependencies unavailable")
        return ", ".join(reasons)


class SemanticSightFactory:
    """Factory for creating semantic sight instances."""

    @staticmethod
    def create(
        model_name: str = "all-MiniLM-L6-v2",
        storage_path: Path | None = None,
    ) -> SemanticSight:
        """
        Create a semantic sight instance.

        Args:
            model_name: Name of the embedding model
            storage_path: Path for embedding storage

        Returns:
            SemanticSight instance
        """
        config = (
            SemanticSearchConfig(model_name=model_name)
            if SemanticSearchConfig is not None
            else None
        )
        return SemanticSight(config, storage_path)

    @staticmethod
    def is_available() -> bool:
        """Check if semantic sight is available."""
        return (
            NUMPY_AVAILABLE
            and SENTENCE_TRANSFORMERS_AVAILABLE
            and SemanticSearchEngine is not None
            and SemanticSearchConfig is not None
            and CodePreprocessor is not None
        )
