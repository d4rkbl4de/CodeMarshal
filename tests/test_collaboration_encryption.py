from collaboration.encryption import CRYPTO_AVAILABLE, EncryptionService


def _require_crypto() -> None:
    assert (
        CRYPTO_AVAILABLE
    ), "cryptography dependency is required for collaboration encryption tests"


def test_encryption_roundtrip(tmp_path) -> None:
    _require_crypto()
    service = EncryptionService(storage_root=tmp_path / "storage")
    metadata = service.initialize_workspace_key("strong-passphrase", "default")

    assert metadata.workspace_id == "default"
    assert service.is_unlocked("default") is True

    envelope = service.encrypt_json(
        {"hello": "world"},
        context="share:test",
        workspace_id="default",
    )
    payload = service.decrypt_json(
        envelope,
        context="share:test",
        workspace_id="default",
    )
    assert payload == {"hello": "world"}


def test_unlock_with_invalid_passphrase_fails(tmp_path) -> None:
    _require_crypto()
    service = EncryptionService(storage_root=tmp_path / "storage")
    service.initialize_workspace_key("strong-passphrase", "default")

    # New instance simulates a fresh process without in-memory unlocked key.
    service2 = EncryptionService(storage_root=tmp_path / "storage")
    assert service2.unlock_workspace("wrong-passphrase", "default") is False
