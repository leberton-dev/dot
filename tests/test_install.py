import io
from pathlib import Path

from dot import commands
from dot.infra.config_loader import RawLink
from dot.state import StateFile, LinkAction

from tests.helpers import MakeCtx, snapshot


def test_creates_link_when_missing(
    make_ctx: MakeCtx, home: Path, dotfiles: Path
) -> None:
    ctx = make_ctx([RawLink(source="git/config", dest="~/.gitconfig")])
    commands.install(ctx)
    assert (home / ".gitconfig").readlink() == dotfiles / "git" / "config"


def test_creates_parent_directories(
    make_ctx: MakeCtx, home: Path, dotfiles: Path
) -> None:
    ctx = make_ctx([RawLink(source="git/config", dest="~/.config/git/ignore")])
    commands.install(ctx)
    assert (home / ".config" / "git").is_dir()
    assert (
        home / ".config" / "git" / "ignore"
    ).readlink() == dotfiles / "git" / "config"


def test_backs_up_real_file_on_conflict(
    make_ctx: MakeCtx, home: Path, dotfiles: Path
) -> None:
    ctx = make_ctx([RawLink(source="git/config", dest="~/.gitconfig")])
    _ = (home / ".gitconfig").write_text("OLD")
    commands.install(ctx)
    assert not (home / ".gitconfig.bak").is_symlink()
    assert (home / ".gitconfig.bak").read_text() == "OLD"
    assert (home / ".gitconfig").readlink() == (dotfiles / "git" / "config")


def test_backs_up_real_directory_on_conflict(
    make_ctx: MakeCtx, home: Path, dotfiles: Path
) -> None:
    ctx = make_ctx([RawLink(source="nvim", dest="~/.config/nvim")])
    (home / ".config" / "nvim").mkdir(parents=True)
    _ = (home / ".config" / "nvim" / "init.lua").write_text("OLD")
    commands.install(ctx)
    assert (home / ".config" / "nvim.bak" / "init.lua").exists()
    assert (home / ".config" / "nvim.bak" / "init.lua").read_text() == "OLD"
    assert (home / ".config" / "nvim").readlink() == (dotfiles / "nvim")


def test_skips_conflict_when_backup_exists(
    make_ctx: MakeCtx, home: Path, err: io.StringIO
) -> None:
    ctx = make_ctx([RawLink(source="git/config", dest="~/.gitconfig")])
    _ = (home / ".gitconfig").write_text("OLD")
    _ = (home / ".gitconfig.bak").write_text("OLDER")
    commands.install(ctx)
    assert not (home / ".gitconfig").is_symlink()
    assert (home / ".gitconfig").read_text() == "OLD"
    assert (home / ".gitconfig.bak").read_text() == "OLDER"
    assert "backup already exists" in err.getvalue()


def test_replaces_dangling_link(
    make_ctx: MakeCtx,
    home: Path,
    dotfiles: Path,
    tmp_path: Path,
) -> None:
    ctx = make_ctx([RawLink(source="git/config", dest="~/.gitconfig")])
    (home / ".gitconfig").symlink_to(tmp_path / "nowhere")
    commands.install(ctx)
    assert (home / ".gitconfig").readlink() == (dotfiles / "git" / "config")


def test_replaces_wrong_target_link(
    make_ctx: MakeCtx,
    home: Path,
    dotfiles: Path,
    tmp_path: Path,
) -> None:
    ctx = make_ctx([RawLink(source="git/config", dest="~/.gitconfig")])
    _ = (tmp_path / "other.txt").write_text("OTHER")
    (home / ".gitconfig").symlink_to(tmp_path / "other.txt")
    commands.install(ctx)
    assert (home / ".gitconfig").readlink() == (dotfiles / "git" / "config")
    assert (tmp_path / "other.txt").read_text() == "OTHER"


def test_skips_link_when_source_missing(
    make_ctx: MakeCtx, home: Path, err: io.StringIO
) -> None:
    ctx = make_ctx([RawLink(source="does/not/exist", dest="~/.missing")])
    commands.install(ctx)
    assert not (home / ".missing").exists()
    assert not (home / ".missing").is_symlink()
    assert "does not exist" in err.getvalue()


def test_records_every_action_in_state_file(
    make_ctx: MakeCtx,
) -> None:
    ctx = make_ctx(
        [
            RawLink(source="git/config", dest="~/.gitconfig"),
            RawLink(source="git/config", dest="~/.gitconfig2"),
            RawLink(source="nvim", dest="~/.config/nvim"),
        ]
    )
    commands.install(ctx)
    actions = StateFile(ctx.path_state).read_actions()
    assert len(actions) == 3
    for action in actions:
        assert action.action == LinkAction.created


def test_state_file_written_inside_context_path(make_ctx: MakeCtx, home: Path) -> None:
    ctx = make_ctx([RawLink(source="git/config", dest="~/.gitconfig")])
    commands.install(ctx)
    assert ctx.path_state.exists()
    assert not (home / ".local").exists()


def test_second_install_changes_nothing(make_ctx: MakeCtx, home: Path) -> None:
    ctx = make_ctx(
        [
            RawLink(source="git/config", dest="~/.gitconfig"),
            RawLink(source="nvim", dest="~/.config/nvim"),
        ]
    )
    commands.install(ctx)
    before = snapshot(home)
    state_before = ctx.path_state.read_text()
    commands.install(ctx)
    assert snapshot(home) == before
    assert ctx.path_state.read_text() == state_before
