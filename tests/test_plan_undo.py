from pathlib import Path

from dot.domain.link_state import LinkState, LinkStatus
from dot.domain.model import Link
from dot.domain.operations import (
    BackupAndLink,
    Change,
    CreateLink,
    RemoveLink,
    ReplaceLink,
    RestoreBackup,
    RestoreLink,
    Skip,
    describe,
)
from dot.domain.planner import plan_undo

LINK = Link(module="test", source=Path("/fake/dotfiles/rc"), dest=Path("/fake/home/.rc"))
BACKUP = Path("/fake/home/.rc.bak")
OLD_TARGET = Path("/old/target")


def _status(
    op: Change, state: LinkState = LinkState.linked, backup_exists: bool = False
) -> LinkStatus:
    return LinkStatus(
        link=op.link, state=state, target=op.link.source, backup_exists=backup_exists
    )


def _linked(op: Change, backup_exists: bool = False) -> tuple[Change, LinkStatus]:
    return op, _status(op, backup_exists=backup_exists)


def test_created_link_is_removed() -> None:
    assert plan_undo([_linked(CreateLink(LINK))]) == [RemoveLink(LINK)]


def test_backup_is_restored() -> None:
    op = BackupAndLink(LINK, backup=BACKUP)
    assert plan_undo([_linked(op, backup_exists=True)]) == [
        RestoreBackup(LINK, backup=BACKUP)
    ]


def test_missing_backup_is_skipped() -> None:
    op = BackupAndLink(LINK, backup=BACKUP)
    ops = plan_undo([_linked(op, backup_exists=False)])
    assert len(ops) == 1
    skip = ops[0]
    assert isinstance(skip, Skip)
    assert "is gone" in skip.reason


def test_replaced_link_is_restored() -> None:
    op = ReplaceLink(LINK, old_target=OLD_TARGET)
    assert plan_undo([_linked(op)]) == [RestoreLink(LINK, old_target=OLD_TARGET)]


def test_link_changed_by_user_is_skipped() -> None:
    op = CreateLink(LINK)
    ops = plan_undo([(op, _status(op, state=LinkState.conflict))])
    assert len(ops) == 1
    skip = ops[0]
    assert isinstance(skip, Skip)
    assert "changed since" in skip.reason


def test_changed_backup_link_is_skipped_even_with_backup() -> None:
    # the user replaced our link: restoring the backup would overwrite their file
    op = BackupAndLink(LINK, backup=BACKUP)
    status = _status(op, state=LinkState.conflict, backup_exists=True)
    ops = plan_undo([(op, status)])
    skip = ops[0]
    assert isinstance(skip, Skip)
    assert "changed since" in skip.reason


def test_undo_operations_are_skipped() -> None:
    ops = plan_undo([_linked(RemoveLink(LINK))])
    assert len(ops) == 1
    skip = ops[0]
    assert isinstance(skip, Skip)
    assert "already undone" in skip.reason


def test_operations_are_undone_in_reverse_order() -> None:
    dests = [Path("/fake/home/.a"), Path("/fake/home/.b"), Path("/fake/home/.c")]
    entries = [
        _linked(CreateLink(Link("test", Path("/fake/dotfiles/x"), dest)))
        for dest in dests
    ]
    assert [op.link.dest for op in plan_undo(entries)] == list(reversed(dests))


def test_empty_journal_gives_empty_plan() -> None:
    assert plan_undo([]) == []


def test_describe_undo_operations() -> None:
    assert describe(RemoveLink(LINK)) == "remove link to /fake/dotfiles/rc"
    assert (
        describe(RestoreBackup(LINK, backup=BACKUP))
        == "restore /fake/home/.rc.bak in place of the link"
    )
    assert (
        describe(RestoreLink(LINK, old_target=OLD_TARGET))
        == "restore link to /old/target"
    )
