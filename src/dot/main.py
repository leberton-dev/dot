from pathlib import Path

from dot.cli import build_parser, DotArgs
from dot.dotfiles import DotfilesDictError, load_dotfiles


def main():
    parser = build_parser()

    args = parser.parse_args(namespace=DotArgs())

    try:
        config_path = Path(args.config).expanduser()
        if not config_path.exists():
            print(f"dot.parsing.toml.error: no toml config found under {config_path}")
            return
        _ = load_dotfiles(config_path=str(config_path))
        print(f"Hello from {config_path}")
    except DotfilesDictError as e:
        print(f"dot.parsing.toml.error: {e.message}")


if __name__ == "__main__":
    main()
