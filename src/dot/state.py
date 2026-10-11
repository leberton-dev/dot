from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

import tomlkit

from dot.link_state import LinkAction

BASE_STATE_FILE_DIR: str = "~/.local/state/dot"
BASE_STATE_FILE: str = f"{BASE_STATE_FILE_DIR}/dot_state.toml"


class StateFileError(Exception):
    pass


class StateFileWrongTypeError(StateFileError):
    """Raised when a value has not the correct type"""

    def __init__(self, method: str, expected: type, got: type) -> None:
        self.method: str = method
        self.expected: type = expected
        self.got: type = got
        message = f"StateFile.{method}().error: expected {expected}, got {got}"
        super().__init__(message)


class StateFileMissingKeyError(StateFileError):
    """Raised when a key is missing"""

    def __init__(self, method: str, missing: str) -> None:
        self.method: str = method
        self.missing: str = missing
        message = f"{method}: missing key '{missing}'"
        super().__init__(message)


@dataclass(frozen=True)
class ActionEntry:
    action: LinkAction
    source: str
    dest: str
    backup: str | None = None
    old_target: str | None = None


class StateFile:
    def __init__(self, path: Path | None = None) -> None:
        self._reset_done: bool = False
        self._path: Path
        if path:
            self._path = path.expanduser()
        else:
            self._path = Path(BASE_STATE_FILE).expanduser()

    def register_action(
        self,
        action: LinkAction,
        source: str,
        dest: str,
        backup: str | None = None,
        old_target: str | None = None,
    ) -> None:
        data = self._load()
        if not self._reset_done:
            data["actions"] = []
            self._reset_done = True

        actions = data.get("actions", [])
        if not isinstance(actions, list):
            raise StateFileWrongTypeError("register_action", list, type(actions))
        actions = cast(list[dict[str, str]], actions)

        state = {"action": action.name, "source": source, "dest": dest}
        if backup:
            state["backup"] = backup
        if old_target:
            state["old_target"] = old_target
        actions.append(state)
        data["actions"] = actions
        self._save_data(data)

    def read_actions(self) -> list[ActionEntry]:
        actions: list[ActionEntry] = []
        raw_config_actions = self._load().get("actions", [])
        if not isinstance(raw_config_actions, list):
            raise StateFileWrongTypeError(
                "register_action", list, type(raw_config_actions)
            )
        config_actions = cast(list[dict[str, str]], raw_config_actions)

        for raw_action in config_actions:
            if not isinstance(raw_action, dict):
                raise StateFileWrongTypeError("read_actions", dict, type(raw_action))
            action_entry = cast(dict[str, object], raw_action)
            actions.append(self._to_action_entry(action_entry))
        return actions

    def _to_action_entry(self, action: dict[str, object]) -> ActionEntry:
        link_action = self._get_required_str(action, "action")
        source = self._get_required_str(action, "source")
        dest = self._get_required_str(action, "dest")
        backup = self._get_optional_str(action, "backup")
        old_target = self._get_optional_str(action, "old_target")
        try:
            return ActionEntry(
                action=LinkAction[link_action],
                source=source,
                dest=dest,
                backup=backup,
                old_target=old_target,
            )
        except KeyError:
            raise StateFileError(
                f"StateFile._get_action_entry().error: unknown action {link_action}"
            )

    def _get_optional_str(self, action: dict[str, object], name: str) -> str | None:
        entry = action.get(name)
        if entry is None:
            return None
        if not isinstance(entry, str):
            raise StateFileWrongTypeError("expected str", str, type(entry))
        return entry

    def _get_required_str(self, action: dict[str, object], name: str) -> str:
        entry = action.get(name)
        if entry is None:
            raise StateFileMissingKeyError("StateFile._get_required_str()", name)
        if not isinstance(entry, str):
            raise StateFileWrongTypeError("expected str", str, type(entry))
        return entry

    def _save_data(self, data: dict[str, object]) -> None:
        self._path.parent.mkdir(exist_ok=True, parents=True)
        with open(self._path, "w") as f:
            tomlkit.dump(data, f)

    def _load(self) -> dict[str, object]:
        if not self._path.exists():
            return {}
        with open(self._path) as f:
            data = tomlkit.load(f)
        return data
