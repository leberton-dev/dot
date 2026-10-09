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

    dotfiles_dir = Path(args.config).parent.expanduser()
    lines = [f"On profile: {args.profile}", ""]
    changes_base = 'Changes to apply:\n  (use "dot link" to apply)'
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
