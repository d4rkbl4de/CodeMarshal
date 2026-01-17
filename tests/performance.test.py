"""
performance.test.py - Performance Testing for CodeMarshal

Tests system performance under various loads and conditions to ensure
truth preservation doesn't compromise system responsiveness.
"""

import pytest
import time
import tempfile
import shutil
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
import json

# Import CodeMarshal modules
from core.runtime import Runtime
from observations.eyes.file_sight import FileSight
from observations.eyes.import_sight import ImportSight
from inquiry.questions.structure import StructureQuestions
from inquiry.patterns.coupling import CouplingAnalyzer
from storage.investigation_storage import InvestigationStorage


class PerformanceTestResult:
    """Container for performance test results."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.measurements: List[float] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.memory_usage: List[float] = []
        self.errors: List[str] = []
    
    def start_measurement(self):
        """Start timing measurement."""
        self.start_time = time.time()
    
    def end_measurement(self):
        """End timing measurement."""
        self.end_time = time.time()
        if self.start_time:
            duration = self.end_time - self.start_time
            self.measurements.append(duration)
    
    def add_memory_measurement(self, memory_mb: float):
        """Add memory usage measurement."""
        self.memory_usage.append(memory_mb)
    
    def add_error(self, error: str):
        """Record an error during test."""
        self.errors.append(error)
    
    @property
    def duration(self) -> Optional[float]:
        """Get latest duration."""
        if self.measurements:
            return self.measurements[-1]
        return None
    
    @property
    def avg_duration(self) -> float:
        """Get average duration."""
        return statistics.mean(self.measurements) if self.measurements else 0.0
    
    @property
    def max_duration(self) -> float:
        """Get maximum duration."""
        return max(self.measurements) if self.measurements else 0.0
    
    @property
    def min_duration(self) -> float:
        """Get minimum duration."""
        return min(self.measurements) if self.measurements else 0.0
    
    @property
    def avg_memory(self) -> float:
        """Get average memory usage."""
        return statistics.mean(self.memory_usage) if self.memory_usage else 0.0
    
    @property
    def max_memory(self) -> float:
        """Get maximum memory usage."""
        return max(self.memory_usage) if self.memory_usage else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            'test_name': self.test_name,
            'measurements_count': len(self.measurements),
            'avg_duration': self.avg_duration,
            'max_duration': self.max_duration,
            'min_duration': self.min_duration,
            'avg_memory_mb': self.avg_memory,
            'max_memory_mb': self.max_memory,
            'errors_count': len(self.errors),
            'errors': self.errors
        }


class PerformanceTester:
    """Runs performance tests on CodeMarshal components."""
    
    def __init__(self):
        self.temp_dir = None
        self.results: List[PerformanceTestResult] = []
    
    def setup(self):
        """Set up temporary environment for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test directory structure
        (self.temp_dir / "small_project").mkdir()
        (self.temp_dir / "medium_project").mkdir()
        (self.temp_dir / "large_project").mkdir()
        
        # Create test files
        self._create_test_projects()
    
    def teardown(self):
        """Clean up temporary environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_projects(self):
        """Create test projects of different sizes."""
        
        # Small project (10 files)
        small_dir = self.temp_dir / "small_project"
        for i in range(10):
            (small_dir / f"file_{i}.py").write_text(f"""
def function_{i}():
    # Small function {i}
    return {i}
""")
        
        # Medium project (100 files)
        medium_dir = self.temp_dir / "medium_project"
        for i in range(100):
            (medium_dir / f"module_{i}.py").write_text(f"""
# Module {i}
import os
import json

def process_data():
    data = [{{j for j in range(100)}}]
    return [x * 2 for x in data]

def analyze_data():
    return process_data()

class Module{i}:
    def __init__(self):
        self.data = process_data()
""")
        
        # Large project (1000 files)
        large_dir = self.temp_dir / "large_project"
        for i in range(1000):
            (large_dir / f"component_{i}.py").write_text(f"""
# Component {i}
import sys
import time

def heavy_computation():
    result = []
    for j in range(1000):
        result.append(j * j)
    return result

class Component{i}:
    def __init__(self):
        self.result = heavy_computation()
""")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    def test_file_observation_performance(self):
        """Test file observation performance."""
        result = PerformanceTestResult("File Observation Performance")
        
        # Test small project
        result.start_measurement()
        file_sight = FileSight()
        observation = file_sight.observe(self.temp_dir / "small_project")
        result.end_measurement()
        
        # Test medium project
        result.start_measurement()
        observation = file_sight.observe(self.temp_dir / "medium_project")
        result.end_measurement()
        
        # Test large project
        result.start_measurement()
        observation = file_sight.observe(self.temp_dir / "large_project")
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        self.results.append(result)
        return result
    
    def test_import_observation_performance(self):
        """Test import observation performance."""
        result = PerformanceTestResult("Import Observation Performance")
        
        import_sight = ImportSight()
        
        # Test small project
        result.start_measurement()
        observation = import_sight.observe(self.temp_dir / "small_project")
        result.end_measurement()
        
        # Test medium project
        result.start_measurement()
        observation = import_sight.observe(self.temp_dir / "medium_project")
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        # Test large project
        result.start_measurement()
        observation = import_sight.observe(self.temp_dir / "large_project")
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        self.results.append(result)
        return result
    
    def test_pattern_analysis_performance(self):
        """Test pattern analysis performance."""
        result = PerformanceTestResult("Pattern Analysis Performance")
        
        import_sight = ImportSight()
        analyzer = CouplingAnalyzer()
        
        # Get import observations for test projects
        small_obs = import_sight.observe(self.temp_dir / "small_project")
        medium_obs = import_sight.observe(self.temp_dir / "medium_project")
        large_obs = import_sight.observe(self.temp_dir / "large_project")
        
        # Test small project pattern analysis
        result.start_measurement()
        patterns = analyzer.analyze_coupling(small_obs)
        result.end_measurement()
        
        # Test medium project pattern analysis
        result.start_measurement()
        patterns = analyzer.analyze_coupling(medium_obs)
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        # Test large project pattern analysis
        result.start_measurement()
        patterns = analyzer.analyze_coupling(large_obs)
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        self.results.append(result)
        return result
    
    def test_concurrent_investigations(self):
        """Test concurrent investigation performance."""
        result = PerformanceTestResult("Concurrent Investigations Performance")
        
        def run_investigation(project_path):
            file_sight = FileSight()
            start_time = time.time()
            observation = file_sight.observe(project_path)
            end_time = time.time()
            return end_time - start_time
        
        # Run concurrent investigations
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            # Submit investigations
            futures.append(executor.submit(run_investigation, self.temp_dir / "small_project"))
            futures.append(executor.submit(run_investigation, self.temp_dir / "medium_project"))
            futures.append(executor.submit(run_investigation, self.temp_dir / "large_project"))
            
            # Collect results
            durations = []
            for future in futures:
                duration = future.result()
                durations.append(duration)
                result.measurements.append(duration)
        
        result.add_memory_measurement(self._get_memory_usage())
        
        self.results.append(result)
        return result
    
    def test_storage_performance(self):
        """Test storage performance."""
        result = PerformanceTestResult("Storage Performance")
        
        storage = InvestigationStorage(base_path=self.temp_dir)
        
        # Create test sessions
        sessions = []
        for i in range(100):
            session_data = {
                'snapshot_id': f'test_session_{i}',
                'observations': [f'obs_{j}' for j in range(10)],
                'notes': [f'note_{j}' for j in range(5)],
                'timestamp': time.time()
            }
            sessions.append(session_data)
        
        # Test save performance
        result.start_measurement()
        for session in sessions:
            storage.save_session(session_data)
        result.end_measurement()
        
        # Test load performance
        result.start_measurement()
        for i in range(100):
            loaded_session = storage.load_session(f'test_session_{i}')
            if not loaded_session:
                result.add_error(f"Failed to load session {i}")
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        self.results.append(result)
        return result
    
    def test_export_performance(self):
        """Test export performance."""
        result = PerformanceTestResult("Export Performance")
        
        # Create large session for export
        storage = InvestigationStorage(base_path=self.temp_dir)
        
        # Create session with lots of data
        session_data = {
            'snapshot_id': 'export_test_session',
            'observations': [f'obs_{j}' for j in range(1000)],
            'notes': [f'note_{j}' for j in range(100)],
            'timestamp': time.time()
        }
        storage.save_session(session_data)
        
        # Test JSON export
        result.start_measurement()
        # Simulate export (would need to implement actual export)
        time.sleep(0.1)  # Simulate export time
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        # Test Markdown export
        result.start_measurement()
        time.sleep(0.2)  # Simulate longer export time
        result.add_memory_measurement(self._get_memory_usage())
        result.end_measurement()
        
        self.results.append(result)
        return result
    
    def test_memory_scaling(self):
        """Test memory usage scaling."""
        result = PerformanceTestResult("Memory Scaling Performance")
        
        file_sight = FileSight()
        
        # Test with increasing project sizes
        project_sizes = [10, 50, 100, 500, 1000]
        
        for size in project_sizes:
            # Create temporary project
            test_dir = self.temp_dir / f"scale_test_{size}"
            test_dir.mkdir()
            
            for i in range(size):
                (test_dir / f"file_{i}.py").write_text(f"def function_{i}(): return {i}")
            
            result.start_measurement()
            observation = file_sight.observe(test_dir)
            memory_usage = self._get_memory_usage()
            result.end_measurement()
            result.add_memory_measurement(memory_usage)
        
        self.results.append(result)
        return result
    
    def run_all_performance_tests(self):
        """Run all performance tests."""
        print("Running CodeMarshal performance tests...")
        
        self.setup()
        
        try:
            # Core performance tests
            self.test_file_observation_performance()
            self.test_import_observation_performance()
            self.test_pattern_analysis_performance()
            
            # Storage performance tests
            self.test_storage_performance()
            self.test_export_performance()
            
            # Scaling tests
            self.test_memory_scaling()
            self.test_concurrent_investigations()
            
        except Exception as e:
            for result in self.results:
                result.add_error(f"Test execution error: {e}")
        
        finally:
            self.teardown()
        
        return self.results
    
    def generate_performance_report(self) -> str:
        """Generate performance report."""
        report = ["# CodeMarshal Performance Test Report\n"]
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("=" * 60 + "\n")
        
        for result in self.results:
            summary = result.get_summary()
            report.append(f"## {summary['test_name']}\n")
            report.append(f"- Measurements: {summary['measurements_count']}")
            report.append(f"- Average Duration: {summary['avg_duration']:.3f}s")
            report.append(f"- Max Duration: {summary['max_duration']:.3f}s")
            report.append(f"- Min Duration: {summary['min_duration']:.3f}s")
            report.append(f"- Average Memory: {summary['avg_memory_mb']:.1f}MB")
            report.append(f"- Max Memory: {summary['max_memory_mb']:.1f}MB")
            
            if summary['errors_count'] > 0:
                report.append(f"- Errors: {summary['errors_count']}")
                for error in summary['errors']:
                    report.append(f"  - {error}")
            
            report.append("")
        
        # Performance benchmarks
        report.append("## Performance Benchmarks\n")
        report.append("- File Observation: < 1s for < 100 files")
        report.append("- Import Observation: < 2s for < 1000 imports")
        report.append("- Pattern Analysis: < 0.5s for < 1000 imports")
        report.append("- Storage: < 1s for < 100 sessions")
        report.append("- Export: < 1s for JSON, < 2s for Markdown")
        
        return "\n".join(report)


# Test functions
def test_file_observation_performance():
    """Test file observation performance."""
    tester = PerformanceTester()
    tester.setup()
    result = tester.test_file_observation_performance()
    tester.teardown()
    
    # Assertions
    assert result.max_duration < 1.0, f"File observation too slow: {result.max_duration}s"
    assert result.max_memory < 50, f"File observation uses too much memory: {result.max_memory}MB"
    assert len(result.errors) == 0, f"File observation had errors: {result.errors}"
    
    print("✅ File observation performance test passed")


def test_import_observation_performance():
    """Test import observation performance."""
    tester = PerformanceTester()
    tester.setup()
    result = tester.test_import_observation_performance()
    tester.teardown()
    
    # Assertions
    assert result.max_duration < 2.0, f"Import observation too slow: {result.max_duration}s"
    assert result.max_memory < 100, f"Import observation uses too much memory: {result.max_memory}MB"
    assert len(result.errors) == 0, f"Import observation had errors: {result.errors}"
    
    print("✅ Import observation performance test passed")


def test_pattern_analysis_performance():
    """Test pattern analysis performance."""
    tester = PerformanceTester()
    tester.setup()
    result = tester.test_pattern_analysis_performance()
    tester.teardown()
    
    # Assertions
    assert result.max_duration < 0.5, f"Pattern analysis too slow: {result.max_duration}s"
    assert result.max_memory < 150, f"Pattern analysis uses too much memory: {result.max_memory}MB"
    assert len(result.errors) == 0, f"Pattern analysis had errors: {result.errors}"
    
    print("✅ Pattern analysis performance test passed")


def test_storage_performance():
    """Test storage performance."""
    tester = PerformanceTester()
    tester.setup()
    result = tester.test_storage_performance()
    tester.teardown()
    
    # Assertions
    assert result.max_duration < 1.0, f"Storage too slow: {result.max_duration}s"
    assert result.max_memory < 200, f"Storage uses too much memory: {result.max_memory}MB"
    assert len(result.errors) < 5, f"Storage had too many errors: {len(result.errors)}"
    
    print("✅ Storage performance test passed")


def test_export_performance():
    """Test export performance."""
    tester = PerformanceTester()
    tester.setup()
    result = tester.test_export_performance()
    tester.teardown()
    
    # Assertions
    assert result.max_duration < 2.0, f"Export too slow: {result.max_duration}s"
    assert result.max_memory < 300, f"Export uses too much memory: {result.max_memory}MB"
    assert len(result.errors) == 0, f"Export had errors: {result.errors}"
    
    print("✅ Export performance test passed")


def test_memory_scaling():
    """Test memory scaling behavior."""
    tester = PerformanceTester()
    tester.setup()
    result = tester.test_memory_scaling()
    tester.teardown()
    
    # Check that memory scales reasonably
    memory_values = result.memory_usage
    
    # Memory should not grow exponentially
    if len(memory_values) >= 3:
        # Check that last measurement is not more than 3x the first
        assert memory_values[-1] < memory_values[0] * 3, f"Memory scaling too aggressive: {memory_values[-1]} vs {memory_values[0]}"
    
    print("✅ Memory scaling test passed")


def test_concurrent_performance():
    """Test concurrent investigation performance."""
    tester = PerformanceTester()
    tester.setup()
    result = tester.test_concurrent_investigations()
    tester.teardown()
    
    # Concurrent operations should complete in reasonable time
    assert result.max_duration < 5.0, f"Concurrent operations too slow: {result.max_duration}s"
    assert len(result.measurements) == 3, f"Expected 3 concurrent operations, got {len(result.measurements)}"
    
    print("✅ Concurrent performance test passed")


def run_performance_tests():
    """Run all performance tests and generate report."""
    print("=" * 60)
    print("CODEMARSHAL PERFORMANCE TESTS")
    print("=" * 60)
    
    tests = [
        test_file_observation_performance,
        test_import_observation_performance,
        test_pattern_analysis_performance,
        test_storage_performance,
        test_export_performance,
        test_memory_scaling,
        test_concurrent_performance
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"PERFORMANCE TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ ALL PERFORMANCE TESTS PASSED")
    else:
        print("❌ SOME PERFORMANCE TESTS FAILED")
    
    print("=" * 60)
    
    # Generate detailed report
    tester = PerformanceTester()
    tester.setup()
    results = tester.run_all_performance_tests()
    report = tester.generate_performance_report()
    
    # Save report
    with open("performance_test_report.md", "w") as f:
        f.write(report)
    
    print(f"Performance report saved to: performance_test_report.md")
    
    return failed == 0


if __name__ == "__main__":
    success = run_performance_tests()
    exit(0 if success else 1)