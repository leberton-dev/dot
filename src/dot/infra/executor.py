import typing
from dot.domain.operations import (
    BackupAndLink,
    CreateLink,
    Operation,
    Noop,
    ReplaceLink,
    Skip,
)


def apply(op: Operation) -> None:
    match op:
        case CreateLink():
            op.link.dest.parent.mkdir(exist_ok=True, parents=True)
            op.link.dest.symlink_to(op.link.source)
        case BackupAndLink():
            _ = op.link.dest.rename(op.backup)
            op.link.dest.symlink_to(op.link.source)
        case ReplaceLink():
            op.link.dest.unlink()
            op.link.dest.symlink_to(op.link.source)
        case Noop() | Skip():
            pass
        case _:
            typing.assert_never(op)
