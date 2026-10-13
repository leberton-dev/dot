import dataclasses
import io
from pathlib import Path

from dot import commands
from dot.context import Context
from dot.infra.config_loader import RawLink

from tests.helpers import MakeCtx, snapshot

GITCONFIG = RawLink(source="git/config", dest="~/.gitconfig")
NVIM = RawLink(source="nvim", dest="~/.config/nvim")
IGNORE = RawLink(source="git/config", dest="~/.config/git/ignore")


def _dry(ctx: Context) -> Context:
    return dataclasses.replace(ctx, dry_run=True)


def test_dry_run_does_not_modify_filesystem(
    make_ctx: MakeCtx, home: Path, tmp_path: Path
) -> None:
    _ = (home / ".gitconfig").write_text("REAL")
    (home / ".config").mkdir()
    (home / ".config" / "nvim").symlink_to(tmp_path / "nowhere")
    ctx = _dry(make_ctx([GITCONFIG, NVIM, IGNORE]))
    before = snapshot(home)
    commands.install(ctx)
    assert snapshot(home) == before


def test_dry_run_does_not_write_state_file(make_ctx: MakeCtx) -> None:
    ctx = _dry(make_ctx([GITCONFIG]))
    commands.install(ctx)
    assert not ctx.path_state.exists()


def test_dry_run_lists_planned_operations(
    make_ctx: MakeCtx, home: Path, out: io.StringIO
) -> None:
    (home / ".config" / "nvim").mkdir(parents=True)
    commands.install(_dry(make_ctx([GITCONFIG, NVIM])))
    output = out.getvalue()
    assert "would create link to" in output
    assert "would backup to" in output


def test_dry_run_still_warns_on_skip(make_ctx: MakeCtx, err: io.StringIO) -> None:
    missing_source = RawLink(source="does/not/exist", dest="~/.missing")
    commands.install(_dry(make_ctx([missing_source])))
    assert "does not exist" in err.getvalue()


def test_dry_run_hides_noops_without_verbose(
    make_ctx: MakeCtx, home: Path, dotfiles: Path, out: io.StringIO
) -> None:
    (home / ".gitconfig").symlink_to(dotfiles / "git" / "config")
    commands.install(_dry(make_ctx([GITCONFIG])))
    assert "nothing to do" not in out.getvalue()


def test_real_install_after_dry_run_still_works(
    make_ctx: MakeCtx, home: Path, dotfiles: Path
) -> None:
    ctx = make_ctx([GITCONFIG])
    commands.install(_dry(ctx))
    commands.install(ctx)
    assert (home / ".gitconfig").readlink() == dotfiles / "git" / "config"
