import io
from pathlib import Path
import pytest

from dot.config import Config, Link, Module, Profile
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
    def func(links: list[Link]) -> Context:
        test_profile = Profile(modules=["test"], package_manager="dnf")
        conf = Config(
            modules={"test": Module(links=links, packages=[])},
            profiles={"test": test_profile},
        )
        return Context(
            config=conf,
            path_home=home,
            path_dotfiles=dotfiles,
            path_state=tmp_path / "state.toml",
            reporter=Reporter(out=out, err=err),
            profile=test_profile,
            profile_name="test",
        )

    return func
