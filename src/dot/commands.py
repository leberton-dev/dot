from pathlib import Path
import shutil

from dot.cli import CliArgs
from dot.config import Config, Profile
from dot.link_state import LinkState, get_link_state


def has_package_manager(manager: str) -> bool:
    return shutil.which(manager) is not None


def get_profile(config: Config, profile_name: str) -> tuple[Profile, str]:
    for name, profile in config["profiles"].items():
        if name == profile_name:
            return profile, name
    raise ValueError("no profile found")


def status(config: Config, args: CliArgs) -> None:
    profile, profile_name = get_profile(config, args.profile)
    dotfiles_dir = Path(args.config).parent.expanduser()
    lines = [f"On profile: {profile_name}", ""]
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
