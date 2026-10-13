import os
import sys
from collections.abc import Callable
from pathlib import Path

from dot import commands
from dot.args import CliArgs
from dot.cli import build_parser
from dot.context import Context
from dot.domain.model import Config, Profile
from dot.errors import (
    CommandNotImplementedError,
    DotError,
    ProfileNotFoundError,
)
from dot.infra.config_loader import load_config
from dot.infra.reporter import Reporter

type Handler = Callable[[Context], None]


HANDLERS: dict[str, Handler] = {
    "status": commands.status,
    "install": commands.install,
}


def _get_profile(config: Config, args: CliArgs) -> Profile:
    profile = config.profiles.get(args.profile)
    if profile is None:
        raise ProfileNotFoundError(args.profile, list(config.profiles))
    return profile


def _state_path(home: Path) -> Path:
    value = os.environ.get("XDG_STATE_HOME")
    if value and Path(value).is_absolute():
        base = Path(value)
    else:
        base = home / ".local" / "state"
    return base / "dot" / "dot_state.toml"


def build_context(args: CliArgs, reporter: Reporter) -> Context:
    path_config = Path(args.config).expanduser().resolve()
    home = Path.home()
    config = load_config(path_config, home)
    profile = _get_profile(config, args)
    state = _state_path(home)
    return Context(
        config=config,
        profile=profile,
        path_dotfiles=path_config.parent,
        path_home=home,
        path_state=state,
        reporter=reporter,
        dry_run=args.dry_run,
    )


def main():
    parser = build_parser()

    args = parser.parse_args(namespace=CliArgs())
    reporter = Reporter(verbose=args.verbose)
    try:
        handler = HANDLERS.get(args.command)
        if handler is None:
            raise CommandNotImplementedError(args.command)
        handler(build_context(args, reporter))
    except DotError as e:
        reporter.error(e.message)
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
