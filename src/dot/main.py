import sys
from pathlib import Path

from dot import commands
from dot.cli import CliArgs, build_parser
from dot.config import Config, load_config
from dot.errors import ConfigError


def load_conf(args: CliArgs) -> Config:
    try:
        config_path = Path(args.config).expanduser()
        if not config_path.exists():
            print(f"dot.parsing.toml.error: no toml config found under {config_path}")
            sys.exit(1)
        config = load_config(config_path=str(config_path))
        return config
    except ConfigError as e:
        print(e.message)
        sys.exit(1)


def main():
    parser = build_parser()

    args = parser.parse_args(namespace=CliArgs())
    config = load_conf(args)

    if args.command == "status":
        commands.status(config, args)
    elif args.command == "install":
        commands.install(config, args)


if __name__ == "__main__":
    main()
