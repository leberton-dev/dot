from dot.cli import CliArgs
from dot.config import Config
from dot.link_state import LinkState
from dot.profile import get_dotfiles_path, get_profile, links_of_profile


def status(config: Config, args: CliArgs) -> None:
    profile = get_profile("status", config, args)
    dotfiles = get_dotfiles_path(args)
    lines = [f"On profile: {args.profile}", ""]
    changes_base = 'Changes to apply:\n  (use "dot install" to apply)'
    changes: list[str] = []
    correct = 0

    for link in links_of_profile(profile, config, dotfiles):
        if link.state == LinkState.linked:
            correct += 1
            continue
        if changes_base not in changes:
            changes.append(changes_base)
        changes.append(f"        {link.state.name:<10}: {link.dest}")

    if not changes:
        lines.append("You are up to date with all links")
    else:
        lines.extend(changes)
    lines.append(f"\nUp to date: {correct} links")

    for line in lines:
        print(line)

