from collaboration.comments import CommentService
from collaboration.encryption import CRYPTO_AVAILABLE, EncryptionService


def _require_crypto() -> None:
    assert (
        CRYPTO_AVAILABLE
    ), "cryptography dependency is required for collaboration comments tests"


def test_add_list_resolve_comments(tmp_path) -> None:
    _require_crypto()
    encryption = EncryptionService(storage_root=tmp_path / "storage")
    encryption.initialize_workspace_key("strong-passphrase", "default")
    comments = CommentService(
        storage_root=str(tmp_path / "storage"),
        encryption=encryption,
        workspace_id="default",
    )

    comment = comments.add_comment(
        share_id="share_1",
        author_id="user_1",
        author_name="User One",
        body="Initial comment",
    )
    assert comment.comment_id.startswith("cmt_")
    assert comment.body == "Initial comment"

    reply = comments.add_comment(
        share_id="share_1",
        author_id="user_2",
        author_name="User Two",
        body="Reply comment",
        parent_comment_id=comment.comment_id,
    )
    assert reply.parent_comment_id == comment.comment_id

    listed = comments.list_comments("share_1")
    assert len(listed) == 2
    assert listed[0].share_id == "share_1"

    resolved = comments.resolve_comment(comment.comment_id, "user_1")
    assert resolved.status == "resolved"
