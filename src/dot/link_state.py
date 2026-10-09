from enum import Enum, auto
from pathlib import Path


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
