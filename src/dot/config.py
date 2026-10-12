import tomllib
from typing import TypedDict, cast

from dot.errors import ConfigTypeError, ConfigMissingKeyError, ConfigUnknownKeyError


class Link(TypedDict):
    source: str
    dest: str


class Module(TypedDict):
    packages: list[str]
    links: list[Link]


class Profile(TypedDict):
    modules: list[str]
    package_manager: str


class Config(TypedDict):
    modules: dict[str, Module]
    profiles: dict[str, Profile]


def parse_link(raw: object, path: str) -> Link:
    if not isinstance(raw, dict):
        raise ConfigTypeError(f"{path}", dict, type(raw))
    link = cast(dict[str, object], raw)

    allowed_keys = {"source", "dest"}
    unknown_keys = set(link) - allowed_keys
    if len(unknown_keys) != 0:
        raise ConfigUnknownKeyError(path, unknown_keys)

    raw_source = link.get("source")
    if raw_source is None:
        raise ConfigMissingKeyError(path, "source")
    if not isinstance(raw_source, str):
        raise ConfigTypeError(f"{path}.source", str, type(raw_source))

    raw_dest = link.get("dest")
    if raw_dest is None:
        raise ConfigMissingKeyError(path, "dest")
    if not isinstance(raw_dest, str):
        raise ConfigTypeError(f"{path}.dest", str, type(raw_dest))

    link_dict: Link = {"source": raw_source, "dest": raw_dest}

    return link_dict


def parse_links(raw: dict[str, object], path: str) -> list[Link]:
    raw_links = raw.get("links")
    if raw_links is None:
        raise ConfigMissingKeyError(path, "links")
    if not isinstance(raw_links, list):
        raise ConfigTypeError(f"{path}.links", list, type(raw_links))
    links = cast(list[object], raw_links)

    _list: list[Link] = []
    for i, raw_link in enumerate(links):
        _list.append(parse_link(raw_link, f"{path}.links[{i}]"))

    return _list


def parse_packages(raw: dict[str, object], path: str) -> list[str]:
    raw_packages = raw.get("packages")
    if raw_packages is None:
        raise ConfigMissingKeyError(path, "packages")
    if not isinstance(raw_packages, list):
        raise ConfigTypeError(f"{path}.packages", list, type(raw_packages))
    packages = cast(list[object], raw_packages)

    _list: list[str] = []
    for i, raw_package in enumerate(packages):
        if not isinstance(raw_package, str):
            raise ConfigTypeError(f"{path}.packages[{i}]", str, type(raw_package))
        _list.append(raw_package)

    return _list


def parse_modules(raw: dict[str, object], path: str) -> dict[str, Module]:
    modules_dict: dict[str, Module] = {}
    for name, raw_module in raw.items():
        module_path = f"{path}.{name}"

        if not isinstance(raw_module, dict):
            raise ConfigTypeError(module_path, dict, type(raw_module))
        module = cast(dict[str, object], raw_module)

        allowed_keys = {"packages", "links"}
        unknown_keys = set(module) - allowed_keys
        if len(unknown_keys) != 0:
            raise ConfigUnknownKeyError(module_path, unknown_keys)

        modules_dict[name] = {
            "packages": parse_packages(module, module_path),
            "links": parse_links(module, module_path),
        }

    return modules_dict


def parse_module_names(raw: dict[str, object], path: str) -> list[str]:
    raw_modules = raw.get("modules")
    if raw_modules is None:
        raise ConfigMissingKeyError(path, "modules")
    if not isinstance(raw_modules, list):
        raise ConfigTypeError(f"{path}.modules", list, type(raw_modules))
    modules = cast(list[object], raw_modules)

    _list: list[str] = []
    for i, module in enumerate(modules):
        if not isinstance(module, str):
            raise ConfigTypeError(f"{path}.modules[{i}]", str, type(module))
        _list.append(module)

    return _list


def parse_package_manager(raw: dict[str, object], path: str) -> str:
    raw_pm = raw.get("package_manager")
    if raw_pm is None:
        raise ConfigMissingKeyError(path, "package_manager")
    if not isinstance(raw_pm, str):
        raise ConfigTypeError(f"{path}.package_manager", str, type(raw_pm))

    return raw_pm


def parse_profile(raw: object, path: str) -> Profile:
    if not isinstance(raw, dict):
        raise ConfigTypeError(path, dict, type(raw))
    profile = cast(dict[str, object], raw)

    allowed_keys = {"modules", "package_manager"}
    unknown_keys = set(profile) - allowed_keys
    if len(unknown_keys) != 0:
        raise ConfigUnknownKeyError(path, unknown_keys)

    profile_dict: Profile = {
        "modules": parse_module_names(profile, path),
        "package_manager": parse_package_manager(profile, path),
    }

    return profile_dict


def parse_profiles(raw: dict[str, object], path: str) -> dict[str, Profile]:
    profiles_dict: dict[str, Profile] = {}

    for name, raw_profile in raw.items():
        profiles_dict[name] = parse_profile(raw_profile, f"{path}.{name}")

    return profiles_dict


def parse_config(data: dict[str, object]) -> Config:
    path = "toml"

    allowed_keys = {"modules", "profiles"}
    unknown_keys = set(data) - allowed_keys
    if len(unknown_keys) != 0:
        raise ConfigUnknownKeyError(path, unknown_keys)

    modules = data.get("modules")
    if modules is None:
        raise ConfigMissingKeyError(path, "modules")
    if not isinstance(modules, dict):
        raise ConfigTypeError(f"{path}.modules", dict, type(modules))
    modules = cast(dict[str, object], modules)

    profiles = data.get("profiles")
    if profiles is None:
        raise ConfigMissingKeyError(path, "profiles")
    if not isinstance(profiles, dict):
        raise ConfigTypeError(f"{path}.profiles", dict, type(profiles))
    profiles = cast(dict[str, object], profiles)

    return {
        "modules": parse_modules(modules, f"{path}.modules"),
        "profiles": parse_profiles(profiles, f"{path}.profiles"),
    }


def load_config(config_path: str = "examples/dotfiles.toml") -> Config:
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    return parse_config(data)
