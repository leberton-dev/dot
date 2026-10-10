from pathlib import Path
from typing import cast

import tomlkit

from dot.link_state import LinkAction

STATE_FILE_DIR: str = "~/.local/state/dot"
STATE_FILE: str = f"{STATE_FILE_DIR}/dot_state.toml"


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


class StateFile:
    @staticmethod
    def save_state(
        action: LinkAction,
        source: str,
        dest: str,
        backup: str | None = None,
        old_target: str | None = None,
    ) -> None:
        data = StateFile.load()
        actions = data["actions"]
        if not isinstance(actions, list):
            raise StateFileWrongTypeError("save_state", list, type(actions))
        actions = cast(list[object], actions)
        d: dict[str, str] = {"action": action.name, "source": source, "dest": dest}
        if backup:
            d["backup"] = backup
        if old_target:
            d["old_target"] = old_target
        actions.append(d)
        data["actions"] = actions
        StateFile.save(data)

    @staticmethod
    def save(data: dict[str, object]) -> None:
        path = Path(STATE_FILE).expanduser()
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "w") as f:
            tomlkit.dump(data, f)

    @staticmethod
    def load() -> dict[str, object]:
        path = Path(STATE_FILE).expanduser()
        if not path.exists():
            return {}
        with open(path) as f:
            data = tomlkit.load(f)
        return data

    @staticmethod
    def reset_actions() -> None:
        data = StateFile.load()
        data["actions"] = []
        StateFile.save(data)
