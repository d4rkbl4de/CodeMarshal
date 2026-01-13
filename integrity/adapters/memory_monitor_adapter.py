from typing import Any

from core.memory_monitor_interface import MemoryMonitorInterface


class IntegrityMemoryMonitorAdapter(MemoryMonitorInterface):
    def setup_monitoring(
        self,
        *,
        context: Any,
        warning_threshold_mb: int,
        critical_threshold_mb: int,
    ) -> Any:
        from integrity.monitoring.memory import setup_memory_monitoring

        return setup_memory_monitoring(
            context=context,
            warning_threshold_mb=warning_threshold_mb,
            critical_threshold_mb=critical_threshold_mb,
        )
