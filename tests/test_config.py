from pathlib import Path

import pytest

from dot.errors import (
    ConfigFileNotFoundError,
    ConfigMissingKeyError,
    ConfigSyntaxError,
    ConfigTypeError,
    ConfigUnknownKeyError,
)
from dot.infra.config_loader import load_config, parse_config

EXAMPLE_CONFIG = Path(__file__).parent.parent / "examples" / "dotfiles.toml"


def _data() -> dict[str, object]:
    """A minimal valid toml document, as tomllib would return it."""
    return {
        "modules": {
            "git": {
                "packages": ["git"],
                "links": [{"source": "git/config", "dest": "~/.gitconfig"}],
            }
        },
        "profiles": {"test": {"modules": ["git"], "package_manager": "dnf"}},
    }


def _git_module(data: dict[str, object]) -> dict[str, object]:
    return data["modules"]["git"]  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]


def test_loads_example_config() -> None:
    config = load_config(EXAMPLE_CONFIG, Path("/fake/home"))
    assert "asahi" in config.profiles
    assert "git" in config.modules


def test_parses_minimal_config() -> None:
    raw = parse_config(_data())
    assert raw["modules"]["git"]["links"][0]["dest"] == "~/.gitconfig"
    assert raw["profiles"]["test"]["modules"] == ["git"]


def test_missing_config_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope.toml"
    with pytest.raises(ConfigFileNotFoundError) as err:
        _ = load_config(missing, tmp_path)
    assert err.value.path == str(missing)


def test_invalid_toml_syntax_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.toml"
    _ = bad.write_text("modules = [\n")
    with pytest.raises(ConfigSyntaxError) as err:
        _ = load_config(bad, tmp_path)
    assert err.value.path == str(bad)


def test_missing_top_level_key_reports_path() -> None:
    data = _data()
    del data["profiles"]
    with pytest.raises(ConfigMissingKeyError) as err:
        _ = parse_config(data)
    assert err.value.path == "toml"
    assert err.value.missing == "profiles"


def test_missing_key_error_reports_path() -> None:
    data = _data()
    _git_module(data)["links"] = [{"source": "git/config"}]
    with pytest.raises(ConfigMissingKeyError) as err:
        _ = parse_config(data)
    assert err.value.path == "toml.modules.git.links[0]"
    assert err.value.missing == "dest"


def test_wrong_type_error_reports_path() -> None:
    data = _data()
    _git_module(data)["links"] = [{"source": "git/config", "dest": 42}]
    with pytest.raises(ConfigTypeError) as err:
        _ = parse_config(data)
    assert err.value.path == "toml.modules.git.links[0].dest"
    assert err.value.expected is str
    assert err.value.got is int
    assert err.value.message.endswith("expected string, got integer")


def test_wrong_type_in_list_reports_index() -> None:
    data = _data()
    _git_module(data)["packages"] = ["git", 1]
    with pytest.raises(ConfigTypeError) as err:
        _ = parse_config(data)
    assert err.value.path == "toml.modules.git.packages[1]"


def test_unknown_key_error_lists_keys() -> None:
    data = _data()
    _git_module(data)["foo"] = 1
    _git_module(data)["bar"] = 2
    with pytest.raises(ConfigUnknownKeyError) as err:
        _ = parse_config(data)
    assert err.value.path == "toml.modules.git"
    assert err.value.unknown == {"foo", "bar"}


def test_unknown_top_level_key_is_rejected() -> None:
    data = _data()
    data["extra"] = {}
    with pytest.raises(ConfigUnknownKeyError) as err:
        _ = parse_config(data)
    assert err.value.path == "toml"
    assert err.value.unknown == {"extra"}
