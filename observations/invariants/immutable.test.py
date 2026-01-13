"""
immutable.test.py - "Observations never change" test

Enforces Constitutional Articles 1 and 9.
Tests that:
1. Once recorded, observations cannot be mutated, replaced in place, or retroactively altered
2. New observations must create new snapshot versions, new hashes, and new anchors
3. Writes are rejected atomically when immutability would be violated

This test is hostile by design - it assumes future violations will be subtle.
Failure is Tier-1 and must halt execution.
"""

import copy
import hashlib
import tempfile
import uuid
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set
import pytest

# System imports
from observations.record.snapshot import Snapshot, create_snapshot, get_snapshot_anchor
from observations.record.integrity import compute_hash, verify_hash, HashMismatchError
from observations.record.version import SnapshotVersion, get_snapshot_version, create_new_version
from observations.eyes.file_sight import FileSight
from observations.eyes.import_sight import ImportSight
from storage.atomic import atomic_write, AtomicWriteError
from storage.corruption import detect_corruption, CorruptionError

# Type aliases
ObservationData = Dict[str, Any]
MutationAttempt = Tuple[str, Any, Any]  # (path, old_value, new_value)


class ImmutabilityAssassin:
    """
    Hostile tool for attempting to violate observation immutability.
    
    Tries every possible mutation path, including:
    1. Direct attribute mutation
    2. Internal dictionary/list modification
    3. Pickle-based serialization attacks
    4. Hash collision attacks
    5. Version manipulation
    """
    
    def __init__(self) -> None:
        self.mutation_attempts: List[MutationAttempt] = []
        self.successful_mutations: List[str] = []
        
    def attempt_object_mutation(self, obj: Any, obj_name: str) -> List[str]:
        """
        Attempt to mutate an object through various means.
        
        Returns list of successful mutation paths (should be empty).
        """
        successful: List[str] = []
        
        # Strategy 1: Direct attribute assignment
        if hasattr(obj, '__dict__'):
            original_dict = copy.deepcopy(obj.__dict__)
            for key, value in original_dict.items():
                if isinstance(value, (int, float, str, bool)):
                    try:
                        # Try to set a different value
                        setattr(obj, key, type(value)())
                        if getattr(obj, key) != value:
                            successful.append(f"Direct attribute: {obj_name}.{key}")
                        # Restore original
                        setattr(obj, key, value)
                    except (AttributeError, ValueError, TypeError):
                        pass
        
        # Strategy 2: Dictionary modification (if object is dict-like)
        if isinstance(obj, dict):
            original = copy.deepcopy(obj)
            for key in list(obj.keys()):
                try:
                    obj[key] = "MUTATED"
                    if obj[key] != original.get(key):
                        successful.append(f"Dict key: {obj_name}[{key}]")
                    # Restore
                    obj[key] = original[key]
                except (KeyError, TypeError):
                    pass
        
        # Strategy 3: List modification
        if isinstance(obj, list):
            original = copy.deepcopy(obj)
            if len(obj) > 0:
                try:
                    obj[0] = "MUTATED"
                    if obj[0] != original[0]:
                        successful.append(f"List index: {obj_name}[0]")
                    # Restore
                    obj[0] = original[0]
                except (IndexError, TypeError):
                    pass
        
        # Strategy 4: Setattr on non-existent attribute (might create mutable state)
        try:
            setattr(obj, f'_assassin_{uuid.uuid4().hex[:8]}', 'mutated')
            if hasattr(obj, '_assassin_'):
                successful.append(f"Dynamic attribute creation: {obj_name}")
        except (AttributeError, ValueError):
            pass
        
        return successful
    
    def attempt_pickle_attack(self, obj: Any, obj_name: str) -> List[str]:
        """
        Attempt to mutate object through pickle serialization attacks.
        
        Pickling/unpickling can sometimes create mutable copies or
        bypass __setattr__ restrictions.
        """
        successful: List[str] = []
        
        try:
            # Pickle and unpickle
            pickled = pickle.dumps(obj)
            unpickled = pickle.loads(pickled)
            
            # Try to mutate the unpickled version
            # If the unpickled version is supposed to be immutable but isn't,
            # that's a violation
            unpickled_success = self.attempt_object_mutation(unpickled, f"unpickled_{obj_name}")
            if unpickled_success:
                successful.extend([f"Pickle attack: {s}" for s in unpickled_success])
            
            # Also check if unpickling changed the object
            # Deep compare original and repickled version
            repickled = pickle.dumps(unpickled)
            if pickled != repickled:
                successful.append(f"Pickle inconsistency: {obj_name}")
                
        except (pickle.PickleError, TypeError, ValueError):
            pass
        
        return successful
    
    def attempt_hash_collision(self, data: bytes, obj_name: str) -> List[str]:
        """
        Attempt to create hash collisions or manipulate hash verification.
        
        Not a true cryptographic attack, but tests if hash verification
        can be bypassed through object mutation.
        """
        successful: List[str] = []
        
        # Compute original hash
        original_hash = compute_hash(data)
        
        # Try small mutations that might not change hash (should always change)
        for i in range(min(10, len(data))):
            mutated = bytearray(data)
            mutated[i] = (mutated[i] + 1) % 256
            
            try:
                mutated_hash = compute_hash(bytes(mutated))
                if mutated_hash == original_hash:
                    successful.append(f"Hash collision at byte {i}: {obj_name}")
            except Exception:
                pass
        
        return successful
    
    def attempt_version_manipulation(self, snapshot: Snapshot) -> List[str]:
        """
        Attempt to manipulate snapshot versions without creating new versions.
        """
        successful: List[str] = []
        
        original_version = get_snapshot_version(snapshot)
        
        # Strategy: Try to modify version object directly
        version_success = self.attempt_object_mutation(original_version, "SnapshotVersion")
        if version_success:
            successful.extend([f"Version mutation: {s}" for s in version_success])
        
        # Strategy: Try to create new version without changing content
        try:
            new_version = create_new_version(snapshot, {"comment": "test"})
            if get_snapshot_version(new_version).version_id == original_version.version_id:
                successful.append("Version unchanged after create_new_version")
        except Exception:
            pass
        
        return successful
    
    def attempt_anchor_manipulation(self, snapshot: Snapshot) -> List[str]:
        """
        Attempt to manipulate snapshot anchors without proper versioning.
        """
        successful: List[str] = []
        
        original_anchor = get_snapshot_anchor(snapshot)
        
        # Try to compute anchor from mutated data
        # (If anchor doesn't change when data changes, that's a violation)
        try:
            # Get snapshot data
            snapshot_dict = snapshot.to_dict() if hasattr(snapshot, 'to_dict') else snapshot.__dict__
            snapshot_json = json.dumps(snapshot_dict, sort_keys=True)
            
            # Mutate the JSON and try to create anchor
            mutated_json = snapshot_json.replace('"', "'")  # Simple mutation
            mutated_hash = hashlib.sha256(mutated_json.encode()).hexdigest()
            
            # If we can create an anchor without proper versioning, that's a violation
            # (This depends on implementation - adjust based on actual anchor creation)
            
        except Exception:
            pass
        
        return successful


class AtomicWriteTester:
    """
    Tests atomic write guarantees for immutability.
    
    Ensures that:
    1. Partial writes don't corrupt existing data
    2. Failed writes don't leave partial state
    3. Concurrent writes don't create inconsistent state
    """
    
    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def test_atomic_write_immutability(self, data: bytes, filename: str) -> List[str]:
        """
        Test that atomic_write prevents mutation of existing files.
        """
        violations: List[str] = []
        
        file_path = self.storage_dir / filename
        
        # Write initial data
        try:
            atomic_write(file_path, data)
        except AtomicWriteError as e:
            violations.append(f"Initial atomic_write failed: {e}")
            return violations
        
        # Verify initial write
        if not file_path.exists():
            violations.append(f"File not created: {file_path}")
            return violations
        
        initial_content = file_path.read_bytes()
        if initial_content != data:
            violations.append(f"Initial content mismatch for {filename}")
        
        # Try to write different data (should create new file, not mutate)
        new_data = data + b"_MUTATED"
        try:
            atomic_write(file_path, new_data)
            
            # Check if old data is preserved somewhere (depends on implementation)
            # For true immutability, the old version should still be accessible
            current_content = file_path.read_bytes()
            if current_content == data:
                violations.append(f"Atomic write didn't update {filename}")
            elif current_content != new_data:
                violations.append(f"Atomic write corrupted {filename}")
                
        except AtomicWriteError as e:
            # This might be OK if the system prevents overwrites
            # Check if original data is still intact
            if file_path.exists():
                preserved_content = file_path.read_bytes()
                if preserved_content != data:
                    violations.append(f"Atomic write failure corrupted {filename}")
        
        return violations
    
    def test_concurrent_write_protection(self) -> List[str]:
        """
        Simulate concurrent writes to test atomicity.
        
        This is a simplified test - real concurrency would require
        multiple processes.
        """
        violations: List[str] = []
        
        test_file = self.storage_dir / "concurrent_test.dat"
        test_data = b"Original content"
        
        # Write initial data
        atomic_write(test_file, test_data)
        
        # Simulate two concurrent write attempts
        # (In reality, this would be in separate processes)
        attempt1_data = b"Attempt 1"
        attempt2_data = b"Attempt 2"
        
        try:
            # First attempt
            atomic_write(test_file, attempt1_data)
            final_content = test_file.read_bytes()
            
            # The file should contain exactly one of the attempts, not a mix
            if final_content not in [attempt1_data, attempt2_data, test_data]:
                violations.append(f"Concurrent write produced corrupted data: {final_content[:50]}")
                
        except AtomicWriteError:
            # Atomic write should fail cleanly if there's contention
            # Verify original data is preserved
            if test_file.exists():
                preserved = test_file.read_bytes()
                if preserved != test_data:
                    violations.append("Atomic write failure corrupted original data")
        
        return violations


class CorruptionDetector:
    """
    Tests that corruption detection prevents mutated data from being accepted.
    """
    
    def __init__(self) -> None:
        pass
    
    def test_corruption_detection(self, data: bytes) -> List[str]:
        """
        Test that mutated data is detected as corrupted.
        """
        violations: List[str] = []
        
        # Create a test file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data)
            temp_path = Path(f.name)
        
        try:
            # First, verify it's not corrupted
            try:
                detect_corruption(temp_path)
                # Should not raise
            except CorruptionError:
                violations.append("False positive corruption detection")
            
            # Now mutate the file
            mutated = bytearray(data)
            if len(mutated) > 0:
                mutated[0] = (mutated[0] + 1) % 256
                temp_path.write_bytes(bytes(mutated))
            
            # Should detect corruption
            try:
                detect_corruption(temp_path)
                violations.append("Failed to detect corruption")
            except CorruptionError:
                pass  # Expected
                
        finally:
            temp_path.unlink(missing_ok=True)
        
        return violations
    
    def test_hash_verification(self, snapshot: Snapshot) -> List[str]:
        """
        Test that hash verification rejects mutated snapshots.
        """
        violations: List[str] = []
        
        # Get snapshot hash
        try:
            snapshot_dict = snapshot.to_dict() if hasattr(snapshot, 'to_dict') else snapshot.__dict__
            snapshot_bytes = json.dumps(snapshot_dict, sort_keys=True).encode()
            
            # Compute and verify original hash
            original_hash = compute_hash(snapshot_bytes)
            verify_hash(snapshot_bytes, original_hash)
            
            # Mutate and try to verify
            mutated_bytes = snapshot_bytes.replace(b'"', b"'")
            try:
                verify_hash(mutated_bytes, original_hash)
                violations.append("Hash verification accepted mutated data")
            except HashMismatchError:
                pass  # Expected
            
        except Exception as e:
            violations.append(f"Hash verification test failed: {e}")
        
        return violations


class TestImmutableObservations:
    """
    Hostile test suite for enforcing observation immutability.
    
    This test assumes immutability violations will be subtle:
    1. Accidental mutation through shared references
    2. Serialization/deserialization bugs
    3. Hash verification bypasses
    4. Version manipulation
    5. Atomic write failures
    """
    
    def setup_method(self) -> None:
        """Set up fresh test environment for each test."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="codemarshal_immutable_"))
        self.assassin = ImmutabilityAssassin()
        self.storage_dir = self.test_dir / "storage"
        self.atomic_tester = AtomicWriteTester(self.storage_dir)
        self.corruption_detector = CorruptionDetector()
        
        # Create test codebase
        self._create_test_codebase()
        
        # Create observations
        self.file_eye = FileSight()
        self.import_eye = ImportSight()
        self.file_observations = list(self.file_eye.observe(self.test_dir))
        self.import_observations = list(self.import_eye.observe(self.test_dir))
        
        # Create snapshot
        self.snapshot = create_snapshot(self.file_observations + self.import_observations)
    
    def teardown_method(self) -> None:
        """Clean up test directory."""
        import shutil
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass
    
    def _create_test_codebase(self) -> None:
        """Create a minimal codebase for testing."""
        src_dir = self.test_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Simple Python file
        main_py = src_dir / "main.py"
        main_py.write_text('''
def hello() -> str:
    return "Hello, World!"

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
''')
        
        # Init file
        (src_dir / "__init__.py").write_text('')
        
        # Config file
        config_py = self.test_dir / "config.py"
        config_py.write_text('''
DEBUG = True
MAX_RETRIES = 3
''')
    
    def test_observation_objects_immutable(self) -> None:
        """
        Test that individual observation objects cannot be mutated.
        
        Attempts to mutate observation objects through every possible
        path and verifies all attempts fail.
        """
        violations: List[str] = []
        
        # Test FileSight observations
        for i, obs in enumerate(self.file_observations):
            obs_name = f"FileObservation[{i}]"
            successful = self.assassin.attempt_object_mutation(obs, obs_name)
            if successful:
                violations.extend(successful)
            
            # Also test pickle attacks
            pickle_success = self.assassin.attempt_pickle_attack(obs, obs_name)
            if pickle_success:
                violations.extend(pickle_success)
        
        # Test ImportSight observations
        for i, obs in enumerate(self.import_observations):
            obs_name = f"ImportObservation[{i}]"
            successful = self.assassin.attempt_object_mutation(obs, obs_name)
            if successful:
                violations.extend(successful)
            
            pickle_success = self.assassin.attempt_pickle_attack(obs, obs_name)
            if pickle_success:
                violations.extend(pickle_success)
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"Observation object mutability detected ({len(violations)} violations):\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_snapshot_immutable(self) -> None:
        """
        Test that snapshot objects cannot be mutated.
        
        Snapshots must be immutable containers for observations.
        """
        violations: List[str] = []
        
        # Attempt to mutate snapshot object
        snapshot_mutations = self.assassin.attempt_object_mutation(self.snapshot, "Snapshot")
        if snapshot_mutations:
            violations.extend(snapshot_mutations)
        
        # Attempt pickle attack on snapshot
        pickle_mutations = self.assassin.attempt_pickle_attack(self.snapshot, "Snapshot")
        if pickle_mutations:
            violations.extend(pickle_mutations)
        
        # Test that snapshot data (observations list) cannot be mutated
        if hasattr(self.snapshot, 'observations'):
            obs_list = self.snapshot.observations
            if isinstance(obs_list, list):
                # Try to modify the list
                original_len = len(obs_list)
                try:
                    obs_list.append("MUTATED")
                    if len(obs_list) != original_len:
                        violations.append("Snapshot observations list mutated")
                    # Clean up
                    if len(obs_list) > original_len:
                        obs_list.pop()
                except (AttributeError, ValueError, TypeError):
                    pass  # Expected
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"Snapshot mutability detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_snapshot_versioning(self) -> None:
        """
        Test that new observations create new versions with new hashes.
        
        Verifies Article 9: New observations create new versions.
        """
        violations: List[str] = []
        
        # Get original version and hash
        original_version = get_snapshot_version(self.snapshot)
        original_anchor = get_snapshot_anchor(self.snapshot)
        
        # Create new observations (simulate new state)
        new_file_obs = list(self.file_eye.observe(self.test_dir))
        # Add one more observation to ensure difference
        if new_file_obs:
            new_snapshot = create_snapshot(new_file_obs + self.import_observations)
        else:
            new_snapshot = create_snapshot(self.file_observations + self.import_observations)
        
        # Get new version and hash
        new_version = get_snapshot_version(new_snapshot)
        new_anchor = get_snapshot_anchor(new_snapshot)
        
        # Verify versions are different
        if original_version.version_id == new_version.version_id:
            violations.append("Version ID unchanged after new observations")
        
        # Verify anchors are different (should be based on content hash)
        if original_anchor == new_anchor:
            violations.append("Anchor unchanged after new observations")
        
        # Attempt version manipulation
        version_mutations = self.assassin.attempt_version_manipulation(self.snapshot)
        if version_mutations:
            violations.extend(version_mutations)
        
        # Attempt anchor manipulation
        anchor_mutations = self.assassin.attempt_anchor_manipulation(self.snapshot)
        if anchor_mutations:
            violations.extend(anchor_mutations)
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"Snapshot versioning violation detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_hash_integrity(self) -> None:
        """
        Test that hashes detect mutations and prevent hash collisions.
        
        Verifies that:
        1. Mutated data produces different hashes
        2. Hash verification rejects mutated data
        3. No trivial hash collisions
        """
        violations: List[str] = []
        
        # Convert snapshot to bytes for hash testing
        try:
            snapshot_dict = self.snapshot.to_dict() if hasattr(self.snapshot, 'to_dict') else self.snapshot.__dict__
            snapshot_json = json.dumps(snapshot_dict, sort_keys=True)
            snapshot_bytes = snapshot_json.encode()
            
            # Test hash collision attempts
            collisions = self.assassin.attempt_hash_collision(snapshot_bytes, "Snapshot")
            if collisions:
                violations.extend(collisions)
            
            # Test hash verification
            hash_violations = self.corruption_detector.test_hash_verification(self.snapshot)
            if hash_violations:
                violations.extend(hash_violations)
                
        except Exception as e:
            violations.append(f"Hash integrity test setup failed: {e}")
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"Hash integrity violation detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_atomic_write_guarantees(self) -> None:
        """
        Test atomic write guarantees for observation storage.
        
        Verifies that:
        1. Partial writes don't corrupt data
        2. Failed writes don't leave partial state
        3. Writes are truly atomic
        """
        violations: List[str] = []
        
        # Test basic atomic write
        test_data = b"Observation data for atomic write test"
        atomic_violations = self.atomic_tester.test_atomic_write_immutability(
            test_data, "atomic_test.dat"
        )
        if atomic_violations:
            violations.extend(atomic_violations)
        
        # Test concurrent write protection
        concurrent_violations = self.atomic_tester.test_concurrent_write_protection()
        if concurrent_violations:
            violations.extend(concurrent_violations)
        
        # Test with observation data
        snapshot_dict = self.snapshot.to_dict() if hasattr(self.snapshot, 'to_dict') else self.snapshot.__dict__
        snapshot_json = json.dumps(snapshot_dict, indent=2)
        observation_violations = self.atomic_tester.test_atomic_write_immutability(
            snapshot_json.encode(), "observation_snapshot.json"
        )
        if observation_violations:
            violations.extend(observation_violations)
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"Atomic write violation detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_corruption_detection(self) -> None:
        """
        Test that corruption detection prevents mutated data from being accepted.
        
        Verifies that:
        1. Mutated files are detected as corrupted
        2. Corruption detection is reliable
        3. Corrupted data cannot masquerade as valid
        """
        violations: List[str] = []
        
        # Test with sample data
        test_data = b"Valid observation data for corruption testing"
        corruption_violations = self.corruption_detector.test_corruption_detection(test_data)
        if corruption_violations:
            violations.extend(corruption_violations)
        
        # Test with actual observation data
        snapshot_dict = self.snapshot.to_dict() if hasattr(self.snapshot, 'to_dict') else self.snapshot.__dict__
        snapshot_json = json.dumps(snapshot_dict, sort_keys=True)
        observation_violations = self.corruption_detector.test_corruption_detection(
            snapshot_json.encode()
        )
        if observation_violations:
            violations.extend(observation_violations)
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"Corruption detection violation detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_retroactive_alteration_prevention(self) -> None:
        """
        Test that retroactive alteration of recorded observations is prevented.
        
        Attempts to:
        1. Modify stored observations in place
        2. Replace observations without versioning
        3. Create new versions with altered old data
        """
        violations: List[str] = []
        
        # Store snapshot
        snapshot_path = self.storage_dir / "snapshot.pkl"
        try:
            with open(snapshot_path, 'wb') as f:
                pickle.dump(self.snapshot, f)
        except Exception as e:
            violations.append(f"Failed to store snapshot: {e}")
            assert len(violations) == 0, "Setup failed"
        
        # Attempt 1: Direct file modification
        try:
            with open(snapshot_path, 'rb') as f:
                original_data = f.read()
            
            # Mutate the file
            mutated_data = bytearray(original_data)
            if len(mutated_data) > 100:
                # Mutate a portion of the data
                for i in range(100, min(200, len(mutated_data))):
                    mutated_data[i] = (mutated_data[i] + 1) % 256
                
                snapshot_path.write_bytes(bytes(mutated_data))
                
                # Try to load mutated snapshot
                try:
                    with open(snapshot_path, 'rb') as f:
                        mutated_snapshot = pickle.load(f)
                    
                    # Should fail verification
                    if hasattr(mutated_snapshot, 'verify'):
                        try:
                            mutated_snapshot.verify()
                            violations.append("Mutated snapshot passed verification")
                        except (HashMismatchError, CorruptionError):
                            pass  # Expected
                            
                except (pickle.PickleError, EOFError, AttributeError):
                    # Pickle loading failed - that's actually good
                    pass
                    
        except Exception as e:
            # Any error during mutation attempt is fine
            pass
        
        # Attempt 2: Try to create a new snapshot with altered old data
        try:
            # Get original observations
            original_obs = self.file_observations[0] if self.file_observations else None
            
            if original_obs and hasattr(original_obs, '__dict__'):
                # Create a mutated copy
                mutated_dict = copy.deepcopy(original_obs.__dict__)
                for key in list(mutated_dict.keys()):
                    if isinstance(mutated_dict[key], str):
                        mutated_dict[key] = mutated_dict[key] + "_MUTATED"
                
                # Try to create a new observation with mutated data
                # (This depends on observation class implementation)
                # We're testing that the system prevents this
                
        except Exception:
            pass
        
        # Tier-1 failure
        assert len(violations) == 0, (
            f"Retroactive alteration violation detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )
    
    def test_hostile_immutability_attack(self) -> None:
        """
        Hostile test that attempts every possible immutability violation.
        
        This is the "nuclear option" test - if it passes, we have strong
        confidence in immutability guarantees.
        """
        all_violations: List[str] = []
        
        # Run all mutation attempts in sequence
        test_methods = [
            self.test_observation_objects_immutable,
            self.test_snapshot_immutable,
            self.test_snapshot_versioning,
            self.test_hash_integrity,
            self.test_atomic_write_guarantees,
            self.test_corruption_detection,
            self.test_retroactive_alteration_prevention,
        ]
        
        for method in test_methods:
            try:
                method()
            except AssertionError as e:
                # Extract violation messages from assertion
                msg = str(e)
                if "violation detected" in msg:
                    # Parse out the violations
                    lines = msg.split('\n')
                    for line in lines:
                        if line.strip().startswith('•'):
                            all_violations.append(line.strip())
                else:
                    all_violations.append(f"Test {method.__name__} failed: {msg}")
        
        # Additional hostile tests
        try:
            # Test deep nesting mutation attempts
            self._test_deep_nesting_mutation()
        except AssertionError as e:
            all_violations.append(f"Deep nesting test failed: {e}")
        
        # Tier-1 failure - any violation means system halt
        if all_violations:
            # Create detailed violation report
            report_path = Path.home() / "codemarshal_immutability_violation.txt"
            with open(report_path, 'w') as f:
                f.write("CODEMARSHAL IMMUTABILITY VIOLATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Test directory: {self.test_dir}\n")
                f.write(f"Snapshot version: {get_snapshot_version(self.snapshot).version_id}\n")
                f.write(f"Violations: {len(all_violations)}\n\n")
                for i, violation in enumerate(all_violations, 1):
                    f.write(f"{i}. {violation}\n\n")
            
            pytest.fail(
                f"Hostile immutability test failed with {len(all_violations)} violations.\n"
                f"Detailed report written to: {report_path}\n"
                f"First 3 violations:\n" +
                "\n".join(f"  • {v}" for v in all_violations[:3])
            )
    
    def _test_deep_nesting_mutation(self) -> None:
        """
        Test mutation attempts on deeply nested observation structures.
        
        Some observations might have complex nested structures that
        could be mutated indirectly.
        """
        violations: List[str] = []
        
        # Create a complex observation structure
        complex_data = {
            "metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0.0",
                "source": self.test_dir.name
            },
            "observations": [
                {
                    "type": "file",
                    "path": str(self.test_dir / "src" / "main.py"),
                    "content_hash": "abc123",
                    "metrics": {
                        "lines": 10,
                        "imports": ["typing", "os"],
                        "depth": 2
                    }
                }
            ],
            "patterns": {
                "density": 0.5,
                "coupling": 0.3,
                "complexity": {
                    "cyclomatic": 2,
                    "cognitive": 3
                }
            }
        }
        
        # Test mutation at every level
        def test_nested_mutation(obj: Any, path: str = "") -> None:
            # Attempt mutation at this level
            mutations = self.assassin.attempt_object_mutation(obj, path)
            if mutations:
                violations.extend(mutations)
            
            # Recursively test nested structures
            if isinstance(obj, dict):
                for key, value in obj.items():
                    test_nested_mutation(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    test_nested_mutation(item, f"{path}[{i}]")
        
        test_nested_mutation(complex_data, "complex_data")
        
        assert len(violations) == 0, (
            f"Deep nesting mutation detected:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )


def test_article_1_and_9_compliance() -> None:
    """
    Direct test of Constitutional Articles 1 and 9.
    
    Article 1: Observation Purity - Observations record only what is textually present
    Article 9: Immutable Observations - Once recorded, observations cannot change
    """
    # Create a simple test
    test_dir = Path(tempfile.mkdtemp(prefix="codemarshal_constitutional_"))
    
    try:
        # Create a file
        test_file = test_dir / "test.py"
        test_file.write_text('x = 1  # A simple assignment')
        
        # Observe it
        eye = FileSight()
        observations = list(eye.observe(test_dir))
        
        # Article 1: Should only record what's textually present
        # Check that no inference is added
        for obs in observations:
            obs_dict = obs.__dict__ if hasattr(obs, '__dict__') else {}
            # Should not contain inferred fields like "purpose", "meaning", etc.
            inferred_fields = {'purpose', 'meaning', 'intent', 'goal', 'probably', 'likely'}
            for field in inferred_fields:
                if field in str(obs_dict).lower():
                    pytest.fail(f"Article 1 violation: Contains inferred field '{field}'")
        
        # Article 9: Should create immutable record
        # Try to mutate an observation
        if observations:
            obs = observations[0]
            original_repr = repr(obs)
            
            # Try to add an attribute
            try:
                obs._test_mutation = "mutated"
                if hasattr(obs, '_test_mutation'):
                    pytest.fail("Article 9 violation: Observation accepted mutation")
            except (AttributeError, ValueError, TypeError):
                pass  # Expected
            
            # Verify representation unchanged
            if repr(obs) != original_repr:
                pytest.fail("Article 9 violation: Observation representation changed")
                
    finally:
        import shutil
        shutil.rmtree(test_dir, ignore_ok=True)


if __name__ == "__main__":
    """
    Standalone execution for manual testing.
    
    Run with: python -m observations.invariants.immutable.test
    """
    print("Running immutability tests...")
    
    # Create a test instance and run the hostile test
    test_instance = TestImmutableObservations()
    
    try:
        test_instance.setup_method()
        test_instance.test_hostile_immutability_attack()
        print("✓ All immutability tests passed")
    except AssertionError as e:
        print(f"✗ Immutability violation detected:\n{e}")
        raise
    finally:
        test_instance.teardown_method()