"""
collaboration/encryption.py

Local workspace encryption service using passphrase-derived AES-256-GCM keys.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from storage.collaboration_storage import CollaborationStorage

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    CRYPTO_AVAILABLE = True
except Exception:  # pragma: no cover - depends on optional dependency
    AESGCM = None  # type: ignore[assignment]
    CRYPTO_AVAILABLE = False


@dataclass(frozen=True)
class EncryptionConfig:
    """Encryption configuration defaults."""

    kdf: str = "pbkdf2_sha256"
    iterations: int = 390000
    salt_bytes: int = 16
    nonce_bytes: int = 12


@dataclass(frozen=True)
class KeyMetadata:
    """Persisted key metadata for one workspace."""

    workspace_id: str
    kdf: str
    iterations: int
    salt_b64: str
    key_check_nonce_b64: str
    key_check_ciphertext_b64: str
    created_at: str
    rotated_at: str | None = None


class EncryptionService:
    """AES-256-GCM encryption service with in-memory unlocked keys."""

    def __init__(
        self,
        *,
        storage_root: str | os.PathLike[str] = "storage",
        config: EncryptionConfig | None = None,
    ) -> None:
        self.storage = CollaborationStorage(storage_root)
        self.config = config or EncryptionConfig()
        self._unlocked_keys: dict[str, bytes] = {}

    def initialize_workspace_key(
        self,
        passphrase: str,
        workspace_id: str,
    ) -> KeyMetadata:
        """Initialize workspace key metadata and unlock key in-memory."""
        self._require_crypto()
        self._validate_passphrase(passphrase)
        salt = os.urandom(self.config.salt_bytes)
        key = _derive_key(
            passphrase=passphrase,
            salt=salt,
            iterations=self.config.iterations,
        )
        key_check_nonce = os.urandom(self.config.nonce_bytes)
        key_check_ciphertext = AESGCM(key).encrypt(
            key_check_nonce,
            b"codemarshal-workspace-key-check",
            workspace_id.encode("utf-8"),
        )

        metadata = KeyMetadata(
            workspace_id=workspace_id,
            kdf=self.config.kdf,
            iterations=self.config.iterations,
            salt_b64=_b64encode(salt),
            key_check_nonce_b64=_b64encode(key_check_nonce),
            key_check_ciphertext_b64=_b64encode(key_check_ciphertext),
            created_at=_now_iso(),
            rotated_at=None,
        )
        self.storage.save_key_metadata(workspace_id, asdict(metadata))
        self._unlocked_keys[workspace_id] = key
        return metadata

    def unlock_workspace(self, passphrase: str, workspace_id: str) -> bool:
        """Unlock workspace key in memory using passphrase."""
        self._require_crypto()
        self._validate_passphrase(passphrase)
        metadata = self.storage.load_key_metadata(workspace_id)
        if not isinstance(metadata, dict):
            return False

        salt_b64 = str(metadata.get("salt_b64") or "")
        nonce_b64 = str(metadata.get("key_check_nonce_b64") or "")
        ciphertext_b64 = str(metadata.get("key_check_ciphertext_b64") or "")
        iterations = int(metadata.get("iterations") or self.config.iterations)

        if not salt_b64 or not nonce_b64 or not ciphertext_b64:
            return False

        salt = _b64decode(salt_b64)
        nonce = _b64decode(nonce_b64)
        ciphertext = _b64decode(ciphertext_b64)
        key = _derive_key(passphrase=passphrase, salt=salt, iterations=iterations)
        try:
            plaintext = AESGCM(key).decrypt(
                nonce,
                ciphertext,
                workspace_id.encode("utf-8"),
            )
        except Exception:
            return False
        if plaintext != b"codemarshal-workspace-key-check":
            return False

        self._unlocked_keys[workspace_id] = key
        return True

    def is_unlocked(self, workspace_id: str) -> bool:
        """Return whether workspace key is unlocked."""
        return workspace_id in self._unlocked_keys

    def encrypt_json(
        self,
        payload: dict[str, Any],
        *,
        context: str,
        workspace_id: str,
    ) -> dict[str, Any]:
        """Encrypt JSON payload with AES-256-GCM."""
        self._require_crypto()
        key = self._require_unlocked_key(workspace_id)
        nonce = os.urandom(self.config.nonce_bytes)
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ciphertext = AESGCM(key).encrypt(nonce, serialized, context.encode("utf-8"))
        return {
            "version": 1,
            "algorithm": "AES-256-GCM",
            "workspace_id": workspace_id,
            "context": context,
            "nonce_b64": _b64encode(nonce),
            "ciphertext_b64": _b64encode(ciphertext),
            "created_at": _now_iso(),
        }

    def decrypt_json(
        self,
        envelope: dict[str, Any],
        *,
        context: str,
        workspace_id: str,
    ) -> dict[str, Any]:
        """Decrypt JSON payload envelope."""
        self._require_crypto()
        key = self._require_unlocked_key(workspace_id)
        nonce = _b64decode(str(envelope.get("nonce_b64") or ""))
        ciphertext = _b64decode(str(envelope.get("ciphertext_b64") or ""))
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, context.encode("utf-8"))
        payload = json.loads(plaintext.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Decrypted payload must be an object")
        return payload

    def rotate_key(
        self,
        *,
        old_passphrase: str,
        new_passphrase: str,
        workspace_id: str,
    ) -> KeyMetadata:
        """Rotate workspace key metadata and replace unlocked key."""
        self._require_crypto()
        if not self.unlock_workspace(old_passphrase, workspace_id):
            raise ValueError("Unable to unlock workspace with old passphrase")
        self._validate_passphrase(new_passphrase)

        salt = os.urandom(self.config.salt_bytes)
        key = _derive_key(
            passphrase=new_passphrase,
            salt=salt,
            iterations=self.config.iterations,
        )
        key_check_nonce = os.urandom(self.config.nonce_bytes)
        key_check_ciphertext = AESGCM(key).encrypt(
            key_check_nonce,
            b"codemarshal-workspace-key-check",
            workspace_id.encode("utf-8"),
        )

        metadata = KeyMetadata(
            workspace_id=workspace_id,
            kdf=self.config.kdf,
            iterations=self.config.iterations,
            salt_b64=_b64encode(salt),
            key_check_nonce_b64=_b64encode(key_check_nonce),
            key_check_ciphertext_b64=_b64encode(key_check_ciphertext),
            created_at=_now_iso(),
            rotated_at=_now_iso(),
        )
        self.storage.save_key_metadata(workspace_id, asdict(metadata))
        self._unlocked_keys[workspace_id] = key
        return metadata

    def _require_unlocked_key(self, workspace_id: str) -> bytes:
        key = self._unlocked_keys.get(workspace_id)
        if key is None:
            raise ValueError(
                f"Workspace key is locked: {workspace_id}. Unlock with passphrase first."
            )
        return key

    @staticmethod
    def _validate_passphrase(passphrase: str) -> None:
        if len(str(passphrase or "")) < 8:
            raise ValueError("Passphrase must be at least 8 characters")

    @staticmethod
    def _require_crypto() -> None:
        if not CRYPTO_AVAILABLE:
            raise RuntimeError(
                "cryptography package is required for collaboration encryption "
                "(install with `pip install cryptography`)."
            )


def _derive_key(*, passphrase: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt,
        max(int(iterations), 1),
        dklen=32,
    )


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
