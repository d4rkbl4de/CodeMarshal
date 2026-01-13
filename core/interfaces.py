"""
Core layer interfaces for CodeMarshal architecture.

These interfaces define the contracts between layers without importing
higher layer implementations. This preserves Article 9 (Layer Independence).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pathlib import Path


class ObservationInterface(ABC):
    """Abstract interface for observation layer coordination."""
    
    @abstractmethod
    def observe_directory(self, directory_path: Path) -> Dict[str, Any]:
        """Observe a directory without interpretation."""
        pass
    
    @abstractmethod
    def get_limitations(self) -> Dict[str, Any]:
        """Get declared limitations of observation methods."""
        pass


class InquiryInterface(ABC):
    """Abstract interface for inquiry layer coordination."""
    
    @abstractmethod
    def ask_question(self, question_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ask a human question about observations."""
        pass
    
    @abstractmethod
    def detect_patterns(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Detect numeric patterns in observations."""
        pass
    
    @abstractmethod
    def record_thought(self, observation_id: str, thought: str) -> Dict[str, Any]:
        """Record a human thought about observations."""
        pass


class LensInterface(ABC):
    """Abstract interface for lens layer coordination."""
    
    @abstractmethod
    def present_observations(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Present observations through truth-preserving lens."""
        pass
    
    @abstractmethod
    def present_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Present patterns through truth-preserving lens."""
        pass
