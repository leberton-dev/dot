import typing

from dot.context import Context
from dot.infra.inspector import inspect_link
from dot.infra.reporter import Reporter
from dot.domain.link_state import LinkState, LinkStatus, backup_path
from dot.state import StateFile, LinkAction


def _format_link(status: LinkStatus, action: str) -> str:
    return f"{f'{status.link.module}:':<10}{str(status.link.dest):<50} state={status.state.name} -> {action}"


def handle_linked_state(status: LinkStatus, reporter: Reporter) -> None:
    reporter.debug(_format_link(status, "nothing to do"))


def handle_missing_state(
    status: LinkStatus, state_file: StateFile, reporter: Reporter
) -> None:
    reporter.debug(_format_link(status, f"create link to {status.link.source}"))
    status.link.dest.parent.mkdir(exist_ok=True, parents=True)
    status.link.dest.symlink_to(status.link.source)
    state_file.register_action(
        action=LinkAction.created,
        source=str(status.link.source),
        dest=str(status.link.dest),
    )


def handle_conflict_state(
    status: LinkStatus, state_file: StateFile, reporter: Reporter
) -> None:
    backup = backup_path(status.link.dest)
    reporter.debug(_format_link(status, f"backup to {backup}"))

    if status.backup_exists:
        reporter.warn(f"backup already exists at {backup}, skipping {status.link.dest}")
        return

    _ = status.link.dest.rename(backup)
    status.link.dest.symlink_to(status.link.source)
    state_file.register_action(
        action=LinkAction.backed_up,
        source=str(status.link.source),
        dest=str(status.link.dest),
        backup=str(backup),
    )


def handle_dangling_wrong_target_state(
    status: LinkStatus, state_file: StateFile, reporter: Reporter
) -> None:
    reporter.debug(_format_link(status, f"unlink then link to {status.link.source}"))
    status.link.dest.unlink()
    status.link.dest.symlink_to(status.link.source)
    state_file.register_action(
        action=LinkAction.replaced,
        source=str(status.link.source),
        dest=str(status.link.dest),
        old_target=str(status.target),
    )


def handle_state(status: LinkStatus, state_file: StateFile, reporter: Reporter) -> None:
    match status.state:
        case LinkState.linked:
            handle_linked_state(status, reporter)
        case LinkState.missing:
            handle_missing_state(status, state_file, reporter)
        case LinkState.conflict:
            handle_conflict_state(status, state_file, reporter)
        case LinkState.dangling | LinkState.wrong_target:
            handle_dangling_wrong_target_state(status, state_file, reporter)
        case LinkState.source_missing:
            reporter.warn(
                f"{status.link.source} does not exist, skipping {status.link.dest}"
            )
        case _:
            typing.assert_never(status.state)


def install(ctx: Context) -> None:
    ctx.reporter.debug(f"profile={ctx.profile.name}, dotfiles_dir={ctx.path_dotfiles}")
    state_file = StateFile(ctx.path_state)
    for link in ctx.profile.links:
        status = inspect_link(link)
        handle_state(status, state_file, ctx.reporter)
