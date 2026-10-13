import io
from pathlib import Path
import pytest

from dot.infra.config_loader import (
    RawConfig,
    RawLink,
    RawModule,
    RawProfile,
    resolve_config,
)
from dot.context import Context
from dot.infra.reporter import Reporter
from tests.helpers import MakeCtx


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def dotfiles(tmp_path: Path) -> Path:
    dots = tmp_path / "dotfiles"
    dots.mkdir()
    _ = (dots / "git").mkdir()
    _ = (dots / "git" / "config").write_text("TEST GIT CONFIG")
    _ = (dots / "nvim").mkdir()
    return dots


@pytest.fixture
def out() -> io.StringIO:
    return io.StringIO()


@pytest.fixture
def err() -> io.StringIO:
    return io.StringIO()


@pytest.fixture
def make_ctx(
    home: Path, dotfiles: Path, tmp_path: Path, out: io.StringIO, err: io.StringIO
) -> MakeCtx:
    def func(links: list[RawLink]) -> Context:
        raw = RawConfig(
            modules={"test": RawModule(links=links, packages=[])},
            profiles={"test": RawProfile(modules=["test"], package_manager="dnf")},
        )
        config = resolve_config(raw, dotfiles, home)
        return Context(
            config=config,
            path_home=home,
            path_dotfiles=dotfiles,
            path_state=tmp_path / "state.toml",
            reporter=Reporter(out=out, err=err),
            profile=config.profiles["test"],
            dry_run=False,
        )

    return func
