# Collaboration Guide

CodeMarshal collaboration is local-first and encrypted-at-rest for shared payloads and comments.

## Prerequisites

- Install dependencies:

```bash
python -m pip install -e .
```

- Export a passphrase environment variable (example in PowerShell):

```bash
$env:CM_PASS = "strong-passphrase"
```

## 1. Initialize or Unlock Workspace Key

Run once for a new workspace (`--initialize`), then unlock on future sessions.

```bash
codemarshal team unlock --workspace-id default --passphrase-env CM_PASS --initialize
codemarshal team unlock --workspace-id default --passphrase-env CM_PASS
```

## 2. Manage Teams

```bash
codemarshal team create "Alpha Team" --owner-id owner_1 --owner-name "Owner One"
codemarshal team add <team_id> user_2 --name "User Two" --role member --by owner_1
codemarshal team list --limit 50
```

Roles: `owner`, `maintainer`, `member`, `viewer`.

## 3. Share Investigation Artifacts

Create encrypted shares for users or teams:

```bash
codemarshal share create <session_id> \
  --by owner_1 \
  --target-team <team_id> \
  --permission read \
  --title "Architecture review" \
  --summary "Initial findings" \
  --workspace-id default \
  --passphrase-env CM_PASS
```

List/revoke/resolve:

```bash
codemarshal share list --session-id <session_id>
codemarshal share revoke <share_id> --by owner_1
codemarshal share resolve <share_id> --accessor <team_id> --workspace-id default --passphrase-env CM_PASS
```

## 4. Comment Threads

Add, list, and resolve encrypted comments:

```bash
codemarshal comment add <share_id> --by owner_1 --name "Owner One" --body "Please verify module boundaries." --passphrase-env CM_PASS
codemarshal comment list <share_id> --passphrase-env CM_PASS
codemarshal comment resolve <comment_id> --by owner_1 --passphrase-env CM_PASS
```

Reply in a thread using `--parent <comment_id>` when adding a comment.

## Notes

- If passphrase env var is missing/empty, commands refuse to run.
- If workspace key metadata is missing and `--initialize` is not set, unlock fails with a clear error.
- Collaboration data is stored under `storage/collaboration/`.
