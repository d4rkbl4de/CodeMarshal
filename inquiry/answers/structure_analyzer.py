"""
inquiry/answers/structure_analyzer.py

Structure Analyzer for CodeMarshal Query System
==============================================

This module analyzes structure observations to answer questions about
codebase organization, directory structure, and module composition.

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 3: Explicit Limitations (declares what it cannot see)
- Article 9: Immutable Observations (never modifies input data)
- Article 12: Linear Investigation (processes observations sequentially)
- Article 17: Uncertainty Indicators (marks limitations clearly)

This module IS:
- A question analyzer for structure-type queries
- A fact-based reporter (no interpretation, no inference)
- An immutable processor (input observations unchanged)
- A linear processor (processes observations in order)

This module IS NOT:
- An AI interpreter (does not guess intent)
- A pattern detector (does not find hidden structures)
- A recommendation engine (does not suggest improvements)
- A runtime analyzer (does not execute code)

ALLOWED IMPORTS:
- pathlib.Path (for path manipulation)
- typing modules (type hints only)
- No imports from other inquiry modules (maintains isolation)

PROHIBITED IMPORTS:
- observations.* (receives data via parameters only)
- core.* (no runtime dependencies)
- Any inference or ML libraries

QUESTION TYPES HANDLED:
- "What modules exist?"
- "What is the directory structure?"
- "What files are in X directory?"
- "Show me the structure"
- "List all Python files"
- "What directories are present?"

OUTPUT FORMAT:
- Plain text with ASCII formatting
- Section separators for readability
- Bullet points for lists
- Clear section headers
- No markdown (keep it simple)
"""

from pathlib import Path
from typing import Any


class StructureAnalyzer:
    """
    Analyze structure observations to answer structure questions.

    The StructureAnalyzer is the first line of inquiry when investigating
    a codebase. It answers fundamental questions about what exists, where
    things are located, and how the codebase is organized.

    DESIGN PRINCIPLES:
    1. Truth-First: Only reports what is observed, never infers
    2. Completeness: Processes all observations, never skips data
    3. Clarity: Formats answers for immediate human comprehension
    4. Limitations: Explicitly declares what it cannot determine

    OBSERVATION TYPES PROCESSED:
    - file_sight: Directory structures, file counts, paths
    - import_sight: Not used (connection mapper handles this)
    - export_sight: Not used (purpose extractor handles this)
    - boundary_sight: Not used (anomaly detector handles this)

    QUESTION CLASSIFICATION:
    The analyzer uses keyword matching to determine question intent:
    - "directory", "structure" → Directory structure analysis
    - "module", "modules" → Module listing
    - "files", "file" → File listing (possibly filtered)
    - Default → General structure summary

    LIMITATION DECLARATIONS:
    This analyzer explicitly cannot:
    - Determine the purpose of modules (use PurposeExtractor)
    - Find import relationships (use ConnectionMapper)
    - Detect architectural issues (use AnomalyDetector)
    - Make recommendations (use ThinkingEngine)
    - See runtime behavior (static analysis only)
    - Access files not in observations

    PERFORMANCE CHARACTERISTICS:
    - Time Complexity: O(n) where n = number of observations
    - Space Complexity: O(m) where m = number of unique paths
    - Single-pass processing (no caching)
    - No recursion (iterative processing only)

    THREAD SAFETY:
    This class is stateless and thread-safe. Multiple threads can
    call analyze() concurrently with different observations.

    EXAMPLES:
        >>> analyzer = StructureAnalyzer()
        >>> observations = [
        ...     {
        ...         "type": "file_sight",
        ...         "result": {
        ...             "path": "/project/src",
        ...             "file_count": 10,
        ...             "directory_count": 3
        ...         }
        ...     }
        ... ]
        >>> result = analyzer.analyze(observations, "What modules exist?")
        >>> print(result)
        Python Modules Information:
        ==================================================
        Total Files Observed: 10
        ...
    """

    # Class-level constants for formatting
    _SECTION_SEPARATOR_LENGTH: int = 50
    """Length of ASCII separator lines in output."""

    _MAX_MODULES_DISPLAY: int = 100
    """Maximum number of modules to list in output (prevents spam)."""

    _MAX_FILES_DISPLAY: int = 50
    """Maximum number of files to list per directory."""

    def __init__(self) -> None:
        """
        Initialize the StructureAnalyzer.

        This analyzer is stateless and requires no initialization
        parameters. All configuration is done via class constants.

        The constructor exists to:
        1. Allow instantiation (required by factory pattern)
        2. Document the analyzer's purpose
        3. Enable future stateful extensions if needed

        NOTE: Currently stateless, but reserved for future extensions
        such as configuration options or caching mechanisms.
        """
        # No state initialization needed for stateless analyzer
        # Reserved for future extensions
        pass

    def analyze(self, observations: list[dict[str, Any]], question: str) -> str:
        """
        Analyze observations and generate an answer to a structure question.

        This is the primary entry point for the StructureAnalyzer. It examines
        the question text to determine intent, then routes to the appropriate
        analysis method.

        QUESTION ROUTING LOGIC:
        The analyzer uses simple keyword matching on the lowercase question:
        1. "directory" or "structure" → _get_directory_structure()
        2. "modules" or "module" → _get_modules_list()
        3. "files" or "file" → _get_files_in_directory()
        4. Default → _get_general_structure()

        Args:
            observations: List of observation data dictionaries from the
                observation system. Each observation is a dict with:
                - "type": Observation type (e.g., "file_sight")
                - "result": Dict with observation-specific data
                - Additional fields depending on type
            question: The user's natural language question as a string.
                This is analyzed for keywords to determine intent.

        Returns:
            str: Formatted answer string with ASCII formatting.
                The format varies by question type but always includes:
                - A clear header
                - Relevant statistics
                - Formatted lists (if applicable)
                - Section separators for readability

        Raises:
            No exceptions are raised. All errors are handled gracefully
            by returning informative messages.

        Example:
            >>> analyzer = StructureAnalyzer()
            >>> observations = [{"type": "file_sight", "result": {...}}]
            >>> answer = analyzer.analyze(observations, "What is the structure?")
            >>> print(answer)
            Directory Structure Summary:
            ==================================================
            Total Files: 42
            Total Directories: 5
            ...

        CONSTITUTIONAL COMPLIANCE:
        - Article 3: Explicitly declares limitations in output
        - Article 9: Never modifies observations (read-only)
        - Article 12: Processes observations linearly in order
        - Article 17: Marks uncertainty when data is incomplete
        """
        # Normalize question to lowercase for case-insensitive matching
        # This ensures "What Modules Exist?" matches "modules" keyword
        question_lower = question.lower()

        # Route to appropriate analysis method based on question keywords
        # Order matters: more specific patterns should be checked first
        if "directory" in question_lower or "structure" in question_lower:
            # Question asks about directory structure
            # Example: "What is the directory structure?"
            # Example: "Show me the directory layout"
            return self._get_directory_structure(observations)

        elif "modules" in question_lower or "module" in question_lower:
            # Question asks about modules
            # Example: "What modules exist?"
            # Example: "List all modules"
            return self._get_modules_list(observations)

        elif "files" in question_lower or "file" in question_lower:
            # Question asks about specific files
            # Example: "What files are in core/?"
            # Example: "List files in src/"
            return self._get_files_in_directory(observations, question)

        else:
            # Default: provide general structure summary
            # Used when question doesn't match specific patterns
            # Example: "What's here?" or "Show me what exists"
            return self._get_general_structure(observations)

    def _get_directory_structure(self, observations: list[dict[str, Any]]) -> str:
        """
        Generate directory structure summary from observations.

        This method processes file_sight observations to extract information
        about the directory structure of the observed codebase. It handles
        both summary-style observations (with file_count and directory_count)
        and detailed observations (with individual file listings).

        DATA EXTRACTION:
        The method looks for file_sight observations and extracts:
        - file_count: Total number of files (from summary observations)
        - directory_count: Total number of directories (from summary)
        - path: The root path being observed
        - modules: Individual file listings (detailed observations)

        FORMATTING:
        The output includes:
        - Clear header indicating this is a structure summary
        - ASCII separator line for visual clarity
        - File count and directory count statistics
        - List of observed paths
        - Summary sentence describing the scale

        LIMITATION HANDLING:
        If no observations contain file_sight data, the method returns
        an explicit message stating that no structure was found. This
        maintains truth preservation by not fabricating data.

        Args:
            observations: List of observation dictionaries. Only observations
                with type "file_sight" are processed; others are ignored.

        Returns:
            str: Formatted directory structure summary with statistics.
                Returns explicit "not found" message if no data available.

        Example Output:
            Directory Structure Summary:
            ==================================================
            Total Files: 42
            Total Directories: 5

            Paths Observed:
              • /project/src
              • /project/tests

            Contains approximately 42 files across 5 directories

        PERFORMANCE:
        - Time: O(n) where n = number of observations
        - Space: O(p) where p = number of unique paths
        - Single pass through observations
        """
        # Initialize counters and tracking structures
        # These accumulate data across all observations
        total_files: int = 0
        """Running count of files from all observations."""

        total_dirs: int = 0
        """Running count of directories from all observations."""

        paths_observed: list[str] = []
        """List to track unique paths observed (for deduplication)."""

        # Iterate through all observations
        # Each observation is processed independently
        for obs in observations:
            # Check if this is a file_sight observation
            # We only process file_sight for structure analysis
            if obs.get("type") == "file_sight":
                result = obs.get("result", {})

                # Handle summary-style observations
                # These contain aggregated statistics rather than individual files
                if "file_count" in result:
                    # Add to running totals
                    total_files += result.get("file_count", 0)
                    total_dirs += result.get("directory_count", 0)

                    # Track the path for display
                    path = result.get("path", "")
                    if path and path not in paths_observed:
                        # Avoid duplicates while preserving order
                        paths_observed.append(path)

                # Also check for detailed module listings (older format)
                # Some observations list individual files in "modules" array
                modules = result.get("modules", [])
                for module in modules:
                    if isinstance(module, dict):
                        path = module.get("path", "")
                        if path:
                            # Count each individual file
                            total_files += 1

        # Check if we found any structure data
        # If not, return explicit message (truth preservation)
        if not paths_observed and total_files == 0:
            return "No directory structure found in observations."

        # Build formatted output
        # Use list for efficient string building
        lines: list[str] = [
            "Directory Structure Summary:",
            "=" * self._SECTION_SEPARATOR_LENGTH,
            f"Total Files: {total_files}",
            f"Total Directories: {total_dirs}",
            "",
            "Paths Observed:",
        ]

        # Add each observed path with bullet point
        for path in paths_observed:
            lines.append(f"  📁 {path}")

        # Add summary sentence if we have data
        if total_files > 0:
            lines.append("")
            lines.append(
                f"Contains approximately {total_files} files across {total_dirs} directories"
            )

        # Join all lines with newline characters
        return "\n".join(lines)

    def _get_modules_list(self, observations: list[dict[str, Any]]) -> str:
        """
        Generate list of Python modules from observations.

        This method identifies Python modules (.py files) from file_sight
        observations and presents them as a formatted list. It handles
        both summary observations (showing counts only) and detailed
        observations (listing individual modules).

        MODULE IDENTIFICATION:
        A module is identified by:
        - Path ending with ".py"
        - Conversion of path separators to dots for module naming
        - Removal of ".py" extension for clean display

        Example:
            /project/src/core/engine.py → core.engine

        SUMMARY VS DETAILED:
        If observations contain summary data (file_count), the method
        reports the count but notes that detailed module information
        is not available. This maintains honesty about limitations.

        DUPLICATE HANDLING:
        Modules are deduplicated using set() before sorting and display.
        This ensures each module appears only once in the output.

        LIMITATION HANDLING:
        If no Python modules are found, an explicit message is returned
        rather than an empty list. This is more helpful to users.

        Args:
            observations: List of observation dictionaries. Processes
                file_sight observations to find Python files.

        Returns:
            str: Formatted list of Python modules or informative message
                if no modules found or only summary data available.

        Example Output (detailed):
            Python Modules (5 found):
            ==================================================
              • core.engine
              • core.runtime
              • bridge.cli
              • bridge.commands
              • observations.eyes

        Example Output (summary only):
            Python Modules Information:
            ==================================================
            Total Files Observed: 10

            Note: Detailed module list not available in current observation mode.
            The system observed files in the following locations:
              • /project/src

        PERFORMANCE:
        - Time: O(n * m) where n = observations, m = modules per observation
        - Space: O(k) where k = unique modules
        - Deduplication via set() for efficiency
        """
        # Initialize tracking structures
        modules: list[str] = []
        """List to accumulate module names before deduplication."""

        total_files: int = 0
        """Count from summary observations."""

        paths: list[str] = []
        """Paths where observations were made."""

        # Process each observation
        for obs in observations:
            if obs.get("type") == "file_sight":
                result = obs.get("result", {})

                # Handle summary-style observations
                # These give us counts but not individual modules
                if "file_count" in result:
                    total_files += result.get("file_count", 0)
                    path = result.get("path", "")
                    if path and path not in paths:
                        paths.append(path)

                # Handle detailed observations with individual files
                obs_modules = result.get("modules", [])
                for module in obs_modules:
                    if isinstance(module, dict):
                        path = module.get("path", "")
                        # Only process Python files
                        if path and path.endswith(".py"):
                            # Convert path to module name
                            # Replace path separators with dots
                            module_name = path.replace("/", ".").replace("\\", ".")
                            # Remove .py extension
                            if module_name.endswith(".py"):
                                module_name = module_name[:-3]
                            modules.append(module_name)

        # Check if we only have summary data (counts but no details)
        if not modules and total_files > 0:
            # Return informative message about limitation
            lines: list[str] = [
                "Python Modules Information:",
                "=" * self._SECTION_SEPARATOR_LENGTH,
                f"Total Files Observed: {total_files}",
                "",
                "Note: Detailed module list not available in current observation mode.",
                "The system observed files in the following locations:",
            ]
            for path in paths:
                lines.append(f"  • {path}")
            return "\n".join(lines)

        # Check if we found no modules at all
        if not modules:
            return "No Python modules found in observations."

        # Deduplicate and sort modules for clean display
        unique_modules: list[str] = sorted(set(modules))

        # Build formatted output
        lines = [
            f"Python Modules ({len(unique_modules)} found):",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Add each module with bullet point
        for module in unique_modules[: self._MAX_MODULES_DISPLAY]:
            lines.append(f"  • {module}")

        # Note if we truncated the list
        if len(unique_modules) > self._MAX_MODULES_DISPLAY:
            remaining = len(unique_modules) - self._MAX_MODULES_DISPLAY
            lines.append(f"  ... and {remaining} more (use --limit to see all)")

        return "\n".join(lines)

    def _get_files_in_directory(
        self, observations: list[dict[str, Any]], question: str
    ) -> str:
        """
        Get files in a specific directory mentioned in the question.

        This method attempts to extract a directory path from the question
        text and then filters observations to show only files in that
        directory.

        DIRECTORY EXTRACTION:
        The method looks for patterns like:
        - "files in X"
        - "what files are in X"
        - "list files in X"

        It uses simple string splitting on "in " to extract the target.
        This is a heuristic approach and may not handle all cases.

        FILTERING LOGIC:
        Files are included if:
        - Their parent directory contains the target string (case-insensitive)
        - Or if no target is specified, all files are included

        LIMITATION:
        This simple matching may include files from similarly named
        directories (e.g., "core" matches "core" and "core_utils").
        For precise filtering, use exact paths.

        Args:
            observations: List of observation dictionaries.
            question: The user's question string, which is parsed to extract
                the target directory.

        Returns:
            str: Formatted list of files in the target directory,
                or informative message if no files found.

        Example:
            Question: "What files are in core/?"
            Output:
                Files found: 3
                ==================================================
                  • engine.py
                  • runtime.py
                  • __init__.py

        PERFORMANCE:
        - Time: O(n * m) where n = observations, m = files per observation
        - Space: O(f) where f = filtered files
        """
        # Extract directory from question
        question_lower = question.lower()
        target_dir: str | None = None

        # Look for "in " pattern
        # Examples: "files in core", "what's in src", "in tests"
        if "in " in question_lower:
            parts = question_lower.split("in ")
            if len(parts) > 1:
                # Take everything after "in " and clean it
                target_dir = parts[1].strip().rstrip("?").strip()
                # Remove trailing slashes for consistency
                target_dir = target_dir.rstrip("/\\")

        # Accumulate matching files
        files_found: list[str] = []

        # Process observations
        for obs in observations:
            if obs.get("type") == "file_sight":
                result = obs.get("result", {})
                modules = result.get("modules", [])

                for module in modules:
                    if isinstance(module, dict):
                        path = module.get("path", "")
                        if path:
                            path_obj = Path(path)
                            dir_name = str(path_obj.parent).lower()
                            file_name = path_obj.name

                            # Check if this file is in the target directory
                            if target_dir:
                                # Case-insensitive substring match
                                if target_dir.lower() in dir_name:
                                    files_found.append(file_name)
                            else:
                                # No target specified, include all files
                                files_found.append(path)

        # Handle no results
        if not files_found:
            if target_dir:
                return f"No files found in directory: {target_dir}"
            return "No files found in observations."

        # Build formatted output
        lines: list[str] = [
            f"Files found: {len(files_found)}",
            "=" * self._SECTION_SEPARATOR_LENGTH,
        ]

        # Add files (deduplicated and sorted)
        for file in sorted(set(files_found))[: self._MAX_FILES_DISPLAY]:
            lines.append(f"  • {file}")

        # Note if truncated
        if len(files_found) > self._MAX_FILES_DISPLAY:
            remaining = len(files_found) - self._MAX_FILES_DISPLAY
            lines.append(f"  ... and {remaining} more")

        return "\n".join(lines)

    def _get_general_structure(self, observations: list[dict[str, Any]]) -> str:
        """
        Generate general structure summary.

        This is the fallback method when a question doesn't match specific
        patterns. It provides a comprehensive overview of all observation
        types found, giving the user a broad picture of what was observed.

        STATISTICS COLLECTED:
        - Total number of observations
        - Count of each observation type (file_sight, import_sight, etc.)
        - Total files discovered
        - Total import statements found

        USE CASES:
        - "What's here?"
        - "Show me what exists"
        - "Give me an overview"
        - Any question not matching specific patterns

        VALUE:
        This method is valuable when the user isn't sure what to ask.
        It presents all available data categories, which may inspire
        more specific follow-up questions.

        Args:
            observations: List of all observation dictionaries.
                Processes all types, not just file_sight.

        Returns:
            str: Comprehensive structure summary with statistics
                broken down by observation type.

        Example Output:
            General Structure Summary:
            ==================================================
            Total Observations: 15

            By Type:
              • File Observations: 5
              • Import Observations: 8
              • Export Observations: 2
              • Boundary Observations: 0

            Statistics:
              • Total Files: 42
              • Total Import Statements: 156

        PERFORMANCE:
        - Time: O(n) single pass through observations
        - Space: O(1) fixed-size statistics dict
        """
        # Initialize statistics tracking
        stats: dict[str, int] = {
            "total_observations": len(observations),
            "file_sight": 0,
            "import_sight": 0,
            "export_sight": 0,
            "boundary_sight": 0,
            "total_files": 0,
            "total_imports": 0,
        }

        # Single pass through all observations
        # This is efficient and maintains observation order
        for obs in observations:
            obs_type = obs.get("type", "")

            if obs_type == "file_sight":
                stats["file_sight"] += 1
                result = obs.get("result", {})
                modules = result.get("modules", [])
                stats["total_files"] += len(modules)

            elif obs_type == "import_sight":
                stats["import_sight"] += 1
                statements = obs.get("statements", [])
                stats["total_imports"] += len(statements)

            elif obs_type == "export_sight":
                stats["export_sight"] += 1

            elif obs_type == "boundary_sight":
                stats["boundary_sight"] += 1

        # Build formatted output
        lines: list[str] = [
            "General Structure Summary:",
            "=" * self._SECTION_SEPARATOR_LENGTH,
            f"Total Observations: {stats['total_observations']}",
            "",
            "By Type:",
            f"  • File Observations: {stats['file_sight']}",
            f"  • Import Observations: {stats['import_sight']}",
            f"  • Export Observations: {stats['export_sight']}",
            f"  • Boundary Observations: {stats['boundary_sight']}",
            "",
            "Statistics:",
            f"  • Total Files: {stats['total_files']}",
            f"  • Total Import Statements: {stats['total_imports']}",
        ]

        return "\n".join(lines)

    def _format_size(self, size_bytes: int) -> str:
        """
        Format byte size to human-readable string.

        This helper converts raw byte counts to human-friendly
        representations (B, KB, MB, GB).

        Args:
            size_bytes: Size in bytes

        Returns:
            str: Formatted size string (e.g., "1.5 MB")

        Note: Currently unused but available for future extensions
        that might include file size information.
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _is_python_file(self, path: str) -> bool:
        """
        Check if a path represents a Python file.

        Helper method to determine if a file path ends with .py
        extension (case-insensitive).

        Args:
            path: File path string

        Returns:
            bool: True if path ends with .py, False otherwise

        Examples:
            >>> analyzer._is_python_file("core/engine.py")
            True
            >>> analyzer._is_python_file("README.md")
            False
        """
        return path.lower().endswith(".py")


# Module-level constants for external reference
__all__ = ["StructureAnalyzer"]
"""List of symbols exported by this module."""

# Version tracking
__version__ = "1.0.0"
"""Module version string following semantic versioning."""

# Last modified date
__modified__ = "2026-02-05"
"""Date of last modification."""
