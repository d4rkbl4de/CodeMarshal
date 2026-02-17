"""
embedding_storage.py - Vector storage for code embeddings.

Purpose:
    Persistent storage for code embeddings with efficient retrieval.
    Supports incremental updates and similarity search.

Constitutional Basis:
    - Article 9: Immutable Observations (embeddings are immutable)
    - Article 15: Checkpoints (embedding storage is checkpointed)
    - Article 18: Explicit Limitations (storage limits declared)

Storage Format:
    - Embeddings stored as numpy arrays (.npy files)
    - Metadata stored as JSON
    - Hierarchical structure by investigation
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore[assignment]
    NUMPY_AVAILABLE = False


@dataclass(frozen=True)
class EmbeddingRecord:
    """Immutable embedding record."""

    id: str
    file_path: str
    line_number: int
    content: str
    embedding: Any
    created_at: datetime
    investigation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (embedding excluded)."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "content": self.content[:200] if self.content else "",
            "embedding_shape": list(self.embedding.shape),
            "embedding_dtype": str(self.embedding.dtype),
            "created_at": self.created_at.isoformat(),
            "investigation_id": self.investigation_id,
        }


@dataclass
class EmbeddingIndex:
    """Index for fast embedding lookup."""

    investigation_id: str
    file_paths: dict[str, list[str]] = field(
        default_factory=dict
    )  # path -> embedding_ids
    total_embeddings: int = 0
    last_updated: datetime | None = None
    embedding_dim: int = 384  # Default for all-MiniLM-L6-v2

    def add_embedding(self, file_path: str, embedding_id: str) -> None:
        """Add embedding to index."""
        if file_path not in self.file_paths:
            self.file_paths[file_path] = []
        self.file_paths[file_path].append(embedding_id)
        self.total_embeddings += 1
        self.last_updated = datetime.now(UTC)

    def remove_file(self, file_path: str) -> list[str]:
        """Remove all embeddings for a file."""
        removed = self.file_paths.pop(file_path, [])
        self.total_embeddings -= len(removed)
        self.last_updated = datetime.now(UTC)
        return removed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "investigation_id": self.investigation_id,
            "file_paths": self.file_paths,
            "total_embeddings": self.total_embeddings,
            "last_updated": self.last_updated.isoformat()
            if self.last_updated
            else None,
            "embedding_dim": self.embedding_dim,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmbeddingIndex":
        """Create from dictionary."""
        index = cls(
            investigation_id=data["investigation_id"],
            embedding_dim=data.get("embedding_dim", 384),
        )
        index.file_paths = data.get("file_paths", {})
        index.total_embeddings = data.get("total_embeddings", 0)
        if data.get("last_updated"):
            index.last_updated = datetime.fromisoformat(data["last_updated"])
        return index


class EmbeddingStorage:
    """
    Storage for code embeddings with efficient retrieval.

    Features:
    - Persistent storage as numpy arrays
    - Metadata indexing
    - Incremental updates
    - Investigation-scoped storage
    """

    def __init__(self, storage_dir: Path | str | None = None):
        """
        Initialize embedding storage.

        Args:
            storage_dir: Directory for storage (default: storage/embeddings)
        """
        if storage_dir is None:
            storage_dir = Path("storage/embeddings")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._embedding_cache: dict[str, EmbeddingRecord] = {}
        self._index_cache: dict[str, EmbeddingIndex] = {}
        self._max_cache_size = 10000

    def store_embedding(
        self,
        embedding_id: str,
        file_path: str,
        line_number: int,
        content: str,
        embedding: Any,
        investigation_id: str | None = None,
    ) -> EmbeddingRecord:
        """
        Store a single embedding.

        Args:
            embedding_id: Unique identifier for this embedding
            file_path: Path to source file
            line_number: Line number in source
            content: Code content
            embedding: Numpy embedding vector
            investigation_id: Optional investigation scope

        Returns:
            Stored EmbeddingRecord
        """
        _require_numpy()
        record = EmbeddingRecord(
            id=embedding_id,
            file_path=file_path,
            line_number=line_number,
            content=content,
            embedding=embedding,
            created_at=datetime.now(UTC),
            investigation_id=investigation_id,
        )

        # Store in cache
        self._embedding_cache[embedding_id] = record

        # Persist to disk
        self._persist_embedding(record, investigation_id)

        # Update index
        self._update_index(file_path, embedding_id, investigation_id)

        # Manage cache size
        if len(self._embedding_cache) > self._max_cache_size:
            self._trim_cache()

        return record

    def store_embeddings(
        self,
        embeddings: list[tuple],
        investigation_id: str | None = None,
    ) -> list[EmbeddingRecord]:
        """
        Store multiple embeddings.

        Args:
            embeddings: List of (id, file_path, line, content, embedding) tuples
            investigation_id: Optional investigation scope

        Returns:
            List of stored EmbeddingRecords
        """
        records = []
        for emb_data in embeddings:
            record = self.store_embedding(
                embedding_id=emb_data[0],
                file_path=emb_data[1],
                line_number=emb_data[2],
                content=emb_data[3],
                embedding=emb_data[4],
                investigation_id=investigation_id,
            )
            records.append(record)

        return records

    def get_embedding(self, embedding_id: str) -> EmbeddingRecord | None:
        """
        Retrieve an embedding by ID.

        Args:
            embedding_id: Embedding identifier

        Returns:
            EmbeddingRecord or None
        """
        # Check cache first
        if embedding_id in self._embedding_cache:
            return self._embedding_cache[embedding_id]

        # Load from disk
        return self._load_embedding(embedding_id)

    def get_embeddings_for_file(
        self,
        file_path: str,
        investigation_id: str | None = None,
    ) -> list[EmbeddingRecord]:
        """
        Get all embeddings for a file.

        Args:
            file_path: Path to source file
            investigation_id: Optional investigation filter

        Returns:
            List of EmbeddingRecords
        """
        index = self._get_index(investigation_id)
        embedding_ids = index.file_paths.get(file_path, [])

        records = []
        for emb_id in embedding_ids:
            record = self.get_embedding(emb_id)
            if record:
                records.append(record)

        return records

    def get_all_embeddings(
        self,
        investigation_id: str | None = None,
    ) -> list[EmbeddingRecord]:
        """
        Get all embeddings (optionally filtered by investigation).

        Args:
            investigation_id: Optional investigation filter

        Returns:
            List of EmbeddingRecords
        """
        index = self._get_index(investigation_id)

        records = []
        for emb_ids in index.file_paths.values():
            for emb_id in emb_ids:
                record = self.get_embedding(emb_id)
                if record:
                    records.append(record)

        return records

    def delete_embeddings_for_file(
        self,
        file_path: str,
        investigation_id: str | None = None,
    ) -> int:
        """
        Delete all embeddings for a file.

        Args:
            file_path: Path to source file
            investigation_id: Optional investigation scope

        Returns:
            Number of embeddings deleted
        """
        index = self._get_index(investigation_id)
        removed_ids = index.remove_file(file_path)

        # Remove from cache
        for emb_id in removed_ids:
            self._embedding_cache.pop(emb_id, None)

        # Remove from disk
        for emb_id in removed_ids:
            self._delete_embedding_file(emb_id, investigation_id)

        # Persist updated index
        self._persist_index(index, investigation_id)

        return len(removed_ids)

    def search_similar(
        self,
        query_embedding: Any,
        top_k: int = 10,
        threshold: float = 0.5,
        investigation_id: str | None = None,
    ) -> list[tuple[EmbeddingRecord, float]]:
        """
        Find similar embeddings using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            threshold: Minimum similarity score
            investigation_id: Optional investigation filter

        Returns:
            List of (EmbeddingRecord, similarity_score) tuples
        """
        _require_numpy()
        records = self.get_all_embeddings(investigation_id)

        if not records:
            return []

        # Normalize query
        query_norm = query_embedding / np.linalg.norm(query_embedding)

        # Compute similarities
        similarities = []
        for record in records:
            emb_norm = record.embedding / np.linalg.norm(record.embedding)
            similarity = np.dot(query_norm, emb_norm)

            if similarity >= threshold:
                similarities.append((record, float(similarity)))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def get_stats(self, investigation_id: str | None = None) -> dict[str, Any]:
        """
        Get storage statistics.

        Args:
            investigation_id: Optional investigation filter

        Returns:
            Statistics dictionary
        """
        index = self._get_index(investigation_id)

        total_files = len(index.file_paths)
        total_embeddings = index.total_embeddings

        # Calculate storage size
        storage_size = 0
        inv_dir = self._get_investigation_dir(investigation_id)
        if inv_dir.exists():
            for f in inv_dir.rglob("*"):
                if f.is_file():
                    storage_size += f.stat().st_size

        return {
            "total_files": total_files,
            "total_embeddings": total_embeddings,
            "embedding_dim": index.embedding_dim,
            "cache_size": len(self._embedding_cache),
            "storage_size_bytes": storage_size,
            "storage_size_mb": round(storage_size / (1024 * 1024), 2),
            "last_updated": index.last_updated.isoformat()
            if index.last_updated
            else None,
        }

    def clear_cache(self) -> None:
        """Clear in-memory cache."""
        self._embedding_cache.clear()
        self._index_cache.clear()

    def clear_investigation(self, investigation_id: str) -> None:
        """Clear all data for an investigation."""
        inv_dir = self._get_investigation_dir(investigation_id)
        if inv_dir.exists():
            import shutil

            shutil.rmtree(inv_dir)

        # Remove from cache
        self._index_cache.pop(investigation_id, None)
        to_remove = [
            k
            for k, v in self._embedding_cache.items()
            if v.investigation_id == investigation_id
        ]
        for k in to_remove:
            self._embedding_cache.pop(k, None)

    def _get_investigation_dir(self, investigation_id: str | None) -> Path:
        """Get storage directory for investigation."""
        if investigation_id:
            return self.storage_dir / investigation_id
        return self.storage_dir / "default"

    def _persist_embedding(
        self,
        record: EmbeddingRecord,
        investigation_id: str | None,
    ) -> None:
        """Persist embedding to disk."""
        _require_numpy()
        inv_dir = self._get_investigation_dir(investigation_id)
        emb_dir = inv_dir / "embeddings"
        emb_dir.mkdir(parents=True, exist_ok=True)

        # Save embedding as numpy file
        emb_file = emb_dir / f"{record.id}.npy"
        np.save(emb_file, record.embedding)

        # Save metadata as JSON
        meta_file = emb_dir / f"{record.id}.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)

    def _load_embedding(self, embedding_id: str) -> EmbeddingRecord | None:
        """Load embedding from disk."""
        _require_numpy()
        # Try default first, then other investigations
        for inv_dir in self.storage_dir.iterdir():
            if not inv_dir.is_dir():
                continue

            emb_dir = inv_dir / "embeddings"
            emb_file = emb_dir / f"{embedding_id}.npy"
            meta_file = emb_dir / f"{embedding_id}.json"

            if emb_file.exists() and meta_file.exists():
                try:
                    # Load embedding
                    embedding = np.load(emb_file)

                    # Load metadata
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)

                    return EmbeddingRecord(
                        id=meta["id"],
                        file_path=meta["file_path"],
                        line_number=meta["line_number"],
                        content=meta.get("content", ""),
                        embedding=embedding,
                        created_at=datetime.fromisoformat(meta["created_at"]),
                        investigation_id=meta.get("investigation_id"),
                    )
                except (OSError, json.JSONDecodeError, KeyError):
                    continue

        return None

    def _delete_embedding_file(
        self,
        embedding_id: str,
        investigation_id: str | None,
    ) -> None:
        """Delete embedding files from disk."""
        inv_dir = self._get_investigation_dir(investigation_id)
        emb_dir = inv_dir / "embeddings"

        emb_file = emb_dir / f"{embedding_id}.npy"
        meta_file = emb_dir / f"{embedding_id}.json"

        if emb_file.exists():
            emb_file.unlink()
        if meta_file.exists():
            meta_file.unlink()

    def _get_index(self, investigation_id: str | None) -> EmbeddingIndex:
        """Get or load index for investigation."""
        inv_id = investigation_id or "default"

        if inv_id in self._index_cache:
            return self._index_cache[inv_id]

        # Try to load from disk
        inv_dir = self._get_investigation_dir(investigation_id)
        index_file = inv_dir / "index.json"

        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                index = EmbeddingIndex.from_dict(data)
            except (OSError, json.JSONDecodeError):
                index = EmbeddingIndex(investigation_id=inv_id)
        else:
            index = EmbeddingIndex(investigation_id=inv_id)

        self._index_cache[inv_id] = index
        return index

    def _update_index(
        self,
        file_path: str,
        embedding_id: str,
        investigation_id: str | None,
    ) -> None:
        """Update index with new embedding."""
        index = self._get_index(investigation_id)
        index.add_embedding(file_path, embedding_id)
        self._persist_index(index, investigation_id)

    def _persist_index(
        self,
        index: EmbeddingIndex,
        investigation_id: str | None,
    ) -> None:
        """Persist index to disk."""
        inv_dir = self._get_investigation_dir(investigation_id)
        inv_dir.mkdir(parents=True, exist_ok=True)

        index_file = inv_dir / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index.to_dict(), f, indent=2)

    def _trim_cache(self) -> None:
        """Trim cache to max size."""
        if len(self._embedding_cache) <= self._max_cache_size:
            return

        # Remove oldest entries (simple FIFO)
        to_remove = len(self._embedding_cache) - self._max_cache_size // 2
        for _ in range(to_remove):
            if self._embedding_cache:
                key = next(iter(self._embedding_cache))
                self._embedding_cache.pop(key)


def create_embedding_storage(
    storage_dir: Path | str | None = None,
) -> EmbeddingStorage:
    """
    Create an embedding storage instance.

    Args:
        storage_dir: Directory for storage

    Returns:
        EmbeddingStorage instance
    """
    return EmbeddingStorage(storage_dir)


def _require_numpy() -> None:
    if not NUMPY_AVAILABLE:
        raise RuntimeError(
            "numpy is required for embedding storage operations. "
            "Install dependencies with `pip install -e .`."
        )
