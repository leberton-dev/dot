from dot.cli import build_parser, DotArgs
from dot.dotfiles import DotfilesDictError, load_dotfiles


def main():
    parser = build_parser()

    args = parser.parse_args(namespace=DotArgs())

    config_path = "/home/leberton/.dotfiles/" + args.config
    try:
        _ = load_dotfiles(config_path=config_path)
    except DotfilesDictError as e:
        print(f"dot.parsing.toml.error: {e.message}")


if __name__ == "__main__":
    main()
