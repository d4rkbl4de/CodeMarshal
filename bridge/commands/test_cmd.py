"""
bridge.commands.test - Test CLI command

This module provides the test command for running CodeMarshal's test suite.

Command:
- test: Run pytest test suite with various options
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TestResult:
    """Result of test command."""

    success: bool
    exit_code: int = 0
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    coverage_percent: float | None = None
    output: str = ""
    errors: list[str] = field(default_factory=list)
    message: str = ""


class TestCommand:
    """Test command implementation."""

    def execute(
        self,
        path: Path | None = None,
        pattern: str = "test_*.py",
        coverage: bool = False,
        fail_fast: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        markers: list[str] | None = None,
        ignore: list[str] | None = None,
        parallel: bool = False,
        junit_xml: Path | None = None,
        html_report: Path | None = None,
        show_locals: bool = False,
        tb_style: str = "short",
        last_failed: bool = False,
        no_header: bool = False,
    ) -> TestResult:
        """
        Execute test command.

        Args:
            path: Test directory or file (default: tests/)
            pattern: Test file pattern
            coverage: Enable coverage reporting
            fail_fast: Stop on first failure
            verbose: Verbose output
            quiet: Minimal output
            markers: Only run tests with these markers
            ignore: Ignore these test files/directories
            parallel: Run tests in parallel
            junit_xml: Output JUnit XML report to this file
            html_report: Output HTML coverage report to this directory
            show_locals: Show local variables in tracebacks
            tb_style: Traceback style (auto/long/short/line/native/no)
            last_failed: Run only previously failed tests
            no_header: Suppress header output

        Returns:
            TestResult with test execution results
        """
        target_path = path or Path("tests")

        if not target_path.exists():
            return TestResult(
                success=False,
                exit_code=1,
                errors=[f"Test path does not exist: {target_path}"],
                message="Test path not found",
            )

        # Build pytest arguments
        pytest_args = ["pytest"]

        # Test path
        pytest_args.append(str(target_path))

        # Verbosity
        if verbose:
            pytest_args.append("-v")
        elif quiet:
            pytest_args.append("-q")

        # Pattern
        if pattern and pattern != "test_*.py":
            pytest_args.extend(["-k", pattern])

        # Fail fast
        if fail_fast:
            pytest_args.append("-x")

        # Coverage
        if coverage:
            pytest_args.extend(["--cov", "."])
            pytest_args.extend(["--cov-report", "term-missing"])
            if html_report:
                pytest_args.extend(["--cov-report", f"html:{html_report}"])

        # Markers
        if markers:
            for marker in markers:
                pytest_args.extend(["-m", marker])

        # Ignore
        if ignore:
            for item in ignore:
                pytest_args.extend(["--ignore", item])

        # Parallel execution
        if parallel:
            pytest_args.extend(["-n", "auto"])

        # JUnit XML output
        if junit_xml:
            pytest_args.extend(["--junitxml", str(junit_xml)])

        # Show locals
        if show_locals:
            pytest_args.append("--showlocals")

        # Traceback style
        if tb_style != "auto":
            pytest_args.extend(["--tb", tb_style])

        # Last failed
        if last_failed:
            pytest_args.append("--lf")

        # No header
        if no_header:
            pytest_args.append("--no-header")

        # Capture output
        try:
            result = subprocess.run(
                pytest_args,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Parse output
            output = result.stdout + result.stderr

            # Parse test counts from output
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            tests_skipped = 0
            coverage_percent = None

            # Parse pytest summary line
            # Example: "============================= 50 passed, 2 failed, 3 skipped in 12.34s ============================="
            for line in output.split("\n"):
                if "passed" in line or "failed" in line or "skipped" in line:
                    # Try to parse counts
                    import re

                    # Find numbers followed by status words
                    patterns = [
                        (r"(\d+) passed", "passed"),
                        (r"(\d+) failed", "failed"),
                        (r"(\d+) skipped", "skipped"),
                        (r"(\d+) error", "error"),
                    ]

                    for pattern, status in patterns:
                        match = re.search(pattern, line)
                        if match:
                            count = int(match.group(1))
                            if status == "passed":
                                tests_passed = count
                            elif status == "failed":
                                tests_failed = count
                            elif status == "skipped":
                                tests_skipped = count

                    tests_run = tests_passed + tests_failed + tests_skipped
                    break

            # Parse coverage percentage
            # Example: "TOTAL                              1500    120    92%"
            if coverage:
                for line in output.split("\n"):
                    if "TOTAL" in line and "%" in line:
                        import re

                        match = re.search(r"(\d+)%", line)
                        if match:
                            coverage_percent = float(match.group(1))
                            break

            return TestResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                tests_skipped=tests_skipped,
                coverage_percent=coverage_percent,
                output=output,
                message=f"Tests completed: {tests_passed} passed, {tests_failed} failed, {tests_skipped} skipped",
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                exit_code=1,
                errors=["Test execution timed out (5 minutes)"],
                message="Test timeout",
            )
        except FileNotFoundError:
            return TestResult(
                success=False,
                exit_code=1,
                errors=["pytest not found. Install with: pip install pytest"],
                message="pytest not installed",
            )
        except Exception as e:
            return TestResult(
                success=False,
                exit_code=1,
                errors=[f"Test execution failed: {e}"],
                message=f"Test error: {e}",
            )


# Convenience function for direct execution
def execute_test(
    path: Path | None = None,
    pattern: str = "test_*.py",
    coverage: bool = False,
    fail_fast: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    markers: list[str] | None = None,
    ignore: list[str] | None = None,
    parallel: bool = False,
    junit_xml: Path | None = None,
    html_report: Path | None = None,
    show_locals: bool = False,
    tb_style: str = "short",
    last_failed: bool = False,
    no_header: bool = False,
) -> TestResult:
    """Convenience function for test execution."""
    cmd = TestCommand()
    return cmd.execute(
        path=path,
        pattern=pattern,
        coverage=coverage,
        fail_fast=fail_fast,
        verbose=verbose,
        quiet=quiet,
        markers=markers,
        ignore=ignore,
        parallel=parallel,
        junit_xml=junit_xml,
        html_report=html_report,
        show_locals=show_locals,
        tb_style=tb_style,
        last_failed=last_failed,
        no_header=no_header,
    )
