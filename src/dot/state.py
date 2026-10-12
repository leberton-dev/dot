from dataclasses import dataclass
from enum import auto, Enum
from pathlib import Path
from typing import cast

import tomlkit

from dot.errors import (
    StateFileMissingKeyError,
    StateFileUnknownActionError,
    StateFileWrongTypeError,
)


class LinkAction(Enum):
    created = auto()
    backed_up = auto()
    replaced = auto()


@dataclass(frozen=True)
class ActionEntry:
    action: LinkAction
    source: str
    dest: str
    backup: str | None = None
    old_target: str | None = None


class StateFile:
    def __init__(self, path: Path) -> None:
        self._reset_done: bool = False
        self._path: Path = path

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
        for i, raw_action in enumerate(config_actions):
            action_entry = cast(dict[str, object], raw_action)
            actions.append(self._to_action_entry(action_entry, i))
        return actions

    def _to_action_entry(self, action: dict[str, object], i: int) -> ActionEntry:
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
            raise StateFileUnknownActionError(f"actions[{i}]", "")

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
