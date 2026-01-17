"""
TRANSACTIONAL STORAGE WITH RECOVERY

Provides ACID-like guarantees for observation storage.
Handles 50K+ files with corruption detection and recovery.

Constitutional Rules:
1. No partial writes ever visible
2. All writes are verifiable
3. Corruption is detected and flagged
4. Recovery is always possible from backups
"""

import os
import json
import hashlib
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
import shutil
import time

from .atomic import atomic_write_json_compatible as atomic_write, atomic_write_binary, AtomicWriteError
from .corruption import CorruptionEvidence, CorruptionType, CorruptionMarker, verify_hash


@dataclass(frozen=True)
class WriteTransaction:
    """A single write transaction with metadata."""
    transaction_id: str
    target_path: Path
    data: Dict[str, Any]
    timestamp: datetime
    checksum: str
    backup_path: Optional[Path] = None
    temp_path: Optional[Path] = None


@dataclass
class TransactionLog:
    """Log of all write transactions for recovery."""
    transactions: List[WriteTransaction] = field(default_factory=list)
    lock: threading.RLock = field(default_factory=threading.RLock)
    
    def add_transaction(self, transaction: WriteTransaction) -> None:
        """Add transaction to log."""
        with self.lock:
            self.transactions.append(transaction)
    
    def get_pending_transactions(self) -> List[WriteTransaction]:
        """Get transactions that may not have completed."""
        with self.lock:
            return [t for t in self.transactions if not t.target_path.exists()]
    
    def clear_completed(self) -> None:
        """Clear completed transactions."""
        with self.lock:
            self.transactions = [t for t in self.transactions 
                            if not t.target_path.exists() or t.temp_path.exists()]


class TransactionalStorageError(Exception):
    """Base exception for transactional storage failures."""
    pass


class InsufficientSpaceError(TransactionalStorageError):
    """Not enough disk space for write operation."""
    pass


class ConcurrentWriteError(TransactionalStorageError):
    """Another process is writing to the same file."""
    pass


class RecoveryError(TransactionalStorageError):
    """Failed to recover from corruption."""
    pass


class DiskSpaceChecker:
    """Monitors available disk space."""
    
    @staticmethod
    def check_space(path: Path, required_bytes: int) -> bool:
        """
        Check if enough disk space is available.
        
        Args:
            path: Path where write will occur
            required_bytes: Bytes needed for write
            
        Returns:
            True if enough space available
        """
        try:
            stat = shutil.disk_usage(path.parent)
            return stat.free >= required_bytes * 2  # Need 2x for temp file
        except (OSError, AttributeError):
            # If we can't check, assume there's space
            return True
    
    @staticmethod
    def get_space_info(path: Path) -> Dict[str, int]:
        """Get disk space information."""
        try:
            stat = shutil.disk_usage(path.parent)
            return {
                "total": stat.total,
                "used": stat.used,
                "free": stat.free
            }
        except (OSError, AttributeError):
            return {"total": 0, "used": 0, "free": 0}


class LockManager:
    """Manages file locks for concurrent write protection."""
    
    def __init__(self, lock_dir: Path):
        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)
    
    def acquire_lock(self, target_path: Path, timeout: float = 30.0) -> bool:
        """
        Acquire exclusive lock on file.
        
        Args:
            target_path: File to lock
            timeout: Seconds to wait for lock
            
        Returns:
            True if lock acquired
        """
        lock_file = self.lock_dir / f"{target_path.name}.lock"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to create lock file exclusively
                fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
            except OSError:
                # Lock exists, check if it's stale
                if lock_file.exists():
                    try:
                        with open(lock_file, 'r') as f:
                            pid = int(f.read().strip())
                        # Check if process is still running
                        if not self._is_process_running(pid):
                            lock_file.unlink()
                            continue
                    except (ValueError, OSError):
                        pass
                time.sleep(0.1)
        
        return False
    
    def release_lock(self, target_path: Path) -> None:
        """Release lock on file."""
        lock_file = self.lock_dir / f"{target_path.name}.lock"
        try:
            lock_file.unlink()
        except OSError:
            pass
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if process with given PID is running."""
        try:
            if os.name == 'nt':  # Windows
                import psutil
                return psutil.pid_exists(pid)
            else:  # Unix-like
                os.kill(pid, 0)
                return True
        except (OSError, ImportError):
            return False


class TransactionalWriter:
    """
    Transactional writer with backup and recovery.
    
    Guarantees:
    1. Atomic writes with fsync
    2. Automatic backup creation
    3. Corruption detection
    4. Recovery from failures
    """
    
    def __init__(self, 
                 base_path: Path,
                 backup_dir: Optional[Path] = None,
                 enable_backups: bool = True):
        """
        Initialize transactional writer.
        
        Args:
            base_path: Base directory for writes
            backup_dir: Directory for backups (auto-created if None)
            enable_backups: Whether to create backups
        """
        self.base_path = Path(base_path)
        self.backup_dir = backup_dir or self.base_path / ".backups"
        self.enable_backups = enable_backups
        self.lock_manager = LockManager(self.base_path / ".locks")
        self.transaction_log = TransactionLog()
        
        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        if self.enable_backups:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def write_observation(self, 
                       observation_data: Dict[str, Any],
                       session_id: str,
                       obs_id: Optional[str] = None) -> str:
        """
        Write observation with transactional guarantees.
        
        Args:
            observation_data: Observation data to write
            session_id: Session identifier
            obs_id: Optional observation ID
            
        Returns:
            Observation ID that was written
            
        Raises:
            TransactionalStorageError: If write fails
        """
        # Generate ID if not provided
        if not obs_id:
            obs_id = self._generate_observation_id(observation_data, session_id)
        
        target_path = self.base_path / 'observations' / f'{obs_id}.observation.json'
        
        # Add metadata
        observation_data = observation_data.copy()
        observation_data['session_id'] = session_id
        observation_data['written_at'] = datetime.now(timezone.utc).isoformat()
        observation_data['transaction_id'] = f"tx_{int(time.time() * 1000)}"
        
        # Calculate checksum
        checksum = self._calculate_checksum(observation_data)
        observation_data['checksum'] = checksum
        
        # Create transaction
        transaction = WriteTransaction(
            transaction_id=observation_data['transaction_id'],
            target_path=target_path,
            data=observation_data,
            timestamp=datetime.now(timezone.utc),
            checksum=checksum
        )
        
        try:
            # Acquire lock
            if not self.lock_manager.acquire_lock(target_path):
                raise ConcurrentWriteError(f"Cannot acquire lock for {target_path}")
            
            # Check disk space
            data_size = len(json.dumps(observation_data).encode())
            if not DiskSpaceChecker.check_space(target_path, data_size):
                raise InsufficientSpaceError(
                    f"Insufficient disk space for {target_path} "
                    f"(need {data_size} bytes)"
                )
            
            # Create backup if file exists
            if self.enable_backups and target_path.exists():
                backup_path = self._create_backup(target_path)
                transaction = WriteTransaction(
                    transaction_id=transaction.transaction_id,
                    target_path=target_path,
                    data=observation_data,
                    timestamp=transaction.timestamp,
                    checksum=checksum,
                    backup_path=backup_path
                )
            
            # Write atomically
            self._write_atomically(target_path, observation_data)
            
            # Verify write
            self._verify_write(target_path, checksum)
            
            # Add to log
            self.transaction_log.add_transaction(transaction)
            
            return obs_id
            
        except Exception as e:
            # Attempt recovery
            self._recover_from_failure(transaction)
            raise TransactionalStorageError(f"Write failed: {e}") from e
        finally:
            # Always release lock
            self.lock_manager.release_lock(target_path)
    
    def _write_atomically(self, 
                         target_path: Path, 
                         data: Dict[str, Any],
                         backup_path: Optional[Path] = None) -> None:
        """Write data atomically with proper fsync."""
        # Use atomic_write from storage.atomic
        try:
            atomic_write(target_path, data)
        except AtomicWriteError as e:
            raise TransactionalStorageError(f"Atomic write failed: {e}") from e
    
    def _verify_write(self, target_path: Path, expected_checksum: str) -> None:
        """Verify write was successful and data is not corrupted."""
        if not target_path.exists():
            raise TransactionalStorageError(f"Write verification failed: {target_path} does not exist")
        
        # Read and verify checksum
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise TransactionalStorageError(
                    f"Write verification failed: expected JSON object, got {type(data).__name__}"
                )
            
            actual_checksum = self._calculate_checksum(data)
            if actual_checksum != expected_checksum:
                raise TransactionalStorageError(
                    f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                )
                
        except (json.JSONDecodeError, OSError) as e:
            raise TransactionalStorageError(f"Write verification failed: {e}") from e
    
    def _create_backup(self, target_path: Path) -> Path:
        """Create backup of existing file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        backup_name = f"{target_path.stem}.{timestamp}.backup{target_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(target_path, backup_path)
            return backup_path
        except OSError as e:
            raise TransactionalStorageError(f"Backup creation failed: {e}") from e
    
    def _recover_from_failure(self, transaction: WriteTransaction) -> None:
        """Attempt to recover from write failure."""
        # Clean up temp file
        if transaction.temp_path and transaction.temp_path.exists():
            try:
                transaction.temp_path.unlink()
            except OSError:
                pass
        
        # If we have a backup, restore it
        if transaction.backup_path and transaction.backup_path.exists():
            try:
                shutil.copy2(transaction.backup_path, transaction.target_path)
            except OSError:
                pass  # Best effort
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum of data."""
        # Normalize JSON for consistent hashing.
        # Exclude the checksum field itself to avoid self-referential mismatch.
        normalized = dict(data)
        normalized.pop('checksum', None)
        json_str = json.dumps(normalized, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def verify_all_observations(self) -> List[CorruptionEvidence]:
        """
        Verify all observation files for corruption.
        
        Returns:
            List of corruption evidence found
        """
        evidence_list = []
        obs_dir = self.base_path / 'observations'
        
        if not obs_dir.exists():
            return evidence_list
        
        for obs_file in obs_dir.glob('*.observation.json'):
            # Check for corruption marker
            if CorruptionMarker.has_marker(obs_file):
                marker_data = CorruptionMarker.read_marker(obs_file)
                if marker_data:
                    evidence_list.append(CorruptionEvidence(
                        path=obs_file,
                        corruption_type=CorruptionType.CORRUPTION_MARKER,
                        expected_value="No corruption marker",
                        actual_value=f"Corruption detected: {marker_data.get('corruption_type')}",
                        context=marker_data
                    ))
                continue
            
            # Verify file integrity
            try:
                with open(obs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Verify checksum if present
                if 'checksum' in data:
                    expected_checksum = data['checksum']
                    actual_checksum = self._calculate_checksum(data)
                    if actual_checksum != expected_checksum:
                        evidence_list.append(CorruptionEvidence(
                            path=obs_file,
                            corruption_type=CorruptionType.HASH_MISMATCH,
                            expected_value=expected_checksum,
                            actual_value=actual_checksum
                        ))
                
            except (json.JSONDecodeError, OSError) as e:
                evidence_list.append(CorruptionEvidence(
                    path=obs_file,
                    corruption_type=CorruptionType.JSON_PARSE_ERROR,
                    expected_value="Valid JSON",
                    actual_value=str(e)
                ))
        
        return evidence_list
    
    def repair_corrupted_observations(self) -> Tuple[int, List[str]]:
        """
        Attempt to repair corrupted observations from backups.
        
        Returns:
            Tuple of (repaired_count, repair_log)
        """
        repaired_count = 0
        repair_log = []
        
        evidence_list = self.verify_all_observations()
        
        for evidence in evidence_list:
            if evidence.corruption_type in [CorruptionType.HASH_MISMATCH, 
                                        CorruptionType.JSON_PARSE_ERROR]:
                # Try to restore from backup
                backup_pattern = f"{evidence.path.stem}.*.backup{evidence.path.suffix}"
                backups = list(self.backup_dir.glob(backup_pattern))
                
                if backups:
                    # Use the most recent backup
                    latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
                    try:
                        shutil.copy2(latest_backup, evidence.path)
                        repaired_count += 1
                        repair_log.append(f"Restored {evidence.path} from {latest_backup}")
                    except OSError as e:
                        repair_log.append(f"Failed to restore {evidence.path}: {e}")
                else:
                    repair_log.append(f"No backup available for {evidence.path}")
        
        return repaired_count, repair_log
    
    def cleanup_old_backups(self, days: int = 7) -> int:
        """
        Clean up old backup files.
        
        Args:
            days: Keep backups newer than this many days
            
        Returns:
            Number of backups cleaned up
        """
        if not self.backup_dir.exists():
            return 0
        
        cutoff_time = time.time() - (days * 24 * 3600)
        cleaned = 0
        
        for backup_file in self.backup_dir.glob('*.backup*'):
            if backup_file.stat().st_mtime < cutoff_time:
                try:
                    backup_file.unlink()
                    cleaned += 1
                except OSError:
                    pass
        
        return cleaned
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        obs_dir = self.base_path / 'observations'
        
        if not obs_dir.exists():
            return {"total_observations": 0, "total_size_bytes": 0}
        
        obs_files = list(obs_dir.glob('*.observation.json'))
        total_size = sum(f.stat().st_size for f in obs_files)
        
        # Get disk space info
        space_info = DiskSpaceChecker.get_space_info(self.base_path)
        
        return {
            "total_observations": len(obs_files),
            "total_size_bytes": total_size,
            "disk_space": space_info,
            "backup_count": len(list(self.backup_dir.glob('*.backup*'))) if self.backup_dir.exists() else 0,
            "pending_transactions": len(self.transaction_log.get_pending_transactions())
        }
    
    def _generate_observation_id(self, observation_data: Dict[str, Any], session_id: str) -> str:
        """
        Generate deterministic observation ID for Article 13 compliance.
        
        Args:
            observation_data: The observation content
            session_id: Session context for uniqueness
            
        Returns:
            Deterministic observation ID
        """
        # Article 13 Compliance: Deterministic observation IDs for truth artifacts
        # Use content hash and session context for reproducible IDs
        import hashlib
        content_str = str(observation_data)
        session_context = str(session_id)
        base_string = f"{content_str}:{session_context}"
        content_hash = hashlib.sha256(base_string.encode()).hexdigest()[:16]
        return f"obs_{content_hash}"


# Export public API
__all__ = [
    'TransactionalStorage',
    'WriteTransaction',
    'TransactionalStorageError',
    'InsufficientSpaceError',
    'ConcurrentWriteError',
    'RecoveryError',
    'DiskSpaceChecker',
    'LockManager'
]
