import typing
from dot.context import Context
from dot.domain.operations import (
    BackupAndLink,
    CreateLink,
    Noop,
    Operation,
    ReplaceLink,
    Skip,
    describe,
)
from dot.domain.planner import plan_install
from dot.infra.executor import apply
from dot.infra.inspector import inspect_link
from dot.state import LinkAction, StateFile


def _format(op: Operation) -> str:
    return f"{f'{op.link.module}:':<10}{str(op.link.dest):<50} {describe(op)}"


def _record(state_file: StateFile, op: Operation) -> None:
    match op:
        case CreateLink():
            state_file.register_action(
                action=LinkAction.created,
                source=str(op.link.source),
                dest=str(op.link.dest),
            )
        case BackupAndLink():
            state_file.register_action(
                action=LinkAction.backed_up,
                source=str(op.link.source),
                dest=str(op.link.dest),
                backup=str(op.backup),
            )
        case ReplaceLink():
            state_file.register_action(
                action=LinkAction.replaced,
                source=str(op.link.source),
                dest=str(op.link.dest),
                old_target=str(op.old_target),
            )
        case Noop() | Skip():
            pass
        case _:
            typing.assert_never(op)


def install(ctx: Context) -> None:
    ctx.reporter.debug(f"profile={ctx.profile.name}, dotfiles_dir={ctx.path_dotfiles}")
    statuses = [inspect_link(link) for link in ctx.profile.links]
    ops = plan_install(statuses)
    state_file = StateFile(ctx.path_state)
    for op in ops:
        if isinstance(op, Skip):
            ctx.reporter.warn(f"{op.link.dest}: {op.reason}")
        else:
            ctx.reporter.debug(_format(op))
            apply(op)
            _record(state_file, op)
