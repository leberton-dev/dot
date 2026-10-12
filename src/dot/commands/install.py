from pathlib import Path
import typing

from dot.context import Context
from dot.infra.reporter import Reporter
from dot.link_state import LinkAction, LinkState, ProfileLink, inspect_links
from dot.state import StateFile


def _format_link(link: ProfileLink, action: str) -> str:
    return f"{f'{link.module}:':<10}{str(link.dest):<50} state={link.state.name} -> {action}"


def handle_linked_state(link: ProfileLink, reporter: Reporter) -> None:
    reporter.debug(_format_link(link, "nothing to do"))


def handle_missing_state(
    link: ProfileLink, state_file: StateFile, reporter: Reporter
) -> None:
    reporter.debug(_format_link(link, f"create link to {link.source}"))
    link.dest.parent.mkdir(exist_ok=True, parents=True)
    link.dest.symlink_to(link.source)
    state_file.register_action(
        action=LinkAction.created, source=str(link.source), dest=str(link.dest)
    )


def handle_conflict_state(
    link: ProfileLink, state_file: StateFile, reporter: Reporter
) -> None:
    backup = Path(str(link.dest) + ".bak")
    reporter.debug(_format_link(link, f"backup to {backup}"))

    if backup.exists() or backup.is_symlink():
        reporter.warn(f"backup already exists at {backup}, skipping {link.dest}")
        return

    _ = link.dest.rename(backup)
    link.dest.symlink_to(link.source)
    state_file.register_action(
        action=LinkAction.backed_up,
        source=str(link.source),
        dest=str(link.dest),
        backup=str(backup),
    )


def handle_dangling_wrong_target_state(
    link: ProfileLink, state_file: StateFile, reporter: Reporter
) -> None:
    reporter.debug(_format_link(link, f"unlink then link to {link.source}"))
    old_target = link.dest.readlink()
    link.dest.unlink()
    link.dest.symlink_to(link.source)
    state_file.register_action(
        action=LinkAction.replaced,
        source=str(link.source),
        dest=str(link.dest),
        old_target=str(old_target),
    )


def handle_state(link: ProfileLink, state_file: StateFile, reporter: Reporter) -> None:
    match link.state:
        case LinkState.linked:
            handle_linked_state(link, reporter)
        case LinkState.missing:
            handle_missing_state(link, state_file, reporter)
        case LinkState.conflict:
            handle_conflict_state(link, state_file, reporter)
        case LinkState.dangling | LinkState.wrong_target:
            handle_dangling_wrong_target_state(link, state_file, reporter)
        case _:
            typing.assert_never(link.state)


def install(ctx: Context) -> None:
    ctx.reporter.debug(f"profile={ctx.profile.name}, dotfiles_dir={ctx.path_dotfiles}")
    state_file = StateFile(ctx.path_state)
    for link in inspect_links(ctx.profile.links):
        if not link.source.exists():
            ctx.reporter.warn(f"{link.source} does not exist, skipping {link.dest}")
            continue
        handle_state(link, state_file, ctx.reporter)
