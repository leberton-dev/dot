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
from dot.infra.executor import apply
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


def _report_plan(ctx: Context, ops: list[Operation]) -> None:
    for op in ops:
        if isinstance(op, Skip):
            ctx.reporter.warn(f"{op.link.dest}: {op.reason}")
        elif isinstance(op, Noop):
            ctx.reporter.debug(_format(op))
        else:
            ctx.reporter.info(f"would {describe(op)}: {op.link.dest}")


def _execute_plan(ctx: Context, ops: list[Operation], state_file: StateFile) -> None:
    for op in ops:
        if isinstance(op, Skip):
            ctx.reporter.warn(f"{op.link.dest}: {op.reason}")
        else:
            ctx.reporter.debug(_format(op))
            apply(op)
            _record(state_file, op)


# INFO: This function is the only function allowed to test dry_run
def execute_plan(ctx: Context, ops: list[Operation]) -> None:
    if ctx.dry_run:
        _report_plan(ctx, ops)
        return
    state_file = StateFile(ctx.path_state)
    _execute_plan(ctx, ops, state_file)
