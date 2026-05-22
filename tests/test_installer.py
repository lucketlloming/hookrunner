"""Tests for hookrunner.installer."""

import stat
from pathlib import Path

import pytest

from hookrunner.installer import (
    InstallerError,
    install_hook,
    is_installed,
    uninstall_hook,
    MANAGED_MARKER,
)


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Create a minimal fake git repo with a hooks directory."""
    hooks_dir = tmp_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    return tmp_path


def test_install_hook_creates_file(fake_repo):
    hook_path = install_hook("pre-commit", repo_root=fake_repo)
    assert hook_path.exists()
    assert MANAGED_MARKER in hook_path.read_text()
    assert "hookrunner run pre-commit" in hook_path.read_text()


def test_install_hook_is_executable(fake_repo):
    hook_path = install_hook("pre-push", repo_root=fake_repo)
    mode = hook_path.stat().st_mode
    assert mode & stat.S_IXUSR, "Hook should be executable by owner"


def test_install_hook_overwrites_managed(fake_repo):
    hook_path = install_hook("pre-commit", repo_root=fake_repo)
    first_content = hook_path.read_text()
    hook_path2 = install_hook("pre-commit", repo_root=fake_repo)
    assert hook_path == hook_path2
    assert hook_path.read_text() == first_content


def test_install_hook_refuses_unmanaged(fake_repo):
    hook_path = fake_repo / ".git" / "hooks" / "pre-commit"
    hook_path.write_text("#!/bin/sh\necho 'custom hook'\n")
    with pytest.raises(InstallerError, match="not managed by hookrunner"):
        install_hook("pre-commit", repo_root=fake_repo)


def test_install_hook_missing_hooks_dir(tmp_path):
    with pytest.raises(InstallerError, match="Git hooks directory not found"):
        install_hook("pre-commit", repo_root=tmp_path)


def test_uninstall_hook_removes_file(fake_repo):
    install_hook("commit-msg", repo_root=fake_repo)
    removed = uninstall_hook("commit-msg", repo_root=fake_repo)
    assert removed is True
    assert not (fake_repo / ".git" / "hooks" / "commit-msg").exists()


def test_uninstall_hook_returns_false_when_missing(fake_repo):
    result = uninstall_hook("pre-commit", repo_root=fake_repo)
    assert result is False


def test_uninstall_hook_refuses_unmanaged(fake_repo):
    hook_path = fake_repo / ".git" / "hooks" / "pre-commit"
    hook_path.write_text("#!/bin/sh\necho hi\n")
    with pytest.raises(InstallerError, match="not managed by hookrunner"):
        uninstall_hook("pre-commit", repo_root=fake_repo)


def test_is_installed_true(fake_repo):
    install_hook("pre-commit", repo_root=fake_repo)
    assert is_installed("pre-commit", repo_root=fake_repo) is True


def test_is_installed_false_missing(fake_repo):
    assert is_installed("pre-commit", repo_root=fake_repo) is False


def test_is_installed_false_unmanaged(fake_repo):
    hook_path = fake_repo / ".git" / "hooks" / "pre-commit"
    hook_path.write_text("#!/bin/sh\necho hi\n")
    assert is_installed("pre-commit", repo_root=fake_repo) is False
