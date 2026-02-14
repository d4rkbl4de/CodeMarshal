"""
core/memory_monitor_interface.py - Memory monitoring interface for system resource tracking.

This module provides the abstract interface for monitoring system memory usage.
Implementations track memory usage and provide warnings when resources are constrained.

Constitutional Context:
- Article 5: Resource Transparency (system resources must be monitored)
- Article 18: Explicit Limitations (must declare monitoring capabilities)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MemoryStats:
    """
    Memory usage statistics container.

    Attributes:
        total_mb: Total system memory in MB
        used_mb: Currently used memory in MB
        free_mb: Available memory in MB
        percent_used: Percentage of memory used (0-100)
    """

    total_mb: int
    used_mb: int
    free_mb: int
    percent_used: float


class MemoryMonitorInterface(ABC):
    """
    Abstract interface for memory monitoring.

    Implementations track memory usage and provide warnings
    when resources are constrained. This interface allows
    different monitoring backends (psutil, platform-specific, etc.)

    Constitutional Compliance:
    - All methods must handle errors gracefully
    - No hidden state or side effects
    - Explicit about limitations

    Example:
        >>> from core.memory_monitor_interface import MemoryMonitorInterface
        >>> # Use concrete implementation
        >>> monitor = PsutilMemoryMonitor()  # or other implementation
        >>> stats = monitor.get_stats()
        >>> if monitor.check_threshold(80.0):
        ...     print("Warning: High memory usage")
    """

    @abstractmethod
    def get_stats(self) -> MemoryStats:
        """
        Get current memory statistics.

        Returns:
            MemoryStats with current memory usage information

        Raises:
            MemoryMonitorError: If unable to retrieve memory stats
        """
        pass

    @abstractmethod
    def check_threshold(self, threshold_percent: float = 80.0) -> bool:
        """
        Check if memory usage exceeds threshold.

        Args:
            threshold_percent: Percentage threshold (0-100)

        Returns:
            True if usage is above threshold, False otherwise

        Raises:
            ValueError: If threshold_percent is invalid (<0 or >100)
        """
        pass

    @abstractmethod
    def get_available_memory(self) -> int:
        """
        Get available memory in MB.

        Returns:
            Amount of free memory in megabytes

        Raises:
            MemoryMonitorError: If unable to retrieve memory info
        """
        pass

    def is_memory_constrained(self, min_free_mb: int = 512) -> bool:
        """
        Check if system is memory constrained.

        Default implementation that subclasses can override.

        Args:
            min_free_mb: Minimum free memory threshold in MB

        Returns:
            True if free memory is below threshold
        """
        try:
            stats = self.get_stats()
            return stats.free_mb < min_free_mb
        except Exception:
            # If we can't determine, assume constrained for safety
            return True


class MemoryMonitorError(Exception):
    """Exception raised when memory monitoring fails."""

    pass


class MemoryMonitorNotAvailableError(MemoryMonitorError):
    """Exception raised when memory monitoring is not available on this system."""

    pass
