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
from dot.infra.journal import Journal


def _format(op: Operation) -> str:
    return f"{f'{op.link.module}:':<10}{str(op.link.dest):<50} {describe(op)}"


def _report_plan(ctx: Context, ops: list[Operation]) -> None:
    for op in ops:
        if isinstance(op, Skip):
            ctx.reporter.warn(f"{op.link.dest}: {op.reason}")
        elif isinstance(op, Noop):
            ctx.reporter.debug(_format(op))
        else:
            ctx.reporter.info(f"would {describe(op)}: {op.link.dest}")


def _execute_plan(ctx: Context, command: str, ops: list[Operation], journal: Journal) -> None:
    journal.begin(command)
    for op in ops:
        match op:
            case Skip():
                ctx.reporter.warn(f"{op.link.dest}: {op.reason}")
            case Noop():
                ctx.reporter.debug(_format(op))
            case CreateLink() | BackupAndLink() | ReplaceLink():
                ctx.reporter.debug(_format(op))
                apply(op)
                journal.record(op)
            case _:
                typing.assert_never(op)
    journal.commit()


# INFO: This function is the only function allowed to test dry_run
def execute_plan(ctx: Context, command: str, ops: list[Operation]) -> None:
    if ctx.dry_run:
        _report_plan(ctx, ops)
        return
    journal = Journal(ctx.path_state)
    _execute_plan(ctx, command, ops, journal)
