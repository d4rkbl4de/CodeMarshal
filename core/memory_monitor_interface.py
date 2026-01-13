from typing import Any, Protocol


class MemoryMonitorInterface(Protocol):
    def setup_monitoring(
        self,
        *,
        context: Any,
        warning_threshold_mb: int,
        critical_threshold_mb: int,
    ) -> Any: ...
