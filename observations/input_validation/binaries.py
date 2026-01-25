# observations/input_validation\binaries.py
"""
Binary file handling: distinguishes inspectable text from opaque artifacts.

Draws a clear line between what can be observed and what must be recorded as opaque.
Treating binaries as 'just text that failed to decode' is how tools get exploited.
"""

import codecs
import logging
import mimetypes
import sys
import warnings
from codecs import UnicodeDecodeWarning
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

# Suppress warnings about invalid binary sequences
warnings.filterwarnings("ignore", category=UnicodeDecodeWarning)


class BinaryClassification(Enum):
    """Classification of file content type."""

    # The file can be safely read as text with a known encoding
    TEXT_SAFE = auto()

    # The file contains binary content that cannot be safely read as text
    BINARY_OPAQUE = auto()

    # The file type is known but we cannot determine content safely
    UNKNOWN = auto()


@dataclass(frozen=True)
class BinaryDetectionPolicy:
    """
    Policy for detecting and handling binary files.

    These rules define what constitutes 'binary' vs 'text' and how to handle each.
    """

    # Maximum bytes to sample for binary detection
    max_sample_bytes: int = 8192  # 8KB

    # Minimum bytes to sample for reliable detection
    min_sample_bytes: int = 512

    # Encodings to try (in order) for text detection
    text_encodings: tuple[str, ...] = (
        "utf-8",
        "ascii",
        "utf-16le",
        "utf-16be",
        "utf-32le",
        "utf-32be",
        "latin-1",  # Note: latin-1 will decode ANY byte sequence
    )

    # Strictness: if True, only files that cleanly decode are text
    # If False, may use heuristics (not recommended for truth preservation)
    strict_decoding: bool = True

    # Whether to use file extension as a hint (but never rely solely on it)
    consider_file_extension: bool = True

    # Known binary file extensions (high confidence)
    known_binary_extensions: set[str] = field(
        default_factory=lambda: {
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            ".o",
            ".obj",
            ".class",
            ".pyc",
            ".pyo",
            ".pyd",
            ".jar",
            ".war",
            ".ear",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".rar",
            ".7z",
            ".iso",
            ".img",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".ico",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".wav",
            ".flac",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".db",
            ".sqlite",
            ".mdb",
            ".pdb",
            ".ttf",
            ".otf",
            ".woff",
            ".woff2",
        }
    )

    # Known text file extensions (high confidence)
    known_text_extensions: set[str] = field(
        default_factory=lambda: {
            ".py",
            ".txt",
            ".md",
            ".rst",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".xml",
            ".html",
            ".htm",
            ".css",
            ".js",
            ".ts",
            ".rs",
            ".go",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".rb",
            ".php",
            ".pl",
            ".sh",
            ".bash",
            ".zsh",
            ".csv",
            ".tsv",
            ".log",
        }
    )

    # MIME types that are definitely binary (if mimetypes detection is available)
    binary_mime_types: set[str] = field(
        default_factory=lambda: {
            "application/octet-stream",
            "application/x-binary",
            "application/x-executable",
            "application/x-sharedlib",
            "application/zip",
            "application/x-gzip",
            "application/x-bzip2",
            "application/x-xz",
            "application/x-rar",
            "application/x-7z-compressed",
            "application/pdf",
            "image/",
            "audio/",
            "video/",
            "font/",
        }
    )

    # Whether to treat zero-byte files as text (empty content)
    treat_empty_as_text: bool = True

    @classmethod
    def strict(cls) -> "BinaryDetectionPolicy":
        """Return a strict binary detection policy."""
        return cls(
            strict_decoding=True,
            consider_file_extension=True,
            text_encodings=("utf-8", "ascii"),  # Only modern encodings
        )

    @classmethod
    def permissive(cls) -> "BinaryDetectionPolicy":
        """Return a more permissive binary detection policy."""
        return cls(
            strict_decoding=False,
            consider_file_extension=True,
            text_encodings=("utf-8", "ascii", "latin-1"),  # Latin-1 accepts anything
            treat_empty_as_text=True,
        )

    def validate(self) -> None:
        """Validate policy configuration is sane."""
        if self.max_sample_bytes < self.min_sample_bytes:
            raise ValueError(
                f"max_sample_bytes ({self.max_sample_bytes}) must be >= "
                f"min_sample_bytes ({self.min_sample_bytes})"
            )
        if self.min_sample_bytes < 0:
            raise ValueError("min_sample_bytes cannot be negative")

        # Validate encoding names
        for encoding in self.text_encodings:
            try:
                codecs.lookup(encoding)
            except LookupError as e:
                raise ValueError(f"Invalid encoding '{encoding}': {e}") from e


class BinaryValidator:
    """
    Validates files to determine if they contain binary or text content.

    Uses multiple detection methods with clear confidence levels.
    Opaque must stay opaque.
    """

    def __init__(self, policy: BinaryDetectionPolicy | None = None) -> None:
        """
        Initialize the binary validator.

        Args:
            policy: Binary detection policy. Uses strict if None.
        """
        self._policy: BinaryDetectionPolicy = policy or BinaryDetectionPolicy.strict()
        self._policy.validate()

        # Initialize mimetypes module
        mimetypes.init()

        logger.debug(
            f"BinaryValidator initialized with policy: "
            f"sample_bytes={self._policy.max_sample_bytes}, "
            f"encodings={self._policy.text_encodings}, "
            f"strict={self._policy.strict_decoding}"
        )

    @property
    def policy(self) -> BinaryDetectionPolicy:
        """Get the current policy (read-only)."""
        return self._policy

    def classify_file(
        self, file_path: Path, file_size: int | None = None
    ) -> dict[str, Any]:
        """
        Classify a file as text-safe, binary-opaque, or unknown.

        This is the main classification method that applies multiple checks:
        1. File extension hint (if enabled)
        2. File size check (empty files)
        3. Binary content detection
        4. Text encoding validation

        Args:
            file_path: Path to the file to classify.
            file_size: Pre-computed file size (optional). If not provided,
                will be computed from the file.

        Returns:
            Dictionary with classification results:
                - "classification": BinaryClassification enum
                - "confidence": float (0.0 to 1.0)
                - "reason": str - Explanation of classification
                - "encoding": Optional[str] - Detected encoding if text
                - "sample_size": int - Bytes actually sampled
                - "binary_indicators": List[str] - Binary indicators found
                - "extension_hint": Optional[str] - Extension-based hint

        Raises:
            FileNotFoundError: If file doesn't exist.
            OSError: If file cannot be accessed.
        """
        # Resolve and validate path exists
        resolved_path = file_path.resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {resolved_path}")
        if not resolved_path.is_file():
            raise ValueError(f"Path is not a file: {resolved_path}")

        # Get file size if not provided
        if file_size is None:
            try:
                file_size = resolved_path.stat().st_size
            except OSError as e:
                raise OSError(f"Cannot stat file {resolved_path}: {e}") from e

        # Initialize result structure
        result: dict[str, Any] = {
            "classification": BinaryClassification.UNKNOWN,
            "confidence": 0.0,
            "reason": "",
            "encoding": None,
            "sample_size": 0,
            "binary_indicators": [],
            "extension_hint": None,
            "file_size": file_size,
            "file_path": str(resolved_path),
        }

        # Step 1: Check file extension (as hint only)
        extension_hint = self._check_extension(resolved_path)
        result["extension_hint"] = extension_hint

        # Step 2: Handle empty files
        if file_size == 0:
            return self._classify_empty_file(result)

        # Step 3: Sample file content
        try:
            sample_data = self._sample_file(resolved_path, file_size)
        except OSError as e:
            logger.warning(f"Cannot sample file {resolved_path}: {e}")
            result["reason"] = f"Cannot sample file: {e}"
            result["confidence"] = 0.1  # Very low confidence
            return result

        result["sample_size"] = len(sample_data)

        # Step 4: Detect binary indicators
        binary_indicators = self._detect_binary_indicators(sample_data)
        result["binary_indicators"] = binary_indicators

        # Step 5: If binary indicators found, classify as binary with high confidence
        if binary_indicators:
            result["classification"] = BinaryClassification.BINARY_OPAQUE
            result["confidence"] = 0.9
            result["reason"] = (
                f"Binary indicators detected: {', '.join(binary_indicators)}"
            )
            return result

        # Step 6: Try to decode as text
        encoding_result = self._try_decode_as_text(sample_data)

        if encoding_result["success"]:
            # Successfully decoded as text
            result["classification"] = BinaryClassification.TEXT_SAFE
            result["confidence"] = 0.8  # Good confidence, but could be lucky sample
            result["encoding"] = encoding_result["encoding"]
            result["reason"] = f"Decodes as {encoding_result['encoding']} text"

            # Boost confidence if extension matches
            if extension_hint == "text":
                result["confidence"] = 0.95
            elif extension_hint == "binary":
                result["confidence"] = 0.7  # Lower confidence despite decoding
                result["reason"] += (
                    f" (but has binary extension .{resolved_path.suffix})"
                )
        else:
            # Could not decode as text
            result["classification"] = BinaryClassification.BINARY_OPAQUE
            result["confidence"] = 0.85
            result["reason"] = "Cannot decode as any known text encoding"

            # Adjust confidence based on extension
            if extension_hint == "binary":
                result["confidence"] = 0.95
            elif extension_hint == "text":
                result["confidence"] = 0.6  # Lower confidence - unexpected binary
                result["reason"] += f" (but has text extension .{resolved_path.suffix})"

        return result

    def _check_extension(self, file_path: Path) -> str | None:
        """
        Check file extension for hints about content type.

        Returns:
            "text", "binary", or None if unknown
        """
        if not self._policy.consider_file_extension:
            return None

        suffix = file_path.suffix.lower()

        if suffix in self._policy.known_text_extensions:
            return "text"
        elif suffix in self._policy.known_binary_extensions:
            return "binary"

        # Try MIME type as fallback
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if any(
                mime_type.startswith(binary_prefix)
                for binary_prefix in self._policy.binary_mime_types
            ):
                return "binary"
            elif mime_type.startswith("text/"):
                return "text"

        return None

    def _classify_empty_file(self, result: dict[str, Any]) -> dict[str, Any]:
        """Classify a zero-byte file."""
        if self._policy.treat_empty_as_text:
            result["classification"] = BinaryClassification.TEXT_SAFE
            result["confidence"] = 1.0
            result["reason"] = "Empty file (0 bytes)"
            result["encoding"] = "utf-8"  # Empty files decode as any encoding
        else:
            result["classification"] = BinaryClassification.UNKNOWN
            result["confidence"] = 0.5
            result["reason"] = "Empty file - cannot determine content type"

        return result

    def _sample_file(self, file_path: Path, file_size: int) -> bytes:
        """
        Sample the beginning of a file.

        Reads up to max_sample_bytes, or the entire file if smaller.
        """
        sample_size = min(self._policy.max_sample_bytes, file_size)

        # Ensure we read at least min_sample_bytes if file is large enough
        if file_size >= self._policy.min_sample_bytes:
            sample_size = max(sample_size, self._policy.min_sample_bytes)

        try:
            with open(file_path, "rb") as f:
                return f.read(sample_size)
        except OSError as e:
            logger.error(f"Failed to read sample from {file_path}: {e}")
            raise

    def _detect_binary_indicators(self, data: bytes) -> list[str]:
        """
        Detect binary content indicators in sampled data.

        Returns a list of indicator names found.
        """
        indicators: list[str] = []

        if not data:
            return indicators

        # Check for null bytes (common in binary formats)
        if b"\x00" in data:
            indicators.append("null_byte")

        # Check for control characters (excluding common whitespace)
        for byte in data:
            if 0 <= byte <= 8:  # C0 control codes (excluding tab, newline, etc.)
                indicators.append("control_character")
                break
            if 14 <= byte <= 31 and byte not in (27,):  # More control codes
                indicators.append("control_character")
                break

        # Check for high ASCII (bytes with high bit set)
        # This is NOT a reliable binary indicator for modern text with UTF-8,
        # but combined with other checks can be informative.
        high_ascii_count = sum(1 for byte in data if byte > 127)
        if high_ascii_count > len(data) * 0.5:  # More than 50% high bytes
            indicators.append("high_byte_density")

        # Check for common binary signatures (magic numbers)
        if len(data) >= 4:
            # PNG
            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                indicators.append("png_signature")
            # JPEG
            if data.startswith(b"\xff\xd8\xff"):
                indicators.append("jpeg_signature")
            # GIF
            if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
                indicators.append("gif_signature")
            # PDF
            if data.startswith(b"%PDF-"):
                indicators.append("pdf_signature")
            # ZIP (also Java JAR, Office docs)
            if data.startswith(b"PK\x03\x04"):
                indicators.append("zip_signature")
            # Windows PE executable
            if data.startswith(b"MZ"):
                indicators.append("pe_executable_signature")
            # ELF executable
            if data.startswith(b"\x7fELF"):
                indicators.append("elf_executable_signature")
            # Mach-O executable
            if data.startswith(b"\xfe\xed\xfa\xce") or data.startswith(
                b"\xfe\xed\xfa\xcf"
            ):
                indicators.append("macho_signature")

        return indicators

    def _try_decode_as_text(self, data: bytes) -> dict[str, Any]:
        """
        Try to decode data with configured text encodings.

        Returns:
            Dictionary with:
                - "success": bool
                - "encoding": str if successful
                - "error": str if failed
        """
        if not data:
            return {
                "success": True,
                "encoding": "utf-8",  # Empty data decodes as anything
                "error": None,
            }

        for encoding in self._policy.text_encodings:
            try:
                # Try to decode with this encoding
                decoded = data.decode(
                    encoding,
                    errors="strict" if self._policy.strict_decoding else "replace",
                )

                # Additional check: if we used 'replace', count replacement characters
                if not self._policy.strict_decoding and "\ufffd" in decoded:
                    # Contains replacement characters, may not be clean text
                    replacement_count = decoded.count("\ufffd")
                    if replacement_count > len(decoded) * 0.1:  # More than 10% replaced
                        continue  # Try next encoding

                # Successfully decoded
                return {"success": True, "encoding": encoding, "error": None}

            except UnicodeDecodeError as e:
                logger.debug(f"Failed to decode as {encoding}: {e}")
                continue
            except LookupError as e:
                logger.warning(f"Invalid encoding {encoding}: {e}")
                continue

        # All encodings failed
        return {
            "success": False,
            "encoding": None,
            "error": "Failed to decode with any configured encoding",
        }

    def is_likely_text(self, classification_result: dict[str, Any]) -> bool:
        """
        Determine if classification result indicates text content.

        Uses confidence threshold to make determination.

        Args:
            classification_result: Result from classify_file()

        Returns:
            True if likely text, False otherwise.
        """
        classification = classification_result.get("classification")
        confidence = classification_result.get("confidence", 0.0)

        if classification == BinaryClassification.TEXT_SAFE:
            return confidence >= 0.7  # 70% confidence threshold
        return False

    def is_definitely_binary(self, classification_result: dict[str, Any]) -> bool:
        """
        Determine if classification result indicates binary content.

        Uses confidence threshold to make determination.

        Args:
            classification_result: Result from classify_file()

        Returns:
            True if definitely binary, False if uncertain or text.
        """
        classification = classification_result.get("classification")
        confidence = classification_result.get("confidence", 0.0)

        if classification == BinaryClassification.BINARY_OPAQUE:
            return confidence >= 0.8  # 80% confidence threshold

        # Unknown classification with high confidence of binary indicators
        if (
            classification == BinaryClassification.UNKNOWN
            and confidence >= 0.9
            and classification_result.get("binary_indicators")
        ):
            return True

        return False


# Public API functions for standalone use


def classify_file_against_policy(
    file_path: Path, policy: BinaryDetectionPolicy | None = None
) -> dict[str, Any]:
    """
    Classify a file using the specified policy.

    Convenience function for standalone use.

    Args:
        file_path: Path to the file to classify.
        policy: Binary detection policy. Uses strict if None.

    Returns:
        Classification results dictionary.
    """
    validator = BinaryValidator(policy)
    return validator.classify_file(file_path)


def is_text_file(file_path: Path) -> bool:
    """
    Quick check if a file is likely text (using strict policy).

    This is a convenience function for simple checks.
    For detailed analysis, use classify_file_against_policy.

    Args:
        file_path: Path to the file to check.

    Returns:
        True if file is likely text, False otherwise.
    """
    validator = BinaryValidator(BinaryDetectionPolicy.strict())
    result = validator.classify_file(file_path)
    return validator.is_likely_text(result)


# Test function for module verification
def _test_module() -> None:
    """Run basic tests on the module."""
    import tempfile

    print("Testing binaries.py module...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Test 1: Plain text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello, world!\nThis is plain text.")

        validator = BinaryValidator()
        result = validator.classify_file(text_file)

        assert result["classification"] == BinaryClassification.TEXT_SAFE
        assert validator.is_likely_text(result)
        print("✓ Plain text file detection passed")

        # Test 2: Python file (text with extension hint)
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    print('Hello')")

        result = validator.classify_file(py_file)
        assert result["classification"] == BinaryClassification.TEXT_SAFE
        assert result["extension_hint"] == "text"
        print("✓ Python file detection passed")

        # Test 3: Empty file
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")

        result = validator.classify_file(empty_file)
        assert result["classification"] == BinaryClassification.TEXT_SAFE
        assert result["reason"] == "Empty file (0 bytes)"
        print("✓ Empty file detection passed")

        # Test 4: Create a "binary" file (with null bytes)
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04Binary data\xff\xfe\xfd")

        result = validator.classify_file(binary_file)
        assert result["classification"] == BinaryClassification.BINARY_OPAQUE
        assert "null_byte" in result["binary_indicators"]
        assert validator.is_definitely_binary(result)
        print("✓ Binary file detection passed")

        # Test 5: UTF-8 with BOM
        utf8_file = tmp_path / "test_utf8.txt"
        utf8_file.write_bytes(b"\xef\xbb\xbfUTF-8 with BOM")

        result = validator.classify_file(utf8_file)
        assert result["classification"] == BinaryClassification.TEXT_SAFE
        assert result["encoding"] == "utf-8"
        print("✓ UTF-8 BOM detection passed")

        # Test 6: Quick check function
        assert is_text_file(text_file) is True
        assert is_text_file(binary_file) is False
        print("✓ Quick check functions work")

    print("All tests passed!")


if __name__ == "__main__":
    # When run directly, execute tests
    try:
        _test_module()
        sys.exit(0)
    except Exception as e:
        print(f"Test failed: {e}", file=sys.stderr)
        sys.exit(1)
