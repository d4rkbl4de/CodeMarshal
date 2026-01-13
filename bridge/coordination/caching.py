"""
bridge.coordination.caching
===========================

Shared caching logic for truth-preserving investigations.

Core Responsibility:
    Store immutable observations, session snapshots, and computed patterns
    temporarily for performance while ensuring cache never mutates truth.

Architectural Principles:
    1. Immutable storage: once cached, cannot be overwritten silently
    2. Deterministic retrieval: same key → same value always
    3. Versioned updates: prevent regression or data loss
    4. Recovery capability: cache rebuilds from truth sources on failure

Import Rules:
    Allowed: standard library, storage.atomic, storage.layout
    Forbidden: anything that could introduce interpretation or inference
"""

import threading
import hashlib
import time
import logging
from typing import Any, Optional, Dict, Callable, List, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import pickle  # For Python object serialization (immutable only)

# Configure logging for audit trail
logger = logging.getLogger(__name__)


class CacheEntryType(Enum):
    """Types of cache entries for classification and policy enforcement."""
    OBSERVATION_SNAPSHOT = auto()  # Immutable observation records
    PATTERN_RESULT = auto()        # Computed numeric patterns
    SESSION_STATE = auto()         # Investigation session context
    COMPUTED_METRIC = auto()       # Performance metrics
    TRANSIENT_DATA = auto()        # Temporary data (evictable)


class CacheConsistencyLevel(Enum):
    """Consistency requirements for different data types."""
    STRONG = auto()      # Must be exactly correct (observations)
    WEAK = auto()        # Can be recomputed if lost (patterns)
    TRANSIENT = auto()   # Pure performance (can be dropped)


@dataclass(frozen=True)
class CacheKey:
    """Immutable cache key with structured components.
    
    Ensures deterministic key generation and prevents key collisions.
    """
    entry_type: CacheEntryType
    investigation_id: str
    session_id: Optional[str] = None
    observation_id: Optional[str] = None
    pattern_name: Optional[str] = None
    version: int = 1
    
    def to_string(self) -> str:
        """Generate deterministic string representation for hashing."""
        components = [
            f"type:{self.entry_type.name}",
            f"inv:{self.investigation_id}",
            f"ver:{self.version}",
        ]
        
        if self.session_id:
            components.append(f"sess:{self.session_id}")
        if self.observation_id:
            components.append(f"obs:{self.observation_id}")
        if self.pattern_name:
            components.append(f"pattern:{self.pattern_name}")
        
        return "|".join(components)
    
    def to_hash(self) -> str:
        """Generate SHA-256 hash of key for storage."""
        key_string = self.to_string()
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class CacheEntry:
    """Immutable cache entry with integrity guarantees."""
    key: CacheKey
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: Optional[int] = None
    consistency_level: CacheConsistencyLevel = CacheConsistencyLevel.STRONG
    
    def mark_accessed(self) -> 'CacheEntry':
        """Return new entry with updated access metadata.
        
        Note: Returns new instance to maintain immutability.
        """
        import copy
        new_entry = copy.copy(self)
        # We need to bypass frozen dataclass - use object.__setattr__
        object.__setattr__(new_entry, 'accessed_at', time.time())
        object.__setattr__(new_entry, 'access_count', self.access_count + 1)
        return new_entry
    
    def estimate_size(self) -> int:
        """Estimate memory size of cached value in bytes."""
        if self.size_bytes is not None:
            return self.size_bytes
        
        try:
            # Try to serialize to get size estimate
            serialized = pickle.dumps(self.value)
            return len(serialized)
        except (pickle.PickleError, TypeError):
            # Fallback to string representation
            return len(str(self.value).encode('utf-8'))


class CacheManager:
    """Manages caching of immutable truths and computed patterns.
    
    Implementation Notes:
        - Thread-safe operations with fine-grained locking
        - Versioned updates prevent regression
        - Memory bounds with LRU eviction for transient data
        - Deterministic retrieval guarantees
        - No mutation of cached truths (Article 9 compliance)
    """
    
    def __init__(
        self,
        max_memory_mb: int = 1024,  # 1GB default
        persistence_path: Optional[Path] = None,
        enable_persistence: bool = False
    ) -> None:
        """Initialize cache manager with memory bounds and persistence options.
        
        Args:
            max_memory_mb: Maximum memory usage in megabytes
            persistence_path: Directory for persistent cache storage
            enable_persistence: Whether to persist cache across runs
            
        Note:
            Observation snapshots are never persisted - they must be
            regenerated from source truth to ensure integrity.
        """
        # Primary in-memory cache
        self._cache: Dict[str, CacheEntry] = {}
        
        # Index for fast lookups by entry type
        self._indices: Dict[CacheEntryType, Set[str]] = {
            entry_type: set()
            for entry_type in CacheEntryType
        }
        
        # Memory tracking
        self._max_bytes = max_memory_mb * 1024 * 1024
        self._current_bytes = 0
        
        # Thread safety
        self._lock = threading.RLock()
        self._entry_locks: Dict[str, threading.RLock] = {}
        self._entry_lock_lock = threading.Lock()  # For _entry_locks dict
        
        # Persistence
        self._persistence_path = persistence_path
        self._enable_persistence = enable_persistence
        
        # Statistics for monitoring
        self._stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "version_conflicts": 0,
            "integrity_errors": 0,
        }
        
        # Callback for status updates
        self._status_callback: Optional[Callable[[str, Any], None]] = None
        
        # Eviction policy: LRU for transient data only
        self._lru_queue: List[str] = []  # Most recently used at end
        
        logger.info(
            f"CacheManager initialized: max_memory={max_memory_mb}MB, "
            f"persistence={'enabled' if enable_persistence else 'disabled'}"
        )
    
    def set_status_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Set callback for status updates to indicators layer."""
        self._status_callback = callback
    
    def _notify_status(self, status_type: str, data: Any = None) -> None:
        """Notify status callback if set."""
        if self._status_callback:
            try:
                self._status_callback(status_type, data)
            except Exception as e:
                logger.warning(f"Status callback failed: {e}")
    
    def _get_entry_lock(self, key_hash: str) -> threading.RLock:
        """Get or create lock for specific cache entry."""
        with self._entry_lock_lock:
            if key_hash not in self._entry_locks:
                self._entry_locks[key_hash] = threading.RLock()
            return self._entry_locks[key_hash]
    
    def _make_space(self, required_bytes: int) -> bool:
        """Evict entries to make space if needed.
        
        Args:
            required_bytes: Bytes needed for new entry
            
        Returns:
            True if space was made, False if impossible
            
        Note:
            Only evicts TRANSIENT and WEAK consistency entries.
            STRONG consistency entries (observations) are never evicted.
        """
        with self._lock:
            available = self._max_bytes - self._current_bytes
            
            if available >= required_bytes:
                return True
            
            # Sort entries by eviction priority
            evictable_entries: List[tuple[float, int, str]] = []
            for key_hash, entry in self._cache.items():
                if entry.consistency_level in (CacheConsistencyLevel.TRANSIENT, 
                                              CacheConsistencyLevel.WEAK):
                    evictable_entries.append((
                        entry.accessed_at,  # LRU: oldest first
                        entry.estimate_size(),
                        key_hash
                    ))
            
            # Sort by access time (oldest first)
            evictable_entries.sort(key=lambda x: x[0])
            
            bytes_freed = 0
            entries_evicted = 0
            
            for _, entry_size, key_hash in evictable_entries:
                if bytes_freed >= required_bytes - available:
                    break
                
                # Evict entry
                self._evict_entry(key_hash)
                bytes_freed += entry_size
                entries_evicted += 1
            
            if bytes_freed >= required_bytes - available:
                logger.debug(f"Evicted {entries_evicted} entries, freed {bytes_freed} bytes")
                self._stats["evictions"] += entries_evicted
                return True
            
            # Not enough evictable space
            logger.warning(
                f"Cannot make {required_bytes} bytes of space. "
                f"Available: {available}, Could free: {bytes_freed}"
            )
            return False
    
    def _evict_entry(self, key_hash: str) -> None:
        """Remove entry from cache completely."""
        with self._lock:
            if key_hash not in self._cache:
                return
            
            entry = self._cache[key_hash]
            
            # Update indices
            if entry.key.entry_type in self._indices:
                self._indices[entry.key.entry_type].discard(key_hash)
            
            # Update memory tracking
            entry_size = entry.estimate_size()
            self._current_bytes = max(0, self._current_bytes - entry_size)
            
            # Remove from LRU queue
            if key_hash in self._lru_queue:
                self._lru_queue.remove(key_hash)
            
            # Remove entry
            del self._cache[key_hash]
            
            # Clean up lock if no longer needed
            with self._entry_lock_lock:
                if key_hash in self._entry_locks:
                    del self._entry_locks[key_hash]
    
    def _update_lru(self, key_hash: str) -> None:
        """Update LRU tracking for entry."""
        with self._lock:
            if key_hash in self._lru_queue:
                self._lru_queue.remove(key_hash)
            self._lru_queue.append(key_hash)
            
            # Keep LRU queue bounded
            if len(self._lru_queue) > 10000:  # Reasonable upper bound
                self._lru_queue = self._lru_queue[-5000:]
    
    def get(self, key: CacheKey) -> Optional[Any]:
        """Retrieve cached value deterministically.
        
        Args:
            key: CacheKey identifying the desired entry
            
        Returns:
            Cached value or None if not found
            
        Note:
            Access tracking updates do not mutate the cached value,
            only metadata about access patterns.
        """
        key_hash = key.to_hash()
        
        # Get entry-specific lock to prevent concurrent modification
        entry_lock = self._get_entry_lock(key_hash)
        
        with entry_lock:
            with self._lock:
                if key_hash not in self._cache:
                    self._stats["misses"] += 1
                    logger.debug(f"Cache miss for key: {key.to_string()}")
                    return None
                
                entry = self._cache[key_hash]
                
                # Verify version compatibility
                if entry.key.version != key.version:
                    logger.warning(
                        f"Version mismatch for {key.to_string()}: "
                        f"cached={entry.key.version}, requested={key.version}"
                    )
                    self._stats["version_conflicts"] += 1
                    return None
                
                # Update access tracking
                updated_entry = entry.mark_accessed()
                self._cache[key_hash] = updated_entry
                self._stats["hits"] += 1
                
                # Update LRU tracking
                self._update_lru(key_hash)
                
                logger.debug(f"Cache hit for key: {key.to_string()}")
                return updated_entry.value
    
    def set(
        self, 
        key: CacheKey, 
        value: Any, 
        consistency_level: CacheConsistencyLevel = CacheConsistencyLevel.STRONG
    ) -> bool:
        """Add a value to cache with version protection.
        
        Args:
            key: CacheKey identifying the entry
            value: Value to cache (should be immutable)
            consistency_level: Required consistency level
            
        Returns:
            True if cached successfully, False otherwise
            
        Note:
            Cannot overwrite entries with same or higher version.
            Lower version entries can be replaced (prevent regression).
        """
        # Estimate size before acquiring locks
        try:
            serialized = pickle.dumps(value)
            estimated_size = len(serialized)
        except (pickle.PickleError, TypeError):
            # Conservative estimate for non-picklable objects
            estimated_size = 1024  # 1KB default
        
        key_hash = key.to_hash()
        entry_lock = self._get_entry_lock(key_hash)
        
        with entry_lock:
            with self._lock:
                # Check if entry already exists
                if key_hash in self._cache:
                    existing_entry = self._cache[key_hash]
                    
                    # Version check: cannot overwrite with same or lower version
                    if key.version <= existing_entry.key.version:
                        logger.warning(
                            f"Version regression prevented for {key.to_string()}: "
                            f"existing={existing_entry.key.version}, new={key.version}"
                        )
                        self._stats["version_conflicts"] += 1
                        self._notify_status("version_conflict", {
                            "key": key.to_string(),
                            "existing_version": existing_entry.key.version,
                            "new_version": key.version
                        })
                        return False
                    
                    # Remove existing entry to make space
                    self._evict_entry(key_hash)
                
                # Make space for new entry
                if not self._make_space(estimated_size):
                    logger.error(f"Cannot cache {key.to_string()}: insufficient space")
                    self._notify_status("cache_full", {
                        "key": key.to_string(),
                        "required_bytes": estimated_size
                    })
                    return False
                
                # Create and store new entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    consistency_level=consistency_level,
                    size_bytes=estimated_size
                )
                
                self._cache[key_hash] = entry
                self._indices[key.entry_type].add(key_hash)
                self._current_bytes += estimated_size
                
                # Update LRU for evictable entries
                if consistency_level in (CacheConsistencyLevel.TRANSIENT, 
                                       CacheConsistencyLevel.WEAK):
                    self._update_lru(key_hash)
                
                logger.debug(f"Cached entry: {key.to_string()} ({estimated_size} bytes)")
                self._notify_status("entry_cached", {
                    "key": key.to_string(),
                    "type": key.entry_type.name,
                    "size_bytes": estimated_size
                })
                
                # Persist if enabled (except for observations - must regenerate)
                if (self._enable_persistence and 
                    self._persistence_path and
                    consistency_level != CacheConsistencyLevel.STRONG):
                    self._persist_entry(key_hash, entry)
                
                return True
    
    def invalidate(self, key: CacheKey) -> bool:
        """Remove specific entry from cache.
        
        Args:
            key: CacheKey identifying entry to remove
            
        Returns:
            True if entry was removed, False if not found
            
        Note:
            Only removes evictable entries (not STRONG consistency
            observation snapshots).
        """
        key_hash = key.to_hash()
        entry_lock = self._get_entry_lock(key_hash)
        
        with entry_lock:
            with self._lock:
                if key_hash not in self._cache:
                    return False
                
                entry = self._cache[key_hash]
                
                # Cannot invalidate observation snapshots
                if entry.consistency_level == CacheConsistencyLevel.STRONG:
                    logger.warning(
                        f"Cannot invalidate STRONG consistency entry: {key.to_string()}"
                    )
                    return False
                
                self._evict_entry(key_hash)
                logger.info(f"Invalidated cache entry: {key.to_string()}")
                return True
    
    def invalidate_by_type(self, entry_type: CacheEntryType) -> int:
        """Invalidate all entries of specific type.
        
        Args:
            entry_type: Type of entries to invalidate
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if entry_type not in self._indices:
                return 0
            
            # Get copy of key hashes to avoid modification during iteration
            key_hashes = list(self._indices[entry_type])
            invalidated = 0
            
            for key_hash in key_hashes:
                if key_hash in self._cache:
                    entry = self._cache[key_hash]
                    
                    # Skip STRONG consistency entries
                    if entry.consistency_level == CacheConsistencyLevel.STRONG:
                        continue
                    
                    # Get lock for this entry
                    entry_lock = self._get_entry_lock(key_hash)
                    with entry_lock:
                        self._evict_entry(key_hash)
                        invalidated += 1
            
            logger.info(f"Invalidated {invalidated} entries of type {entry_type.name}")
            return invalidated
    
    def clear(self, include_strong: bool = False) -> Dict[str, int]:
        """Clear cache entries based on consistency level.
        
        Args:
            include_strong: If True, also clear STRONG consistency entries
            
        Returns:
            Dictionary with counts of cleared entries by type
            
        Note:
            By default, only clears TRANSIENT and WEAK entries.
            STRONG entries (observations) should only be cleared
            during system shutdown or explicit reset.
        """
        with self._lock:
            cleared_counts: Dict[str, int] = {}
            
            # Get all entries
            all_entries = list(self._cache.items())
            
            for key_hash, entry in all_entries:
                if (include_strong or 
                    entry.consistency_level != CacheConsistencyLevel.STRONG):
                    
                    # Get lock for this entry
                    entry_lock = self._get_entry_lock(key_hash)
                    with entry_lock:
                        self._evict_entry(key_hash)
                        
                        # Update counts
                        type_name = entry.key.entry_type.name
                        cleared_counts[type_name] = cleared_counts.get(type_name, 0) + 1
            
            logger.info(f"Cleared cache: {sum(cleared_counts.values())} entries")
            self._notify_status("cache_cleared", {
                "total_cleared": sum(cleared_counts.values()),
                "by_type": cleared_counts,
                "include_strong": include_strong
            })
            
            return cleared_counts
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and current state.
        
        Returns:
            Dictionary with cache statistics and metrics
        """
        with self._lock:
            # Build result dictionary with explicit typing
            result_stats: Dict[str, Any] = {}
            
            # Copy base stats
            result_stats.update({
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "version_conflicts": self._stats["version_conflicts"],
                "integrity_errors": self._stats["integrity_errors"],
            })
            
            # Add current state metrics
            result_stats.update({
                "total_entries": len(self._cache),
                "memory_used_mb": self._current_bytes / (1024 * 1024),
                "memory_max_mb": self._max_bytes / (1024 * 1024),
                "memory_usage_percent": (self._current_bytes / self._max_bytes * 100) 
                                      if self._max_bytes > 0 else 0,
                "entries_by_type": {
                    entry_type.name: len(keys)
                    for entry_type, keys in self._indices.items()
                },
                "lru_queue_size": len(self._lru_queue),
                "hit_ratio": (
                    self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                    if (self._stats["hits"] + self._stats["misses"]) > 0 else 0
                ),
            })
            
            return result_stats
    
    def verify_integrity(self) -> List[Dict[str, Any]]:
        """Verify integrity of cached entries.
        
        Returns:
            List of integrity issues found (empty if all good)
            
        Note:
            Checks for:
            1. Size estimation accuracy
            2. Version consistency
            3. Hash collisions
            4. Index consistency
        """
        issues: List[Dict[str, Any]] = []
        
        with self._lock:
            # Check index consistency
            for entry_type, key_hashes in self._indices.items():
                for key_hash in key_hashes:
                    if key_hash not in self._cache:
                        issues.append({
                            "type": "index_inconsistency",
                            "entry_type": entry_type.name,
                            "key_hash": key_hash,
                            "message": "Key in index but not in cache"
                        })
            
            # Check cache entries
            for key_hash, entry in self._cache.items():
                # Verify key hash matches
                computed_hash = entry.key.to_hash()
                if computed_hash != key_hash:
                    issues.append({
                        "type": "hash_mismatch",
                        "key": entry.key.to_string(),
                        "expected_hash": computed_hash,
                        "actual_hash": key_hash
                    })
                
                # Verify entry is in correct index
                if key_hash not in self._indices.get(entry.key.entry_type, set()):
                    issues.append({
                        "type": "missing_index",
                        "key": entry.key.to_string(),
                        "entry_type": entry.key.entry_type.name
                    })
                
                # Verify size estimation
                if entry.size_bytes is not None:
                    actual_size = entry.estimate_size()
                    if abs(actual_size - entry.size_bytes) > 1024:  # 1KB tolerance
                        issues.append({
                            "type": "size_mismatch",
                            "key": entry.key.to_string(),
                            "estimated_bytes": entry.size_bytes,
                            "actual_bytes": actual_size
                        })
            
            if issues:
                logger.warning(f"Found {len(issues)} integrity issues")
                self._stats["integrity_errors"] += len(issues)
                self._notify_status("integrity_issues", {"count": len(issues)})
            else:
                logger.debug("Cache integrity verified")
            
            return issues
    
    def _persist_entry(self, key_hash: str, entry: CacheEntry) -> None:
        """Persist cache entry to disk (if enabled).
        
        Args:
            key_hash: Hash of cache key
            entry: CacheEntry to persist
            
        Note:
            Only persists WEAK and TRANSIENT entries.
            STRONG entries must be regenerated from truth sources.
        """
        if not self._persistence_path or not self._enable_persistence:
            return
        
        if entry.consistency_level == CacheConsistencyLevel.STRONG:
            return  # Never persist observations
        
        try:
            # Create persistence directory
            self._persistence_path.mkdir(parents=True, exist_ok=True)
            
            # Create safe filename from hash
            filename = self._persistence_path / f"cache_{key_hash}.pkl"
            
            # Prepare data for persistence with explicit typing
            persistence_data: Dict[str, Any] = {
                "entry": entry,
                "persisted_at": time.time(),
                "version": 1
            }
            
            # Write with atomic replacement
            temp_filename = filename.with_suffix(".tmp")
            with open(temp_filename, 'wb') as f:
                pickle.dump(persistence_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            temp_filename.replace(filename)
            
            logger.debug(f"Persisted cache entry: {entry.key.to_string()}")
            
        except Exception as e:
            logger.error(f"Failed to persist cache entry {key_hash}: {e}")
    
    def _load_persisted(self) -> int:
        """Load persisted cache entries from disk.
        
        Returns:
            Number of entries loaded
            
        Note:
            Only called if persistence is enabled.
        """
        if not self._persistence_path or not self._enable_persistence:
            return 0
        
        loaded = 0
        
        try:
            for filepath in self._persistence_path.glob("cache_*.pkl"):
                try:
                    with open(filepath, 'rb') as f:
                        persistence_data = pickle.load(f)
                    
                    entry = persistence_data.get("entry")
                    if not isinstance(entry, CacheEntry):
                        continue
                    
                    # Skip STRONG consistency entries
                    if entry.consistency_level == CacheConsistencyLevel.STRONG:
                        continue
                    
                    key_hash = entry.key.to_hash()
                    
                    # Add to cache if not already present
                    with self._lock:
                        if key_hash not in self._cache:
                            self._cache[key_hash] = entry
                            self._indices[entry.key.entry_type].add(key_hash)
                            self._current_bytes += entry.estimate_size()
                            loaded += 1
                    
                except (pickle.PickleError, EOFError, KeyError) as e:
                    logger.warning(f"Failed to load persisted cache file {filepath}: {e}")
                    # Remove corrupted file
                    filepath.unlink(missing_ok=True)
        
        except Exception as e:
            logger.error(f"Error loading persisted cache: {e}")
        
        logger.info(f"Loaded {loaded} persisted cache entries")
        return loaded


# Singleton cache manager instance for system-wide use
_system_cache: Optional[CacheManager] = None
_cache_lock = threading.Lock()


def get_system_cache() -> CacheManager:
    """Get or create the system-wide cache manager instance.
    
    Returns:
        Shared CacheManager instance
        
    Note:
        Configured with sensible defaults for production use.
    """
    global _system_cache
    
    with _cache_lock:
        if _system_cache is None:
            # Default configuration
            persistence_path = Path.home() / ".codemarshal" / "cache"
            _system_cache = CacheManager(
                max_memory_mb=512,  # 512MB default
                persistence_path=persistence_path,
                enable_persistence=True
            )
            logger.info("Created system cache manager singleton")
        
        return _system_cache


def reset_system_cache(include_strong: bool = False) -> Dict[str, int]:
    """Reset the system cache (for testing and recovery).
    
    Args:
        include_strong: If True, also clear STRONG consistency entries
        
    Returns:
        Counts of cleared entries by type
        
    Warning:
        Clearing STRONG entries may cause performance degradation
        as observations must be regenerated.
    """
    global _system_cache
    
    with _cache_lock:
        if _system_cache:
            cleared = _system_cache.clear(include_strong=include_strong)
            logger.warning(f"System cache reset: {sum(cleared.values())} entries cleared")
            return cleared
        
        return {}