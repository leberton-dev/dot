import os
import sys
from collections.abc import Callable
from pathlib import Path

from dot import commands
from dot.args import CliArgs
from dot.cli import build_parser
from dot.config import Config, Profile, load_config
from dot.context import Context
from dot.errors import (
    CommandNotImplementedError,
    ConfigFileNotFoundError,
    DotError,
    ProfileNotFoundError,
)
from dot.infra.reporter import Reporter

type Handler = Callable[[Context], None]


HANDLERS: dict[str, Handler] = {
    "status": commands.status,
    "install": commands.install,
}


def _load_conf(path_config: Path) -> Config:
    if not path_config.exists():
        raise ConfigFileNotFoundError(str(path_config))
    return load_config(config_path=str(path_config))


def _get_profile(config: Config, args: CliArgs) -> Profile:
    profile = config["profiles"].get(args.profile)
    if profile is None:
        raise ProfileNotFoundError(args.profile, list(config["profiles"]))
    return profile


def _state_path(home: Path) -> Path:
    value = os.environ.get("XDG_STATE_HOME")
    if value and Path(value).is_absolute():
        base = Path(value)
    else:
        base = home / ".local" / "state"
    return base / "dot" / "dot_state.toml"


def build_context(args: CliArgs, reporter: Reporter) -> Context:
    path_config = Path(args.config).expanduser()
    config = _load_conf(path_config)
    profile = _get_profile(config, args)
    dotfiles = path_config.parent.resolve()
    home = Path.home()
    state = _state_path(home)
    return Context(
        config=config,
        profile=profile,
        profile_name=args.profile,
        path_dotfiles=dotfiles,
        path_home=home,
        path_state=state,
        reporter=reporter,
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
