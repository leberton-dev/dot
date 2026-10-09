from pathlib import Path
import shutil

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


def _debug_action(module: str, dest: str, state: LinkState, action: str) -> None:
    print(f"[DEBUG] {f'{module}:':<10}{dest:<50} state={state.name} -> {action}")


def install(config: Config, args: CliArgs) -> None:
    profile = config["profiles"].get(args.profile)
    if profile is None:
        print("error: profile not found")
        exit(1)

    dotfiles_dir = Path(args.config).parent.expanduser().resolve()
    print(f"[DEBUG] profile={args.profile}, dotfiles_dir={dotfiles_dir}")

    for module in profile["modules"]:
        for link in config["modules"][module]["links"]:
            source = dotfiles_dir / link["source"]
            dest = Path(link["dest"]).expanduser()
            state = get_link_state(source, dest)

            if not source.exists():
                print(
                    f"commands.install.error: {source} does not exist cannot perform link to {dest}"
                )
                continue

            if state == LinkState.linked:
                _debug_action(module, str(dest), state, "nothing to do")

            elif state == LinkState.missing:
                _debug_action(module, str(dest), state, f"create link to {source}")
                dest.parent.mkdir(exist_ok=True, parents=True)
                dest.symlink_to(source)

            elif state == LinkState.conflict:
                backup = Path(str(dest) + ".bak")
                _debug_action(module, str(dest), state, f"backup to {backup}")

                if backup.exists() or backup.is_symlink():
                    print(f"commands.install.error: backup already exists at {backup}")
                    continue

                _ = dest.rename(backup)
                dest.symlink_to(source)

            elif state in [LinkState.dangling, LinkState.wrong_target]:
                _debug_action(module, str(dest), state, f"unlink then link to {source}")
                dest.unlink()
                dest.symlink_to(source)

            else:
                print("error: something went wrog linking")
