from pathlib import Path

from dot.cli import CliArgs
from dot.config import Config
from dot.link_state import LinkAction, LinkState
from dot.logger import DotLogger
from dot.profile import ProfileLink, get_dotfiles_path, get_profile, links_of_profile
from dot.state import StateFile


def handle_linked_state(link: ProfileLink) -> None:
    DotLogger.debug(link.module, str(link.dest), link.state, "nothing to do")


def handle_missing_state(link: ProfileLink, state_file: StateFile) -> None:
    DotLogger.debug(
        link.module, str(link.dest), link.state, f"create link to {link.source}"
    )
    link.dest.parent.mkdir(exist_ok=True, parents=True)
    link.dest.symlink_to(link.source)
    state_file.register_action(
        action=LinkAction.created, source=str(link.source), dest=str(link.dest)
    )


def handle_conflict_state(link: ProfileLink, state_file: StateFile) -> None:
    backup = Path(str(link.dest) + ".bak")
    DotLogger.debug(link.module, str(link.dest), link.state, f"backup to {backup}")

    if backup.exists() or backup.is_symlink():
        DotLogger.error("commands.install", f"backup already exists at {backup}")
        return

    _ = link.dest.rename(backup)
    link.dest.symlink_to(link.source)
    state_file.register_action(
        action=LinkAction.backed_up,
        source=str(link.source),
        dest=str(link.dest),
        backup=str(backup),
    )


def handle_dangling_wrong_target_state(link: ProfileLink, state_file: StateFile) -> None:
    DotLogger.debug(
        link.module,
        str(link.dest),
        link.state,
        f"unlink then link to {link.source}",
    )
    old_target = link.dest.readlink()
    link.dest.unlink()
    link.dest.symlink_to(link.source)
    state_file.register_action(
        action=LinkAction.replaced,
        source=str(link.source),
        dest=str(link.dest),
        old_target=str(old_target),
    )


def handle_state(link: ProfileLink, state_file: StateFile) -> None:
    if link.state == LinkState.linked:
        handle_linked_state(link)
    elif link.state == LinkState.missing:
        handle_missing_state(link, state_file)
    elif link.state == LinkState.conflict:
        handle_conflict_state(link, state_file)
    elif link.state in [LinkState.dangling, LinkState.wrong_target]:
        handle_dangling_wrong_target_state(link, state_file)
    else:
        print("error: something went wrog linking")


def install(config: Config, args: CliArgs) -> None:
    profile = get_profile("install", config, args)
    dotfiles = get_dotfiles_path(args)
    state_file = StateFile()
    DotLogger.debug_line(f"profile={args.profile}, dotfiles_dir={dotfiles}")

    for link in links_of_profile(profile, config, dotfiles):
        if not link.source.exists():
            DotLogger.error(
                "commands.install",
                f"{link.source} does not exist cannot perform link to {link.dest}",
            )
            continue
        handle_state(link, state_file)
