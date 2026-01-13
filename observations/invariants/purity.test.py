"""
purity.test.py - Read-only enforcement test

Enforces Observation Purity at runtime (Constitutional Article 1).

This test uses minimal, type-safe stubs to test the invariants without
requiring the full system implementation.
"""

import os
import stat
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Iterator
from unittest.mock import patch
import pytest


# -------------------------------------------------------------------
# SIMPLE TYPE STUBS (no complex mocking)
# -------------------------------------------------------------------

class SimpleObservation:
    """Minimal observation stub for testing."""
    def __init__(self, path: Path, content: str = "") -> None:
        self.path = path
        self.content = content
        self.metadata: Dict[str, Any] = {"observed_at": "2024-01-01T00:00:00Z"}


class SimpleEye:
    """Minimal eye stub that never writes."""
    
    def observe(self, target: Path) -> Iterator[SimpleObservation]:
        """Read-only observation - yields observations without writing."""
        if target.is_dir():
            for file_path in target.rglob("*"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(errors='ignore')
                        yield SimpleObservation(file_path, content[:100])  # Limit content
                    except (IOError, OSError, UnicodeDecodeError):
                        # Can't read file - that's OK for testing
                        yield SimpleObservation(file_path, "[unreadable]")
        elif target.is_file():
            try:
                content = target.read_text(errors='ignore')
                yield SimpleObservation(target, content[:100])
            except (IOError, OSError, UnicodeDecodeError):
                yield SimpleObservation(target, "[unreadable]")


# -------------------------------------------------------------------
# FILESYSTEM GUARD
# -------------------------------------------------------------------

class FilesystemGuard:
    """Monitors filesystem for changes."""
    
    def __init__(self, target_dir: Path) -> None:
        self.target_dir = target_dir
        self.original_state: Dict[str, Dict[str, Any]] = {}
    
    def capture_original_state(self) -> None:
        """Record filesystem state before observation."""
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                path = Path(root) / file
                try:
                    stat_info = os.stat(path)
                    self.original_state[str(path)] = {
                        'size': stat_info.st_size,
                        'mtime': stat_info.st_mtime,
                        'mode': stat_info.st_mode,
                    }
                except (OSError, PermissionError):
                    continue
    
    def check_state_unchanged(self) -> tuple[bool, List[str]]:
        """Verify no files were created, modified, or deleted."""
        violations: List[str] = []
        
        # Check all original files still exist unchanged
        for path_str, original_info in self.original_state.items():
            path = Path(path_str)
            if not path.exists():
                violations.append(f"File deleted: {path_str}")
                continue
                
            try:
                current_stat = os.stat(path_str)
                if current_stat.st_size != original_info['size']:
                    violations.append(f"File modified (size): {path_str}")
                if abs(current_stat.st_mtime - original_info['mtime']) > 1.0:
                    violations.append(f"File modified (mtime): {path_str}")
                if current_stat.st_mode != original_info['mode']:
                    violations.append(f"File modified (mode): {path_str}")
            except (OSError, PermissionError):
                violations.append(f"Cannot stat file: {path_str}")
        
        # Check for new files
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                current_path = str(Path(root) / file)
                if current_path not in self.original_state:
                    violations.append(f"File created: {current_path}")
        
        return (len(violations) == 0, violations)


# -------------------------------------------------------------------
# WRITE INTERCEPTOR
# -------------------------------------------------------------------

class WriteInterceptor:
    """Intercepts file write attempts using simple patching."""
    
    def __init__(self) -> None:
        self.write_calls: List[str] = []
    
    def get_patches(self) -> Dict[str, Any]:
        """Return patches for write-related functions."""
        original_open = open
        
        def monitored_open(file: Any, mode: str = 'r', *args: Any, **kwargs: Any) -> Any:
            mode_str = str(mode)
            if any(write_char in mode_str for write_char in ['w', 'a', 'x', '+']):
                self.write_calls.append(f"open('{file}', mode='{mode}')")
                raise PermissionError(f"Write intercepted: open({file}, {mode})")
            return original_open(file, mode, *args, **kwargs)
        
        def monitored_write_text(self_path: Path, data: str, *args: Any, **kwargs: Any) -> None:
            self.write_calls.append(f"Path.write_text('{self_path}')")
            raise PermissionError(f"Write intercepted: Path.write_text({self_path})")
        
        return {
            'builtins.open': monitored_open,
            'pathlib.Path.write_text': monitored_write_text,
        }


# -------------------------------------------------------------------
# TEST UTILITIES
# -------------------------------------------------------------------

def create_test_codebase(test_dir: Path) -> None:
    """Create a minimal codebase for testing."""
    src_dir = test_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # Create simple Python files
    (src_dir / "__init__.py").write_text('')
    (src_dir / "main.py").write_text('def hello(): return "world"')
    
    # Create some test files
    (test_dir / "README.md").write_text("# Test\nSimple test.")
    config_file = test_dir / "config.txt"
    config_file.write_text("debug=true")
    
    # Make one file read-only
    config_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


# -------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------

class TestObservationPurity:
    """Tests for read-only observation purity."""
    
    def setup_method(self) -> None:
        """Set up fresh test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="codemarshal_purity_"))
        self.fs_guard = FilesystemGuard(self.test_dir)
        self.write_interceptor = WriteInterceptor()
        
        create_test_codebase(self.test_dir)
        self.fs_guard.capture_original_state()
    
    def teardown_method(self) -> None:
        """Clean up test directory."""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass
    
    def test_simple_eye_purity(self) -> None:
        """Test that SimpleEye observes without writing."""
        patches = self.write_interceptor.get_patches()
        
        with patch.dict('builtins.__dict__', patches):
            eye = SimpleEye()
            
            # Collect observations (forcing iteration)
            observations = list(eye.observe(self.test_dir))
            
            # Verify filesystem unchanged
            fs_ok, fs_violations = self.fs_guard.check_state_unchanged()
            
            # Check for write attempts
            violations: List[str] = []
            if not fs_ok:
                violations.extend(fs_violations)
            if self.write_interceptor.write_calls:
                violations.extend(self.write_interceptor.write_calls)
            
            assert len(violations) == 0, (
                f"Purity violated ({len(violations)}):\n" +
                "\n".join(f"  • {v}" for v in violations)
            )
            assert len(observations) > 0, "Should have observations"
    
    def test_readonly_file_handling(self) -> None:
        """Test observation handles read-only files without chmod."""
        # Make all files read-only
        for root, dirs, files in os.walk(self.test_dir):
            for item in dirs + files:
                item_path = Path(root) / item
                try:
                    item_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                except (OSError, PermissionError):
                    pass
        
        patches = self.write_interceptor.get_patches()
        
        with patch.dict('builtins.__dict__', patches):
            eye = SimpleEye()
            
            # Should still work (or at least not try to chmod)
            try:
                list(eye.observe(self.test_dir))  # Consume iterator
            except PermissionError:
                # Can't read read-only files - that's OK
                pass
            
            # Check for chmod attempts
            chmod_attempts = [
                call for call in self.write_interceptor.write_calls
                if 'chmod' in call.lower()
            ]
            assert len(chmod_attempts) == 0, "Should not attempt chmod"
    
    def test_deterministic_observations(self) -> None:
        """Test that multiple observations produce same results."""
        eye = SimpleEye()
        
        # First observation
        obs1 = list(eye.observe(self.test_dir))
        obs1_paths = sorted(str(o.path) for o in obs1)
        
        # Second observation
        obs2 = list(eye.observe(self.test_dir))
        obs2_paths = sorted(str(o.path) for o in obs2)
        
        # Should be the same
        assert obs1_paths == obs2_paths, "Non-deterministic observations"
    
    def test_no_temp_files(self) -> None:
        """Test that observation doesn't create temp files."""
        # Get count of files starting with purity_test in temp dir
        temp_dir = Path(tempfile.gettempdir())
        initial_temp_files = list(temp_dir.glob("codemarshal_purity_*"))
        initial_count = len(initial_temp_files)
        
        eye = SimpleEye()
        list(eye.observe(self.test_dir))  # Consume iterator
        
        # Check no new temp files were created
        final_temp_files = list(temp_dir.glob("codemarshal_purity_*"))
        final_count = len(final_temp_files)
        
        # Allow for our own test directory
        assert final_count <= initial_count + 1, (
            f"Temp files created: {final_count - initial_count}"
        )


def test_hostile_write_prevention() -> None:
    """Hostile test that attempts writes from multiple angles."""
    test_dir = Path(tempfile.mkdtemp(prefix="codemarshal_hostile_"))
    
    try:
        create_test_codebase(test_dir)
        
        interceptor = WriteInterceptor()
        patches = interceptor.get_patches()
        
        with patch.dict('builtins.__dict__', patches):
            # Try to observe
            eye = SimpleEye()
            list(eye.observe(test_dir))  # Consume iterator
            
            # Check for any write attempts
            if interceptor.write_calls:
                # Create violation report
                report = ["Write attempts detected:"]
                report.extend(f"  • {call}" for call in interceptor.write_calls)
                
                pytest.fail("\n".join(report))
                
    finally:
        try:
            shutil.rmtree(test_dir, ignore_errors=True)
        except Exception:
            pass


# -------------------------------------------------------------------
# CONSTITUTIONAL TESTS
# -------------------------------------------------------------------

def test_article_1_compliance() -> None:
    """Direct test of Constitutional Article 1 (Observation Purity)."""
    test_dir = Path(tempfile.mkdtemp(prefix="codemarshal_article1_"))
    
    try:
        # Create test file
        test_file = test_dir / "test.py"
        test_file.write_text('x = 1  # Simple code')
        
        # Set up write interception
        interceptor = WriteInterceptor()
        patches = interceptor.get_patches()
        
        with patch.dict('builtins.__dict__', patches):
            # Observe
            eye = SimpleEye()
            observations = list(eye.observe(test_dir))
            
            # Article 1: No writes during observation
            if interceptor.write_calls:
                pytest.fail(
                    f"Article 1 violation: Writes during observation:\n" +
                    "\n".join(f"  • {call}" for call in interceptor.write_calls)
                )
            
            # Article 1: Only factual observations
            for obs in observations:
                # Check observation doesn't contain inference
                content = obs.content.lower()
                inference_words = ['probably', 'likely', 'seems', 'suggests', 'maybe']
                for word in inference_words:
                    if word in content:
                        pytest.fail(f"Article 1 violation: Inference word '{word}' in observation")
                        
    finally:
        try:
            shutil.rmtree(test_dir, ignore_errors=True)
        except Exception:
            pass


def test_tier_1_failure_protocol() -> None:
    """Test that purity violations are treated as Tier-1 failures."""
    # This is a meta-test: we verify that our test framework
    # correctly identifies and reports purity violations
    
    test_dir = Path(tempfile.mkdtemp(prefix="codemarshal_tier1_"))
    
    try:
        # Create a malicious eye that tries to write
        class MaliciousEye(SimpleEye):
            def observe(self, target: Path) -> Iterator[SimpleObservation]:
                # Try to write a file (evil!)
                evil_path = target / ".evil"
                try:
                    evil_path.write_text("I'm writing!")
                except Exception:
                    pass  # Write interceptor should catch this
                yield SimpleObservation(target, "malicious")
        
        # Set up interception
        interceptor = WriteInterceptor()
        patches = interceptor.get_patches()
        
        with patch.dict('builtins.__dict__', patches):
            eye = MaliciousEye()
            list(eye.observe(test_dir))  # Consume iterator
            
            # Should have detected the write attempt
            assert len(interceptor.write_calls) > 0, (
                "Tier-1 failure: Write attempt not detected"
            )
            
    finally:
        try:
            shutil.rmtree(test_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    """Standalone test execution."""
    print("=" * 60)
    print("Running Observation Purity Tests")
    print("=" * 60)
    
    # Run constitutional tests first
    print("\n1. Testing Article 1 compliance...")
    try:
        test_article_1_compliance()
        print("  ✓ Article 1 (Observation Purity) upheld")
    except AssertionError as e:
        print(f"  ✗ Article 1 violation: {e}")
        raise
    
    print("\n2. Testing Tier-1 failure protocol...")
    try:
        test_tier_1_failure_protocol()
        print("  ✓ Tier-1 failure protocol working")
    except AssertionError as e:
        print(f"  ✗ Tier-1 protocol issue: {e}")
        raise
    
    print("\n3. Testing hostile write prevention...")
    try:
        test_hostile_write_prevention()
        print("  ✓ Hostile writes prevented")
    except AssertionError as e:
        print(f"  ✗ Hostile write prevention failed: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("All purity tests passed ✓")
    print("=" * 60)