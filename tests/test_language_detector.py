"""
Tests for LanguageDetector heuristics.
"""

from observations.eyes.language_detector import LanguageDetector


def test_detect_language_by_extension_and_markers() -> None:
    detector = LanguageDetector()

    python_text = "def foo():\n    return 1\n"
    js_text = "function foo() { return 1; }\n"
    ts_text = "interface Foo { name: string }\n"
    java_text = "public class Foo { }\n"
    go_text = "package main\nfunc Foo() {}\n"

    assert detector.detect_language_from_text(python_text, ".py").primary == "python"
    assert (
        detector.detect_language_from_text(js_text, ".js").primary == "javascript"
    )
    assert (
        detector.detect_language_from_text(ts_text, ".ts").primary == "typescript"
    )
    assert detector.detect_language_from_text(java_text, ".java").primary == "java"
    assert detector.detect_language_from_text(go_text, ".go").primary == "go"


def test_unknown_extension_returns_unknown() -> None:
    detector = LanguageDetector()
    detection = detector.detect_language_from_text("some text", ".txt")
    assert detection.primary == "unknown"
