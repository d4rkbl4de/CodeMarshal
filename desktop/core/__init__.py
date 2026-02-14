"""Desktop core integration layer."""

from .exceptions import OperationCancelledError
from .runtime_facade import RuntimeFacade
from .session_manager import SessionManager

__all__ = [
    "RuntimeFacade",
    "SessionManager",
    "OperationCancelledError",
]

try:  # Optional while PySide6 is not installed.
    from .command_bridge import GUICommandBridge
    from .worker import BridgeWorker, WorkerSignals
except Exception:  # pragma: no cover - depends on optional GUI dependency
    GUICommandBridge = None
    BridgeWorker = None
    WorkerSignals = None
else:
    __all__.extend(["GUICommandBridge", "BridgeWorker", "WorkerSignals"])

