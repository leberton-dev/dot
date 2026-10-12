from dataclasses import dataclass
from enum import auto, Enum
from pathlib import Path

from dot.domain.model import Link


class LinkState(Enum):
    missing = auto()
    conflict = auto()
    dangling = auto()
    wrong_target = auto()
    source_missing = auto()
    linked = auto()


@dataclass(frozen=True)
class LinkStatus:
    link: Link
    state: LinkState
    target: Path | None
    backup_exists: bool


def backup_path(dest: Path) -> Path:
    return Path(str(dest) + ".bak")
