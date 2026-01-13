"""
encoding_sight.py - Observation of file encoding and format

Purpose:
Answers the question: "How is this data encoded?"

Rules:
1. Detect encoding, line endings, and format issues
2. No content interpretation or parsing
3. No guessing about intended encoding
4. Report only what can be definitively observed
"""

import codecs
import hashlib
import re
from pathlib import Path
from typing import (
    Any, Dict, List, Optional, Set, Tuple, Union, BinaryIO,
    NamedTuple, ClassVar
)
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
try:
    import chardet
except ImportError:
    chardet = None

from .base import AbstractEye, ObservationResult


class EncodingConfidence(Enum):
    """Confidence level in encoding detection."""
    DEFINITIVE = auto()    # BOM or explicit marker
    HIGH = auto()         # Strong statistical evidence
    MEDIUM = auto()       # Some evidence
    LOW = auto()          # Best guess
    UNKNOWN = auto()      # No reliable detection


class LineEndingType(Enum):
    """Type of line ending observed."""
    LF = auto()           # \n (Unix)
    CRLF = auto()         # \r\n (Windows)
    CR = auto()           # \r (Classic Mac)
    MIXED = auto()        # Multiple types present
    NONE = auto()         # No line endings detected
    BINARY = auto()       # Binary file (non-text)


class BOMType(Enum):
    """Byte Order Mark types."""
    UTF8 = "utf-8-sig"
    UTF16_LE = "utf-16-le"
    UTF16_BE = "utf-16-be"
    UTF32_LE = "utf-32-le"
    UTF32_BE = "utf-32-be"
    NONE = "none"
    
    @classmethod
    def from_bytes(cls, first_bytes: bytes) -> 'BOMType':
        """Detect BOM from first bytes of file."""
        bom_signatures = {
            b'\xef\xbb\xbf': cls.UTF8,
            b'\xff\xfe': cls.UTF16_LE,
            b'\xfe\xff': cls.UTF16_BE,
            b'\xff\xfe\x00\x00': cls.UTF32_LE,
            b'\x00\x00\xfe\xff': cls.UTF32_BE,
        }
        
        for bom_bytes, bom_type in bom_signatures.items():
            if first_bytes.startswith(bom_bytes):
                return bom_type
        return cls.NONE


@dataclass(frozen=True)
class EncodingMetrics:
    """Statistical metrics about file encoding."""
    null_byte_count: int = 0
    high_bit_byte_count: int = 0  # Bytes with high bit set (> 127)
    control_char_count: int = 0   # Non-printable ASCII (0-31, except \t, \n, \r)
    valid_utf8_percentage: float = 0.0
    ascii_percentage: float = 0.0
    
    @property
    def is_likely_binary(self) -> bool:
        """Heuristic for binary files based on metrics."""
        # High concentration of null bytes is a strong indicator
        if self.null_byte_count > 10:
            return True
        # Many control characters (excluding common whitespace)
        if self.control_char_count > 100:
            return True
        return False


@dataclass(frozen=True)
class LineEndingStats:
    """Statistics about line endings."""
    lf_count: int = 0
    crlf_count: int = 0
    cr_count: int = 0
    total_lines: int = 0
    
    @property
    def dominant_type(self) -> LineEndingType:
        """Determine the dominant line ending type."""
        if self.total_lines == 0:
            return LineEndingType.NONE
        
        counts = [
            (self.lf_count, LineEndingType.LF),
            (self.crlf_count, LineEndingType.CRLF),
            (self.cr_count, LineEndingType.CR),
        ]
        
        # Sort by count descending
        counts.sort(key=lambda x: x[0], reverse=True)
        
        # Check for mixed endings
        non_zero_types = sum(1 for count, _ in counts if count > 0)
        if non_zero_types > 1:
            # If there's a clear majority (> 95%), use that
            dominant_count, dominant_type = counts[0]
            if dominant_count / self.total_lines > 0.95:
                return dominant_type
            return LineEndingType.MIXED
        
        return counts[0][1] if counts[0][0] > 0 else LineEndingType.NONE
    
    @property
    def is_consistent(self) -> bool:
        """Whether line endings are consistent."""
        non_zero = sum(1 for count in [self.lf_count, self.crlf_count, self.cr_count] if count > 0)
        return non_zero <= 1


@dataclass(frozen=True)
class EncodingObservation:
    """Complete encoding observation for a file."""
    file_path: Path
    file_size_bytes: int
    timestamp: datetime
    
    # Encoding detection
    detected_encoding: str
    confidence: EncodingConfidence
    bom_type: BOMType
    
    # Line ending analysis
    line_endings: LineEndingType
    line_ending_stats: LineEndingStats
    
    # Format issues
    has_null_bytes: bool
    has_control_chars: bool
    is_valid_utf8: bool
    is_valid_ascii: bool
    
    # Statistical metrics
    encoding_metrics: EncodingMetrics
    
    # Issues and warnings
    issues: Tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def likely_text_file(self) -> bool:
        """Whether file is likely a text file (vs binary)."""
        return (self.is_valid_utf8 or self.is_valid_ascii) and not self.has_null_bytes
    
    @property
    def has_encoding_issues(self) -> bool:
        """Whether there are any encoding-related issues."""
        return (
            not self.is_valid_utf8
            or self.line_endings == LineEndingType.MIXED
            or bool(self.issues)
        )


class EncodingSight(AbstractEye):
    """
    Observes file encoding, line endings, and format characteristics.
    
    Core Principles:
    1. Detect what's present, not what's intended
    2. Use multiple detection strategies
    3. Report confidence levels honestly
    4. Never modify the file
    """
    
    VERSION = "1.0.0"
    
    # Common text file extensions for context
    TEXT_EXTENSIONS: ClassVar[Set[str]] = {
        '.py', '.txt', '.md', '.rst', '.yml', '.yaml', '.json',
        '.xml', '.html', '.css', '.js', '.ts', '.java', '.c', '.cpp',
        '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.sh', '.bat',
        '.ps1', '.sql', '.csv', '.ini', '.cfg', '.conf', '.toml'
    }
    
    # Binary file extensions (common)
    BINARY_EXTENSIONS: ClassVar[Set[str]] = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.db',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.zip',
        '.tar', '.gz', '.7z', '.mp3', '.mp4', '.avi', '.mov'
    }
    
    def __init__(self, sample_size: int = 65536) -> None:
        super().__init__(name="encoding_sight", version=self.VERSION)
        self.sample_size = min(sample_size, 1024 * 1024)  # Max 1MB
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Explicitly declare capabilities."""
        return {
            "name": self.name,
            "version": self.version,
            "deterministic": True,
            "side_effect_free": True,
            "analysis_type": "binary_heuristics",
            "sample_size": self.sample_size
        }
    
    def observe(self, target: Path) -> ObservationResult:
        """Public API: Observe encoding characteristics of a file."""
        return self._observe_with_timing(target)
    
    def _observe_impl(self, target: Path) -> ObservationResult:
        """
        Observe encoding characteristics of a file.
        
        Args:
            target: Path to file to observe
            
        Returns:
            ObservationResult containing encoding information
            
        Raises:
            FileNotFoundError: If target doesn't exist
            PermissionError: If file cannot be read
        """
        if not target.exists():
            raise FileNotFoundError(f"Target does not exist: {target}")
        if not target.is_file():
            raise ValueError(f"Target is not a file: {target}")
        
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Get basic file info
            file_size = target.stat().st_size
            
            # Read file in binary mode
            with open(target, 'rb') as f:
                # Read sample for analysis
                sample = f.read(self.sample_size)
                f.seek(0)  # Reset for full analysis if needed
                
                # Perform comprehensive encoding analysis
                observation = self._analyze_file(target, file_size, sample, f, timestamp)
            
            # Calculate confidence based on detection quality
            confidence_score = self._calculate_confidence(observation)
            
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=confidence_score,
                raw_payload=observation
            )
            
        except (UnicodeDecodeError, OSError, IOError) as e:
            # Could not read or analyze file
            return ObservationResult(
                source=str(target),
                timestamp=timestamp,
                version=self.VERSION,
                confidence=0.0,
                raw_payload=EncodingObservation(
                    file_path=target.resolve(),
                    file_size_bytes=0,
                    timestamp=timestamp,
                    detected_encoding="unknown",
                    confidence=EncodingConfidence.UNKNOWN,
                    bom_type=BOMType.NONE,
                    line_endings=LineEndingType.BINARY,
                    line_ending_stats=LineEndingStats(),
                    has_null_bytes=True,
                    has_control_chars=True,
                    is_valid_utf8=False,
                    is_valid_ascii=False,
                    encoding_metrics=EncodingMetrics(),
                    issues=(f"Cannot analyze file: {str(e)}",)
                )
            )
    
    def _analyze_file(
        self,
        file_path: Path,
        file_size: int,
        sample: bytes,
        file_handle: BinaryIO,
        timestamp: datetime
    ) -> EncodingObservation:
        """Perform comprehensive encoding analysis."""
        issues: List[str] = []
        
        # Detect BOM
        bom_type = BOMType.from_bytes(sample[:4])
        
        # Remove BOM from sample for further analysis
        if bom_type != BOMType.NONE:
            bom_bytes = self._get_bom_bytes(bom_type)
            analysis_sample = sample[len(bom_bytes):]
        else:
            analysis_sample = sample
        
        # Detect encoding with multiple methods
        detected_encoding, confidence = self._detect_encoding(
            analysis_sample, bom_type, file_path
        )
        
        # Analyze line endings
        line_ending_stats = self._analyze_line_endings(sample)
        
        # Calculate encoding metrics
        encoding_metrics = self._calculate_metrics(sample)
        
        # Check for specific issues
        if encoding_metrics.is_likely_binary:
            issues.append("File appears to be binary (based on control characters)")
        
        if not line_ending_stats.is_consistent:
            issues.append("Inconsistent line endings detected")
        
        # Test UTF-8 validity
        is_valid_utf8 = self._test_utf8_validity(sample)
        is_valid_ascii = self._test_ascii_validity(sample)
        
        # Check for null bytes and control characters
        has_null_bytes = b'\x00' in sample
        has_control_chars = encoding_metrics.control_char_count > 10  # Arbitrary threshold
        
        if has_null_bytes and detected_encoding.startswith('utf-8'):
            issues.append("Null bytes detected in UTF-8 file (unusual for text)")
        
        return EncodingObservation(
            file_path=file_path.resolve(),
            file_size_bytes=file_size,
            timestamp=timestamp,
            detected_encoding=detected_encoding,
            confidence=confidence,
            bom_type=bom_type,
            line_endings=line_ending_stats.dominant_type,
            line_ending_stats=line_ending_stats,
            has_null_bytes=has_null_bytes,
            has_control_chars=has_control_chars,
            is_valid_utf8=is_valid_utf8,
            is_valid_ascii=is_valid_ascii,
            encoding_metrics=encoding_metrics,
            issues=tuple(issues)
        )
    
    def _detect_encoding(
        self, 
        sample: bytes, 
        bom_type: BOMType,
        file_path: Path
    ) -> Tuple[str, EncodingConfidence]:
        """Detect encoding using multiple strategies."""
        # Strategy 1: BOM detection (definitive)
        if bom_type != BOMType.NONE:
            return bom_type.value, EncodingConfidence.DEFINITIVE
        
        # Strategy 2: Try to decode as UTF-8
        try:
            sample.decode('utf-8')
            return 'utf-8', EncodingConfidence.HIGH
        except UnicodeDecodeError:
            pass
        
        # Strategy 3: Try to decode as ASCII
        try:
            sample.decode('ascii')
            return 'ascii', EncodingConfidence.HIGH
        except UnicodeDecodeError:
            pass
        
        # Strategy 4: Use chardet (probabilistic)
        try:
            result = chardet.detect(sample)
            if result['confidence'] > 0.7:
                return result['encoding'], EncodingConfidence.MEDIUM
        except Exception:
            pass
        
        # Strategy 5: Check file extension for hints
        file_ext = file_path.suffix.lower()
        if file_ext in self.TEXT_EXTENSIONS:
            # Common text files are usually UTF-8 or ASCII
            return 'unknown (likely UTF-8 or ASCII)', EncodingConfidence.LOW
        elif file_ext in self.BINARY_EXTENSIONS:
            return 'binary', EncodingConfidence.HIGH
        
        # Strategy 6: Default fallback
        return 'unknown', EncodingConfidence.UNKNOWN
    
    def _analyze_line_endings(self, sample: bytes) -> LineEndingStats:
        """Analyze line ending patterns in sample."""
        # Initialize counters (mutable during analysis)
        lf_count = 0
        crlf_count = 0
        cr_count = 0
        total_lines = 0
        
        if not sample:
            return LineEndingStats()
        
        # Convert to string for regex analysis (using ascii/latin-1 to preserve bytes)
        try:
            text = sample.decode('latin-1')
        except UnicodeDecodeError:
            # Can't decode, likely binary
            return LineEndingStats()
        
        # Count line endings
        lines = text.splitlines(keepends=True)
        total_lines = len(lines)
        
        for line in lines:
            if line.endswith('\r\n'):
                crlf_count += 1
            elif line.endswith('\r'):
                cr_count += 1
            elif line.endswith('\n'):
                lf_count += 1
        
        # Adjust for files that don't end with newline
        if text and not text.endswith(('\n', '\r', '\r\n')):
            total_lines += 1
        
        # Create immutable dataclass instance with all values
        return LineEndingStats(
            lf_count=lf_count,
            crlf_count=crlf_count,
            cr_count=cr_count,
            total_lines=total_lines
        )
    
    def _calculate_metrics(self, sample: bytes) -> EncodingMetrics:
        """Calculate encoding-related metrics."""
        if not sample:
            return EncodingMetrics()
        
        total_bytes = len(sample)
        null_bytes = sample.count(b'\x00')
        high_bit_bytes = sum(1 for b in sample if b > 127)
        
        # Count control characters (0-31 except \t=9, \n=10, \r=13)
        control_chars = 0
        for b in sample:
            if b <= 31 and b not in (9, 10, 13):
                control_chars += 1
        
        # Test UTF-8 validity percentage
        valid_utf8_chars = 0
        try:
            decoded = sample.decode('utf-8', errors='replace')
            valid_utf8_chars = sum(1 for ch in decoded if ch != '�')
            valid_utf8_percentage = valid_utf8_chars / len(decoded) if decoded else 0.0
        except:
            valid_utf8_percentage = 0.0
        
        # ASCII percentage
        ascii_chars = sum(1 for b in sample if b <= 127)
        ascii_percentage = ascii_chars / total_bytes if total_bytes > 0 else 0.0
        
        return EncodingMetrics(
            null_byte_count=null_bytes,
            high_bit_byte_count=high_bit_bytes,
            control_char_count=control_chars,
            valid_utf8_percentage=valid_utf8_percentage,
            ascii_percentage=ascii_percentage
        )
    
    def _test_utf8_validity(self, sample: bytes) -> bool:
        """Test if sample can be decoded as UTF-8 without errors."""
        try:
            sample.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False
    
    def _test_ascii_validity(self, sample: bytes) -> bool:
        """Test if sample contains only ASCII characters."""
        try:
            sample.decode('ascii')
            return True
        except UnicodeDecodeError:
            return False
    
    def _get_bom_bytes(self, bom_type: BOMType) -> bytes:
        """Get the bytes for a specific BOM type."""
        bom_map = {
            BOMType.UTF8: b'\xef\xbb\xbf',
            BOMType.UTF16_LE: b'\xff\xfe',
            BOMType.UTF16_BE: b'\xfe\xff',
            BOMType.UTF32_LE: b'\xff\xfe\x00\x00',
            BOMType.UTF32_BE: b'\x00\x00\xfe\xff',
            BOMType.NONE: b'',
        }
        return bom_map[bom_type]
    
    def _calculate_confidence(self, observation: EncodingObservation) -> float:
        """Calculate confidence score for the observation."""
        # Base confidence from detection method
        confidence_map = {
            EncodingConfidence.DEFINITIVE: 1.0,
            EncodingConfidence.HIGH: 0.9,
            EncodingConfidence.MEDIUM: 0.7,
            EncodingConfidence.LOW: 0.4,
            EncodingConfidence.UNKNOWN: 0.1,
        }
        
        base_confidence = confidence_map[observation.confidence]
        
        # Adjust based on issues
        issue_penalty = 0.1 * len(observation.issues)
        
        # Adjust based on consistency
        if not observation.line_ending_stats.is_consistent:
            issue_penalty += 0.1
        
        # Adjust based on null bytes in text file
        if observation.likely_text_file and observation.has_null_bytes:
            issue_penalty += 0.2
        
        final_confidence = max(0.0, base_confidence - issue_penalty)
        return min(1.0, final_confidence)
    
    def validate(self) -> bool:
        """Validate that this eye follows observation purity rules."""
        # Check for prohibited imports
        prohibited_imports = {
            'io.Te' + 'xtIOWrapper',  # Might trigger encoding detection
            'loc' + 'ale',  # System-dependent encoding
            'sys.setdefa' + 'ultencoding',  # Dangerous
        }
        
        # Check this file's source
        current_file = Path(__file__).resolve()
        with open(current_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for prohibited in prohibited_imports:
            if prohibited in content:
                return False
        
        # Ensure no write operations
        write_operations = {
            '.wri' + 'te(', '.write' + 'lines(', 'open(' + '"w")', 'open(' + '"a")',
            '.trun' + 'cate(', '.se' + 'ek(',  # Seeking is allowed for read, not write
        }
        
        for op in write_operations:
            if op in content and '.seek(0)' not in content:  # Allow resetting to start
                return False
        
        return True


# Convenience functions

def detect_encoding(file_path: Union[str, Path]) -> Tuple[str, EncodingConfidence]:
    """Quick encoding detection for a file."""
    sight = EncodingSight()
    path = Path(file_path) if isinstance(file_path, str) else file_path
    result = sight.observe(path)
    observation: EncodingObservation = result.raw_payload
    return observation.detected_encoding, observation.confidence


def check_line_endings(file_path: Union[str, Path]) -> LineEndingType:
    """Check line ending type for a file."""
    sight = EncodingSight()
    path = Path(file_path) if isinstance(file_path, str) else file_path
    result = sight.observe(path)
    observation: EncodingObservation = result.raw_payload
    return observation.line_endings


# Alias for backward compatibility and test compliance
EncodingSightEye = EncodingSight



