"""
Transactional storage integration for engine.

Moved from core layer to storage layer to preserve Article 9 (layer independence).
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from storage.transactional import TransactionalWriter, TransactionalStorageError, DiskSpaceChecker
from storage.corruption import CorruptionEvidence, CorruptionType, CorruptionMarker
from storage.atomic import atomic_write_json_compatible


class InvestigationStorage:
    """
    Transactional storage with corruption detection and recovery.

    Features:
    - Atomic writes with fsync
    - Automatic backups
    - Corruption detection
    - Recovery from failures
    - Disk space checking
    - Concurrent write protection
    """

    def __init__(self, base_path='storage', enable_backups=True):
        """
        Initialize transactional storage.

        Args:
            base_path: Base storage directory
            enable_backups: Whether to create backups of existing files
        """
        self.base_path = Path(base_path)
        self.writer = TransactionalWriter(
            base_path=self.base_path,
            enable_backups=enable_backups
        )
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directory structure."""
        directories = [
            self.base_path / 'sessions',
            self.base_path / 'observations',
            self.base_path / 'questions',
            self.base_path / 'patterns',
            self.base_path / 'snapshots'
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def save_session(self, session_data):
        """Save session metadata with transactional guarantees."""
        session_id = session_data.get('id', f'session_{int(datetime.now().timestamp()*1000)}')
        filename = self.base_path / 'sessions' / f'{session_id}.session.json'

        # Add metadata
        session_data = session_data.copy()
        session_data['saved_at'] = datetime.now().isoformat()
        session_data['storage_version'] = '1.0'
        session_data['checksum'] = self._calculate_hash(session_data)

        try:
            # Use transactional write
            self.writer._write_atomically(
                filename,
                session_data,
                type(self.writer)._create_backup(self.writer, filename) if filename.exists() else None
            )
            return session_id
        except Exception as e:
            raise TransactionalStorageError(f"Failed to save session: {e}") from e

    def save_observation(self, observation_data, session_id):
        """
        Save observation with full transactional guarantees.

        Returns observation ID and verifies integrity.
        """
        # Ensure immutability
        observation_data = observation_data.copy()
        observation_data['hash'] = self._calculate_hash(observation_data)

        try:
            obs_id = self.writer.write_observation(
                observation_data=observation_data,
                session_id=session_id
            )
            return obs_id
        except TransactionalStorageError as e:
            # Log the failure but don't crash
            print(f"[WARNING] Observation save failed: {e}", flush=True)
            # Try to save with minimal data
            minimal_data = {
                'id': observation_data.get('id', 'unknown'),
                'error': str(e),
                'session_id': session_id,
                'saved_at': datetime.now().isoformat(),
                'corruption_detected': True
            }
            return self.writer.write_observation(
                observation_data=minimal_data,
                session_id=session_id,
                obs_id=f"corrupt_{int(datetime.now().timestamp()*1000)}"
            )

    def create_streaming_observation(self, session_id: str) -> 'StreamingObservation':
        """
        Create a streaming observation writer for incremental saves.

        Constitutional Basis:
        - Article 8: Honest performance (real-time progress)
        - Article 9: Immutable observations (each chunk is immutable)
        - Article 13: Deterministic (streaming order preserved)
        - Article 15: Checkpoints (incremental saves enable resume)

        Args:
            session_id: Session identifier

        Returns:
            StreamingObservation context manager
        """
        return StreamingObservation(
            storage=self,
            session_id=session_id,
            base_path=self.base_path
        )

    def save_question(self, question_data, session_id):
        """Save question with transactional guarantees."""
        question_id = question_data.get('id', f'q_{int(datetime.now().timestamp()*1000)}')
        filename = self.base_path / 'questions' / f'{question_id}.question.json'

        question_data = question_data.copy()
        question_data['session_id'] = session_id
        question_data['type'] = 'human_question'
        question_data['checksum'] = self._calculate_hash(question_data)

        try:
            self.writer._write_atomically(
                filename,
                question_data,
                type(self.writer)._create_backup(self.writer, filename) if filename.exists() else None
            )
            return question_id
        except Exception as e:
            raise TransactionalStorageError(f"Failed to save question: {e}") from e

    def save_pattern(self, pattern_data, session_id):
        """Save pattern with transactional guarantees."""
        pattern_id = pattern_data.get('id', f'p_{int(datetime.now().timestamp()*1000)}')
        filename = self.base_path / 'patterns' / f'{pattern_id}.pattern.json'

        pattern_data = pattern_data.copy()
        pattern_data['session_id'] = session_id
        pattern_data['type'] = 'numeric_pattern'
        pattern_data['checksum'] = self._calculate_hash(pattern_data)

        try:
            self.writer._write_atomically(
                filename,
                pattern_data,
                type(self.writer)._create_backup(self.writer, filename) if filename.exists() else None
            )
            return pattern_id
        except Exception as e:
            raise TransactionalStorageError(f"Failed to save pattern: {e}") from e

    def verify_storage_integrity(self) -> Dict[str, Any]:
        """
        Verify all stored data for corruption.

        Returns:
            Dictionary with integrity report
        """
        # Check observations
        observation_evidence = self.writer.verify_all_observations()

        # Check other files
        all_evidence = observation_evidence.copy()

        # Check session files
        sessions_dir = self.base_path / 'sessions'
        if sessions_dir.exists():
            for session_file in sessions_dir.glob('*.session.json'):
                if CorruptionMarker.has_marker(session_file):
                    all_evidence.append(CorruptionEvidence(
                        path=session_file,
                        corruption_type=CorruptionType.CORRUPTION_MARKER,
                        expected_value="No corruption marker",
                        actual_value="Corruption marker present"
                    ))

        # Get storage stats
        stats = self.writer.get_storage_stats()

        return {
            "is_corrupt": len(all_evidence) > 0,
            "corruption_count": len(all_evidence),
            "corruption_evidence": [
                {
                    "path": str(e.path),
                    "type": e.corruption_type.name,
                    "expected": str(e.expected_value)[:100],
                    "actual": str(e.actual_value)[:100]
                }
                for e in all_evidence[:10]  # Limit to first 10
            ],
            "storage_stats": stats,
            "verified_at": datetime.now().isoformat()
        }

    def repair_corruption(self) -> Dict[str, Any]:
        """
        Attempt to repair corrupted storage.

        Returns:
            Dictionary with repair results
        """
        # Repair observations
        repaired_count, repair_log = self.writer.repair_corrupted_observations()

        # Clean up old backups
        cleaned_backups = self.writer.cleanup_old_backups(days=7)

        return {
            "repaired_count": repaired_count,
            "cleaned_backups": cleaned_backups,
            "repair_log": repair_log,
            "repaired_at": datetime.now().isoformat()
        }

    def prepare_for_large_run(self, file_count: int) -> Dict[str, Any]:
        """
        Prepare storage for large run (50K+ files).

        Args:
            file_count: Expected number of files to process

        Returns:
            Preparation status
        """
        # Check disk space
        space_info = DiskSpaceChecker.get_space_info(self.base_path)

        # Estimate space needed (rough calculation)
        avg_obs_size = 1024 * 10  # 10KB per observation
        estimated_space = file_count * avg_obs_size * 3  # 3x for backups and temp

        ready = True
        warnings = []

        if space_info['free'] < estimated_space:
            ready = False
            warnings.append(
                f"Insufficient disk space: need {estimated_space//1024//1024}MB, have {space_info['free']//1024//1024}MB"
            )

        # Clean up old backups before large run
        cleaned = self.writer.cleanup_old_backups(days=1)
        if cleaned > 0:
            warnings.append(f"Cleaned {cleaned} old backup files")

        return {
            "ready": ready,
            "warnings": warnings,
            "disk_space": space_info,
            "estimated_space_needed": estimated_space
        }

    def _calculate_hash(self, data):
        """Calculate hash for immutability verification."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()


class StreamingObservation:
    """
    Streaming observation writer for large-scale operations.

    Writes observations incrementally to avoid memory accumulation.
    Each observation is written atomically as it's collected.

    Constitutional Guarantees:
    - Article 9: Each observation immutable when written
    - Article 13: Deterministic streaming order
    - Article 15: Checkpoint after each write for resumability
    """

    def __init__(self, storage: InvestigationStorage, session_id: str, base_path: Path):
        self.storage = storage
        self.session_id = session_id
        self.base_path = base_path
        self.observation_ids: List[str] = []
        self.boundary_crossings: List[Dict[str, Any]] = []
        self.files_processed: int = 0
        self.start_time = datetime.now()

        # Create manifest file for this streaming session
        self.manifest_id = f"obs_stream_{int(self.start_time.timestamp()*1000)}"
        self.manifest_path = self.base_path / 'observations' / f'{self.manifest_id}.manifest.json'

    def __enter__(self):
        """Start streaming observation session."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finalize streaming session and save manifest."""
        # Save final manifest with all observation IDs
        manifest_data = {
            'id': self.manifest_id,
            'session_id': self.session_id,
            'observation_ids': self.observation_ids,
            'boundary_crossings': self.boundary_crossings,
            'files_processed': self.files_processed,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'streaming': True,
            'complete': exc_type is None
        }

        atomic_write_json_compatible(
            self.manifest_path,
            manifest_data,
            indent=2
        )

        return False  # Don't suppress exceptions

    def write_file_observation(self, file_path: str, observations: List[Dict[str, Any]]) -> str:
        """
        Write observations for a single file atomically.

        Args:
            file_path: Path to file being observed
            observations: List of observations for this file

        Returns:
            Observation ID
        """
        obs_id = f"obs_{int(datetime.now().timestamp()*1000)}_{self.files_processed}_{abs(hash(file_path))}"

        # Convert Path objects to strings recursively
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return type(obj)(convert_paths(item) for item in obj)
            else:
                return obj

        obs_data = {
            'id': obs_id,
            'session_id': self.session_id,
            'file_path': file_path,
            'observations': convert_paths(observations),
            'file_index': self.files_processed,
            'timestamp': datetime.now().isoformat(),
            'streaming': True
        }

        # Calculate hash for immutability (Article 9)
        obs_data['hash'] = self.storage._calculate_hash(obs_data)

        # Write atomically with explicit flush
        obs_path = self.base_path / 'observations' / f'{obs_id}.observation.json'
        atomic_write_json_compatible(obs_path, obs_data, indent=2)

        # Force flush to ensure write is complete (fix incomplete writes)
        import os
        try:
            if not os.name == 'nt':  # Non-Windows
                fd = os.open(obs_path, os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
        except OSError:
            pass  # Best effort

        # Track in manifest and update incrementally (fix missing manifest updates)
        self.observation_ids.append(obs_id)
        self.files_processed += 1

        # Update manifest incrementally every 100 files
        if self.files_processed % 100 == 0:
            self._update_incremental_manifest()

        # Extract boundary crossings
        for obs in observations:
            if obs.get('type') == 'boundary_sight' and 'crossings' in obs:
                for cross in obs['crossings']:
                    self.boundary_crossings.append({
                        'source': cross.get('source_module'),
                        'target': cross.get('target_module'),
                        'file': file_path,
                        'line': cross.get('line_number'),
                        'violation': 'cross_boundary'
                    })

        return obs_id

    def _update_incremental_manifest(self):
        """Update manifest incrementally to enable resume functionality."""
        manifest_data = {
            'id': self.manifest_id,
            'session_id': self.session_id,
            'observation_ids': self.observation_ids.copy(),
            'boundary_crossings': self.boundary_crossings.copy(),
            'files_processed': self.files_processed,
            'start_time': self.start_time.isoformat(),
            'last_update': datetime.now().isoformat(),
            'streaming': True,
            'complete': False  # Mark as incomplete until final
        }

        atomic_write_json_compatible(
            self.manifest_path,
            manifest_data,
            indent=2
        )

    def can_resume_from(self, session_id: str) -> bool:
        """Check if we can resume from an existing session."""
        # Look for existing manifest with this session_id
        observations_dir = self.base_path / 'observations'
        if not observations_dir.exists():
            return False

        # Find manifests that contain our session_id
        for manifest_file in observations_dir.glob('*.manifest.json'):
            try:
                import json
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                if manifest.get('session_id') == session_id and not manifest.get('complete', True):
                    return True
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        return False

    def resume_from(self, session_id: str) -> Dict[str, Any]:
        """Resume from existing streaming session."""
        # Find existing manifest with this session_id
        observations_dir = self.base_path / 'observations'
        if not observations_dir.exists():
            raise ValueError(f"No resumable session found for {session_id}")

        # Find the manifest for this session
        manifest_path = None
        for manifest_file in observations_dir.glob('*.manifest.json'):
            try:
                import json
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                if manifest.get('session_id') == session_id and not manifest.get('complete', True):
                    manifest_path = manifest_file
                    break
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        if not manifest_path:
            raise ValueError(f"No resumable session found for {session_id}")

        try:
            import json
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            # Restore state
            self.manifest_id = manifest['id']
            self.observation_ids = manifest['observation_ids']
            self.boundary_crossings = manifest['boundary_crossings']
            self.files_processed = manifest['files_processed']

            return {
                'resumed': True,
                'files_already_processed': self.files_processed,
                'observations_restored': len(self.observation_ids),
                'boundary_crossings_found': len(self.boundary_crossings)
            }
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            raise ValueError(f"Failed to resume from session: {e}")

    def write_batch_observations(self, batch: List[Dict[str, Any]]) -> List[str]:
        """
        Write a batch of observations atomically.

        Args:
            batch: List of (file_path, observations) tuples

        Returns:
            List of observation IDs
        """
        batch_ids = []
        for item in batch:
            file_path = item.get('file_path')
            observations = item.get('observations', [])
            obs_id = self.write_file_observation(file_path, observations)
            batch_ids.append(obs_id)
        return batch_ids

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current streaming progress (Article 8: Honest performance).

        Returns:
            Progress information
        """
        return {
            'files_processed': self.files_processed,
            'observations_written': len(self.observation_ids),
            'boundary_crossings': len(self.boundary_crossings),
            'elapsed_seconds': (datetime.now() - self.start_time).total_seconds()
        }
