import psutil # psutil still needed here for system_memory.total/available/used
from typing import Any

from core.memory_monitor_interface import (
    MemoryMonitorInterface,
    MemoryMonitorError,
    MemoryMonitorNotAvailableError,
    MemoryStats,
)
from integrity.monitoring.memory import MemoryMonitor, PSUTIL_AVAILABLE


class IntegrityMemoryMonitorAdapter(MemoryMonitorInterface):
    """
    Adapter to make the concrete MemoryMonitor conform to the MemoryMonitorInterface.
    """

    def __init__(self, monitor: MemoryMonitor):
        self._monitor = monitor

    def get_stats(self) -> MemoryStats:
        if not PSUTIL_AVAILABLE:
            raise MemoryMonitorNotAvailableError(
                "psutil not available for detailed memory statistics"
            )
        try:
            # Trigger the internal MemoryMonitor's check to update its state and callbacks
            self._monitor.check_current_memory()

            # Get system-wide memory statistics, as required by MemoryMonitorInterface.MemoryStats
            system_memory = psutil.virtual_memory()
            total_mb = round(system_memory.total / (1024 * 1024), 2)
            free_mb = round(system_memory.available / (1024 * 1024), 2) # 'available' is a better metric than 'free'
            used_mb = round(system_memory.used / (1024 * 1024), 2)
            percent_used = system_memory.percent

            return MemoryStats(
                total_mb=total_mb,
                used_mb=used_mb,
                free_mb=free_mb,
                percent_used=percent_used,
            )
        except Exception as e:
            raise MemoryMonitorError(f"Failed to retrieve memory stats: {e}") from e



    def check_threshold(self, threshold_percent: float = 80.0) -> bool:
        if not (0 <= threshold_percent <= 100):
            raise ValueError("Threshold percentage must be between 0 and 100")
        stats = self.get_stats()
        return stats.percent_used > threshold_percent

    def get_available_memory(self) -> int:
        stats = self.get_stats()
        return int(stats.free_mb)


def create_memory_monitor_adapter(
    context: Any,
    warning_threshold_mb: int = 2048,
    critical_threshold_mb: int = 4096,
) -> IntegrityMemoryMonitorAdapter:
    """
    Factory function to create an IntegrityMemoryMonitorAdapter instance.
    Sets up the internal MemoryMonitor with callbacks.
    """
    monitor = MemoryMonitor(
        context=context,
        warning_threshold_mb=warning_threshold_mb,
        critical_threshold_mb=critical_threshold_mb,
    )

    # Set up callbacks for the internal monitor
    # These callbacks can be more elaborate if needed, e.g., logging to context
    def warning_callback(snapshot):
        pass

    def critical_callback(snapshot):
        pass

    monitor.set_callbacks(warning_callback, critical_callback)

    return IntegrityMemoryMonitorAdapter(monitor)

