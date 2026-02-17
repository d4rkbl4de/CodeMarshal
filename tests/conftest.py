"""Pytest fixtures for repository-local temporary directories.

This overrides the default ``tmp_path`` fixture to avoid host-specific temp
directory ACL issues on some Windows environments.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def _workspace_tmp_root() -> Path:
    root = (Path(".") / ".test_tmp").resolve()
    root.mkdir(parents=True, exist_ok=True)
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def _force_workspace_tempdir(_workspace_tmp_root: Path) -> None:
    """Force tempfile APIs to use repository-local tmp root on Windows CI."""
    workspace_tmp = str(_workspace_tmp_root)
    original_tempdir = tempfile.tempdir
    original_env = {key: os.environ.get(key) for key in ("TMP", "TEMP", "TMPDIR")}

    tempfile.tempdir = workspace_tmp
    os.environ["TMP"] = workspace_tmp
    os.environ["TEMP"] = workspace_tmp
    os.environ["TMPDIR"] = workspace_tmp
    try:
        yield
    finally:
        tempfile.tempdir = original_tempdir
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture
def tmp_path(_workspace_tmp_root: Path) -> Path:
    case_dir = _workspace_tmp_root / f"case_{uuid.uuid4().hex}"
    case_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield case_dir
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)
