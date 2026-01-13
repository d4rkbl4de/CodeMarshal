"""
ANOMALIES: "What seems unusual?" - Statistical Deviations Without Judgment

This module answers the fourth legitimate human question about a codebase:
What patterns differ from local norms, without claiming they are wrong or bugs.

CONSTITUTIONAL RULES:
1. This is NOT a bug detector
2. Only highlight deviations from local norms, statistically defined
3. Always attach comparison baseline and uncertainty flag
4. Say "This differs from most others" - NEVER "This is wrong"
5. An anomaly is a raised eyebrow, not an accusation

Tier 1 Violation: If this module makes any claim about correctness,
bug existence, or code quality, the system halts immediately.
"""

import collections
import math
import statistics
from datetime import datetime, timezone
from typing import (
    Optional, Dict, Any, List, Set, Tuple, Union, Iterator,
    DefaultDict, Counter, NamedTuple, FrozenSet, Callable
)
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import json

# Allowed Layer 2 patterns
from inquiry.patterns.density import DensityPatterns
from inquiry.patterns.complexity import ComplexityPatterns

# Allowed Layer 1
from observations.record.snapshot import Snapshot

# Python stdlib
import statistics
import math


class AnomalyType(Enum):
    """Types of statistical anomalies without judgment.
    
    Each type describes a statistical pattern, not a problem.
    """
    SIZE_OUTLIER = auto()           # File/module unusually large or small
    COMPLEXITY_OUTLIER = auto()     # Unusual structural complexity
    DENSITY_OUTLIER = auto()        # Unusual import/export density
    ISOLATION_OUTLIER = auto()      # Unusually isolated or connected
    DISTRIBUTION_SKEW = auto()      # Skewed distribution within module
    TEMPORAL_DISCONTINUITY = auto() # Sudden change from nearby files
    PATTERN_DEVIATION = auto()      # Deviates from similar modules
    STATISTICAL_EXTREME = auto()    # Statistical extreme value
    UNCERTAIN = auto()              # Potential anomaly, low confidence


@dataclass(frozen=True)
class ComparisonBaseline:
    """Statistical baseline for anomaly detection.
    
    Contains only mathematical descriptions of the norm.
    No qualitative labels like "normal" or "acceptable".
    """
    population_size: int
    mean: float
    median: float
    standard_deviation: float
    interquartile_range: Tuple[float, float]
    
    # Statistical validity indicators
    has_sufficient_data: bool = True
    distribution_type: Optional[str] = None  # e.g., "normal", "skewed", "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            'population_size': self.population_size,
            'mean': self.mean,
            'median': self.median,
            'standard_deviation': self.standard_deviation,
            'interquartile_range': list(self.interquartile_range),
            'has_sufficient_data': self.has_sufficient_data,
            'distribution_type': self.distribution_type,
            '_type': 'comparison_baseline'
        }


@dataclass(frozen=True)
class StatisticalAnomaly:
    """Observation of a statistical deviation without judgment.
    
    Contains only mathematical description of the deviation.
    No inference about whether it's good, bad, or problematic.
    """
    anomaly_id: str
    anomaly_type: AnomalyType
    source_path: str
    metric_name: str
    metric_value: float
    
    # Statistical context
    baseline: ComparisonBaseline
    deviation_score: float  # z-score or similar
    percentile: float  # 0-100, where this value falls in distribution
    
    # Uncertainty and confidence
    confidence: float  # 0.0-1.0, statistical confidence
    false_positive_risk: float  # Risk this is not anomalous
    
    # Context for understanding
    comparison_group: List[str]  # What was compared against
    statistical_test: str  # e.g., "z-score", "iqr", "percentile"
    
    # Constitutional: No judgment fields
    _is_problem: bool = False  # Always False
    _requires_action: bool = False  # Always False
    _severity: str = "statistical"  # Always "statistical"
    
    def __post_init__(self) -> None:
        """Validate anomaly doesn't contain judgment."""
        # Constitutional: Confidence must reflect uncertainty
        if self.confidence > 0.8:
            raise ConstitutionalViolation(
                f"Confidence {self.confidence} too high. "
                "Anomaly detection must reflect uncertainty (max 0.8)."
            )
        
        # Constitutional: No judgment in description
        if hasattr(self, 'description') and isinstance(self.description, str):
            judgment_words = ['wrong', 'bad', 'poor', 'should', 'must', 'fix', 'bug']
            if any(word in self.description.lower() for word in judgment_words):
                raise ConstitutionalViolation(
                    "Anomaly description contains judgmental language."
                )
    
    def describe_deviation(self) -> str:
        """Describe the statistical deviation without judgment.
        
        Constitutional: Must use statistical language only.
        """
        if self.anomaly_type == AnomalyType.SIZE_OUTLIER:
            direction = "larger" if self.metric_value > self.baseline.mean else "smaller"
            return (
                f"This file is statistically {direction} than most others. "
                f"It falls in the {self.percentile:.1f}th percentile. "
                f"(Baseline mean: {self.baseline.mean:.1f}, this: {self.metric_value:.1f})"
            )
        
        elif self.anomaly_type == AnomalyType.COMPLEXITY_OUTLIER:
            return (
                f"This module shows unusual structural complexity. "
                f"Deviation score: {self.deviation_score:.2f} standard deviations. "
                f"Compared to {len(self.comparison_group)} similar modules."
            )
        
        elif self.anomaly_type == AnomalyType.DENSITY_OUTLIER:
            return (
                f"Import/export density differs from the norm. "
                f"Percentile: {self.percentile:.1f}. "
                f"Confidence in anomaly: {self.confidence:.2f}."
            )
        
        elif self.anomaly_type == AnomalyType.ISOLATION_OUTLIER:
            if self.metric_value > self.baseline.mean:
                return (
                    f"This module is unusually connected compared to others. "
                    f"{self.deviation_score:.2f} standard deviations above mean."
                )
            else:
                return (
                    f"This module is unusually isolated compared to others. "
                    f"{abs(self.deviation_score):.2f} standard deviations below mean."
                )
        
        elif self.anomaly_type == AnomalyType.DISTRIBUTION_SKEW:
            return (
                f"Internal distribution is skewed compared to similar modules. "
                f"Statistical test: {self.statistical_test}. "
                f"False positive risk: {self.false_positive_risk:.2f}."
            )
        
        else:
            return (
                f"Statistical deviation detected. "
                f"Type: {self.anomaly_type.name}. "
                f"Deviation score: {self.deviation_score:.2f}. "
                f"Uncertainty: {1 - self.confidence:.2f}."
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary without judgment."""
        return {
            'anomaly_id': self.anomaly_id,
            'anomaly_type': self.anomaly_type.name,
            'source_path': self.source_path,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'baseline': self.baseline.to_dict(),
            'deviation_score': self.deviation_score,
            'percentile': self.percentile,
            'confidence': self.confidence,
            'false_positive_risk': self.false_positive_risk,
            'comparison_group': self.comparison_group,
            'statistical_test': self.statistical_test,
            'description': self.describe_deviation(),
            '_type': 'statistical_anomaly',
            '_disclaimer': 'This is a statistical observation, not a judgment of quality.'
        }


@dataclass
class AnomalyAnalysis:
    """Collection of statistical anomalies with context.
    
    Constitutional: This is a statistical report, not a bug report.
    """
    anomalies: List[StatisticalAnomaly]
    total_analyzed: int
    anomaly_rate: float  # Percentage of items with anomalies
    
    # Statistical context
    baseline_distributions: Dict[str, ComparisonBaseline]
    
    # Limitations
    insufficient_data_for: List[str] = field(default_factory=list)
    uncertain_detections: int = 0
    
    def summary(self) -> str:
        """Generate statistical summary without judgment."""
        if not self.anomalies:
            return "No statistical anomalies detected above confidence threshold."
        
        # Group by type
        type_counts: DefaultDict[str, int] = collections.defaultdict(int)
        for anomaly in self.anomalies:
            type_counts[anomaly.anomaly_type.name] += 1
        
        parts = []
        parts.append("Statistical anomalies detected (deviations from local norms):")
        parts.append("")
        
        # Type breakdown
        for anomaly_type, count in sorted(type_counts.items()):
            percentage = (count / len(self.anomalies)) * 100
            parts.append(f"• {anomaly_type}: {count} ({percentage:.1f}% of anomalies)")
        
        parts.append("")
        parts.append(f"Total analyzed: {self.total_analyzed}")
        parts.append(f"Anomaly rate: {self.anomaly_rate:.2%}")
        parts.append(f"Uncertain detections: {self.uncertain_detections}")
        
        if self.insufficient_data_for:
            parts.append("")
            parts.append(f"⚠️ Insufficient data for: {', '.join(self.insufficient_data_for[:3])}")
        
        parts.append("")
        parts.append("⚠️ Note: Anomalies are statistical deviations, not bug reports.")
        parts.append("   Further human investigation is required for interpretation.")
        
        return "\n".join(parts)
    
    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[StatisticalAnomaly]:
        """Get anomalies of specific type."""
        return [a for a in self.anomalies if a.anomaly_type == anomaly_type]
    
    def get_most_deviant(self, count: int = 5) -> List[StatisticalAnomaly]:
        """Get anomalies with highest deviation scores."""
        sorted_anomalies = sorted(
            self.anomalies,
            key=lambda a: abs(a.deviation_score),
            reverse=True
        )
        return sorted_anomalies[:count]
    
    def get_by_source_path(self, source_path: str) -> List[StatisticalAnomaly]:
        """Get all anomalies for a specific source path."""
        return [a for a in self.anomalies if a.source_path == source_path]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            'anomalies': [a.to_dict() for a in self.anomalies],
            'total_analyzed': self.total_analyzed,
            'anomaly_rate': self.anomaly_rate,
            'baseline_distributions': {
                name: baseline.to_dict()
                for name, baseline in self.baseline_distributions.items()
            },
            'insufficient_data_for': self.insufficient_data_for,
            'uncertain_detections': self.uncertain_detections,
            'summary': self.summary(),
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            '_type': 'anomaly_analysis',
            '_disclaimer': 'Statistical analysis only. Human interpretation required.'
        }


class AnomalyDetector:
    """Detects statistical anomalies without making quality judgments.
    
    Uses statistical methods to identify deviations from local norms.
    Always includes uncertainty measures and comparison baselines.
    """
    
    # Statistical thresholds (configurable, not judgments)
    Z_SCORE_THRESHOLD: float = 2.5  # 2.5 standard deviations
    IQR_THRESHOLD: float = 1.5      # 1.5 * IQR for outliers
    MIN_POPULATION: int = 5         # Minimum samples for statistical validity
    CONFIDENCE_THRESHOLD: float = 0.6  # Minimum confidence to report
    
    def __init__(self, snapshot: Snapshot):
        """Initialize with snapshot and pattern analyzers."""
        self.snapshot = snapshot
        
        # Initialize pattern analyzers
        self.density_patterns = DensityPatterns(snapshot)
        self.complexity_patterns = ComplexityPatterns(snapshot)
        
        # Cache for computed metrics
        self._metrics_cache: Dict[str, List[Tuple[str, float]]] = {}
        
        # Track limitations
        self.insufficient_data: List[str] = []
        self.uncertain_detections: int = 0
    
    def analyze_all(self) -> AnomalyAnalysis:
        """Run all anomaly detection methods."""
        all_anomalies: List[StatisticalAnomaly] = []
        baselines: Dict[str, ComparisonBaseline] = {}
        
        # 1. File size anomalies
        size_anomalies, size_baseline = self._detect_size_anomalies()
        all_anomalies.extend(size_anomalies)
        if size_baseline:
            baselines['file_size'] = size_baseline
        
        # 2. Complexity anomalies
        complexity_anomalies, complexity_baseline = self._detect_complexity_anomalies()
        all_anomalies.extend(complexity_anomalies)
        if complexity_baseline:
            baselines['complexity'] = complexity_baseline
        
        # 3. Density anomalies
        density_anomalies, density_baseline = self._detect_density_anomalies()
        all_anomalies.extend(density_anomalies)
        if density_baseline:
            baselines['density'] = density_baseline
        
        # 4. Isolation anomalies
        isolation_anomalies, isolation_baseline = self._detect_isolation_anomalies()
        all_anomalies.extend(isolation_anomalies)
        if isolation_baseline:
            baselines['isolation'] = isolation_baseline
        
        # Filter by confidence threshold
        confident_anomalies = [
            a for a in all_anomalies 
            if a.confidence >= self.CONFIDENCE_THRESHOLD
        ]
        
        # Count uncertain ones
        self.uncertain_detections = len(all_anomalies) - len(confident_anomalies)
        
        # Calculate anomaly rate
        total_analyzed = self._count_analyzed_items()
        anomaly_rate = len(confident_anomalies) / total_analyzed if total_analyzed > 0 else 0
        
        return AnomalyAnalysis(
            anomalies=confident_anomalies,
            total_analyzed=total_analyzed,
            anomaly_rate=anomaly_rate,
            baseline_distributions=baselines,
            insufficient_data_for=self.insufficient_data,
            uncertain_detections=self.uncertain_detections
        )
    
    def _detect_size_anomalies(self) -> Tuple[List[StatisticalAnomaly], Optional[ComparisonBaseline]]:
        """Detect files with unusual sizes."""
        # Get file sizes from snapshot
        file_sizes = self._get_file_sizes()
        
        if len(file_sizes) < self.MIN_POPULATION:
            self.insufficient_data.append("file_size_analysis")
            return [], None
        
        # Calculate statistics
        values = [size for _, size in file_sizes]
        baseline = self._calculate_baseline(values)
        
        # Find outliers using IQR method (robust to non-normal distributions)
        q1, q3 = baseline.interquartile_range
        iqr = q3 - q1
        lower_bound = q1 - self.IQR_THRESHOLD * iqr
        upper_bound = q3 + self.IQR_THRESHOLD * iqr
        
        anomalies = []
        for path, size in file_sizes:
            if size < lower_bound or size > upper_bound:
                # Calculate deviation metrics
                z_score = (size - baseline.mean) / baseline.standard_deviation if baseline.standard_deviation > 0 else 0
                percentile = self._calculate_percentile(values, size)
                
                # Determine direction
                anomaly_type = AnomalyType.SIZE_OUTLIER
                
                # Calculate confidence based on deviation magnitude
                confidence = min(0.8, abs(z_score) / 4.0)  # Cap at 0.8
                
                anomaly = StatisticalAnomaly(
                    anomaly_id=f"size_{hash(path)}",
                    anomaly_type=anomaly_type,
                    source_path=path,
                    metric_name="file_size_bytes",
                    metric_value=size,
                    baseline=baseline,
                    deviation_score=z_score,
                    percentile=percentile,
                    confidence=confidence,
                    false_positive_risk=1.0 - confidence,
                    comparison_group=[p for p, _ in file_sizes if p != path],
                    statistical_test="iqr_outlier"
                )
                anomalies.append(anomaly)
        
        return anomalies, baseline
    
    def _detect_complexity_anomalies(self) -> Tuple[List[StatisticalAnomaly], Optional[ComparisonBaseline]]:
        """Detect modules with unusual complexity."""
        # Get complexity metrics
        complexity_metrics = self._get_complexity_metrics()
        
        if len(complexity_metrics) < self.MIN_POPULATION:
            self.insufficient_data.append("complexity_analysis")
            return [], None
        
        # Calculate statistics
        values = [metric for _, metric in complexity_metrics]
        baseline = self._calculate_baseline(values)
        
        # Use z-score method for complexity (assuming roughly normal-ish)
        anomalies = []
        for path, complexity in complexity_metrics:
            if baseline.standard_deviation > 0:
                z_score = (complexity - baseline.mean) / baseline.standard_deviation
                
                # Check if it's an outlier
                if abs(z_score) > self.Z_SCORE_THRESHOLD:
                    percentile = self._calculate_percentile(values, complexity)
                    
                    # Calculate confidence
                    confidence = min(0.8, abs(z_score) / (2 * self.Z_SCORE_THRESHOLD))
                    
                    anomaly = StatisticalAnomaly(
                        anomaly_id=f"complexity_{hash(path)}",
                        anomaly_type=AnomalyType.COMPLEXITY_OUTLIER,
                        source_path=path,
                        metric_name="structural_complexity",
                        metric_value=complexity,
                        baseline=baseline,
                        deviation_score=z_score,
                        percentile=percentile,
                        confidence=confidence,
                        false_positive_risk=1.0 - confidence,
                        comparison_group=[p for p, _ in complexity_metrics if p != path],
                        statistical_test="z_score_outlier"
                    )
                    anomalies.append(anomaly)
        
        return anomalies, baseline
    
    def _detect_density_anomalies(self) -> Tuple[List[StatisticalAnomaly], Optional[ComparisonBaseline]]:
        """Detect modules with unusual import/export density."""
        try:
            density_metrics = self.density_patterns.get_module_densities()
        except Exception:
            self.insufficient_data.append("density_analysis")
            return [], None
        
        if len(density_metrics) < self.MIN_POPULATION:
            self.insufficient_data.append("density_analysis")
            return [], None
        
        # Extract density values
        values = list(density_metrics.values())
        baseline = self._calculate_baseline(values)
        
        # Find statistical extremes
        anomalies = []
        for path, density in density_metrics.items():
            percentile = self._calculate_percentile(values, density)
            
            # Flag extremes in top/bottom 5%
            if percentile > 95 or percentile < 5:
                z_score = (density - baseline.mean) / baseline.standard_deviation if baseline.standard_deviation > 0 else 0
                
                # Lower confidence for density anomalies (high uncertainty)
                confidence = 0.65  # Fixed moderate confidence
                
                anomaly = StatisticalAnomaly(
                    anomaly_id=f"density_{hash(path)}",
                    anomaly_type=AnomalyType.DENSITY_OUTLIER,
                    source_path=path,
                    metric_name="import_export_density",
                    metric_value=density,
                    baseline=baseline,
                    deviation_score=z_score,
                    percentile=percentile,
                    confidence=confidence,
                    false_positive_risk=0.35,
                    comparison_group=list(density_metrics.keys()),
                    statistical_test="percentile_extreme"
                )
                anomalies.append(anomaly)
        
        return anomalies, baseline
    
    def _detect_isolation_anomalies(self) -> Tuple[List[StatisticalAnomaly], Optional[ComparisonBaseline]]:
        """Detect modules with unusual connection patterns."""
        # This would require connection data
        # For now, return empty as placeholder
        return [], None
    
    def _get_file_sizes(self) -> List[Tuple[str, float]]:
        """Extract file sizes from snapshot."""
        sizes = []
        
        # Simplified extraction - in production, would use snapshot API
        if hasattr(self.snapshot, 'get_file_observations'):
            for obs in self.snapshot.get_file_observations():
                if hasattr(obs, 'size_bytes') and hasattr(obs, 'relative_path'):
                    sizes.append((str(obs.relative_path), float(obs.size_bytes)))
        
        return sizes
    
    def _get_complexity_metrics(self) -> List[Tuple[str, float]]:
        """Extract complexity metrics."""
        metrics = []
        
        try:
            # Get complexity from patterns module
            complexity_data = self.complexity_patterns.get_module_complexities()
            for module, complexity in complexity_data.items():
                metrics.append((module, float(complexity)))
        except Exception:
            # Fallback to simple metrics if available
            pass
        
        return metrics
    
    def _calculate_baseline(self, values: List[float]) -> ComparisonBaseline:
        """Calculate statistical baseline for a set of values."""
        if not values:
            return ComparisonBaseline(
                population_size=0,
                mean=0.0,
                median=0.0,
                standard_deviation=0.0,
                interquartile_range=(0.0, 0.0),
                has_sufficient_data=False
            )
        
        # Basic statistics
        mean = statistics.mean(values)
        median = statistics.median(values)
        
        # Standard deviation (handle small samples)
        if len(values) > 1:
            stdev = statistics.stdev(values)
        else:
            stdev = 0.0
        
        # Interquartile range
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n >= 4:
            q1_index = n // 4
            q3_index = (3 * n) // 4
            q1 = sorted_values[q1_index]
            q3 = sorted_values[q3_index]
        else:
            q1 = sorted_values[0] if n > 0 else 0.0
            q3 = sorted_values[-1] if n > 0 else 0.0
        
        # Try to characterize distribution
        distribution_type = "unknown"
        if n >= 10:
            # Simple skewness test
            if abs(mean - median) > 0.1 * stdev:
                distribution_type = "skewed"
            else:
                distribution_type = "approximately_normal"
        
        return ComparisonBaseline(
            population_size=n,
            mean=mean,
            median=median,
            standard_deviation=stdev,
            interquartile_range=(q1, q3),
            has_sufficient_data=n >= self.MIN_POPULATION,
            distribution_type=distribution_type
        )
    
    def _calculate_percentile(self, values: List[float], value: float) -> float:
        """Calculate percentile rank of a value."""
        if not values:
            return 50.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Count values less than the given value
        less_than = sum(1 for v in sorted_values if v < value)
        
        # Handle equal values
        equal_to = sum(1 for v in sorted_values if v == value)
        
        # Percentile formula: (count_below + 0.5 * count_equal) / n * 100
        percentile = (less_than + 0.5 * equal_to) / n * 100
        
        return min(100.0, max(0.0, percentile))
    
    def _count_analyzed_items(self) -> int:
        """Count total items analyzed across all metrics."""
        # Count unique files analyzed
        analyzed_files = set()
        
        # Add from file sizes
        for path, _ in self._get_file_sizes():
            analyzed_files.add(path)
        
        # Add from complexity
        for path, _ in self._get_complexity_metrics():
            analyzed_files.add(path)
        
        return len(analyzed_files)


class ConstitutionalViolation(Exception):
    """Exception raised when constitutional rules are violated."""
    
    def __init__(self, message: str, tier: int = 1):
        super().__init__(message)
        self.tier = tier
        self.message = message
        
        # Constitutional: Log violations
        self._log_violation()
    
    def _log_violation(self) -> None:
        """Log constitutional violation."""
        import logging
        logger = logging.getLogger('codemarshal.anomalies')
        logger.error(
            f"Constitutional Violation (Tier {self.tier}): {self.message}"
        )


# Utility functions
def analyze_anomalies(snapshot: Snapshot) -> AnomalyAnalysis:
    """Convenience function to analyze anomalies."""
    detector = AnomalyDetector(snapshot)
    return detector.analyze_all()


def export_anomaly_report(analysis: AnomalyAnalysis, 
                         output_path: str) -> None:
    """Export anomaly analysis as JSON."""
    data = analysis.to_dict()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def filter_high_confidence_anomalies(analysis: AnomalyAnalysis,
                                   min_confidence: float = 0.7) -> List[StatisticalAnomaly]:
    """Filter anomalies by confidence threshold."""
    return [a for a in analysis.anomalies if a.confidence >= min_confidence]


def get_anomaly_summary_by_path(analysis: AnomalyAnalysis,
                               path: str) -> Optional[str]:
    """Get summary of anomalies for a specific path."""
    anomalies = analysis.get_by_source_path(path)
    if not anomalies:
        return None
    
    summary = [f"Statistical anomalies for {path}:"]
    for anomaly in anomalies:
        summary.append(f"  • {anomaly.metric_name}: {anomaly.describe_deviation()}")
    
    return "\n".join(summary)


# Example usage (for testing only)
def demonstrate_anomaly_detection(snapshot_path: str) -> AnomalyAnalysis:
    """Example function to demonstrate usage."""
    from observations.record.snapshot import load_snapshot
    
    snapshot = load_snapshot(snapshot_path)
    return analyze_anomalies(snapshot)


# Export public API
__all__ = [
    'AnomalyType',
    'ComparisonBaseline',
    'StatisticalAnomaly',
    'AnomalyAnalysis',
    'AnomalyDetector',
    'ConstitutionalViolation',
    'analyze_anomalies',
    'export_anomaly_report',
    'filter_high_confidence_anomalies',
    'get_anomaly_summary_by_path'
]