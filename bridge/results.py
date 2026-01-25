"""
Result objects for CLI commands.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InvestigateResult:
    """Result of investigate command."""

    success: bool
    investigation_id: str
    status: str
    path: str
    scope: str
    observation_count: int = 0
    error_message: str | None = None


@dataclass(frozen=True)
class ObserveResult:
    """Result of observe command."""

    success: bool
    observation_id: str
    status: str
    estimated_time: str = "unknown"
    intent_record: dict[str, Any] | None = None
    limitations: dict[str, list[str]] | None = None
    truth_preservation_guarantee: bool = False
    warnings: list[str] | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        # Initialize mutable defaults after construction
        if self.warnings is None:
            object.__setattr__(self, "warnings", [])
        if self.intent_record is None:
            object.__setattr__(self, "intent_record", {})
        if self.limitations is None:
            object.__setattr__(self, "limitations", {})


@dataclass(frozen=True)
class QueryResult:
    """Result of query command."""

    success: bool
    investigation_id: str
    question: str
    question_type: str
    answer: str
    error_message: str | None = None
    uncertainties: list[str] | None = None
    anchors: list[str] | None = None

    def __post_init__(self) -> None:
        # Initialize mutable defaults after construction
        if self.uncertainties is None:
            object.__setattr__(self, "uncertainties", [])
        if self.anchors is None:
            object.__setattr__(self, "anchors", [])


@dataclass(frozen=True)
class ExportResult:
    """Result of export command."""

    success: bool
    export_id: str
    format: str
    path: str
    error_message: str | None = None
