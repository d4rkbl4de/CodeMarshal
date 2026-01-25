"""
lens.indicators - Visual indicators for truth-preserving interface.

Provides loading indicators, error displays, and status signals
that preserve truth while providing user feedback.
"""

from .errors import ErrorCollection, ErrorIndicator
from .loading import LoadingIndicator

# Alias for backward compatibility
ErrorDisplay = ErrorIndicator

__all__ = [
    "LoadingIndicator",
    "ErrorIndicator",
    "ErrorDisplay",  # Alias
    "ErrorCollection",
]
