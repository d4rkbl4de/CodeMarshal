"""
Core layer interfaces for CodeMarshal architecture.

These interfaces define the contracts between layers without importing
higher layer implementations. This preserves Article 9 (Layer Independence).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ObservationInterface(ABC):
    """Abstract interface for observation layer coordination."""

    @abstractmethod
    def observe_directory(self, directory_path: Path) -> dict[str, Any]:
        """Observe a directory without interpretation."""
        pass

    @abstractmethod
    def get_limitations(self) -> dict[str, Any]:
        """Get declared limitations of observation methods."""
        pass


class InquiryInterface(ABC):
    """Abstract interface for inquiry layer coordination."""

    @abstractmethod
    def ask_question(
        self, question_type: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Ask a human question about observations."""
        pass

    @abstractmethod
    def detect_patterns(self, observations: dict[str, Any]) -> dict[str, Any]:
        """Detect numeric patterns in observations."""
        pass

    @abstractmethod
    def record_thought(self, observation_id: str, thought: str) -> dict[str, Any]:
        """Record a human thought about observations."""
        pass


class LensInterface(ABC):
    """Abstract interface for lens layer coordination."""

    @abstractmethod
    def present_observations(self, observations: dict[str, Any]) -> dict[str, Any]:
        """Present observations through truth-preserving lens."""
        pass

    @abstractmethod
    def present_patterns(self, patterns: dict[str, Any]) -> dict[str, Any]:
        """Present patterns through truth-preserving lens."""
        pass
