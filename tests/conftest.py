"""Pytest fixtures for repository-local temporary directories.

This overrides the default ``tmp_path`` fixture to avoid host-specific temp
directory ACL issues on some Windows environments.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def _workspace_tmp_root() -> Path:
    root = (Path(".") / ".test_tmp").resolve()
    root.mkdir(parents=True, exist_ok=True)
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def tmp_path(_workspace_tmp_root: Path) -> Path:
    case_dir = _workspace_tmp_root / f"case_{uuid.uuid4().hex}"
    case_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield case_dir
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)

