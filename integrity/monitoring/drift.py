"""
Truth drift monitoring for CodeMarshal's immutable observations.

Purpose:
    Detect concept drift, data drift, and changes in patterns over time in system outputs or stored observations.
    Ensure reproducibility: the system can detect if the same inputs are now producing different outputs.

Constitutional Constraints:
    Article 3: Truth Preservation - Never obscure, distort, or invent drift information
    Article 9: Immutable Observations - Compare only immutable records
    Article 13: Deterministic Operation - Same inputs must produce same outputs
    Article 19: Backward Truth Compatibility - New versions must not invalidate previous observations
"""

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path

# Type aliases for clarity
from typing import Any

# Core imports
from core.context import RuntimeContext

# Observations imports
from observations.record.snapshot import (
    load_snapshot,
)
from storage.atomic import atomic_write

# Storage imports
from storage.layout import (
    get_investigation_path,
    get_observation_store_path,
    get_snapshot_paths,
)


class DriftSeverity(Enum):
    """
    Severity levels for detected drift.

    Levels:
        CRITICAL: Constitutional violation, truth is compromised
        MAJOR: Significant drift requiring attention
        MINOR: Minor drift, should be monitored
        NONE: No drift detected
        UNCERTAIN: Cannot determine drift with certainty
    """

    CRITICAL = auto()  # Truth preservation at risk
    MAJOR = auto()  # Significant deviation from expected
    MINOR = auto()  # Minor deviation
    NONE = auto()  # No deviation
    UNCERTAIN = auto()  # Cannot determine


class DriftType(Enum):
    """
    Types of drift that can be detected.
    """

    # Observation-level drift
    OBSERVATION_ADDED = auto()  # New observation in same context
    OBSERVATION_REMOVED = auto()  # Observation disappeared
    OBSERVATION_CHANGED = auto()  # Observation content changed

    # Pattern-level drift
    PATTERN_DIVERGENCE = auto()  # Patterns no longer match
    DISTRIBUTION_SHIFT = auto()  # Statistical distribution changed

    # System-level drift
    REPRODUCIBILITY_FAILED = auto()  # Same inputs produce different outputs
    CONSISTENCY_LOST = auto()  # Internal consistency broken

    # Constitutional drift
    TRUTH_CORRUPTION = auto()  # Immutable truth appears corrupted
    ANCHOR_SHIFT = auto()  # Stable reference points changed


class DriftDetectionMethod(Enum):
    """
    Methods for detecting drift, each with different certainty levels.
    """

    HASH_COMPARISON = auto()  # Exact hash match (highest certainty)
    CONTENT_COMPARISON = auto()  # Content comparison (high certainty)
    STATISTICAL_TEST = auto()  # Statistical test (medium certainty)
    PATTERN_MATCHING = auto()  # Pattern matching (low certainty)
    HEURISTIC = auto()  # Heuristic approach (lowest certainty)


@dataclass(frozen=True)
class DriftDetection:
    """
    Immutable detection of a specific drift event.

    Frozen to ensure truth preservation and auditability.
    """

    detection_id: str
    timestamp: datetime
    drift_type: DriftType
    severity: DriftSeverity
    method: DriftDetectionMethod
    certainty: float  # 0.0 to 1.0
    description: str
    anchor_id: str | None = None
    observation_id: str | None = None
    snapshot_version1: str | None = None
    snapshot_version2: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "detection_id": self.detection_id,
            "timestamp": self.timestamp.isoformat(),
            "drift_type": self.drift_type.name,
            "severity": self.severity.name,
            "method": self.method.name,
            "certainty": round(self.certainty, 3),
            "description": self.description,
            "anchor_id": self.anchor_id,
            "observation_id": self.observation_id,
            "snapshot_version1": self.snapshot_version1,
            "snapshot_version2": self.snapshot_version2,
            "evidence": self.evidence.copy(),
            "context": self.context.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DriftDetection":
        """Create from dictionary with validation."""
        return cls(
            detection_id=str(data["detection_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            drift_type=DriftType[data["drift_type"]],
            severity=DriftSeverity[data["severity"]],
            method=DriftDetectionMethod[data["method"]],
            certainty=float(data["certainty"]),
            description=str(data["description"]),
            anchor_id=str(data["anchor_id"]) if data.get("anchor_id") else None,
            observation_id=str(data["observation_id"])
            if data.get("observation_id")
            else None,
            snapshot_version1=str(data["snapshot_version1"])
            if data.get("snapshot_version1")
            else None,
            snapshot_version2=str(data["snapshot_version2"])
            if data.get("snapshot_version2")
            else None,
            evidence=dict(data.get("evidence", {})),
            context=dict(data.get("context", {})),
        )

    def get_truth_preserving_message(self) -> str:
        """Generate truth-preserving drift message."""
        base_msg = f"{self.severity.name} drift detected: {self.description}"

        if self.certainty < 0.9:
            return f"⚠️ {base_msg} (certainty: {self.certainty:.0%})"
        elif self.severity == DriftSeverity.CRITICAL:
            return f"🚨 {base_msg}"
        else:
            return base_msg


class DriftMonitor:
    """
    Thread-safe drift monitoring system.

    Design Principles:
    1. Only compare immutable observations (Article 9)
    2. Use deterministic comparison methods (Article 13)
    3. Preserve backward compatibility (Article 19)
    4. Clearly signal uncertainty (Article 3)
    """

    def __init__(self, context: RuntimeContext):
        """
        Initialize drift monitor.

        Args:
            context: Current runtime context for investigation ID
        """
        self.context: RuntimeContext = context
        self._detections: list[DriftDetection] = []
        self._lock: threading.RLock = threading.RLock()
        self._detection_id_counter: int = 0

        # Cache for performance
        self._snapshot_cache: dict[str, dict[str, Any]] = {}
        self._hash_cache: dict[str, str] = {}

    def _generate_detection_id(self) -> str:
        """Generate unique detection ID."""
        with self._lock:
            self._detection_id_counter += 1
            return f"DRIFT-{self.context.investigation_id}-{self._detection_id_counter:08d}"

    def _load_snapshot(self, version: str) -> dict[str, Any] | None:
        """
        Load snapshot with caching.

        Args:
            version: Snapshot version identifier

        Returns:
            Snapshot data or None if not found
        """
        if version in self._snapshot_cache:
            return self._snapshot_cache[version]

        try:
            snapshot_paths = get_snapshot_paths(self.context.investigation_id)
            for path in snapshot_paths:
                if path.stem == version:
                    snapshot = load_snapshot(path)
                    self._snapshot_cache[version] = snapshot
                    return snapshot
        except Exception as e:
            # Record failure but don't crash
            self.record_drift(
                drift_type=DriftType.TRUTH_CORRUPTION,
                severity=DriftSeverity.UNCERTAIN,
                method=DriftDetectionMethod.HEURISTIC,
                certainty=0.5,
                description=f"Failed to load snapshot {version}: {str(e)}",
                evidence={"version": version, "error": str(e)},
            )

        return None

    def _compute_observation_hash(self, observation: dict[str, Any]) -> str:
        """
        Compute deterministic hash of observation.

        Args:
            observation: Observation data

        Returns:
            SHA-256 hash as hex string
        """
        # Create cache key from observation ID and content
        cache_key = (
            f"{observation.get('id', '')}:{json.dumps(observation, sort_keys=True)}"
        )

        if cache_key in self._hash_cache:
            return self._hash_cache[cache_key]

        # Use the system's integrity hash function
        try:
            from observations.record.integrity import compute_observation_hash

            obs_hash = compute_observation_hash(observation)
        except ImportError:
            # Fallback: compute hash locally
            content = json.dumps(observation, sort_keys=True).encode("utf-8")
            obs_hash = hashlib.sha256(content).hexdigest()

        self._hash_cache[cache_key] = obs_hash
        return obs_hash

    def record_drift(
        self,
        drift_type: DriftType,
        severity: DriftSeverity,
        method: DriftDetectionMethod,
        certainty: float,
        description: str,
        anchor_id: str | None = None,
        observation_id: str | None = None,
        snapshot_version1: str | None = None,
        snapshot_version2: str | None = None,
        evidence: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> DriftDetection:
        """
        Record a drift detection.

        Args:
            drift_type: Type of drift detected
            severity: Severity of drift
            method: Detection method used
            certainty: Certainty level (0.0 to 1.0)
            description: Human-readable description
            anchor_id: Optional anchor ID
            observation_id: Optional observation ID
            snapshot_version1: First snapshot version
            snapshot_version2: Second snapshot version
            evidence: Supporting evidence
            context: Additional context

        Returns:
            DriftDetection that was created
        """
        # Validate certainty
        certainty = max(0.0, min(1.0, certainty))

        detection_id = self._generate_detection_id()
        timestamp = datetime.now(UTC)

        detection = DriftDetection(
            detection_id=detection_id,
            timestamp=timestamp,
            drift_type=drift_type,
            severity=severity,
            method=method,
            certainty=certainty,
            description=description,
            anchor_id=anchor_id,
            observation_id=observation_id,
            snapshot_version1=snapshot_version1,
            snapshot_version2=snapshot_version2,
            evidence=evidence or {},
            context=context or {},
        )

        with self._lock:
            self._detections.append(detection)

        return detection

    def compare_snapshots(
        self,
        version1: str,
        version2: str,
        method: DriftDetectionMethod = DriftDetectionMethod.HASH_COMPARISON,
    ) -> list[DriftDetection]:
        """
        Compare two snapshots for drift.

        Args:
            version1: First snapshot version
            version2: Second snapshot version
            method: Comparison method to use

        Returns:
            List of drift detections found
        """
        snap1 = self._load_snapshot(version1)
        snap2 = self._load_snapshot(version2)

        if not snap1 or not snap2:
            return []

        detections = []

        if method == DriftDetectionMethod.HASH_COMPARISON:
            detections.extend(self._compare_by_hash(snap1, snap2, version1, version2))
        elif method == DriftDetectionMethod.CONTENT_COMPARISON:
            detections.extend(
                self._compare_by_content(snap1, snap2, version1, version2)
            )
        else:
            # For other methods, record uncertainty
            self.record_drift(
                drift_type=DriftType.UNCERTAIN,
                severity=DriftSeverity.UNCERTAIN,
                method=method,
                certainty=0.5,
                description=f"Comparison method {method.name} not fully implemented",
                snapshot_version1=version1,
                snapshot_version2=version2,
            )

        return detections

    def _compare_by_hash(
        self, snap1: dict[str, Any], snap2: dict[str, Any], version1: str, version2: str
    ) -> list[DriftDetection]:
        """
        Compare snapshots by computing hashes of observations.

        Highest certainty method for detecting exact changes.
        """
        detections = []

        # Extract observations
        obs1 = {o.get("id"): o for o in snap1.get("observations", []) if o.get("id")}
        obs2 = {o.get("id"): o for o in snap2.get("observations", []) if o.get("id")}

        all_ids = set(obs1.keys()) | set(obs2.keys())

        for obs_id in all_ids:
            if obs_id in obs1 and obs_id not in obs2:
                # Observation removed
                detections.append(
                    self.record_drift(
                        drift_type=DriftType.OBSERVATION_REMOVED,
                        severity=DriftSeverity.MAJOR,
                        method=DriftDetectionMethod.HASH_COMPARISON,
                        certainty=1.0,
                        description=f"Observation {obs_id} removed between snapshots",
                        observation_id=obs_id,
                        snapshot_version1=version1,
                        snapshot_version2=version2,
                        evidence={
                            "observation_id": obs_id,
                            "in_snapshot1": True,
                            "in_snapshot2": False,
                        },
                    )
                )

            elif obs_id not in obs1 and obs_id in obs2:
                # Observation added
                detections.append(
                    self.record_drift(
                        drift_type=DriftType.OBSERVATION_ADDED,
                        severity=DriftSeverity.MINOR,
                        method=DriftDetectionMethod.HASH_COMPARISON,
                        certainty=1.0,
                        description=f"Observation {obs_id} added between snapshots",
                        observation_id=obs_id,
                        snapshot_version1=version1,
                        snapshot_version2=version2,
                        evidence={
                            "observation_id": obs_id,
                            "in_snapshot1": False,
                            "in_snapshot2": True,
                        },
                    )
                )

            else:
                # Observation in both - compare hashes
                hash1 = self._compute_observation_hash(obs1[obs_id])
                hash2 = self._compute_observation_hash(obs2[obs_id])

                if hash1 != hash2:
                    # Observation changed
                    detections.append(
                        self.record_drift(
                            drift_type=DriftType.OBSERVATION_CHANGED,
                            severity=DriftSeverity.MAJOR,
                            method=DriftDetectionMethod.HASH_COMPARISON,
                            certainty=1.0,
                            description=f"Observation {obs_id} changed between snapshots",
                            observation_id=obs_id,
                            snapshot_version1=version1,
                            snapshot_version2=version2,
                            evidence={
                                "observation_id": obs_id,
                                "hash1": hash1,
                                "hash2": hash2,
                                "content_diff": self._compute_content_diff(
                                    obs1[obs_id], obs2[obs_id]
                                ),
                            },
                        )
                    )

        # Check for reproducibility failure
        if snap1.get("input_hash") and snap2.get("input_hash"):
            if snap1["input_hash"] == snap2["input_hash"] and detections:
                # Same input produced different observations!
                detections.append(
                    self.record_drift(
                        drift_type=DriftType.REPRODUCIBILITY_FAILED,
                        severity=DriftSeverity.CRITICAL,
                        method=DriftDetectionMethod.HASH_COMPARISON,
                        certainty=1.0,
                        description="Same input produced different observations (constitutional violation)",
                        snapshot_version1=version1,
                        snapshot_version2=version2,
                        evidence={
                            "input_hash": snap1["input_hash"],
                            "change_count": len(detections),
                        },
                    )
                )

        return detections

    def _compare_by_content(
        self, snap1: dict[str, Any], snap2: dict[str, Any], version1: str, version2: str
    ) -> list[DriftDetection]:
        """
        Compare snapshots by content analysis.

        Lower certainty but can detect semantic drift.
        """
        detections = []

        # Compare metadata
        meta1 = snap1.get("metadata", {})
        meta2 = snap2.get("metadata", {})

        # Check if observation counts changed significantly
        count1 = len(snap1.get("observations", []))
        count2 = len(snap2.get("observations", []))

        if abs(count1 - count2) > max(count1, count2) * 0.1:  # More than 10% change
            detections.append(
                self.record_drift(
                    drift_type=DriftType.DISTRIBUTION_SHIFT,
                    severity=DriftSeverity.MINOR,
                    method=DriftDetectionMethod.CONTENT_COMPARISON,
                    certainty=0.8,
                    description=f"Observation count changed significantly: {count1} → {count2}",
                    snapshot_version1=version1,
                    snapshot_version2=version2,
                    evidence={
                        "count1": count1,
                        "count2": count2,
                        "change_percent": abs(count1 - count2) / max(count1, 1) * 100,
                    },
                )
            )

        # Check timestamps for temporal drift
        time1 = meta1.get("created_at")
        time2 = meta2.get("created_at")

        if time1 and time2:
            try:
                dt1 = datetime.fromisoformat(time1) if isinstance(time1, str) else time1
                dt2 = datetime.fromisoformat(time2) if isinstance(time2, str) else time2

                if abs((dt2 - dt1).total_seconds()) > 86400:  # More than 1 day apart
                    detections.append(
                        self.record_drift(
                            drift_type=DriftType.PATTERN_DIVERGENCE,
                            severity=DriftSeverity.MINOR,
                            method=DriftDetectionMethod.CONTENT_COMPARISON,
                            certainty=0.7,
                            description=f"Significant time gap between snapshots: {(dt2 - dt1).days} days",
                            snapshot_version1=version1,
                            snapshot_version2=version2,
                            evidence={
                                "time1": time1,
                                "time2": time2,
                                "gap_days": (dt2 - dt1).days,
                            },
                        )
                    )
            except (ValueError, TypeError):
                pass

        return detections

    def _compute_content_diff(
        self, obs1: dict[str, Any], obs2: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Compute content differences between two observations.

        Returns structured diff information.
        """
        diff = {"fields_changed": [], "values1": {}, "values2": {}}

        all_keys = set(obs1.keys()) | set(obs2.keys())

        for key in all_keys:
            val1 = obs1.get(key)
            val2 = obs2.get(key)

            if val1 != val2:
                diff["fields_changed"].append(key)
                diff["values1"][key] = str(val1)[:100]  # Limit length
                diff["values2"][key] = str(val2)[:100]

        return diff

    def check_reproducibility(
        self, current_observations: list[dict[str, Any]], input_hash: str | None = None
    ) -> list[DriftDetection]:
        """
        Check if current observations match historical ones for same input.

        Args:
            current_observations: Current observation set
            input_hash: Hash of input that generated these observations

        Returns:
            List of reproducibility drift detections
        """
        if not input_hash:
            return []

        detections = []

        # Find historical snapshots with same input hash
        try:
            snapshot_paths = get_snapshot_paths(self.context.investigation_id)

            for path in snapshot_paths:
                try:
                    snapshot = load_snapshot(path)
                    if snapshot.get("input_hash") == input_hash:
                        # Found matching historical snapshot
                        historical_obs = {
                            o.get("id"): o for o in snapshot.get("observations", [])
                        }
                        current_obs = {o.get("id"): o for o in current_observations}

                        # Compare observation sets
                        if historical_obs != current_obs:
                            detections.append(
                                self.record_drift(
                                    drift_type=DriftType.REPRODUCIBILITY_FAILED,
                                    severity=DriftSeverity.CRITICAL,
                                    method=DriftDetectionMethod.HASH_COMPARISON,
                                    certainty=0.95,
                                    description="Reproducibility failure: same input produced different observations",
                                    snapshot_version1=path.stem,
                                    snapshot_version2="current",
                                    evidence={
                                        "input_hash": input_hash,
                                        "historical_count": len(historical_obs),
                                        "current_count": len(current_obs),
                                        "matching_snapshot": path.stem,
                                    },
                                )
                            )
                        break
                except Exception:
                    continue
        except Exception as e:
            # Record uncertainty about reproducibility
            detections.append(
                self.record_drift(
                    drift_type=DriftType.UNCERTAIN,
                    severity=DriftSeverity.UNCERTAIN,
                    method=DriftDetectionMethod.HEURISTIC,
                    certainty=0.5,
                    description=f"Could not verify reproducibility: {str(e)}",
                    evidence={"error": str(e)},
                )
            )

        return detections

    def detect_anchor_shift(self) -> list[DriftDetection]:
        """
        Detect shifts in stable reference points (anchors).

        Critical for truth preservation as anchors should not change.
        """
        detections = []

        try:
            from observations.record.anchors import load_anchors

            # Load current anchors
            inv_path = get_investigation_path(self.context.investigation_id)
            anchors_path = inv_path / "anchors.json"

            if anchors_path.exists():
                current_anchors = load_anchors(anchors_path)

                # Check each anchor for stability
                for anchor in current_anchors:
                    # Verify anchor points to valid observation
                    obs_store_path = get_observation_store_path(
                        self.context.investigation_id
                    )
                    target_path = obs_store_path / f"{anchor.observation_id}.json"

                    if not target_path.exists():
                        detections.append(
                            self.record_drift(
                                drift_type=DriftType.ANCHOR_SHIFT,
                                severity=DriftSeverity.CRITICAL,
                                method=DriftDetectionMethod.HASH_COMPARISON,
                                certainty=1.0,
                                description=f"Anchor {anchor.id} points to missing observation",
                                anchor_id=anchor.id,
                                observation_id=anchor.observation_id,
                                evidence={
                                    "anchor_id": anchor.id,
                                    "observation_id": anchor.observation_id,
                                    "expected_path": str(target_path),
                                    "exists": False,
                                },
                            )
                        )
        except ImportError:
            # Anchors module not available yet
            pass
        except Exception as e:
            detections.append(
                self.record_drift(
                    drift_type=DriftType.UNCERTAIN,
                    severity=DriftSeverity.UNCERTAIN,
                    method=DriftDetectionMethod.HEURISTIC,
                    certainty=0.5,
                    description=f"Could not check anchor stability: {str(e)}",
                    evidence={"error": str(e)},
                )
            )

        return detections

    def get_detections(
        self,
        drift_type: DriftType | None = None,
        severity: DriftSeverity | None = None,
        min_certainty: float = 0.0,
        limit: int = 1000,
    ) -> list[DriftDetection]:
        """
        Get drift detections with optional filtering.

        Args:
            drift_type: Filter by drift type
            severity: Filter by severity
            min_certainty: Minimum certainty level
            limit: Maximum number of detections to return

        Returns:
            List of matching drift detections (newest first)
        """
        with self._lock:
            detections = self._detections.copy()

        # Filter detections
        filtered_detections = []
        for detection in reversed(detections):  # Newest first
            if drift_type is not None and detection.drift_type != drift_type:
                continue
            if severity is not None and detection.severity != severity:
                continue
            if detection.certainty < min_certainty:
                continue

            filtered_detections.append(detection)
            if len(filtered_detections) >= limit:
                break

        return filtered_detections

    def get_summary(self) -> dict[str, Any]:
        """
        Generate summary statistics for drift monitoring.

        Returns:
            Dictionary with drift statistics and health indicators
        """
        with self._lock:
            detections = self._detections.copy()

        if not detections:
            return {
                "total_detections": 0,
                "critical_drift": 0,
                "health_status": "STABLE",
                "drift_types": {},
                "severity_distribution": {},
                "recent_detections": [],
                "warnings": [],
            }

        # Count statistics
        total_detections = len(detections)
        critical_drift = sum(
            1 for d in detections if d.severity == DriftSeverity.CRITICAL
        )

        drift_types: dict[str, int] = {}
        severity_distribution: dict[str, int] = {}

        for detection in detections:
            type_name = detection.drift_type.name
            sev_name = detection.severity.name

            drift_types[type_name] = drift_types.get(type_name, 0) + 1
            severity_distribution[sev_name] = severity_distribution.get(sev_name, 0) + 1

        # Determine health status
        if critical_drift > 0:
            health_status = "CRITICAL"
        elif severity_distribution.get("MAJOR", 0) > 3:
            health_status = "UNSTABLE"
        elif severity_distribution.get("MINOR", 0) > 10:
            health_status = "WATCH"
        else:
            health_status = "STABLE"

        # Get recent detections (last 10)
        recent_detections = [
            {
                "id": d.detection_id,
                "timestamp": d.timestamp.isoformat(),
                "drift_type": d.drift_type.name,
                "severity": d.severity.name,
                "certainty": d.certainty,
                "description": d.description[:100] + "..."
                if len(d.description) > 100
                else d.description,
            }
            for d in sorted(detections, key=lambda x: x.timestamp, reverse=True)[:10]
        ]

        # Generate warnings
        warning_messages = []
        if critical_drift > 0:
            warning_messages.append(
                "🚨 Critical drift detected - truth preservation may be compromised"
            )
        if DriftType.REPRODUCIBILITY_FAILED.name in drift_types:
            warning_messages.append(
                "⚠️ Reproducibility failures detected - same inputs produce different outputs"
            )
        if DriftType.ANCHOR_SHIFT.name in drift_types:
            warning_messages.append(
                "⚠️ Anchor shifts detected - stable reference points have changed"
            )

        return {
            "total_detections": total_detections,
            "critical_drift": critical_drift,
            "health_status": health_status,
            "drift_types": drift_types,
            "severity_distribution": severity_distribution,
            "recent_detections": recent_detections,
            "warnings": warning_messages,
            "investigation_id": self.context.investigation_id,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def save_to_disk(self, path: Path | None = None) -> Path:
        """
        Save drift detections to disk for audit trail.

        Args:
            path: Optional custom path, defaults to investigation directory

        Returns:
            Path where detections were saved
        """
        if path is None:
            inv_path = get_investigation_path(self.context.investigation_id)
            path = (
                inv_path
                / "drift"
                / f"detections_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
            )

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            detections_data = [d.to_dict() for d in self._detections]
            summary = self.get_summary()

        data = {
            "detections": detections_data,
            "summary": summary,
            "metadata": {
                "investigation_id": self.context.investigation_id,
                "saved_at": datetime.now(UTC).isoformat(),
                "detection_count": len(detections_data),
            },
        }

        # Atomic write
        atomic_write(data, path)

        return path

    def clear(self) -> int:
        """
        Clear all drift detections.

        Returns:
            Number of detections cleared
        """
        with self._lock:
            count = len(self._detections)
            self._detections.clear()
            self._snapshot_cache.clear()
            self._hash_cache.clear()

        return count


# Global drift monitor instance (thread-safe singleton pattern)
_DRIFT_MONITOR: DriftMonitor | None = None
_MONITOR_LOCK: threading.RLock = threading.RLock()


def get_drift_monitor(context: RuntimeContext | None = None) -> DriftMonitor:
    """
    Get or create the global drift monitor.

    Args:
        context: Runtime context (required on first call)

    Returns:
        DriftMonitor instance

    Raises:
        ValueError: If context is None and monitor hasn't been initialized
    """
    global _DRIFT_MONITOR

    with _MONITOR_LOCK:
        if _DRIFT_MONITOR is None:
            if context is None:
                raise ValueError("RuntimeContext required for first initialization")
            _DRIFT_MONITOR = DriftMonitor(context)

        return _DRIFT_MONITOR


def monitor_drift(context: RuntimeContext | None = None) -> dict[str, Any]:
    """
    Main function for drift monitoring.

    Called from core/engine.py or bridge/coordination/scheduling.py.

    Args:
        context: Runtime context (optional, uses existing monitor if available)

    Returns:
        Structured drift report
    """
    try:
        monitor = get_drift_monitor(context)

        # Run all drift detection checks
        summary = monitor.get_summary()

        # Check for recent snapshots to compare
        try:
            snapshot_paths = get_snapshot_paths(monitor.context.investigation_id)
            if len(snapshot_paths) >= 2:
                # Compare two most recent snapshots
                versions = sorted([p.stem for p in snapshot_paths], reverse=True)[:2]
                detections = monitor.compare_snapshots(versions[1], versions[0])

                if detections:
                    summary["recent_comparison"] = {
                        "snapshot1": versions[1],
                        "snapshot2": versions[0],
                        "detections_found": len(detections),
                        "critical_detections": len(
                            [
                                d
                                for d in detections
                                if d.severity == DriftSeverity.CRITICAL
                            ]
                        ),
                    }
        except Exception as e:
            # Record but don't fail
            summary["comparison_error"] = str(e)

        # Check for anchor shifts
        anchor_detections = monitor.detect_anchor_shift()
        if anchor_detections:
            summary["anchor_issues"] = len(anchor_detections)

        # Add constitutional compliance check
        if summary["health_status"] == "CRITICAL":
            summary["constitutional_status"] = "VIOLATED"
            summary["constitutional_articles"] = [
                "Article 3",
                "Article 9",
                "Article 13",
            ]
        else:
            summary["constitutional_status"] = "COMPLIANT"

        return summary

    except Exception as e:
        # Even drift monitoring can fail - be honest about it
        return {
            "error": f"Drift monitoring failed: {type(e).__name__}: {str(e)}",
            "total_detections": 0,
            "critical_drift": 0,
            "health_status": "UNKNOWN",
            "constitutional_status": "UNKNOWN",
            "drift_types": {},
            "severity_distribution": {},
            "recent_detections": [],
            "warnings": ["Drift monitoring temporarily unavailable"],
            "generated_at": datetime.now(UTC).isoformat(),
        }


def check_reproducibility(
    context: RuntimeContext,
    observations: list[dict[str, Any]],
    input_hash: str | None = None,
) -> list[dict[str, Any]]:
    """
    Check reproducibility of current observations.

    Convenience function for use throughout the system.

    Args:
        context: Runtime context
        observations: Current observations
        input_hash: Hash of input that generated observations

    Returns:
        List of reproducibility issues found
    """
    monitor = get_drift_monitor(context)
    detections = monitor.check_reproducibility(observations, input_hash)

    issues = []
    for detection in detections:
        issues.append(
            {
                "severity": detection.severity.name,
                "type": detection.drift_type.name,
                "detection_id": detection.detection_id,
                "description": detection.description,
                "certainty": detection.certainty,
                "evidence": detection.evidence,
            }
        )

    return issues


def verify_immutability(context: RuntimeContext) -> list[dict[str, Any]]:
    """
    Verify that observations remain immutable over time.

    Critical check for Article 9 compliance.

    Args:
        context: Runtime context

    Returns:
        List of immutability violations found
    """
    monitor = get_drift_monitor(context)

    try:
        snapshot_paths = get_snapshot_paths(context.investigation_id)

        if len(snapshot_paths) < 2:
            return []  # Need at least 2 snapshots to compare

        violations = []

        # Compare each pair of consecutive snapshots
        sorted_paths = sorted(snapshot_paths, key=lambda p: p.stem)

        for i in range(1, len(sorted_paths)):
            version1 = sorted_paths[i - 1].stem
            version2 = sorted_paths[i].stem

            detections = monitor.compare_snapshots(version1, version2)

            # Check for observation changes (should not happen for same observation IDs)
            for detection in detections:
                if detection.drift_type in [
                    DriftType.OBSERVATION_CHANGED,
                    DriftType.REPRODUCIBILITY_FAILED,
                ]:
                    violations.append(
                        {
                            "violation": "IMMUTABILITY_VIOLATION",
                            "article": "Article 9",
                            "description": detection.description,
                            "detection_id": detection.detection_id,
                            "snapshot1": version1,
                            "snapshot2": version2,
                            "evidence": detection.evidence,
                        }
                    )

        return violations

    except Exception as e:
        # Record uncertainty
        monitor.record_drift(
            drift_type=DriftType.UNCERTAIN,
            severity=DriftSeverity.UNCERTAIN,
            method=DriftDetectionMethod.HEURISTIC,
            certainty=0.5,
            description=f"Could not verify immutability: {str(e)}",
            evidence={"error": str(e)},
        )

        return [
            {
                "violation": "VERIFICATION_FAILED",
                "article": "Article 9",
                "description": f"Could not verify immutability: {str(e)}",
                "certainty": 0.5,
            }
        ]


# Test function for module validation
def test_drift_monitoring() -> dict[str, Any]:
    """
    Test the drift monitoring system.

    Returns:
        Test results with pass/fail status
    """
    from core.context import RuntimeContext

    # Create test context
    test_context = RuntimeContext(
        investigation_id="test_drift",
        root_path=Path.cwd(),
        config={},
        started_at=datetime.now(UTC),
    )

    results = {
        "module": "integrity.monitoring.drift",
        "tests_passed": 0,
        "tests_failed": 0,
        "details": [],
    }

    try:
        # Test 1: Monitor creation
        monitor = DriftMonitor(test_context)
        assert monitor.context.investigation_id == "test_drift"
        results["tests_passed"] += 1
        results["details"].append("Test 1: Monitor creation ✓")

        # Test 2: Drift recording
        detection = monitor.record_drift(
            drift_type=DriftType.OBSERVATION_CHANGED,
            severity=DriftSeverity.MAJOR,
            method=DriftDetectionMethod.HASH_COMPARISON,
            certainty=0.95,
            description="Test drift detection",
            observation_id="test_obs_123",
            snapshot_version1="v1",
            snapshot_version2="v2",
            evidence={"test": "data"},
        )

        assert detection.detection_id.startswith("DRIFT-test_drift-")
        assert detection.drift_type == DriftType.OBSERVATION_CHANGED
        assert detection.certainty == 0.95

        results["tests_passed"] += 1
        results["details"].append("Test 2: Drift recording ✓")

        # Test 3: Detection retrieval
        detections = monitor.get_detections()
        assert len(detections) == 1
        assert detections[0].detection_id == detection.detection_id

        results["tests_passed"] += 1
        results["details"].append("Test 3: Detection retrieval ✓")

        # Test 4: Filtering by severity
        minor_detections = monitor.get_detections(severity=DriftSeverity.MINOR)
        assert len(minor_detections) == 0  # We recorded a MAJOR

        results["tests_passed"] += 1
        results["details"].append("Test 4: Severity filtering ✓")

        # Test 5: Summary generation
        summary = monitor.get_summary()
        assert "total_detections" in summary
        assert summary["total_detections"] == 1
        assert "OBSERVATION_CHANGED" in summary["drift_types"]

        results["tests_passed"] += 1
        results["details"].append("Test 5: Summary generation ✓")

        # Test 6: Global monitor access
        global_monitor = get_drift_monitor(test_context)
        assert global_monitor is monitor

        results["tests_passed"] += 1
        results["details"].append("Test 6: Global monitor access ✓")

        # Test 7: Content diff computation
        obs1 = {"id": "test", "content": "Hello"}
        obs2 = {"id": "test", "content": "World"}
        diff = monitor._compute_content_diff(obs1, obs2)

        assert "content" in diff["fields_changed"]
        assert diff["values1"]["content"] == "Hello"
        assert diff["values2"]["content"] == "World"

        results["tests_passed"] += 1
        results["details"].append("Test 7: Content diff computation ✓")

        # Test 8: Certainty bounds
        # Test that certainty is clamped
        high_certainty = monitor.record_drift(
            drift_type=DriftType.PATTERN_DIVERGENCE,
            severity=DriftSeverity.MINOR,
            method=DriftDetectionMethod.HEURISTIC,
            certainty=1.5,  # Above 1.0
            description="Test certainty clamping",
        )
        assert high_certainty.certainty == 1.0

        low_certainty = monitor.record_drift(
            drift_type=DriftType.PATTERN_DIVERGENCE,
            severity=DriftSeverity.MINOR,
            method=DriftDetectionMethod.HEURISTIC,
            certainty=-0.5,  # Below 0.0
            description="Test certainty clamping",
        )
        assert low_certainty.certainty == 0.0

        results["tests_passed"] += 1
        results["details"].append("Test 8: Certainty bounds ✓")

        # Test 9: Truth-preserving messages
        uncertain_detection = monitor.record_drift(
            drift_type=DriftType.UNCERTAIN,
            severity=DriftSeverity.UNCERTAIN,
            method=DriftDetectionMethod.HEURISTIC,
            certainty=0.7,
            description="Test uncertainty",
        )

        msg = uncertain_detection.get_truth_preserving_message()
        assert "⚠️" in msg  # Should have uncertainty indicator

        results["tests_passed"] += 1
        results["details"].append("Test 9: Truth-preserving messages ✓")

        # Test 10: Clear detections
        cleared = monitor.clear()
        assert cleared >= 3  # At least the 3 we recorded

        assert len(monitor.get_detections()) == 0

        results["tests_passed"] += 1
        results["details"].append("Test 10: Clear detections ✓")

    except Exception as e:
        results["tests_failed"] += 1
        results["details"].append(f"Test failed: {type(e).__name__}: {str(e)}")
        import traceback

        results["details"].append(f"Traceback: {traceback.format_exc()}")

    return results


# Export public API
__all__ = [
    "DriftSeverity",
    "DriftType",
    "DriftDetectionMethod",
    "DriftDetection",
    "DriftMonitor",
    "get_drift_monitor",
    "monitor_drift",
    "check_reproducibility",
    "verify_immutability",
    "test_drift_monitoring",
]
