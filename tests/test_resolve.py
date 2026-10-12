import pytest

from pathlib import Path

from dot.errors import (
    UnknownModuleError,
    InvalidDestError,
    InvalidSourceError,
    InvalidChoiceError,
    DestConflictError,
)
from dot.domain.model import PackageManager
from dot.infra.config_loader import RawConfig, resolve_config

HOME = Path("/fake/home")
DOTFILES = Path("/fake/dotfiles")


def _raw(
    modules: dict[str, list[tuple[str, str]]],
    profiles: dict[str, list[str]],
    package_manager: str = "dnf",
) -> RawConfig:
    return {
        "modules": {
            name: {
                "packages": [],
                "links": [{"source": s, "dest": d} for s, d in links],
            }
            for name, links in modules.items()
        },
        "profiles": {
            name: {"modules": mods, "package_manager": package_manager}
            for name, mods in profiles.items()
        },
    }


def test_source_becomes_absolute_under_dotfiles() -> None:
    raw = _raw({"git": [("git/config", "~/.gitconfig")]}, {"test": ["git"]})
    config = resolve_config(raw, DOTFILES, HOME)
    assert config.modules["git"].links[0].source == DOTFILES / "git" / "config"


def test_tilde_dest_expands_to_injected_home() -> None:
    raw = _raw({"git": [("git/config", "~/.gitconfig")]}, {"test": ["git"]})
    config = resolve_config(raw, DOTFILES, HOME)
    assert config.modules["git"].links[0].dest == HOME / ".gitconfig"


def test_absolute_dest_is_kept() -> None:
    raw = _raw({"etc": [("etc/hosts", "/etc/hosts")]}, {"test": ["etc"]})
    config = resolve_config(raw, DOTFILES, HOME)
    assert config.modules["etc"].links[0].dest == Path("/etc/hosts")


def test_relative_dest_is_rejected() -> None:
    raw = _raw({"git": [("git/config", "foo/bar")]}, {"test": ["git"]})
    with pytest.raises(InvalidDestError) as err:
        _ = resolve_config(raw, DOTFILES, HOME)
    assert err.value.path == "toml.modules.git.links[0].dest"
    assert err.value.dest == "foo/bar"


def test_absolute_source_is_rejected() -> None:
    raw = _raw({"git": [("/etc/passwd", "~/.gitconfig")]}, {"test": ["git"]})
    with pytest.raises(InvalidSourceError) as err:
        _ = resolve_config(raw, DOTFILES, HOME)
    assert err.value.path == "toml.modules.git.links[0].source"


def test_source_escaping_dotfiles_is_rejected() -> None:
    raw = _raw({"git": [("../secret", "~/.gitconfig")]}, {"test": ["git"]})
    with pytest.raises(InvalidSourceError) as err:
        _ = resolve_config(raw, DOTFILES, HOME)
    assert err.value.source == "../secret"


def test_unknown_module_in_profile_is_rejected() -> None:
    raw = _raw({"git": [("git/config", "~/.gitconfig")]}, {"test": ["git", "nope"]})
    with pytest.raises(UnknownModuleError) as err:
        _ = resolve_config(raw, DOTFILES, HOME)
    assert err.value.path == "toml.profiles.test.modules[1]"
    assert err.value.module == "nope"


def test_duplicate_dest_in_profile_is_rejected() -> None:
    raw = _raw(
        {"a": [("a/rc", "~/.rc")], "b": [("b/rc", "~/.rc")]},
        {"test": ["a", "b"]},
    )
    with pytest.raises(DestConflictError) as err:
        _ = resolve_config(raw, DOTFILES, HOME)
    assert err.value.module_a == "a"
    assert err.value.module_b == "b"


def test_same_dest_in_different_profiles_is_allowed() -> None:
    raw = _raw(
        {"a": [("a/rc", "~/.rc")], "b": [("b/rc", "~/.rc")]},
        {"one": ["a"], "two": ["b"]},
    )
    config = resolve_config(raw, DOTFILES, HOME)
    assert set(config.profiles) == {"one", "two"}


def test_unknown_package_manager_is_rejected() -> None:
    raw = _raw(
        {"git": [("git/config", "~/.gitconfig")]},
        {"test": ["git"]},
        package_manager="yum",
    )
    with pytest.raises(InvalidChoiceError) as err:
        _ = resolve_config(raw, DOTFILES, HOME)
    assert err.value.path == "toml.profiles.test.package_manager"
    assert err.value.value == "yum"
    assert "dnf" in err.value.allowed


def test_profile_links_follow_module_order() -> None:
    raw = _raw(
        {"a": [("a/1", "~/.a1"), ("a/2", "~/.a2")], "b": [("b/1", "~/.b1")]},
        {"test": ["b", "a"]},
    )
    config = resolve_config(raw, DOTFILES, HOME)
    assert [link.dest.name for link in config.profiles["test"].links] == [
        ".b1",
        ".a1",
        ".a2",
    ]


def test_resolves_when_files_do_not_exist() -> None:
    raw = _raw({"git": [("git/config", "~/.gitconfig")]}, {"test": ["git"]})
    config = resolve_config(raw, DOTFILES, HOME)
    assert config.profiles["test"].package_manager == PackageManager.dnf
    assert len(config.profiles["test"].links) == 1
