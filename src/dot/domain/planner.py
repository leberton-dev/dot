from collections.abc import Iterable, Sequence
import typing

from dot.domain.link_state import LinkState, LinkStatus, backup_path
from dot.domain.operations import (
    BackupAndLink,
    Change,
    CreateLink,
    Noop,
    Operation,
    RemoveLink,
    ReplaceLink,
    RestoreBackup,
    RestoreLink,
    Skip,
)


def _plan_link(status: LinkStatus) -> Operation:
    match status.state:
        case LinkState.linked:
            return Noop(status.link)
        case LinkState.missing:
            return CreateLink(status.link)
        case LinkState.conflict if status.backup_exists:
            return Skip(
                status.link, f"backup already exists at {backup_path(status.link.dest)}"
            )
        case LinkState.conflict:
            return BackupAndLink(status.link, backup=backup_path(status.link.dest))
        case LinkState.dangling | LinkState.wrong_target:
            assert status.target is not None
            return ReplaceLink(status.link, old_target=status.target)
        case LinkState.source_missing:
            return Skip(status.link, f"source {status.link.source} does not exist")
        case _:
            typing.assert_never(status.state)


def plan_install(statuses: Iterable[LinkStatus]) -> list[Operation]:
    operations: list[Operation] = []
    for status in statuses:
        operations.append(_plan_link(status))
    return operations


def _plan_undo_one(op: Change, status: LinkStatus) -> Operation:
    match op:
        case CreateLink() | BackupAndLink() | ReplaceLink() if (
            status.state != LinkState.linked
        ):
            return Skip(op.link, "changed since it was installed, leaving it as is")
        case CreateLink():
            return RemoveLink(op.link)
        case BackupAndLink():
            if status.backup_exists:
                return RestoreBackup(op.link, backup=op.backup)
            return Skip(op.link, f"backup {op.backup} is gone")
        case ReplaceLink():
            return RestoreLink(op.link, old_target=op.old_target)
        case RemoveLink() | RestoreBackup() | RestoreLink():
            return Skip(op.link, "already undone")
        case _:
            typing.assert_never(op)


def plan_undo(entries: Sequence[tuple[Change, LinkStatus]]) -> list[Operation]:
    operations: list[Operation] = []
    for op, status in reversed(entries):
        operations.append(_plan_undo_one(op, status))
    return operations
