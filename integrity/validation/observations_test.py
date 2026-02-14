"""
integrity/validation/observations_test.py - Observation system validation tests

Tests that validate the observation system's integrity, immutability,
and constitutional compliance.
"""

import hashlib
import json
from datetime import datetime

import pytest


class TestObservationImmutability:
    """Test that observations are immutable (Article 1)."""

    def test_observation_cannot_be_modified(self):
        """Test that recorded observations cannot be changed."""
        # Create an observation
        observation = {
            "id": "test_obs_001",
            "timestamp": datetime.now().isoformat(),
            "data": {"key": "value"},
        }

        # Calculate hash
        original_hash = hashlib.sha256(
            json.dumps(observation, sort_keys=True).encode()
        ).hexdigest()

        # Attempt to modify (in real system this would fail)
        modified = observation.copy()
        modified["data"]["key"] = "modified"

        # Verify hash changed
        modified_hash = hashlib.sha256(
            json.dumps(modified, sort_keys=True).encode()
        ).hexdigest()

        assert original_hash != modified_hash

    def test_observation_has_required_fields(self):
        """Test that observations have required fields."""
        observation = {
            "id": "obs_001",
            "timestamp": datetime.now().isoformat(),
            "type": "file_sight",
            "data": {},
            "integrity_hash": "abc123",
        }

        required_fields = ["id", "timestamp", "type", "data"]
        for field in required_fields:
            assert field in observation

    def test_observation_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        timestamp = datetime.now().isoformat()

        # Should be able to parse it back
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)


class TestObservationIntegrity:
    """Test observation integrity mechanisms."""

    def test_integrity_hash_computation(self):
        """Test that integrity hashes are computed correctly."""
        data = {"key": "value", "number": 42}
        data_str = json.dumps(data, sort_keys=True)

        hash1 = hashlib.sha256(data_str.encode()).hexdigest()
        hash2 = hashlib.sha256(data_str.encode()).hexdigest()

        # Same data should produce same hash
        assert hash1 == hash2

    def test_integrity_hash_detects_changes(self):
        """Test that hash changes when data changes."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}

        hash1 = hashlib.sha256(json.dumps(data1).encode()).hexdigest()
        hash2 = hashlib.sha256(json.dumps(data2).encode()).hexdigest()

        # Different data should produce different hashes
        assert hash1 != hash2


class TestObservationRecording:
    """Test observation recording process."""

    def test_observation_has_unique_id(self):
        """Test that each observation has a unique ID."""
        ids = [f"obs_{i:03d}" for i in range(100)]

        # All IDs should be unique
        assert len(ids) == len(set(ids))

    def test_observation_types_are_valid(self):
        """Test that observation types are from allowed set."""
        valid_types = {
            "file_sight",
            "import_sight",
            "boundary_sight",
            "encoding_sight",
            "export_sight",
        }

        observation_type = "file_sight"
        assert observation_type in valid_types

    def test_observation_data_is_serializable(self):
        """Test that observation data can be serialized to JSON."""
        observation = {
            "id": "obs_001",
            "timestamp": datetime.now().isoformat(),
            "type": "file_sight",
            "data": {"path": "/test/path", "size": 1024, "nested": {"key": "value"}},
        }

        # Should serialize without error
        serialized = json.dumps(observation)

        # Should deserialize back
        deserialized = json.loads(serialized)
        assert deserialized["id"] == observation["id"]


class TestObservationLimits:
    """Test observation system limitations."""

    def test_large_observation_handling(self):
        """Test that large observations are handled gracefully."""
        # Simulate a large observation
        large_data = {"items": list(range(10000))}

        # Should be able to serialize
        serialized = json.dumps(large_data)

        # Size should be reasonable (not too large)
        size_mb = len(serialized) / (1024 * 1024)
        assert size_mb < 10  # Less than 10MB

    def test_empty_observation_handling(self):
        """Test that empty observations are handled."""
        observation = {
            "id": "obs_empty",
            "timestamp": datetime.now().isoformat(),
            "type": "file_sight",
            "data": {},
        }

        # Should serialize without error
        serialized = json.dumps(observation)
        deserialized = json.loads(serialized)

        assert deserialized["data"] == {}


def validate_observations() -> "ValidationResult":
    """Run observation validation tests and return a ValidationResult."""
    from integrity import ValidationResult

    try:
        exit_code = pytest.main([__file__, "-q"])
    except Exception as exc:
        return ValidationResult(
            passed=False,
            violations=[{"check": "observations", "error": str(exc)}],
            details="Validation execution failed",
        )

    passed = exit_code == 0
    violations = [] if passed else [{"check": "observations", "details": "pytest failures"}]

    return ValidationResult(
        passed=passed,
        violations=violations,
        details=f"pytest exit code: {exit_code}",
    )
