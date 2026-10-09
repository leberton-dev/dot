from enum import Enum, auto
from pathlib import Path


class DotfileState(Enum):
    missing = auto()
    real_file_in_place = auto()
    broken = auto()
    wrong_target = auto()
    ok = auto()


def compare(source: Path, dest: Path) -> DotfileState:
    source = source.resolve()
    if not dest.is_symlink():
        if not dest.exists():
            return DotfileState.missing
        return DotfileState.real_file_in_place

    if not dest.exists():
        return DotfileState.broken

    dest = dest.resolve()
    if dest != source:
        return DotfileState.wrong_target

    return DotfileState.ok
