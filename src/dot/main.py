from pathlib import Path

from dot.cli import build_parser, CliArgs
from dot.config import ConfigError, load_config
from dot.link_state import get_link_state


def main():
    parser = build_parser()

    args = parser.parse_args(namespace=CliArgs())

    try:
        config_path = Path(args.config).expanduser()
        if not config_path.exists():
            print(f"dot.parsing.toml.error: no toml config found under {config_path}")
            return
        dotfiles_path = config_path.parent

        config = load_config(config_path=str(config_path))
        for _, module in config["modules"].items():
            for link in module["links"]:
                print(
                    get_link_state(
                        dotfiles_path / link["source"],
                        Path(link["dest"]).expanduser(),
                    )
                )

        print(f"Hello from {config_path}")
    except ConfigError as e:
        print(f"dot.parsing.toml.error: {e.message}")


if __name__ == "__main__":
    main()
