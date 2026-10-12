from dot.context import Context
from dot.domain.link_state import LinkState
from dot.infra.inspector import inspect_link


def status(ctx: Context) -> None:
    lines = [f"On profile: {ctx.profile.name}", ""]
    changes_base = 'Changes to apply:\n  (use "dot install" to apply)'
    changes: list[str] = []
    correct = 0

    for link in ctx.profile.links:
        status = inspect_link(link)
        if status.state == LinkState.linked:
            correct += 1
            continue
        if changes_base not in changes:
            changes.append(changes_base)
        changes.append(f"        {status.state.name:<10}: {link.dest}")

    if not changes:
        lines.append("You are up to date with all links")
    else:
        lines.extend(changes)
    lines.append(f"\nUp to date: {correct} links")

    for line in lines:
        ctx.reporter.info(line)
