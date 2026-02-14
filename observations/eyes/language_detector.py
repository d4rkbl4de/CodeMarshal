"""
Language detection for CodeMarshal observations.

Provides lightweight, deterministic heuristics to infer programming language
based on file extensions and textual markers. No external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LanguageDetection:
    """Immutable language detection result."""

    primary: str
    confidence: float
    alternatives: tuple[tuple[str, float], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "confidence": self.confidence,
            "alternatives": [
                {"language": lang, "confidence": score}
                for lang, score in self.alternatives
            ],
        }


class LanguageDetector:
    """
    Heuristic language detector based on extensions + markers.

    Confidence is relative (primary score / total score).
    """

    LANGUAGE_SIGNATURES: dict[str, dict[str, Any]] = {
        "python": {
            "extensions": [".py", ".pyw"],
            "markers": ["def ", "import ", "class ", "__init__"],
            "weight": 0.6,
        },
        "javascript": {
            "extensions": [".js", ".jsx"],
            "markers": ["function", "const ", "=>", "require(", "import ", "export "],
            "weight": 0.6,
        },
        "typescript": {
            "extensions": [".ts", ".tsx"],
            "markers": ["interface ", "type ", ": string", ": number", "implements ", "enum "],
            "weight": 0.6,
        },
        "java": {
            "extensions": [".java"],
            "markers": ["public class", "import java.", "package ", "interface "],
            "weight": 0.6,
        },
        "go": {
            "extensions": [".go"],
            "markers": ["package ", "func ", ":=", "import ("],
            "weight": 0.6,
        },
    }

    MAX_READ_BYTES = 20000

    def supported_extensions(self) -> set[str]:
        extensions: set[str] = set()
        for signature in self.LANGUAGE_SIGNATURES.values():
            for ext in signature.get("extensions", []):
                extensions.add(ext.lower())
        return extensions

    def detect_language_for_path(self, path: Path) -> LanguageDetection:
        if path.is_dir():
            return LanguageDetection(primary="unknown", confidence=0.0)

        extension = path.suffix.lower()
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            content = ""

        if len(content) > self.MAX_READ_BYTES:
            content = content[: self.MAX_READ_BYTES]

        return self.detect_language_from_text(content, extension)

    def detect_language_from_text(
        self, text: str, extension: str | None = None
    ) -> LanguageDetection:
        scores: dict[str, float] = dict.fromkeys(self.LANGUAGE_SIGNATURES, 0.0)
        extension = (extension or "").lower()

        for language, signature in self.LANGUAGE_SIGNATURES.items():
            extensions = signature.get("extensions", [])
            if extension and extension in extensions:
                scores[language] += float(signature.get("weight", 0.6))

            markers = signature.get("markers", [])
            if text:
                marker_hits = 0
                for marker in markers:
                    if marker in text:
                        marker_hits += 1
                if marker_hits:
                    # Scale marker contribution relative to total markers
                    marker_weight = 0.4
                    scores[language] += marker_weight * (marker_hits / max(len(markers), 1))

        total = sum(scores.values())
        if total <= 0:
            return LanguageDetection(primary="unknown", confidence=0.0)

        primary = max(scores.items(), key=lambda item: item[1])[0]
        primary_score = scores[primary]
        confidence = primary_score / total if total else 0.0

        alternatives = sorted(
            ((lang, score / total) for lang, score in scores.items() if lang != primary and score > 0),
            key=lambda item: item[1],
            reverse=True,
        )

        return LanguageDetection(primary=primary, confidence=confidence, alternatives=tuple(alternatives))

    def detect_languages_in_directory(
        self, root: Path, max_files: int = 200
    ) -> dict[str, Any]:
        """
        Scan a directory to estimate language distribution.
        """
        extensions = self.supported_extensions()
        counts: dict[str, int] = dict.fromkeys(self.LANGUAGE_SIGNATURES, 0)
        scanned = 0

        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in extensions:
                continue

            detection = self.detect_language_for_path(path)
            if detection.primary in counts:
                counts[detection.primary] += 1
            scanned += 1
            if scanned >= max_files:
                break

        return {
            "scanned_files": scanned,
            "language_counts": counts,
        }


__all__ = ["LanguageDetector", "LanguageDetection"]
