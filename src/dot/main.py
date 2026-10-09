from pathlib import Path
import shutil

from dot.cli import build_parser, CliArgs
from dot.config import Config, ConfigError, Profile, load_config


def has_package_manager(manager: str) -> bool:
    return shutil.which(manager) is not None


def get_profile(config: Config, profile_name: str) -> Profile:
    for name, profile in config["profiles"].items():
        if name == profile_name:
            return profile
    raise ValueError("no profile found")


def main():
    parser = build_parser()

    args = parser.parse_args(namespace=CliArgs())

    try:
        config_path = Path(args.config).expanduser()
        if not config_path.exists():
            print(f"dot.parsing.toml.error: no toml config found under {config_path}")
            return
        config = load_config(config_path=str(config_path))

        profile = get_profile(config, args.profile)
        print(has_package_manager(profile["package_manager"]))

    except ConfigError as e:
        print(f"dot.parsing.toml.error: {e.message}")


if __name__ == "__main__":
    main()
