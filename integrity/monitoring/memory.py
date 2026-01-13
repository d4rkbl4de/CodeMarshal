"""
Memory monitoring for CodeMarshal's large-scale operations.

Purpose:
    Monitor memory usage during observation and analysis to prevent system overload.
    Track memory consumption patterns and enforce limits gracefully.

Constitutional Constraints:
    Article 8: Honest Performance - Report actual memory usage
    Article 13: Deterministic Operation - Memory checks should not affect timing
    Article 14: Graceful Degradation - Continue operating with reduced capacity
"""

import gc
import os
import threading
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import json

# Try to import psutil for detailed memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    warnings.warn("psutil not available, using basic memory monitoring only")

from core.context import RuntimeContext


@dataclass(frozen=True)
class MemorySnapshot:
    """Immutable memory usage snapshot."""
    timestamp: datetime
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    percent: float  # Memory usage percentage
    files_processed: int = 0
    operation: str = ""
    phase: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'rss_mb': round(self.rss_mb, 2),
            'vms_mb': round(self.vms_mb, 2),
            'percent': round(self.percent, 2),
            'files_processed': self.files_processed,
            'operation': self.operation,
            'phase': self.phase
        }


class MemoryMonitor:
    """
    Thread-safe memory monitoring system for large-scale operations.
    
    Features:
    - Real-time memory tracking
    - Configurable limits and warnings
    - Automatic chunking strategy
    - Graceful degradation
    """
    
    def __init__(self, 
                 context: RuntimeContext,
                 warning_threshold_mb: float = 2048,  # 2GB warning
                 critical_threshold_mb: float = 4096,  # 4GB critical
                 check_interval_files: int = 1000):  # Check every 1000 files
        """
        Initialize memory monitor.
        
        Args:
            context: Runtime context for investigation tracking
            warning_threshold_mb: Memory usage in MB that triggers warning
            critical_threshold_mb: Memory usage in MB that triggers critical action
            check_interval_files: Check memory every N files processed
        """
        self.context = context
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.check_interval_files = check_interval_files
        
        self._snapshots: List[MemorySnapshot] = []
        self._lock: threading.RLock = threading.RLock()
        self._files_processed: int = 0
        self._last_check_files: int = 0
        self._operation: str = ""
        self._phase: str = ""
        self._chunking_enabled: bool = False
        self._emergency_save_triggered: bool = False
        
        # Callbacks for memory limits
        self._warning_callback: Optional[Callable] = None
        self._critical_callback: Optional[Callable] = None
    
    def set_callbacks(self,
                     warning_callback: Optional[Callable] = None,
                     critical_callback: Optional[Callable] = None) -> None:
        """
        Set callbacks for memory limit events.
        
        Args:
            warning_callback: Called when memory > warning_threshold
            critical_callback: Called when memory > critical_threshold
        """
        self._warning_callback = warning_callback
        self._critical_callback = critical_callback
    
    def start_operation(self, operation: str, phase: str = "") -> None:
        """
        Start monitoring a new operation.
        
        Args:
            operation: Name of operation (e.g., "observe", "investigate")
            phase: Current phase of operation
        """
        with self._lock:
            self._operation = operation
            self._phase = phase
            self._files_processed = 0
            self._last_check_files = 0
            self._chunking_enabled = False
            self._emergency_save_triggered = False
    
    def track_files(self, count: int = 1) -> None:
        """
        Track files processed and check memory if needed.
        
        Args:
            count: Number of files just processed
        """
        with self._lock:
            self._files_processed += count
            
            # Check memory at intervals
            if (self._files_processed - self._last_check_files) >= self.check_interval_files:
                self._check_memory()
                self._last_check_files = self._files_processed
    
    def _get_memory_usage(self) -> tuple[float, float, float]:
        """
        Get current memory usage.
        
        Returns:
            Tuple of (rss_mb, vms_mb, percent)
        """
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                rss_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                vms_mb = memory_info.vms / 1024 / 1024
                percent = process.memory_percent()
                return rss_mb, vms_mb, percent
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Fallback to basic memory info
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            rss_mb = usage.ru_maxrss / 1024  # On Linux: KB, on macOS: bytes
            if os.name != 'posix':  # Windows
                rss_mb = rss_mb / 1024  # Convert to MB
            return rss_mb, 0.0, 0.0
        except:
            return 0.0, 0.0, 0.0
    
    def _check_memory(self) -> None:
        """Check memory usage and trigger callbacks if needed."""
        rss_mb, vms_mb, percent = self._get_memory_usage()
        
        snapshot = MemorySnapshot(
            timestamp=datetime.now(timezone.utc),
            rss_mb=rss_mb,
            vms_mb=vms_mb,
            percent=percent,
            files_processed=self._files_processed,
            operation=self._operation,
            phase=self._phase
        )
        
        self._snapshots.append(snapshot)
        
        # Check thresholds
        if rss_mb > self.critical_threshold_mb and not self._emergency_save_triggered:
            self._emergency_save_triggered = True
            if self._critical_callback:
                self._critical_callback(snapshot)
            self._trigger_emergency_save()
        
        elif rss_mb > self.warning_threshold_mb:
            if self._warning_callback:
                self._warning_callback(snapshot)
            self._enable_chunking()
    
    def _enable_chunking(self) -> None:
        """Enable chunking strategy to reduce memory usage."""
        self._chunking_enabled = True
        # Force garbage collection
        gc.collect()
    
    def _trigger_emergency_save(self) -> None:
        """Trigger emergency save and prepare for shutdown."""
        # Save current state
        self.save_to_disk()
        # Force garbage collection
        gc.collect()
        # Log critical memory usage
        print(f"⚠️ CRITICAL: Memory usage {self._get_memory_usage()[0]:.1f}MB exceeds limit", flush=True)
    
    def should_chunk(self) -> bool:
        """
        Check if chunking should be used for current operation.
        
        Returns:
            True if memory usage requires chunking
        """
        return self._chunking_enabled
    
    def get_memory_status(self) -> Dict[str, Any]:
        """
        Get current memory status and statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        rss_mb, vms_mb, percent = self._get_memory_usage()
        
        with self._lock:
            recent_snapshots = self._snapshots[-10:] if self._snapshots else []
            
        return {
            'current_rss_mb': round(rss_mb, 2),
            'current_vms_mb': round(vms_mb, 2),
            'current_percent': round(percent, 2),
            'warning_threshold_mb': self.warning_threshold_mb,
            'critical_threshold_mb': self.critical_threshold_mb,
            'files_processed': self._files_processed,
            'chunking_enabled': self._chunking_enabled,
            'emergency_save_triggered': self._emergency_save_triggered,
            'recent_snapshots': [s.to_dict() for s in recent_snapshots],
            'psutil_available': PSUTIL_AVAILABLE
        }
    
    def save_to_disk(self, path: Optional[Path] = None) -> Path:
        """
        Save memory snapshots to disk.
        
        Args:
            path: Optional custom path
            
        Returns:
            Path where snapshots were saved
        """
        if path is None:
            from storage.layout import get_investigation_path
            inv_path = get_investigation_path(self.context.investigation_id)
            path = inv_path / "memory" / f"snapshots_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            snapshots_data = [s.to_dict() for s in self._snapshots]
            status = self.get_memory_status()
        
        data = {
            'snapshots': snapshots_data,
            'status': status,
            'metadata': {
                'investigation_id': self.context.investigation_id,
                'saved_at': datetime.now(timezone.utc).isoformat(),
                'snapshot_count': len(snapshots_data)
            }
        }
        
        # Atomic write
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        temp_path.rename(path)
        
        return path
    
    def clear(self) -> None:
        """Clear all memory snapshots."""
        with self._lock:
            self._snapshots.clear()
            self._files_processed = 0
            self._last_check_files = 0
            self._chunking_enabled = False
            self._emergency_save_triggered = False


# Global memory monitor instance
_MEMORY_MONITOR: Optional[MemoryMonitor] = None
_MONITOR_LOCK: threading.RLock = threading.RLock()


def get_memory_monitor(context: Optional[RuntimeContext] = None,
                      warning_threshold_mb: float = 2048,
                      critical_threshold_mb: float = 4096) -> MemoryMonitor:
    """
    Get or create the global memory monitor.
    
    Args:
        context: Runtime context (required on first call)
        warning_threshold_mb: Memory warning threshold in MB
        critical_threshold_mb: Memory critical threshold in MB
        
    Returns:
        MemoryMonitor instance
    """
    global _MEMORY_MONITOR
    
    with _MONITOR_LOCK:
        if _MEMORY_MONITOR is None:
            if context is None:
                raise ValueError("RuntimeContext required for first initialization")
            _MEMORY_MONITOR = MemoryMonitor(
                context=context,
                warning_threshold_mb=warning_threshold_mb,
                critical_threshold_mb=critical_threshold_mb
            )
        
        return _MEMORY_MONITOR


def setup_memory_monitoring(context: RuntimeContext,
                           warning_threshold_mb: float = 2048,
                           critical_threshold_mb: float = 4096) -> MemoryMonitor:
    """
    Set up memory monitoring with default callbacks.
    
    Args:
        context: Runtime context
        warning_threshold_mb: Warning threshold in MB
        critical_threshold_mb: Critical threshold in MB
        
    Returns:
        Configured MemoryMonitor instance
    """
    monitor = get_memory_monitor(context, warning_threshold_mb, critical_threshold_mb)
    
    def warning_callback(snapshot: MemorySnapshot):
        """Handle memory warning."""
        print(f"⚠️ Memory warning: {snapshot.rss_mb:.1f}MB used at {snapshot.files_processed} files", flush=True)
    
    def critical_callback(snapshot: MemorySnapshot):
        """Handle critical memory usage."""
        print(f"🚨 CRITICAL: Memory limit exceeded: {snapshot.rss_mb:.1f}MB", flush=True)
        print("Initiating emergency save and chunking...", flush=True)
    
    monitor.set_callbacks(warning_callback, critical_callback)
    
    return monitor


# Export public API
__all__ = [
    'MemoryMonitor',
    'MemorySnapshot',
    'get_memory_monitor',
    'setup_memory_monitoring'
]
