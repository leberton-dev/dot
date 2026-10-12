from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from dot.domain.model import Link


class LinkState(Enum):
    missing = auto()
    conflict = auto()
    dangling = auto()
    wrong_target = auto()
    linked = auto()


def get_link_state(source: Path, dest: Path) -> LinkState:
    source = source.resolve()
    if not dest.is_symlink():
        if not dest.exists():
            return LinkState.missing
        return LinkState.conflict

    if not dest.exists():
        return LinkState.dangling

    dest = dest.resolve()
    if dest != source:
        return LinkState.wrong_target

    return LinkState.linked


@dataclass(frozen=True)
class ProfileLink:
    module: str
    source: Path
    dest: Path
    state: LinkState


def inspect_links(links: Iterable[Link]) -> Iterator[ProfileLink]:
    for link in links:
        state = get_link_state(link.source, link.dest)
        yield ProfileLink(link.module, link.source, link.dest, state)

class LinkAction(Enum):
    created = auto()
    backed_up = auto()
    replaced = auto()

