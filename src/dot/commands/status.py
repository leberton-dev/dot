from dot.context import Context
from dot.domain.operations import Noop, Operation, Skip, describe
from dot.domain.planner import plan_install
from dot.infra.inspector import inspect_link


def status(ctx: Context) -> None:
    statuses = [inspect_link(link) for link in ctx.profile.links]
    ops = plan_install(statuses)
    lines = [f"On profile: {ctx.profile.name}", ""]
    noops: list[Noop] = []
    skips: list[Skip] = []
    others: list[Operation] = []

    for op in ops:
        if isinstance(op, Noop):
            noops.append(op)
        elif isinstance(op, Skip):
            skips.append(op)
        else:
            others.append(op)

    if not others and not skips:
        lines.append("You are up to date with all links")
        lines.append("")
    if others:
        lines.append("Changes to apply:")
        lines.append('  (use "dot install" to apply)')
        for op in others:
            lines.append(f"  {op.link.dest}: {describe(op)}")
        lines.append("")
    if skips:
        lines.append("Skipped:")
        for op in skips:
            lines.append(f"  {op.link.dest}: {describe(op)}")
        lines.append("")

    lines.append(f"Up to date: {len(noops)} links")
    for line in lines:
        ctx.reporter.info(line)
