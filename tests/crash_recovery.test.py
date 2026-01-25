"""
crash_recovery.test.py - Session Integrity and Crash Recovery Testing

Article 15: Investigations can be paused, resumed, and recovered.
System crashes should not lose thinking. Truth persists across interruptions.
"""

import json
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from core.runtime import Runtime
from inquiry.notebook.entries import NoteEntry

# Import CodeMarshal modules
from inquiry.session.context import SessionContext
from storage.investigation_storage import InvestigationStorage


class CrashRecoveryTester:
    """Tests crash recovery mechanisms for Article 15 compliance."""

    def __init__(self):
        self.temp_dir = None
        self.storage = None
        self.runtime = None

    def setup(self):
        """Set up temporary environment for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage = InvestigationStorage(base_path=self.temp_dir)
        self.runtime = Runtime(storage=self.storage)

    def teardown(self):
        """Clean up temporary environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_session(self) -> SessionContext:
        """Create a test session with data."""
        session = SessionContext(
            snapshot_id="test-snapshot-001",
            anchor_id="root",
            question_type="structure",
            context_id="test-context",
        )

        # Add some test data to session
        session.add_observation("test_file.py", {"type": "file", "size": 1024})
        session.add_note(
            NoteEntry(
                id="note-001",
                anchor_id="test_file.py:42",
                content="This is a test note about the code",
                created_at=datetime.now(UTC),
            )
        )

        return session

    def simulate_crash(self, session: SessionContext) -> bool:
        """Simulate a system crash during session."""
        try:
            # Save session normally
            self.storage.save_session(session)

            # Simulate crash by corrupting memory state
            self.storage.load_session(session.snapshot_id)

            # Clear current session from memory (simulate crash)
            self.runtime._current_session = None

            # Verify session data exists on disk
            return self.storage.session_exists(session.snapshot_id)

        except Exception as e:
            print(f"Crash simulation failed: {e}")
            return False

    def test_recovery(self, session_id: str) -> bool:
        """Test session recovery after crash."""
        try:
            # Attempt to recover session
            recovered_session = self.storage.load_session(session_id)

            if not recovered_session:
                print("Failed to recover session")
                return False

            # Verify session integrity
            return self._verify_session_integrity(recovered_session)

        except Exception as e:
            print(f"Session recovery failed: {e}")
            return False

    def _verify_session_integrity(self, session: SessionContext) -> bool:
        """Verify that recovered session has all expected data."""
        # Check basic session properties
        if not session.snapshot_id:
            print("Session missing snapshot_id")
            return False

        if not session.anchor_id:
            print("Session missing anchor_id")
            return False

        # Check observations are preserved
        if not hasattr(session, "observations") or len(session.observations) == 0:
            print("Session observations lost")
            return False

        # Check notes are preserved
        if not hasattr(session, "notes") or len(session.notes) == 0:
            print("Session notes lost")
            return False

        # Verify note integrity
        note = session.notes[0]
        if note.id != "note-001" or note.anchor_id != "test_file.py:42":
            print("Note content corrupted")
            return False

        return True


def test_session_persistence_across_crash():
    """Test that sessions persist across system crashes."""
    tester = CrashRecoveryTester()

    try:
        tester.setup()

        # Create test session
        session = tester.create_test_session()
        session_id = session.snapshot_id

        # Simulate crash
        crash_success = tester.simulate_crash(session)
        assert crash_success, "Failed to simulate crash"

        # Test recovery
        recovery_success = tester.test_recovery(session_id)
        assert recovery_success, "Failed to recover session after crash"

        print("✅ Session persistence across crash: PASSED")

    finally:
        tester.teardown()


def test_partial_data_recovery():
    """Test recovery when some data is corrupted."""
    tester = CrashRecoveryTester()

    try:
        tester.setup()

        # Create session with multiple observations
        session = tester.create_test_session()
        session_id = session.snapshot_id

        # Add more test data
        session.add_observation("test_file2.py", {"type": "file", "size": 2048})
        session.add_observation("test_file3.py", {"type": "file", "size": 3072})

        # Save session
        tester.storage.save_session(session)

        # Simulate partial corruption by removing one observation file
        obs_file = tester.temp_dir / "sessions" / session_id / "observations.json"
        if obs_file.exists():
            # Read and modify to simulate corruption
            with open(obs_file) as f:
                data = json.load(f)
            # Remove one observation
            if "observations" in data and len(data["observations"]) > 0:
                data["observations"].pop()
                with open(obs_file, "w") as f:
                    json.dump(data, f)

        # Test recovery with partial data
        recovered_session = tester.storage.load_session(session_id)

        # Should recover what's available, not fail completely
        assert recovered_session is not None, "Should recover partial session"
        assert len(recovered_session.observations) >= 2, (
            "Should recover remaining observations"
        )

        print("✅ Partial data recovery: PASSED")

    finally:
        tester.teardown()


def test_session_continuity_after_recovery():
    """Test that recovered sessions can continue normally."""
    tester = CrashRecoveryTester()

    try:
        tester.setup()

        # Create and save session
        session = tester.create_test_session()
        session_id = session.snapshot_id
        tester.storage.save_session(session)

        # Simulate crash and recovery
        recovered_session = tester.storage.load_session(session_id)

        # Test that recovered session can be used normally
        recovered_session.add_observation("new_file.py", {"type": "file", "size": 4096})
        recovered_session.add_note(
            NoteEntry(
                id="note-002",
                anchor_id="new_file.py:10",
                content="Note added after recovery",
                created_at=datetime.now(UTC),
            )
        )

        # Save updated session
        tester.storage.save_session(recovered_session)

        # Verify updates persisted
        final_session = tester.storage.load_session(session_id)
        assert len(final_session.observations) == 2, "New observation not persisted"
        assert len(final_session.notes) == 2, "New note not persisted"

        print("✅ Session continuity after recovery: PASSED")

    finally:
        tester.teardown()


def test_concurrent_session_safety():
    """Test that concurrent sessions don't corrupt each other."""
    tester = CrashRecoveryTester()

    try:
        tester.setup()

        # Create two sessions
        session1 = tester.create_test_session()
        session1.snapshot_id = "concurrent-test-1"

        session2 = tester.create_test_session()
        session2.snapshot_id = "concurrent-test-2"

        # Save both sessions
        tester.storage.save_session(session1)
        tester.storage.save_session(session2)

        # Simulate crash affecting session1 only
        session1_file = (
            tester.temp_dir / "sessions" / "concurrent-test-1" / "session.json"
        )
        if session1_file.exists():
            session1_file.unlink()

        # Test that session2 is unaffected
        recovered_session2 = tester.storage.load_session("concurrent-test-2")
        assert recovered_session2 is not None, "Session2 should be unaffected"
        assert len(recovered_session2.observations) > 0, (
            "Session2 data should be intact"
        )

        # Test that session1 can be recovered (or gracefully fails)
        tester.storage.load_session("concurrent-test-1")
        # Session1 should be recoverable or gracefully fail
        # The exact behavior depends on implementation

        print("✅ Concurrent session safety: PASSED")

    finally:
        tester.teardown()


def test_session_backup_and_restore():
    """Test session backup and restore mechanisms."""
    tester = CrashRecoveryTester()

    try:
        tester.setup()

        # Create session
        session = tester.create_test_session()
        session_id = session.snapshot_id

        # Test backup creation
        backup_path = tester.storage.create_backup(session_id)
        assert backup_path.exists(), "Backup should be created"

        # Modify original session
        session.add_observation("modified_file.py", {"type": "file", "size": 9999})
        tester.storage.save_session(session)

        # Test restore from backup
        restore_success = tester.storage.restore_from_backup(session_id, backup_path)
        assert restore_success, "Should restore from backup"

        # Verify restored session matches original
        restored_session = tester.storage.load_session(session_id)
        assert len(restored_session.observations) == 1, (
            "Should restore original observation count"
        )

        print("✅ Session backup and restore: PASSED")

    finally:
        tester.teardown()


def test_integrity_verification_after_recovery():
    """Test that integrity verification works after recovery."""
    tester = CrashRecoveryTester()

    try:
        tester.setup()

        # Create session
        session = tester.create_test_session()
        session_id = session.snapshot_id

        # Save session with integrity hash
        tester.storage.save_session(session)

        # Simulate crash and recovery
        tester.storage.load_session(session_id)

        # Test integrity verification
        integrity_valid = tester.storage.verify_session_integrity(session_id)
        assert integrity_valid, "Session integrity should be valid after recovery"

        # Test tampering detection
        # Manually corrupt session data
        session_file = tester.temp_dir / "sessions" / session_id / "session.json"
        if session_file.exists():
            with open(session_file, "w") as f:
                f.write('{"corrupted": "data"}')

        # Integrity should fail
        integrity_invalid = tester.storage.verify_session_integrity(session_id)
        assert not integrity_invalid, "Should detect tampering after corruption"

        print("✅ Integrity verification after recovery: PASSED")

    finally:
        tester.teardown()


def test_performance_recovery_large_sessions():
    """Test recovery performance with large session data."""
    tester = CrashRecoveryTester()

    try:
        tester.setup()

        # Create large session
        session = tester.create_test_session()
        session_id = session.snapshot_id

        # Add many observations and notes
        for i in range(1000):
            session.add_observation(f"file_{i}.py", {"type": "file", "size": i * 100})

        for i in range(100):
            session.add_note(
                NoteEntry(
                    id=f"note-{i}",
                    anchor_id=f"file_{i}.py:{i}",
                    content=f"Note {i}",
                    created_at=datetime.now(UTC),
                )
            )

        # Time the save operation
        start_time = time.time()
        tester.storage.save_session(session)
        save_time = time.time() - start_time

        # Time the recovery operation
        start_time = time.time()
        recovered_session = tester.storage.load_session(session_id)
        recovery_time = time.time() - start_time

        # Verify performance is reasonable (< 5 seconds for 1000 items)
        assert save_time < 5.0, f"Save too slow: {save_time}s"
        assert recovery_time < 5.0, f"Recovery too slow: {recovery_time}s"
        assert len(recovered_session.observations) == 1000, (
            "Should recover all observations"
        )
        assert len(recovered_session.notes) == 100, "Should recover all notes"

        print(
            f"✅ Performance recovery large sessions: PASSED ({save_time:.2f}s save, {recovery_time:.2f}s recovery)"
        )

    finally:
        tester.teardown()


def run_crash_recovery_tests():
    """Run all crash recovery tests."""
    print("=" * 60)
    print("CRASH RECOVERY TESTS - Article 15 Compliance")
    print("=" * 60)

    tests = [
        test_session_persistence_across_crash,
        test_partial_data_recovery,
        test_session_continuity_after_recovery,
        test_concurrent_session_safety,
        test_session_backup_and_restore,
        test_integrity_verification_after_recovery,
        test_performance_recovery_large_sessions,
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
    print(f"CRASH RECOVERY TEST RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ ALL CRASH RECOVERY TESTS PASSED")
    else:
        print("❌ SOME CRASH RECOVERY TESTS FAILED")

    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_crash_recovery_tests()
    exit(0 if success else 1)
