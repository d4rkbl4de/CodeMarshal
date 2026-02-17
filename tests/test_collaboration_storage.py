from pathlib import Path

from storage.collaboration_storage import CollaborationStorage


def test_collaboration_storage_roundtrip(tmp_path: Path) -> None:
    storage = CollaborationStorage(tmp_path / "storage")

    team = {
        "team_id": "team_test",
        "name": "Test Team",
        "created_by": "owner_1",
        "members": [],
    }
    storage.save_team(team)
    assert storage.load_team("team_test") is not None
    assert len(storage.list_teams()) == 1

    share = {
        "share_id": "share_test",
        "session_id": "session_1",
        "created_by": "owner_1",
        "targets": [{"target_type": "team", "target_id": "team_test", "permission": "read"}],
        "status": "active",
    }
    storage.save_share(share)
    assert storage.load_share("share_test") is not None
    assert len(storage.list_shares()) == 1
    assert len(storage.list_shares(team_id="team_test")) == 1

    comment = {
        "comment_id": "cmt_test",
        "share_id": "share_test",
        "author_id": "owner_1",
        "status": "active",
    }
    storage.save_comment(comment)
    assert storage.load_comment("cmt_test") is not None
    assert len(storage.list_comments(share_id="share_test")) == 1

    envelope = {"nonce_b64": "abc", "ciphertext_b64": "def"}
    storage.save_payload_envelope("share_test", envelope)
    assert storage.load_payload_envelope("share_test") is not None

    key_meta = {"workspace_id": "default", "salt_b64": "x"}
    storage.save_key_metadata("default", key_meta)
    assert storage.load_key_metadata("default") is not None

