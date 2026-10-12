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


type Operation = Noop | CreateLink | BackupAndLink | ReplaceLink | Skip


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
        case _:
            typing.assert_never(op)
