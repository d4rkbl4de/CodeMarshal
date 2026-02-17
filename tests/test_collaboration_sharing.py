from collaboration.encryption import CRYPTO_AVAILABLE, EncryptionService
from collaboration.sharing import SharePermission, ShareTarget, SharingService


def _require_crypto() -> None:
    assert (
        CRYPTO_AVAILABLE
    ), "cryptography dependency is required for collaboration sharing tests"


def test_create_list_resolve_share(tmp_path) -> None:
    _require_crypto()
    encryption = EncryptionService(storage_root=tmp_path / "storage")
    encryption.initialize_workspace_key("strong-passphrase", "default")

    service = SharingService(
        storage_root=str(tmp_path / "storage"),
        encryption=encryption,
        workspace_id="default",
    )
    artifact = service.create_share(
        session_id="session_1",
        created_by="owner_1",
        targets=[
            ShareTarget(
                target_type="team",
                target_id="team_1",
                permission=SharePermission.READ,
            )
        ],
        title="Review Session",
        summary="Please review this session",
    )

    assert artifact.share_id.startswith("share_")
    assert artifact.status == "active"
    shares = service.list_shares()
    assert len(shares) == 1

    payload = service.resolve_share_payload(artifact.share_id, "team_1")
    assert payload.get("session_id") == "session_1"
