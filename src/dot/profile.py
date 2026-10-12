from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from dot.config import Config, Profile
from dot.link_state import LinkState, get_link_state


@dataclass(frozen=True)
class ProfileLink:
    module: str
    source: Path
    dest: Path
    state: LinkState



def links_of_profile(
    profile: Profile, config: Config, dotfiles: Path, home: Path
) -> Iterator[ProfileLink]:
    for module in profile["modules"]:
        for link in config["modules"][module]["links"]:
            source = dotfiles / link["source"]
            p = link["dest"]
            # TODO: dest relative to current path
            if p.startswith("~/"):
                dest = home / p.removeprefix("~/")
            else:
                dest = Path(p)
            state = get_link_state(source, dest)
            yield (ProfileLink(module, source, dest, state))
