import typing

from dataclasses import dataclass
from pathlib import Path

from dot.domain.model import Link


@dataclass(frozen=True)
class Noop:
    link: Link


@dataclass(frozen=True)
class CreateLink:
    link: Link


@dataclass(frozen=True)
class BackupAndLink:
    link: Link
    backup: Path


@dataclass(frozen=True)
class ReplaceLink:
    link: Link
    old_target: Path


@dataclass(frozen=True)
class Skip:
    link: Link
    reason: str


@dataclass(frozen=True)
class RemoveLink:
    link: Link


@dataclass(frozen=True)
class RestoreBackup:
    link: Link
    backup: Path


@dataclass(frozen=True)
class RestoreLink:
    link: Link
    old_target: Path


type InstallChange = CreateLink | BackupAndLink | ReplaceLink
type UndoChange = RemoveLink | RestoreBackup | RestoreLink
type Change = InstallChange | UndoChange
type Operation = Noop | Skip | Change


def describe(op: Operation) -> str:
    match op:
        case Noop():
            return "nothing to do"
        case CreateLink():
            return f"create link to {op.link.source}"
        case BackupAndLink():
            return f"backup to {op.backup}, then link to {op.link.source}"
        case ReplaceLink():
            return f"replace link to {op.old_target} with link to {op.link.source}"
        case Skip():
            return f"skip: {op.reason}"
        case RemoveLink():
            return f"remove link to {op.link.source}"
        case RestoreBackup():
            return f"restore {op.backup} in place of the link"
        case RestoreLink():
            return f"restore link to {op.old_target}"
        case _:
            typing.assert_never(op)
