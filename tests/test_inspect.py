from pathlib import Path

import pytest

from dot.domain.link_state import LinkState, backup_path
from dot.domain.model import Link
from dot.infra.inspector import inspect_link


@pytest.fixture
def source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    _ = source.write_text("SOURCE")
    return source


@pytest.fixture
def dest(tmp_path: Path) -> Path:
    return tmp_path / "dest"


def _link(source: Path, dest: Path) -> Link:
    return Link(module="test", source=source, dest=dest)


def test_missing_when_dest_absent(source: Path, dest: Path) -> None:
    status = inspect_link(_link(source, dest))
    assert status.state == LinkState.missing
    assert status.target is None


def test_conflict_when_dest_is_real_file(source: Path, dest: Path) -> None:
    _ = dest.write_text("REAL")
    status = inspect_link(_link(source, dest))
    assert status.state == LinkState.conflict
    assert status.target is None


def test_conflict_when_dest_is_real_directory(source: Path, dest: Path) -> None:
    dest.mkdir()
    status = inspect_link(_link(source, dest))
    assert status.state == LinkState.conflict


def test_dangling_when_symlink_target_missing(
    source: Path, dest: Path, tmp_path: Path
) -> None:
    dest.symlink_to(tmp_path / "nowhere")
    status = inspect_link(_link(source, dest))
    assert status.state == LinkState.dangling


def test_wrong_target_when_symlink_points_elsewhere(
    source: Path, dest: Path, tmp_path: Path
) -> None:
    other = tmp_path / "other"
    _ = other.write_text("OTHER")
    dest.symlink_to(other)
    status = inspect_link(_link(source, dest))
    assert status.state == LinkState.wrong_target


def test_linked_when_symlink_points_to_source(source: Path, dest: Path) -> None:
    dest.symlink_to(source)
    status = inspect_link(_link(source, dest))
    assert status.state == LinkState.linked


def test_linked_when_symlink_target_is_relative(source: Path, dest: Path) -> None:
    # source and dest share a directory, so "source" is a valid relative target
    dest.symlink_to(source.name)
    status = inspect_link(_link(source, dest))
    assert status.state == LinkState.linked


def test_source_missing_wins_over_dest_state(tmp_path: Path, dest: Path) -> None:
    _ = dest.write_text("REAL")
    status = inspect_link(_link(tmp_path / "no-source", dest))
    assert status.state == LinkState.source_missing


def test_target_is_captured_for_symlinks(
    source: Path, dest: Path, tmp_path: Path
) -> None:
    other = tmp_path / "other"
    _ = other.write_text("OTHER")
    dest.symlink_to(other)
    status = inspect_link(_link(source, dest))
    assert status.target == other


def test_backup_exists_is_detected(source: Path, dest: Path) -> None:
    _ = dest.write_text("REAL")
    _ = backup_path(dest).write_text("OLD BACKUP")
    status = inspect_link(_link(source, dest))
    assert status.backup_exists is True


def test_backup_exists_is_false_without_backup(source: Path, dest: Path) -> None:
    _ = dest.write_text("REAL")
    status = inspect_link(_link(source, dest))
    assert status.backup_exists is False


def test_dangling_backup_counts_as_existing(
    source: Path, dest: Path, tmp_path: Path
) -> None:
    _ = dest.write_text("REAL")
    backup_path(dest).symlink_to(tmp_path / "nowhere")
    status = inspect_link(_link(source, dest))
    assert status.backup_exists is True


def test_backup_path_appends_bak() -> None:
    assert backup_path(Path("/fake/.gitconfig")) == Path("/fake/.gitconfig.bak")
    assert backup_path(Path("/fake/.config/nvim")) == Path("/fake/.config/nvim.bak")
