"""
Compatibility helpers for recovery backup/restore payloads.

This module centralizes:
- package version resolution
- snapshot/observations alias normalization
- integrity hash compatibility across backup format versions
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

_BACKUP_HASH_KEYS_V2 = ("metadata", "state", "snapshot", "config")


def get_system_version(package_name: str = "codemarshal") -> str:
    """Resolve system version from package metadata with pyproject fallback."""
    try:
        return package_version(package_name)
    except PackageNotFoundError:
        pass
    except Exception:
        return "unknown"

    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        project = data.get("project", {})
        resolved = project.get("version")
        if isinstance(resolved, str) and resolved.strip():
            return resolved.strip()
    except Exception:
        return "unknown"

    return "unknown"


def get_snapshot_payload(backup_data: dict[str, Any]) -> Any | None:
    """Return canonical snapshot payload from either snapshot or observations key."""
    if "snapshot" in backup_data and backup_data["snapshot"] is not None:
        return backup_data["snapshot"]
    return backup_data.get("observations")


def with_observation_aliases(backup_data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a shallow-copied payload with both `snapshot` and `observations` aliases.

    This preserves backward compatibility while allowing a canonical internal shape.
    """
    normalized = dict(backup_data)
    snapshot_payload = get_snapshot_payload(backup_data)
    if snapshot_payload is not None:
        normalized.setdefault("snapshot", snapshot_payload)
        normalized.setdefault("observations", snapshot_payload)
    return normalized


def _hash_payload(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash for a JSON-serializable payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_canonical_hash_payload(backup_data: dict[str, Any]) -> dict[str, Any]:
    """Build v2 canonical integrity payload."""
    normalized = with_observation_aliases(backup_data)
    payload: dict[str, Any] = {}
    for key in _BACKUP_HASH_KEYS_V2:
        if key in normalized and normalized[key] is not None:
            payload[key] = normalized[key]
    return payload


def compute_integrity_hash(backup_data: dict[str, Any]) -> str:
    """Compute integrity hash using canonical v2 payload."""
    return _hash_payload(build_canonical_hash_payload(backup_data))


def compute_hash_candidates(backup_data: dict[str, Any]) -> set[str]:
    """
    Compute acceptable hash values across known backup payload strategies.

    Supports:
    - v2 canonical payload hashing
    - legacy restore payload hashing (metadata/state/snapshot)
    - legacy backup writer hashing (all keys except integrity_hashes)
    - legacy backup verifier hashing (all keys except integrity_hash)
    """
    candidates: set[str] = set()
    normalized = with_observation_aliases(backup_data)

    # v2 canonical
    canonical_payload = build_canonical_hash_payload(normalized)
    if canonical_payload:
        candidates.add(_hash_payload(canonical_payload))

    # legacy restore validation payload
    if {"metadata", "state", "snapshot"}.issubset(normalized):
        candidates.add(
            _hash_payload(
                {
                    "metadata": normalized["metadata"],
                    "state": normalized["state"],
                    "snapshot": normalized["snapshot"],
                }
            )
        )

    # legacy backup writer payload (exclude integrity_hashes, before integrity_hash existed)
    legacy_writer_payload = {
        key: value
        for key, value in backup_data.items()
        if key not in {"integrity_hashes", "integrity_hash"}
    }
    if legacy_writer_payload:
        candidates.add(_hash_payload(legacy_writer_payload))

    # legacy backup verifier payload (exclude integrity_hash)
    legacy_verify_payload = {
        key: value for key, value in backup_data.items() if key != "integrity_hash"
    }
    if legacy_verify_payload:
        candidates.add(_hash_payload(legacy_verify_payload))

    return candidates

