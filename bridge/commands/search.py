"""
bridge.commands.search - Code search command

This module provides the search command for searching codebase text patterns.
Uses ripgrep when available (much faster), falls back to Python regex.

Command:
- search: Search codebase for text patterns
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SearchResult:
    """Single search result."""

    file_path: Path
    line_number: int
    line_content: str
    matched_text: str
    context_before: list[str]
    context_after: list[str]
    match_start: int
    match_end: int


@dataclass
class SearchResults:
    """Collection of search results."""

    query: str
    total_matches: int
    files_with_matches: int
    results: list[SearchResult]
    search_time_ms: float
    output_format: str


@dataclass
class SearchCommandResult:
    """Result of search command execution."""

    success: bool
    results: SearchResults | None = None
    message: str = ""
    error: str | None = None


class SearchCommand:
    """Search command implementation."""

    def __init__(self, context_lines: int = 3, max_workers: int = 4):
        self.context_lines = context_lines
        self.max_workers = max_workers
        self._ripgrep_available = None

    def _check_ripgrep(self) -> bool:
        """Check if ripgrep is available."""
        if self._ripgrep_available is None:
            self._ripgrep_available = shutil.which("rg") is not None
        return self._ripgrep_available

    def execute(
        self,
        query: str,
        path: Path | None = None,
        case_insensitive: bool = False,
        context: int | None = None,
        glob: str | None = None,
        file_type: str | None = None,
        limit: int = 100,
        output_format: str = "text",
        json_file: Path | None = None,
        threads: int | None = None,
        exclude_pattern: str | None = None,
        files_with_matches: bool = False,
    ) -> SearchCommandResult:
        """
        Execute search command.

        Args:
            query: Search pattern (regex)
            path: Directory to search (default: current directory)
            case_insensitive: Case-insensitive search
            context: Lines of context around matches
            glob: File glob pattern
            file_type: File type filter
            limit: Maximum results
            output_format: Output format (text/json/count)
            json_file: Output JSON to file
            threads: Number of parallel threads
            exclude_pattern: Exclude pattern
            files_with_matches: Show only filenames

        Returns:
            SearchCommandResult with search status and results
        """
        if not query:
            return SearchCommandResult(success=False, error="Search query is required")

        search_path = path or Path.cwd()

        if not search_path.exists():
            return SearchCommandResult(
                success=False, error=f"Search path does not exist: {search_path}"
            )

        start_time = time.time()

        if context is not None:
            self.context_lines = context

        if threads is not None:
            self.max_workers = threads

        try:
            # Check for ripgrep (preferred for performance)
            if self._check_ripgrep():
                results = self._search_with_ripgrep(
                    query,
                    search_path,
                    case_insensitive,
                    self.context_lines,
                    glob,
                    file_type,
                    limit,
                    exclude_pattern,
                    files_with_matches,
                )
            else:
                results = self._search_with_regex(
                    query,
                    search_path,
                    case_insensitive,
                    glob,
                    file_type,
                    limit,
                    exclude_pattern,
                    files_with_matches,
                )

            search_time_ms = (time.time() - start_time) * 1000
            results.search_time_ms = search_time_ms
            results.output_format = output_format

            # Output results
            if output_format == "json" or json_file:
                output_data = self._to_json(results)
                if json_file:
                    json_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(json_file, "w") as f:
                        json.dump(output_data, f, indent=2)
                else:
                    print(json.dumps(output_data, indent=2))
            elif output_format == "count":
                print(results.total_matches)
            else:
                self._print_results(results, files_with_matches)

            return SearchCommandResult(
                success=True,
                results=results,
                message=f"Found {results.total_matches} matches in {results.files_with_matches} files",
            )

        except Exception as e:
            return SearchCommandResult(success=False, error=f"Search failed: {e}")

    def _search_with_ripgrep(
        self,
        query: str,
        path: Path,
        case_insensitive: bool,
        context: int,
        glob: str | None,
        file_type: str | None,
        limit: int,
        exclude_pattern: str | None,
        files_with_matches: bool,
    ) -> SearchResults:
        """Use ripgrep for fast searching."""
        cmd = ["rg", "--json", "--context", str(context)]

        if case_insensitive:
            cmd.append("--ignore-case")

        if glob:
            cmd.extend(["--glob", glob])

        if file_type:
            cmd.extend(["--type", file_type])

        if exclude_pattern:
            cmd.extend(["--ignore-case", exclude_pattern])

        if files_with_matches:
            cmd.append("--files-with-matches")

        if limit:
            cmd.extend(["--max-count", str(limit)])

        cmd.extend([query, str(path)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        results = SearchResults(
            query=query,
            total_matches=0,
            files_with_matches=0,
            results=[],
            search_time_ms=0,
            output_format="text",
        )

        if result.returncode in (0, 1):  # 0 = matches, 1 = no matches
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        search_result = self._parse_ripgrep_match(data)
                        if search_result:
                            results.results.append(search_result)
                    except json.JSONDecodeError:
                        pass

        results.total_matches = len(results.results)
        results.files_with_matches = len(set(r.file_path for r in results.results))

        return results

    def _parse_ripgrep_match(self, data: dict) -> SearchResult | None:
        """Parse ripgrep JSON output into SearchResult."""
        if data.get("type") != "match":
            return None

        data_obj = data.get("data", {})
        path_obj = data.get("path", {})
        lines_obj = data_obj.get("lines", {})
        submatches = data_obj.get("submatches", [])

        file_path = Path(path_obj.get("text", ""))
        line_number = data_obj.get("line_number", 0)
        line_text = lines_obj.get("text", "")

        # Get matched text from submatches
        matched_text = ""
        match_start = 0
        match_end = 0
        if submatches:
            match = submatches[0]
            match_start = match.get("start", 0)
            match_end = match.get("end", 0)
            matched_text = line_text[match_start:match_end]

        # Get context
        context_before = []
        context_after = []

        return SearchResult(
            file_path=file_path,
            line_number=line_number,
            line_content=line_text.rstrip(),
            matched_text=matched_text,
            context_before=context_before,
            context_after=context_after,
            match_start=match_start,
            match_end=match_end,
        )

    def _search_with_regex(
        self,
        query: str,
        path: Path,
        case_insensitive: bool,
        glob: str | None,
        file_type: str | None,
        limit: int,
        exclude_pattern: str | None,
        files_with_matches: bool,
    ) -> SearchResults:
        """Use Python regex for searching (fallback)."""
        # Compile regex
        regex_flags = re.IGNORECASE if case_insensitive else 0
        try:
            pattern = re.compile(query, regex_flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        # Find files to search
        files = self._find_files(path, glob, file_type, exclude_pattern)

        # Search in parallel
        all_results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(
                    self._search_file, file_path, pattern, files_with_matches
                ): file_path
                for file_path in files[: limit * 10]  # Limit files for performance
            }

            for future in as_completed(future_to_file):
                try:
                    file_results = future.result()
                    all_results.extend(file_results)

                    if len(all_results) >= limit:
                        break
                except Exception:
                    pass

        results = SearchResults(
            query=query,
            total_matches=len(all_results),
            files_with_matches=len(set(r.file_path for r in all_results)),
            results=all_results[:limit],
            search_time_ms=0,
            output_format="text",
        )

        return results

    def _find_files(
        self,
        path: Path,
        glob: str | None,
        file_type: str | None,
        exclude_pattern: str | None,
    ) -> list[Path]:
        """Find files to search."""
        files = []

        # Determine glob pattern
        if glob:
            pattern = glob
        elif file_type:
            # Map file types to patterns
            type_map = {
                "py": "*.py",
                "js": "*.js",
                "ts": "*.ts",
                "java": "*.java",
                "go": "*.go",
                "rs": "*.rs",
                "cpp": "*.{cpp,cxx,cc}",
                "c": "*.{c,h}",
                "rb": "*.rb",
            }
            pattern = type_map.get(file_type, "*")
        else:
            pattern = "*"

        # Find files
        if path.is_file():
            files = [path]
        else:
            for p in path.rglob(pattern):
                if p.is_file():
                    # Check exclude pattern
                    if exclude_pattern and exclude_pattern in str(p):
                        continue
                    files.append(p)

        return files

    def _search_file(
        self, file_path: Path, pattern: re.Pattern, files_with_matches: bool
    ) -> list[SearchResult]:
        """Search in a single file."""
        results = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if pattern.search(line):
                    if files_with_matches:
                        return [
                            SearchResult(
                                file_path=file_path,
                                line_number=i + 1,
                                line_content=line.strip(),
                                matched_text=pattern.search(line).group()
                                if pattern.search(line)
                                else "",
                                context_before=[],
                                context_after=[],
                                match_start=0,
                                match_end=0,
                            )
                        ]
                    else:
                        results.append(
                            self._create_result(file_path, i, lines, pattern)
                        )

        except (UnicodeDecodeError, PermissionError, OSError):
            pass

        return results

    def _create_result(
        self, file_path: Path, line_idx: int, lines: list[str], pattern: re.Pattern
    ) -> SearchResult:
        """Create a search result from a match."""
        line = lines[line_idx]
        match = pattern.search(line)

        context_before = [
            lines[i].rstrip()
            for i in range(max(0, line_idx - self.context_lines), line_idx)
        ]

        context_after = [
            lines[i].rstrip()
            for i in range(
                line_idx + 1, min(len(lines), line_idx + self.context_lines + 1)
            )
        ]

        return SearchResult(
            file_path=file_path,
            line_number=line_idx + 1,
            line_content=line.rstrip(),
            matched_text=match.group() if match else "",
            context_before=context_before,
            context_after=context_after,
            match_start=match.start() if match else 0,
            match_end=match.end() if match else 0,
        )

    def _print_results(self, results: SearchResults, files_with_matches: bool) -> None:
        """Print search results."""
        print(
            f"\nFound {results.total_matches} matches in {results.files_with_matches} files"
        )
        print(f"Search time: {results.search_time_ms:.2f}ms")
        print()

        if files_with_matches:
            seen_files = set()
            for result in results.results:
                if result.file_path not in seen_files:
                    print(f"{result.file_path}")
                    seen_files.add(result.file_path)
        else:
            for result in results.results:
                print(f"{result.file_path}:{result.line_number}")
                print(f"  {result.line_content}")

                if result.context_before:
                    print("  ...")
                    for ctx in result.context_before:
                        print(f"    {ctx}")

                print(f"  > {result.matched_text}")

                if result.context_after:
                    for ctx in result.context_after:
                        print(f"    {ctx}")
                print()

    def _to_json(self, results: SearchResults) -> dict:
        """Convert results to JSON-serializable dict."""
        return {
            "query": results.query,
            "total_matches": results.total_matches,
            "files_with_matches": results.files_with_matches,
            "search_time_ms": results.search_time_ms,
            "results": [
                {
                    "file": str(r.file_path),
                    "line": r.line_number,
                    "content": r.line_content,
                    "matched_text": r.matched_text,
                    "context": {"before": r.context_before, "after": r.context_after},
                }
                for r in results.results
            ],
        }


# Convenience function for direct execution
def execute_search(
    query: str,
    path: Path | None = None,
    case_insensitive: bool = False,
    context: int | None = None,
    glob: str | None = None,
    file_type: str | None = None,
    limit: int = 100,
    output_format: str = "text",
    json_file: Path | None = None,
    threads: int | None = None,
    exclude_pattern: str | None = None,
    files_with_matches: bool = False,
) -> SearchCommandResult:
    """Convenience function for search execution."""
    cmd = SearchCommand()
    return cmd.execute(
        query=query,
        path=path,
        case_insensitive=case_insensitive,
        context=context,
        glob=glob,
        file_type=file_type,
        limit=limit,
        output_format=output_format,
        json_file=json_file,
        threads=threads,
        exclude_pattern=exclude_pattern,
        files_with_matches=files_with_matches,
    )
