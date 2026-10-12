from pathlib import Path

from dot.domain.link_state import LinkState, LinkStatus
from dot.domain.model import Link
from dot.domain.operations import (
    BackupAndLink,
    CreateLink,
    Noop,
    ReplaceLink,
    Skip,
    describe,
)
from dot.domain.planner import plan_install

LINK = Link(
    module="test", source=Path("/fake/dotfiles/rc"), dest=Path("/fake/home/.rc")
)


def _status(
    state: LinkState,
    target: Path | None = None,
    backup_exists: bool = False,
    link: Link = LINK,
) -> LinkStatus:
    return LinkStatus(
        link=link, state=state, target=target, backup_exists=backup_exists
    )


def test_linked_link_is_noop() -> None:
    assert plan_install([_status(LinkState.linked)]) == [Noop(LINK)]


def test_missing_link_is_created() -> None:
    assert plan_install([_status(LinkState.missing)]) == [CreateLink(LINK)]


def test_conflict_is_backed_up_next_to_dest() -> None:
    assert plan_install([_status(LinkState.conflict)]) == [
        BackupAndLink(LINK, backup=Path("/fake/home/.rc.bak"))
    ]


def test_conflict_with_existing_backup_is_skipped() -> None:
    ops = plan_install([_status(LinkState.conflict, backup_exists=True)])
    assert len(ops) == 1
    op = ops[0]
    assert isinstance(op, Skip)
    assert "backup already exists" in op.reason


def test_dangling_link_is_replaced_keeping_old_target() -> None:
    ops = plan_install([_status(LinkState.dangling, target=Path("/old"))])
    assert ops == [ReplaceLink(LINK, old_target=Path("/old"))]


def test_wrong_target_is_replaced_keeping_old_target() -> None:
    ops = plan_install([_status(LinkState.wrong_target, target=Path("/old"))])
    assert ops == [ReplaceLink(LINK, old_target=Path("/old"))]


def test_missing_source_is_skipped() -> None:
    ops = plan_install([_status(LinkState.source_missing)])
    assert len(ops) == 1
    op = ops[0]
    assert isinstance(op, Skip)
    assert "does not exist" in op.reason


def test_plan_keeps_link_order() -> None:
    dests = [Path("/fake/home/.c"), Path("/fake/home/.a"), Path("/fake/home/.b")]
    statuses = [
        _status(LinkState.missing, link=Link("test", Path("/fake/dotfiles/x"), dest))
        for dest in dests
    ]
    assert [op.link.dest for op in plan_install(statuses)] == dests


def test_empty_plan_for_no_links() -> None:
    assert plan_install([]) == []


def test_describe_create_link() -> None:
    assert describe(CreateLink(LINK)) == "create link to /fake/dotfiles/rc"


def test_describe_backup_mentions_backup_path() -> None:
    op = BackupAndLink(LINK, backup=Path("/fake/home/.rc.bak"))
    assert "/fake/home/.rc.bak" in describe(op)


def test_describe_skip_shows_reason() -> None:
    assert describe(Skip(LINK, "why")) == "skip: why"
