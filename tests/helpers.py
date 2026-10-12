from collections.abc import Callable
from pathlib import Path

from dot.infra.config_loader import RawLink
from dot.context import Context


type MakeCtx = Callable[[list[RawLink]], Context]


def snapshot(root: Path) -> set[tuple[Path, bool, Path | None]]:
    """Every path under root, with whether it is a symlink and its raw target."""
    entries: set[tuple[Path, bool, Path | None]] = set()
    for path in root.rglob("*"):
        is_link = path.is_symlink()
        target = path.readlink() if is_link else None
        entries.add((path.relative_to(root), is_link, target))
    return entries
