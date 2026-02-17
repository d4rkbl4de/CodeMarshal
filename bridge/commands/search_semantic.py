"""
search_semantic.py - Semantic search command for CodeMarshal.

Commands:
    - search --semantic: Perform semantic code search
    - search --hybrid: Perform hybrid (text + semantic) search
    - index: Index code for semantic search
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

# Try to import semantic search
try:
    from core.search.semantic_search import (
        SENTENCE_TRANSFORMERS_AVAILABLE,
        SemanticSearchEngine,
        HybridSearchEngine,
        create_semantic_search_engine,
        create_hybrid_search_engine,
    )

    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False


def semantic_search_command(
    query: str,
    path: str,
    top_k: int = 10,
    threshold: float = 0.5,
    output_format: str = "text",
) -> dict[str, Any]:
    """
    Perform semantic code search.

    Args:
        query: Search query (natural language or code)
        path: Directory path to search
        top_k: Number of results to return
        threshold: Minimum similarity threshold
        output_format: Output format (text, json)

    Returns:
        Dictionary with search results
    """
    if not SEMANTIC_AVAILABLE:
        return {
            "success": False,
            "error": (
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            ),
        }

    search_path = Path(path).resolve()

    if not search_path.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {search_path}",
        }

    if not search_path.is_dir():
        return {
            "success": False,
            "error": f"Path is not a directory: {search_path}",
        }

    try:
        # Create search engine
        engine = create_semantic_search_engine()

        if output_format == "text":
            print(f"Indexing code in {search_path}...", file=sys.stderr)

        start_time = time.time()

        # Index and search
        results = engine.search_directory(query, search_path)

        # Filter by threshold
        results = [r for r in results if r.score >= threshold]

        # Limit results
        results = results[:top_k]

        elapsed = time.time() - start_time

        # Format results
        result_dicts = [r.to_dict() for r in results]

        if output_format == "text":
            _print_semantic_results(query, result_dicts, elapsed)
        elif output_format == "json":
            print(
                json.dumps(
                    {
                        "success": True,
                        "query": query,
                        "results": result_dicts,
                        "elapsed_seconds": round(elapsed, 2),
                    },
                    indent=2,
                )
            )

        return {
            "success": True,
            "query": query,
            "results_count": len(result_dicts),
            "results": result_dicts,
            "elapsed_seconds": round(elapsed, 2),
        }

    except Exception as e:
        error_msg = f"Semantic search failed: {str(e)}"
        if output_format == "text":
            print(f"Error: {error_msg}", file=sys.stderr)
        return {
            "success": False,
            "error": error_msg,
        }


def hybrid_search_command(
    query: str,
    path: str,
    top_k: int = 10,
    text_weight: float = 0.3,
    semantic_weight: float = 0.7,
    output_format: str = "text",
) -> dict[str, Any]:
    """
    Perform hybrid (text + semantic) code search.

    Args:
        query: Search query
        path: Directory path to search
        top_k: Number of results
        text_weight: Weight for text search
        semantic_weight: Weight for semantic search
        output_format: Output format

    Returns:
        Dictionary with search results
    """
    if not SEMANTIC_AVAILABLE:
        return {
            "success": False,
            "error": (
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            ),
        }

    search_path = Path(path).resolve()

    if not search_path.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {search_path}",
        }

    try:
        # Create hybrid engine
        engine = create_hybrid_search_engine(
            text_weight=text_weight,
            semantic_weight=semantic_weight,
        )

        if output_format == "text":
            print(f"Performing hybrid search in {search_path}...", file=sys.stderr)

        start_time = time.time()

        # Search
        results = engine.search(query, search_path)
        results = results[:top_k]

        elapsed = time.time() - start_time

        result_dicts = [r.to_dict() for r in results]

        if output_format == "text":
            _print_hybrid_results(query, result_dicts, elapsed)
        elif output_format == "json":
            print(
                json.dumps(
                    {
                        "success": True,
                        "query": query,
                        "results": result_dicts,
                        "elapsed_seconds": round(elapsed, 2),
                    },
                    indent=2,
                )
            )

        return {
            "success": True,
            "query": query,
            "results_count": len(result_dicts),
            "results": result_dicts,
            "elapsed_seconds": round(elapsed, 2),
        }

    except Exception as e:
        error_msg = f"Hybrid search failed: {str(e)}"
        if output_format == "text":
            print(f"Error: {error_msg}", file=sys.stderr)
        return {
            "success": False,
            "error": error_msg,
        }


def index_command(
    path: str,
    output_format: str = "text",
) -> dict[str, Any]:
    """
    Index code for semantic search.

    Args:
        path: Directory to index
        output_format: Output format

    Returns:
        Dictionary with indexing statistics
    """
    if not SEMANTIC_AVAILABLE:
        return {
            "success": False,
            "error": (
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            ),
        }

    index_path = Path(path).resolve()

    if not index_path.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {index_path}",
        }

    try:
        engine = create_semantic_search_engine()

        if output_format == "text":
            print(f"Indexing {index_path}...", file=sys.stderr)

        start_time = time.time()

        # Find all code files
        code_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"}
        files = [
            f
            for f in index_path.rglob("*")
            if f.is_file() and f.suffix in code_extensions
        ]

        # Index each file
        indexed_count = 0
        total_embeddings = 0

        for file_path in files:
            chunks = engine.index_file(file_path)
            if chunks:
                indexed_count += 1
                total_embeddings += len(chunks)

        elapsed = time.time() - start_time

        result = {
            "success": True,
            "path": str(index_path),
            "files_found": len(files),
            "files_indexed": indexed_count,
            "total_embeddings": total_embeddings,
            "cache_size": engine.get_cache_size(),
            "elapsed_seconds": round(elapsed, 2),
        }

        if output_format == "text":
            print(f"\nIndexing complete:", file=sys.stderr)
            print(f"  Files indexed: {indexed_count}/{len(files)}", file=sys.stderr)
            print(f"  Total embeddings: {total_embeddings}", file=sys.stderr)
            print(f"  Cache size: {engine.get_cache_size()}", file=sys.stderr)
            print(f"  Time: {elapsed:.2f}s", file=sys.stderr)
        elif output_format == "json":
            print(json.dumps(result, indent=2))

        return result

    except Exception as e:
        error_msg = f"Indexing failed: {str(e)}"
        if output_format == "text":
            print(f"Error: {error_msg}", file=sys.stderr)
        return {
            "success": False,
            "error": error_msg,
        }


def _print_semantic_results(
    query: str,
    results: list[dict],
    elapsed: float,
) -> None:
    """Print semantic search results in text format."""
    print(f"\nSemantic Search: '{query}'")
    print(f"Time: {elapsed:.2f}s")
    print(f"Results: {len(results)}")
    print("-" * 60)

    for i, result in enumerate(results, 1):
        score = result.get("score", 0)
        path = result.get("path", "")
        line = result.get("line_number", 0)
        content = result.get("content", "")

        print(f"\n{i}. [{score:.3f}] {path}:{line}")
        if content:
            # Show first 100 chars of content
            snippet = content[:100] + "..." if len(content) > 100 else content
            print(f"   {snippet}")


def _print_hybrid_results(
    query: str,
    results: list[dict],
    elapsed: float,
) -> None:
    """Print hybrid search results in text format."""
    print(f"\nHybrid Search: '{query}'")
    print(f"Time: {elapsed:.2f}s")
    print(f"Results: {len(results)}")
    print("-" * 60)

    for i, result in enumerate(results, 1):
        score = result.get("score", 0)
        path = result.get("path", "")
        line = result.get("line_number", 0)
        context = result.get("context", "")
        content = result.get("content", "")

        print(f"\n{i}. [{score:.3f}] {path}:{line} ({context})")
        if content:
            snippet = content[:100] + "..." if len(content) > 100 else content
            print(f"   {snippet}")


# CLI entry points
def execute_semantic_search(
    query: str,
    path: str = ".",
    top_k: int = 10,
    threshold: float = 0.5,
    format: str = "text",
) -> dict[str, Any]:
    """CLI entry point for semantic search."""
    return semantic_search_command(query, path, top_k, threshold, format)


def execute_hybrid_search(
    query: str,
    path: str = ".",
    top_k: int = 10,
    text_weight: float = 0.3,
    semantic_weight: float = 0.7,
    format: str = "text",
) -> dict[str, Any]:
    """CLI entry point for hybrid search."""
    return hybrid_search_command(
        query, path, top_k, text_weight, semantic_weight, format
    )


def execute_index(
    path: str = ".",
    format: str = "text",
) -> dict[str, Any]:
    """CLI entry point for indexing."""
    return index_command(path, format)
