from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from dot.args import CliArgs
from dot.config import Config, Profile
from dot.errors import ProfileNotFoundError
from dot.link_state import LinkState, get_link_state


@dataclass(frozen=True)
class ProfileLink:
    module: str
    source: Path
    dest: Path
    state: LinkState


def get_profile(config: Config, args: CliArgs) -> Profile:
    profile = config["profiles"].get(args.profile)
    if profile is None:
        raise ProfileNotFoundError(args.profile, list(config["profiles"]))
    return profile


def get_dotfiles_path(args: CliArgs) -> Path:
    return Path(args.config).parent.expanduser().resolve()


def links_of_profile(
    profile: Profile, config: Config, dotfiles: Path
) -> Iterator[ProfileLink]:
    for module in profile["modules"]:
        for link in config["modules"][module]["links"]:
            source = dotfiles / link["source"]
            dest = Path(link["dest"]).expanduser()
            state = get_link_state(source, dest)
            yield (ProfileLink(module, source, dest, state))
