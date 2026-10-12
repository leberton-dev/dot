from dot.context import Context
from dot.link_state import LinkState
from dot.profile import links_of_profile


def status(ctx: Context) -> None:
    lines = [f"On profile: {ctx.profile_name}", ""]
    changes_base = 'Changes to apply:\n  (use "dot install" to apply)'
    changes: list[str] = []
    correct = 0

    for link in links_of_profile(ctx.profile, ctx.config, ctx.path_dotfiles, ctx.path_home):
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
        ctx.reporter.info(line)
