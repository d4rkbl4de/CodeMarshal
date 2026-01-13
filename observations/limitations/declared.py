"""
DECLARED LIMITATIONS - Explicit Blind Spots

Machine-readable contract of what the system cannot/will not observe.
This is declaration, not mitigation.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Optional, Sequence


class LimitationCategory(enum.Enum):
    """Why something is not observed."""
    STRUCTURAL = "cannot"  # System cannot observe this
    INTENTIONAL = "will_not"  # System intentionally ignores this
    CONDITIONAL = "not_with_current_config"  # Could observe with different config


class LimitationScope(enum.Enum):
    """What scope this limitation applies to."""
    GLOBAL = "global"  # Applies to all observations
    PER_FILE = "per_file"  # Applies to file-level observations
    PER_OBSERVATION_TYPE = "per_observation_type"  # Specific to one observation type


@dataclasses.dataclass(frozen=True, slots=True)
class Limitation:
    """Immutable declaration of a single observational limitation."""
    
    id: str  # Unique identifier (kebab-case)
    category: LimitationCategory
    scope: LimitationScope
    description: str  # What is not observed
    reason: str  # Why it's not observed
    example: Optional[str] = None  # Concrete example of what's missed
    
    # Stable sorting key
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Limitation):
            return NotImplemented
        return self.id < other.id


# Registry of all limitations
# Add new limitations here. Never remove or modify existing ones.
# Changing a limitation requires creating a new ID.

_ALL_LIMITATIONS: list[Limitation] = [
    Limitation(
        id="dynamic-imports",
        category=LimitationCategory.STRUCTURAL,
        scope=LimitationScope.GLOBAL,
        description="Dynamic imports (importlib, __import__, exec) not executed",
        reason="Static analysis cannot safely execute arbitrary code",
        example="`module = __import__(module_name)` imports are not traced",
    ),
    Limitation(
        id="generated-code",
        category=LimitationCategory.STRUCTURAL,
        scope=LimitationScope.PER_FILE,
        description="Generated code not materialized at observation time",
        reason="Generated code may not exist or may differ from runtime",
        example="Protobuf/Thrift generated classes, Jinja templates",
    ),
    Limitation(
        id="network-modules",
        category=LimitationCategory.INTENTIONAL,
        scope=LimitationScope.GLOBAL,
        description="Network-loaded modules ignored",
        reason="Network access violates local-only operation principle",
        example="`import requests` is observed, but `requests.get()` content is not",
    ),
    Limitation(
        id="runtime-behavior",
        category=LimitationCategory.STRUCTURAL,
        scope=LimitationScope.GLOBAL,
        description="Runtime-only behavior excluded",
        reason="Static analysis cannot observe execution flow",
        example="Conditional imports based on environment variables",
    ),
    Limitation(
        id="binary-files",
        category=LimitationCategory.INTENTIONAL,
        scope=LimitationScope.PER_FILE,
        description="Binary files not decoded or analyzed",
        reason="Binary analysis is outside scope of text-based observation",
        example=".pyc files, images, compiled libraries",
    ),
    Limitation(
        id="symbolic-links-depth",
        category=LimitationCategory.CONDITIONAL,
        scope=LimitationScope.GLOBAL,
        description="Symbolic links followed only to configured depth",
        reason="Infinite recursion protection and performance",
        example="symlink chains longer than max_depth are truncated",
    ),
]


def get_active_limitations() -> Sequence[Limitation]:
    """Return all currently active limitations."""
    return tuple(sorted(_ALL_LIMITATIONS, key=lambda x: x.id))


def get_limitation_by_id(limitation_id: str) -> Optional[Limitation]:
    """Get a specific limitation by its ID."""
    for limitation in _ALL_LIMITATIONS:
        if limitation.id == limitation_id:
            return limitation
    return None