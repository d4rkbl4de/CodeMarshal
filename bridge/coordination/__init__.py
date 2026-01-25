"""
bridge.coordination
===================

Coordination layer for CodeMarshal investigation orchestration.

Core Responsibility:
    Orchestrate and cache the flow of investigations without ever introducing
    interpretation, inference, or race conditions.

Architectural Position:
    Bridge layer - coordinates between system components while maintaining
    truth preservation and deterministic execution.

Import Rules:
    Allowed:
        - core.runtime, core.engine, core.state (to know what's active)
        - storage.atomic, storage.layout (for safe caching)
        - observations.record.* (read-only snapshots)
        - bridge.commands.* (to understand permitted actions)
        - inquiry.session.* (for session context)
        - lens.indicators.* (for signaling status)
        - Standard Python libraries

    Forbidden:
        - lens.views.*, lens.navigation.* (never use UI to drive logic)
        - core.shutdown (cannot terminate silently)
        - Network libraries (local operation only)
        - Anything that mutates truth

Constitutional Compliance:
    - Article 13: Deterministic operation
    - Article 14: Graceful degradation
    - Article 15: Session integrity
    - Article 12: Local operation
"""

from .caching import CacheManager, get_system_cache, reset_system_cache
from .scheduling import Scheduler, get_system_scheduler, reset_system_scheduler

__all__ = [
    # Caching module exports
    "CacheManager",
    "get_system_cache",
    "reset_system_cache",
    # Scheduling module exports
    "Scheduler",
    "get_system_scheduler",
    "reset_system_scheduler",
]

# No initialization logic here - just API declaration
# System components should use get_system_cache() and get_system_scheduler()
# to obtain shared instances rather than instantiating directly.
