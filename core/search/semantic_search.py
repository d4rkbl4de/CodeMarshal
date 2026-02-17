"""
semantic_search.py - Semantic code search using local embeddings.

Purpose:
    Enable semantic search of code using local embedding models.
    Finds semantically similar code even when text doesn't match exactly.

Constitutional Basis:
    - Article 4: Progressive Disclosure (search at different levels)
    - Article 5: Resource Transparency (declare embedding requirements)
    - Article 14: Graceful Degradation (fallback when models unavailable)

Features:
    - Local embedding model (sentence-transformers)
    - Semantic similarity search
    - Code-aware preprocessing
    - Configurable similarity thresholds
    - Memory-efficient batch processing

Requirements:
    - sentence-transformers (optional, enables semantic features)
    - numpy (for vector operations)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


@dataclass(frozen=True)
class SearchResult:
    """Immutable search result."""

    path: Path
    content: str
    score: float
    line_number: int | None = None
    context: str = ""
    embedding: np.ndarray | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "content": self.content[:200] + "..."
            if len(self.content) > 200
            else self.content,
            "score": round(self.score, 4),
            "line_number": self.line_number,
            "context": self.context[:200] if self.context else "",
        }


@dataclass
class SemanticSearchConfig:
    """Configuration for semantic search."""

    model_name: str = "all-MiniLM-L6-v2"  # Lightweight, fast model
    max_seq_length: int = 256  # Max tokens per chunk
    similarity_threshold: float = 0.5  # Minimum similarity score
    top_k: int = 10  # Number of results to return
    batch_size: int = 32  # Batch size for encoding
    device: str = "cpu"  # "cpu" or "cuda"
    cache_embeddings: bool = True  # Cache computed embeddings


class CodePreprocessor:
    """Preprocess code for semantic search."""

    @staticmethod
    def extract_code_chunks(
        content: str,
        chunk_size: int = 50,
        overlap: int = 10,
    ) -> list[tuple[int, str]]:
        """
        Extract overlapping code chunks with line numbers.

        Args:
            content: Source code content
            chunk_size: Lines per chunk
            overlap: Overlapping lines between chunks

        Returns:
            List of (start_line, chunk_text) tuples
        """
        lines = content.splitlines()
        chunks = []

        if len(lines) <= chunk_size:
            # Small file - one chunk
            return [(1, content)]

        step = chunk_size - overlap
        for i in range(0, len(lines), step):
            chunk_lines = lines[i : i + chunk_size]
            chunk_text = "\n".join(chunk_lines)
            chunks.append((i + 1, chunk_text))

        return chunks

    @staticmethod
    def normalize_code(text: str) -> str:
        """
        Normalize code for better semantic matching.

        - Normalize whitespace
        - Remove comments (keep docstrings)
        - Preserve structure
        """
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove single-line comments (but not docstrings)
        lines = []
        for line in text.split("\n"):
            # Keep docstrings
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                lines.append(line)
                continue

            # Remove single-line comments
            if "#" in line:
                line = line[: line.index("#")]

            if line.strip():
                lines.append(line)

        # Normalize whitespace
        text = "\n".join(lines)
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Multiple blank lines to one
        text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces to one

        return text.strip()

    @staticmethod
    def extract_signatures(content: str) -> list[tuple[int, str, str]]:
        """
        Extract function and class signatures.

        Returns:
            List of (line_number, signature_type, signature_text) tuples
        """
        signatures = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Function definitions
            if re.match(r"^def\s+\w+\s*\(", stripped):
                signatures.append((i, "function", stripped))

            # Class definitions
            elif re.match(r"^class\s+\w+", stripped):
                signatures.append((i, "class", stripped))

            # Import statements
            elif stripped.startswith(("import ", "from ")):
                signatures.append((i, "import", stripped))

        return signatures


class SemanticSearchEngine:
    """
    Semantic code search using local embeddings.

    Features:
    - Local embedding computation (no network required)
    - Code-aware chunking and preprocessing
    - Configurable similarity thresholds
    - Batch processing for efficiency
    - Embedding caching
    """

    def __init__(self, config: SemanticSearchConfig | None = None):
        """
        Initialize semantic search engine.

        Args:
            config: Search configuration

        Raises:
            ImportError: If sentence-transformers not installed
        """
        self.config = config or SemanticSearchConfig()
        self._model: SentenceTransformer | None = None
        self._embedding_cache: dict[str, np.ndarray] = {}
        self._preprocessor = CodePreprocessor()

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers required for semantic search. "
                "Install with: pip install sentence-transformers"
            )

    def _load_model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            self._model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device,
            )
            self._model.max_seq_length = self.config.max_seq_length
        return self._model

    def index_file(
        self,
        file_path: Path,
        content: str | None = None,
    ) -> list[tuple[str, np.ndarray, int]]:
        """
        Index a file for semantic search.

        Args:
            file_path: Path to the file
            content: File content (read from disk if not provided)

        Returns:
            List of (chunk_id, embedding, start_line) tuples
        """
        if content is None:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, IOError):
                return []

        # Extract chunks
        chunks = self._preprocessor.extract_code_chunks(
            content,
            chunk_size=self.config.max_seq_length // 5,  # Approximate lines
            overlap=5,
        )

        if not chunks:
            return []

        # Normalize chunks
        normalized_chunks = [
            self._preprocessor.normalize_code(chunk_text) for _, chunk_text in chunks
        ]

        # Compute embeddings in batches
        model = self._load_model()
        embeddings = model.encode(
            normalized_chunks,
            batch_size=self.config.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # Cache embeddings
        results = []
        for (start_line, _), embedding in zip(chunks, embeddings):
            chunk_id = self._compute_chunk_id(file_path, start_line, content)
            results.append((chunk_id, embedding, start_line))

            if self.config.cache_embeddings:
                self._embedding_cache[chunk_id] = embedding

        return results

    def search(
        self,
        query: str,
        indexed_files: list[tuple[Path, list[tuple[str, np.ndarray, int]]]],
    ) -> list[SearchResult]:
        """
        Search for semantically similar code.

        Args:
            query: Search query (natural language or code)
            indexed_files: List of (file_path, embeddings) from index_file

        Returns:
            List of SearchResult sorted by similarity score
        """
        # Encode query
        model = self._load_model()
        query_embedding = model.encode(
            [query],
            convert_to_numpy=True,
        )[0]

        # Normalize query embedding
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Compute similarities
        results = []
        for file_path, file_chunks in indexed_files:
            for chunk_id, embedding, start_line in file_chunks:
                # Normalize embedding
                embedding_norm = embedding / np.linalg.norm(embedding)

                # Cosine similarity
                similarity = np.dot(query_embedding, embedding_norm)

                if similarity >= self.config.similarity_threshold:
                    results.append(
                        SearchResult(
                            path=file_path,
                            content=self._get_chunk_content(file_path, start_line),
                            score=float(similarity),
                            line_number=start_line,
                            context=f"chunk:{chunk_id}",
                        )
                    )

        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)

        return results[: self.config.top_k]

    def search_directory(
        self,
        query: str,
        directory: Path,
        file_patterns: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        Search entire directory semantically.

        Args:
            query: Search query
            directory: Directory to search
            file_patterns: File patterns to include (e.g., ["*.py"])

        Returns:
            List of SearchResult
        """
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.go"]

        # Index all matching files
        indexed_files = []
        for pattern in file_patterns:
            for file_path in directory.rglob(pattern):
                if file_path.is_file():
                    chunks = self.index_file(file_path)
                    if chunks:
                        indexed_files.append((file_path, chunks))

        if not indexed_files:
            return []

        return self.search(query, indexed_files)

    def find_similar(
        self,
        code_snippet: str,
        indexed_files: list[tuple[Path, list[tuple[str, np.ndarray, int]]]],
    ) -> list[SearchResult]:
        """
        Find code similar to a given snippet.

        Args:
            code_snippet: Code to find similar matches for
            indexed_files: Indexed files to search

        Returns:
            List of similar code snippets
        """
        # Normalize the query snippet
        normalized = self._preprocessor.normalize_code(code_snippet)
        return self.search(normalized, indexed_files)

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._embedding_cache.clear()

    def get_cache_size(self) -> int:
        """Get number of cached embeddings."""
        return len(self._embedding_cache)

    def _compute_chunk_id(
        self,
        file_path: Path,
        start_line: int,
        content: str,
    ) -> str:
        """Compute unique ID for a chunk."""
        hash_input = f"{file_path}:{start_line}:{content[:100]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _get_chunk_content(self, file_path: Path, start_line: int) -> str:
        """Get content of a chunk from file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            # Get chunk around start_line
            chunk_start = max(0, start_line - 1)
            chunk_end = min(len(lines), start_line + 19)  # 20 lines

            return "\n".join(lines[chunk_start:chunk_end])
        except (OSError, IOError):
            return ""


class HybridSearchEngine:
    """
    Hybrid search combining text and semantic search.

    Weights text matching and semantic similarity for best results.
    """

    def __init__(
        self,
        semantic_config: SemanticSearchConfig | None = None,
        text_weight: float = 0.3,
        semantic_weight: float = 0.7,
    ):
        """
        Initialize hybrid search.

        Args:
            semantic_config: Configuration for semantic search
            text_weight: Weight for text search (0-1)
            semantic_weight: Weight for semantic search (0-1)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers required for hybrid search. "
                "Install with: pip install sentence-transformers"
            )

        self.semantic_engine = SemanticSearchEngine(semantic_config)
        self.text_weight = text_weight
        self.semantic_weight = semantic_weight
        self._preprocessor = CodePreprocessor()

    def search(
        self,
        query: str,
        directory: Path,
        file_patterns: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query: Search query
            directory: Directory to search
            file_patterns: File patterns to include

        Returns:
            Combined search results
        """
        # Perform semantic search
        semantic_results = self.semantic_engine.search_directory(
            query,
            directory,
            file_patterns,
        )

        # Perform text search (simple substring matching)
        text_results = self._text_search(query, directory, file_patterns)

        # Combine and deduplicate
        combined = self._combine_results(semantic_results, text_results)

        return combined

    def _text_search(
        self,
        query: str,
        directory: Path,
        file_patterns: list[str] | None,
    ) -> list[SearchResult]:
        """Simple text-based search."""
        if file_patterns is None:
            file_patterns = ["*.py"]

        results = []
        query_lower = query.lower()

        for pattern in file_patterns:
            for file_path in directory.rglob(pattern):
                if not file_path.is_file():
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        if query_lower in line.lower():
                            # Simple scoring based on match quality
                            score = 0.5  # Base score for substring match

                            # Boost for exact match
                            if query in line:
                                score = 0.7

                            # Boost for word boundary match
                            if re.search(r"\b" + re.escape(query) + r"\b", line, re.I):
                                score = 0.8

                            results.append(
                                SearchResult(
                                    path=file_path,
                                    content=line.strip(),
                                    score=score,
                                    line_number=i,
                                    context="text_match",
                                )
                            )
                except (OSError, IOError):
                    continue

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:50]  # Limit text results

    def _combine_results(
        self,
        semantic_results: list[SearchResult],
        text_results: list[SearchResult],
    ) -> list[SearchResult]:
        """Combine semantic and text results."""
        # Create lookup by path+line
        combined: dict[tuple[Path, int | None], SearchResult] = {}

        # Add semantic results with weight
        for result in semantic_results:
            key = (result.path, result.line_number)
            weighted_score = result.score * self.semantic_weight

            if key in combined:
                # Boost existing result
                combined[key] = SearchResult(
                    path=result.path,
                    content=result.content,
                    score=combined[key].score + weighted_score,
                    line_number=result.line_number,
                    context="hybrid",
                )
            else:
                combined[key] = SearchResult(
                    path=result.path,
                    content=result.content,
                    score=weighted_score,
                    line_number=result.line_number,
                    context="semantic",
                )

        # Add text results with weight
        for result in text_results:
            key = (result.path, result.line_number)
            weighted_score = result.score * self.text_weight

            if key in combined:
                # Boost existing result
                combined[key] = SearchResult(
                    path=result.path,
                    content=result.content,
                    score=combined[key].score + weighted_score,
                    line_number=result.line_number,
                    context="hybrid",
                )
            else:
                combined[key] = SearchResult(
                    path=result.path,
                    content=result.content,
                    score=weighted_score,
                    line_number=result.line_number,
                    context="text",
                )

        # Sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:20]  # Return top 20


def create_semantic_search_engine(
    model_name: str = "all-MiniLM-L6-v2",
    device: str = "cpu",
) -> SemanticSearchEngine:
    """
    Create a semantic search engine.

    Args:
        model_name: Name of the sentence-transformers model
        device: Device to run on ("cpu" or "cuda")

    Returns:
        SemanticSearchEngine instance
    """
    config = SemanticSearchConfig(
        model_name=model_name,
        device=device,
    )
    return SemanticSearchEngine(config)


def create_hybrid_search_engine(
    model_name: str = "all-MiniLM-L6-v2",
    text_weight: float = 0.3,
    semantic_weight: float = 0.7,
) -> HybridSearchEngine:
    """
    Create a hybrid search engine.

    Args:
        model_name: Name of the sentence-transformers model
        text_weight: Weight for text search
        semantic_weight: Weight for semantic search

    Returns:
        HybridSearchEngine instance
    """
    config = SemanticSearchConfig(model_name=model_name)
    return HybridSearchEngine(config, text_weight, semantic_weight)
