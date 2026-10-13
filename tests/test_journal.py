from pathlib import Path

import pytest

from dot.domain.model import Link
from dot.domain.operations import BackupAndLink, CreateLink, ReplaceLink
from dot.errors import (
    StateFileMissingKeyError,
    StateFileSyntaxError,
    StateFileUnknownActionError,
)
from dot.infra.journal import Journal

LINK = Link(module="git", source=Path("/fake/dotfiles/rc"), dest=Path("/fake/home/.rc"))
CREATE = CreateLink(LINK)
BACKUP = BackupAndLink(LINK, backup=Path("/fake/home/.rc.bak"))
REPLACE = ReplaceLink(LINK, old_target=Path("/old/target"))


@pytest.fixture
def path(tmp_path: Path) -> Path:
    return tmp_path / "state" / "dot_state.toml"


def _record_session(path: Path, *ops: CreateLink | BackupAndLink | ReplaceLink) -> None:
    journal = Journal(path)
    journal.begin("install")
    for op in ops:
        journal.record(op)
    journal.commit()


def test_read_last_returns_none_without_file(path: Path) -> None:
    assert Journal(path).read_last() is None


def test_records_operations_in_order(path: Path) -> None:
    _record_session(path, REPLACE, CREATE, BACKUP)
    session = Journal(path).read_last()
    assert session is not None
    assert session.operations == (REPLACE, CREATE, BACKUP)


def test_roundtrip_keeps_every_operation_type(path: Path) -> None:
    _record_session(path, CREATE, BACKUP, REPLACE)
    session = Journal(path).read_last()
    assert session is not None
    created, backed_up, replaced = session.operations
    assert created == CREATE
    assert backed_up == BACKUP
    assert replaced == REPLACE


def test_commit_marks_session_complete(path: Path) -> None:
    _record_session(path, CREATE)
    session = Journal(path).read_last()
    assert session is not None
    assert session.complete is True
    assert session.command == "install"


def test_uncommitted_session_is_incomplete(path: Path) -> None:
    journal = Journal(path)
    journal.begin("install")
    journal.record(CREATE)
    # no commit: simulates a crash in the middle of an install
    session = Journal(path).read_last()
    assert session is not None
    assert session.complete is False
    assert session.operations == (CREATE,)


def test_session_without_operations_keeps_previous(path: Path) -> None:
    _record_session(path, CREATE)
    _record_session(path)
    session = Journal(path).read_last()
    assert session is not None
    assert session.operations == (CREATE,)


def test_new_session_replaces_previous_on_first_record(path: Path) -> None:
    _record_session(path, CREATE, BACKUP)
    _record_session(path, REPLACE)
    session = Journal(path).read_last()
    assert session is not None
    assert session.operations == (REPLACE,)


def test_no_temp_file_left_behind(path: Path) -> None:
    _record_session(path, CREATE, BACKUP)
    assert [p.name for p in path.parent.iterdir()] == [path.name]


def test_unknown_operation_type_raises(path: Path) -> None:
    path.parent.mkdir(parents=True)
    _ = path.write_text("""
command = "install"
complete = true

[[operations]]
type = "foo"
module = "git"
source = "/s"
dest = "/d"
""")
    with pytest.raises(StateFileUnknownActionError) as err:
        _ = Journal(path).read_last()
    assert err.value.path == "state.operations[0].type"


def test_missing_field_raises(path: Path) -> None:
    path.parent.mkdir(parents=True)
    _ = path.write_text("""
command = "install"
complete = true

[[operations]]
type = "create_link"
module = "git"
source = "/s"
""")
    with pytest.raises(StateFileMissingKeyError) as err:
        _ = Journal(path).read_last()
    assert err.value.path == "state.operations[0]"
    assert err.value.missing == "dest"


def test_corrupt_file_raises_syntax_error(path: Path) -> None:
    path.parent.mkdir(parents=True)
    _ = path.write_text("command = [\n")
    with pytest.raises(StateFileSyntaxError) as err:
        _ = Journal(path).read_last()
    assert err.value.path == str(path)
