import sys
from collections.abc import Callable
from pathlib import Path

from dot import commands
from dot.args import CliArgs
from dot.cli import build_parser
from dot.config import Config, load_config
from dot.errors import CommandNotImplementedError, ConfigFileNotFoundError, DotError
from dot.infra.reporter import Reporter

type Handler = Callable[[Config, CliArgs, Reporter], None]


def not_implemented(_config: Config, args: CliArgs, _reporter: Reporter) -> None:
    raise CommandNotImplementedError(args.command)


HANDLERS: dict[str, Handler] = {
    "status": commands.status,
    "install": commands.install,
}


def load_conf(args: CliArgs) -> Config:
    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        raise ConfigFileNotFoundError(str(config_path))
    return load_config(config_path=str(config_path))


def main():
    parser = build_parser()

    args = parser.parse_args(namespace=CliArgs())
    reporter = Reporter(verbose=args.verbose)
    try:
        config = load_conf(args)
        handler = HANDLERS.get(args.command, not_implemented)
        handler(config, args, reporter)
    except DotError as e:
        reporter.error(e.message)
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
