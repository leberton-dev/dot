import io
from pathlib import Path

from dot import commands
from dot.infra.config_loader import RawLink

from tests.helpers import MakeCtx, snapshot

GITCONFIG = RawLink(source="git/config", dest="~/.gitconfig")
NVIM = RawLink(source="nvim", dest="~/.config/nvim")


def test_reports_up_to_date_when_all_linked(
    make_ctx: MakeCtx, home: Path, dotfiles: Path, out: io.StringIO
) -> None:
    (home / ".gitconfig").symlink_to(dotfiles / "git" / "config")
    commands.status(make_ctx([GITCONFIG]))
    assert "You are up to date with all links" in out.getvalue()
    assert "Up to date: 1 links" in out.getvalue()


def test_lists_each_pending_change(
    make_ctx: MakeCtx, home: Path, out: io.StringIO
) -> None:
    (home / ".config" / "nvim").mkdir(parents=True)
    commands.status(make_ctx([GITCONFIG, NVIM]))
    output = out.getvalue()
    assert "Changes to apply:" in output
    assert "create link to" in output
    assert "backup to" in output


def test_lists_skipped_links_separately(make_ctx: MakeCtx, out: io.StringIO) -> None:
    commands.status(make_ctx([RawLink(source="does/not/exist", dest="~/.missing")]))
    output = out.getvalue()
    assert "Skipped:" in output
    assert "does not exist" in output
    assert "Changes to apply:" not in output


def test_counts_only_noops_as_up_to_date(
    make_ctx: MakeCtx, home: Path, dotfiles: Path, out: io.StringIO
) -> None:
    (home / ".gitconfig").symlink_to(dotfiles / "git" / "config")
    commands.status(make_ctx([GITCONFIG, NVIM]))
    assert "Up to date: 1 links" in out.getvalue()


def test_does_not_modify_filesystem(
    make_ctx: MakeCtx, home: Path, tmp_path: Path
) -> None:
    _ = (home / ".gitconfig").write_text("REAL")
    (home / ".config").mkdir()
    (home / ".config" / "nvim").symlink_to(tmp_path / "nowhere")
    ctx = make_ctx([GITCONFIG, NVIM])
    before = snapshot(home)
    commands.status(ctx)
    assert snapshot(home) == before


def test_does_not_write_state_file(make_ctx: MakeCtx) -> None:
    ctx = make_ctx([GITCONFIG])
    commands.status(ctx)
    assert not ctx.path_state.exists()


def test_shows_changes_and_skips_together(
    make_ctx: MakeCtx, out: io.StringIO
) -> None:
    missing_source = RawLink(source="does/not/exist", dest="~/.missing")
    commands.status(make_ctx([GITCONFIG, missing_source]))
    output = out.getvalue()
    assert "Changes to apply:" in output
    assert "Skipped:" in output
