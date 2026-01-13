"""
lens.indicators - Visual indicators for truth-preserving interface.

Provides loading indicators, error displays, and status signals
that preserve truth while providing user feedback.
"""

from .loading import LoadingIndicator
from .errors import ErrorIndicator, ErrorCollection

# Alias for backward compatibility
ErrorDisplay = ErrorIndicator

__all__ = [
    'LoadingIndicator',
    'ErrorIndicator',
    'ErrorDisplay',  # Alias
    'ErrorCollection',
]

