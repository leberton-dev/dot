from collections.abc import Iterable
import typing

from dot.domain.link_state import LinkState, LinkStatus, backup_path
from dot.domain.operations import (
    BackupAndLink,
    CreateLink,
    Noop,
    Operation,
    ReplaceLink,
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
