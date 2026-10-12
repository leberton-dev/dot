from dot.domain.link_state import LinkState, LinkStatus, backup_path
from dot.domain.model import Link


def _get_state_from_link(link: Link) -> LinkState:
    if not link.source.exists():
        return LinkState.source_missing

    dest = link.dest
    if not dest.is_symlink():
        return LinkState.conflict if dest.exists() else LinkState.missing
    if not dest.exists():
        return LinkState.dangling
    if dest.resolve() != link.source.resolve():
        return LinkState.wrong_target
    return LinkState.linked


def inspect_link(link: Link) -> LinkStatus:
    return LinkStatus(
        link=link,
        state=_get_state_from_link(link),
        target=link.dest.readlink() if link.dest.is_symlink() else None,
        backup_exists=(
            backup_path(link.dest).exists() or backup_path(link.dest).is_symlink()
        ),
    )
