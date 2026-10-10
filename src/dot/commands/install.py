from pathlib import Path

from dot.cli import CliArgs
from dot.config import Config
from dot.link_state import LinkAction, LinkState
from dot.logger import DotLogger
from dot.profile import ProfileLink, get_dotfiles_path, get_profile, links_of_profile
from dot.state import StateFile


def statefile_save_with_reset(
    installed: bool,
    action: LinkAction,
    source: str,
    dest: str,
    backup: str | None = None,
    old_target: str | None = None,
) -> bool:
    if not installed:
        installed = True
        StateFile.reset_actions()
    StateFile.save_state(action, source, dest, backup=backup, old_target=old_target)
    return installed


def handle_linked_state(link: ProfileLink) -> None:
    DotLogger.debug(link.module, str(link.dest), link.state, "nothing to do")


def handle_missing_state(link: ProfileLink, installed: bool) -> bool:
    DotLogger.debug(
        link.module, str(link.dest), link.state, f"create link to {link.source}"
    )
    link.dest.parent.mkdir(exist_ok=True, parents=True)
    link.dest.symlink_to(link.source)
    return statefile_save_with_reset(
        installed, LinkAction.created, str(link.source), str(link.dest)
    )


def handle_conflict_state(link: ProfileLink, installed: bool) -> bool:
    backup = Path(str(link.dest) + ".bak")
    DotLogger.debug(link.module, str(link.dest), link.state, f"backup to {backup}")

    if backup.exists() or backup.is_symlink():
        DotLogger.error("commands.install", f"backup already exists at {backup}")
        return installed

    _ = link.dest.rename(backup)
    link.dest.symlink_to(link.source)
    return statefile_save_with_reset(
        installed,
        LinkAction.backed_up,
        str(link.source),
        str(link.dest),
        backup=str(backup),
    )


def handle_dangling_wrong_target_state(link: ProfileLink, installed: bool) -> bool:
    DotLogger.debug(
        link.module,
        str(link.dest),
        link.state,
        f"unlink then link to {link.source}",
    )
    old_target = link.dest.readlink()
    link.dest.unlink()
    link.dest.symlink_to(link.source)
    return statefile_save_with_reset(
        installed,
        LinkAction.replaced,
        str(link.source),
        str(link.dest),
        old_target=str(old_target),
    )


def handle_state(link: ProfileLink, installed: bool) -> bool:
    if link.state == LinkState.linked:
        handle_linked_state(link)
    elif link.state == LinkState.missing:
        installed = handle_missing_state(link, installed)
    elif link.state == LinkState.conflict:
        installed = handle_conflict_state(link, installed)
    elif link.state in [LinkState.dangling, LinkState.wrong_target]:
        installed = handle_dangling_wrong_target_state(link, installed)
    else:
        print("error: something went wrog linking")
    return installed



def install(config: Config, args: CliArgs) -> None:
    profile = get_profile("install", config, args)
    dotfiles = get_dotfiles_path(args)
    installed = False
    DotLogger.debug_line(f"profile={args.profile}, dotfiles_dir={dotfiles}")

    for link in links_of_profile(profile, config, dotfiles):
        if not link.source.exists():
            DotLogger.error(
                "commands.install",
                f"{link.source} does not exist cannot perform link to {link.dest}",
            )
            continue
        installed = handle_state(link, installed)
