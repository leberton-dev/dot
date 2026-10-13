from dataclasses import dataclass
import os
from pathlib import Path
import tomllib
import tomlkit
import typing

from dot.domain.model import Link
from dot.errors import (
    StateFileMissingKeyError,
    StateFileSyntaxError,
    StateFileUnknownActionError,
    StateFileWrongTypeError,
)
from dot.domain.operations import BackupAndLink, Change, CreateLink, ReplaceLink


def _to_dict(op: Change) -> dict[str, str]:
    match op:
        case CreateLink():
            return {
                "type": "create_link",
                "module": op.link.module,
                "source": str(op.link.source),
                "dest": str(op.link.dest),
            }
        case BackupAndLink():
            return {
                "type": "backup_and_link",
                "module": op.link.module,
                "source": str(op.link.source),
                "dest": str(op.link.dest),
                "backup": str(op.backup),
            }
        case ReplaceLink():
            return {
                "type": "replace_link",
                "module": op.link.module,
                "source": str(op.link.source),
                "dest": str(op.link.dest),
                "old_target": str(op.old_target),
            }
        case _:
            typing.assert_never(op)


def _from_dict(raw: object, path: str) -> Change:
    if not isinstance(raw, dict):
        raise StateFileWrongTypeError(path, dict, type(raw))
    op = typing.cast(dict[str, object], raw)

    link = Link(
        module=_get_str(op, "module", path),
        source=Path(_get_str(op, "source", path)),
        dest=Path(_get_str(op, "dest", path)),
    )

    kind = _get_str(op, "type", path)
    match kind:
        case "create_link":
            return CreateLink(link)
        case "backup_and_link":
            return BackupAndLink(link, backup=Path(_get_str(op, "backup", path)))
        case "replace_link":
            return ReplaceLink(link, old_target=Path(_get_str(op, "old_target", path)))
        case _:
            raise StateFileUnknownActionError(f"{path}.type", kind)


def _get_str(raw: dict[str, object], key: str, path: str) -> str:
    if key not in raw:
        raise StateFileMissingKeyError(path, key)
    value = raw[key]
    if not isinstance(value, str):
        raise StateFileWrongTypeError(f"{path}.{key}", str, type(value))
    return value


def _get_bool(raw: dict[str, object], key: str, path: str) -> bool:
    if key not in raw:
        raise StateFileMissingKeyError(path, key)
    value = raw[key]
    if not isinstance(value, bool):
        raise StateFileWrongTypeError(f"{path}.{key}", bool, type(value))
    return value


def _get_list(raw: dict[str, object], key: str, path: str) -> list[object]:
    if key not in raw:
        raise StateFileMissingKeyError(path, key)
    value = raw[key]
    if not isinstance(value, list):
        raise StateFileWrongTypeError(f"{path}.{key}", list, type(value))
    return typing.cast(list[object], value)


@dataclass(frozen=True)
class Session:
    command: str
    complete: bool
    operations: tuple[Change, ...]


class Journal:
    """Write-ahead log of filesystem changes, persisted as TOML for crash recovery."""

    def __init__(self, path: Path) -> None:
        self._path: Path = path
        self._command: str | None = None
        self._operations: list[Change] = []

    def begin(self, command: str) -> None:
        """Open a new session for `command`, discarding any operations held in memory."""
        assert self._command is None, "begin() called while a session is already open"
        self._command = command
        self._operations = []

    def record(self, op: Change) -> None:
        """Append `op` to the current session and flush it to disk as incomplete."""
        assert self._command is not None, "record() called without begin()"
        self._operations.append(op)
        self._write(self._command, complete=False)

    def commit(self) -> None:
        """Mark the current session complete and close it.

        If no operation was recorded, the file on disk is left untouched.
        """
        assert self._command is not None, "commit() called without begin()"
        if self._operations:
            self._write(self._command, complete=True)
        self._command = None
        self._operations = []

    def _write(self, command: str, complete: bool) -> None:
        """Atomically write the current session to disk via a temp file and rename."""
        data = {
            "command": command,
            "complete": complete,
            "operations": [_to_dict(op) for op in self._operations],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            tomlkit.dump(data, f)
        os.replace(tmp, self._path)

    def read_last(self) -> Session | None:
        """Load the last session from disk, or None if no journal exists.

        Raises StateFileError subclasses if the file is malformed.
        """
        if not self._path.exists():
            return None

        with open(self._path, "rb") as f:
            try:
                data = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise StateFileSyntaxError(str(self._path), str(e)) from None

        command = _get_str(data, "command", "state")
        complete = _get_bool(data, "complete", "state")
        ops = _get_list(data, "operations", "state")

        operations: list[Change] = []
        for i, raw in enumerate(ops):
            operations.append(_from_dict(raw, f"state.operations[{i}]"))

        return Session(command=command, complete=complete, operations=tuple(operations))
