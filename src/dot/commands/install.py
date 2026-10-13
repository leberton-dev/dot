from dot.commands._execute import execute_plan
from dot.context import Context
from dot.domain.planner import plan_install
from dot.infra.inspector import inspect_link


def install(ctx: Context) -> None:
    ctx.reporter.debug(f"profile={ctx.profile.name}, dotfiles_dir={ctx.path_dotfiles}")
    statuses = [inspect_link(link) for link in ctx.profile.links]
    ops = plan_install(statuses)
    execute_plan(ctx, ops)
