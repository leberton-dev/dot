from enum import auto, Enum
from pathlib import Path
import shutil
from typing import cast
import tomlkit

from dot.cli import CliArgs
from dot.config import Config
from dot.link_state import LinkState, get_link_state


def has_package_manager(manager: str) -> bool:
    return shutil.which(manager) is not None


def status(config: Config, args: CliArgs) -> None:
    profile = config["profiles"].get(args.profile)
    if profile is None:
        print("error: profile not found")
        exit(1)

    dotfiles_dir = Path(args.config).parent.expanduser().resolve()
    lines = [f"On profile: {args.profile}", ""]
    changes_base = 'Changes to apply:\n  (use "dot install" to apply)'
    changes: list[str] = []
    correct = 0

    for module in profile["modules"]:
        for link in config["modules"][module]["links"]:
            source = dotfiles_dir / link["source"]
            dest = Path(link["dest"]).expanduser()
            state = get_link_state(source, dest)
            if state == LinkState.linked:
                correct += 1
                continue
            if changes_base not in changes:
                changes.append(changes_base)
            changes.append(f"        {state.name:<10}: {dest}")

    if not changes:
        lines.append("You are up to date with all links")
    else:
        lines.extend(changes)
    lines.append(f"\nUp to date: {correct} links")

    for line in lines:
        print(line)


# LOG_FILE_DIR: str = "~/.local/state/dot"
# LOG_FILE: str = f"{LOG_FILE_DIR}/dot.log"


class DotLogger:
    @staticmethod
    def error(command: str, cause: str) -> None:
        line = f"{command}.error: {cause}"
        print(line)
        # DotLogger.log_to_file(line, LOG_FILE)

    @staticmethod
    def debug(module: str, dest: str, state: LinkState, action: str) -> None:
        line = f"{f'{module}:':<10}{dest:<50} state={state.name} -> {action}"
        print(f"[DEBUG] {line}")
        # DotLogger.log_to_file(line, LOG_FILE)

    # @staticmethod
    # def log_to_file(line: str, file: str) -> None:
    #     t = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    #     complete_line = t + " " + line
    #     with open(file, "a") as f:
    #         _ = f.write(complete_line)


STATE_FILE_DIR: str = "~/.local/state/dot"
STATE_FILE: str = f"{STATE_FILE_DIR}/dot_state.toml"


class LinkAction(Enum):
    created = auto()
    backed_up = auto()
    replaced = auto()


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


def statefile_save_with_reset(
    installed: bool,
    action: LinkAction,
    source: str,
    dest: str,
    backed_up: str | None = None,
    replaced: str | None = None,
) -> bool:
    if not installed:
        installed = True
        StateFile.reset_actions()
    StateFile.save_state(action, source, dest, backup=backed_up, old_target=replaced)
    return installed


def install(config: Config, args: CliArgs) -> None:
    profile = config["profiles"].get(args.profile)
    if profile is None:
        DotLogger.error("commands.install", "profile not found")
        exit(1)

    dotfiles_dir = Path(args.config).parent.expanduser().resolve()
    print(f"[DEBUG] profile={args.profile}, dotfiles_dir={dotfiles_dir}")
    installed = False

    for module in profile["modules"]:
        for link in config["modules"][module]["links"]:
            source = dotfiles_dir / link["source"]
            dest = Path(link["dest"]).expanduser()
            state = get_link_state(source, dest)

            if not source.exists():
                DotLogger.error(
                    "commands.install",
                    f"{source} does not exist cannot perform link to {dest}",
                )
                continue

            if state == LinkState.linked:
                DotLogger.debug(module, str(dest), state, "nothing to do")

            elif state == LinkState.missing:
                DotLogger.debug(module, str(dest), state, f"create link to {source}")
                dest.parent.mkdir(exist_ok=True, parents=True)
                dest.symlink_to(source)
                installed = statefile_save_with_reset(
                    installed, LinkAction.created, str(source), str(dest)
                )

            elif state == LinkState.conflict:
                backup = Path(str(dest) + ".bak")
                DotLogger.debug(module, str(dest), state, f"backup to {backup}")

                if backup.exists() or backup.is_symlink():
                    DotLogger.error(
                        "commands.install", f"backup already exists at {backup}"
                    )
                    continue

                _ = dest.rename(backup)
                dest.symlink_to(source)
                installed = statefile_save_with_reset(
                    installed,
                    LinkAction.backed_up,
                    str(source),
                    str(dest),
                    backed_up=str(backup),
                )

            elif state in [LinkState.dangling, LinkState.wrong_target]:
                DotLogger.debug(
                    module, str(dest), state, f"unlink then link to {source}"
                )
                old_target = dest.readlink()
                dest.unlink()
                dest.symlink_to(source)
                installed = statefile_save_with_reset(
                    installed,
                    LinkAction.replaced,
                    str(source),
                    str(dest),
                    replaced=str(old_target),
                )

            else:
                print("error: something went wrog linking")
