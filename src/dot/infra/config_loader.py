import tomllib
from pathlib import Path
from typing import TypedDict, cast

from dot.domain.model import Config, Link, Module, PackageManager, Profile
from dot.errors import (
    ConfigFileNotFoundError,
    ConfigMissingKeyError,
    ConfigSyntaxError,
    ConfigTypeError,
    ConfigUnknownKeyError,
    DestConflictError,
    InvalidChoiceError,
    InvalidDestError,
    InvalidSourceError,
    UnknownModuleError,
)


class RawLink(TypedDict):
    source: str
    dest: str


class RawModule(TypedDict):
    packages: list[str]
    links: list[RawLink]


class RawProfile(TypedDict):
    modules: list[str]
    package_manager: str


class RawConfig(TypedDict):
    modules: dict[str, RawModule]
    profiles: dict[str, RawProfile]


def parse_link(raw: object, path: str) -> RawLink:
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

    link_dict: RawLink = {"source": raw_source, "dest": raw_dest}

    return link_dict


def parse_links(raw: dict[str, object], path: str) -> list[RawLink]:
    raw_links = raw.get("links")
    if raw_links is None:
        raise ConfigMissingKeyError(path, "links")
    if not isinstance(raw_links, list):
        raise ConfigTypeError(f"{path}.links", list, type(raw_links))
    links = cast(list[object], raw_links)

    _list: list[RawLink] = []
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


def parse_modules(raw: dict[str, object], path: str) -> dict[str, RawModule]:
    modules_dict: dict[str, RawModule] = {}
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


def parse_profile(raw: object, path: str) -> RawProfile:
    if not isinstance(raw, dict):
        raise ConfigTypeError(path, dict, type(raw))
    profile = cast(dict[str, object], raw)

    allowed_keys = {"modules", "package_manager"}
    unknown_keys = set(profile) - allowed_keys
    if len(unknown_keys) != 0:
        raise ConfigUnknownKeyError(path, unknown_keys)

    profile_dict: RawProfile = {
        "modules": parse_module_names(profile, path),
        "package_manager": parse_package_manager(profile, path),
    }

    return profile_dict


def parse_profiles(raw: dict[str, object], path: str) -> dict[str, RawProfile]:
    profiles_dict: dict[str, RawProfile] = {}

    for name, raw_profile in raw.items():
        profiles_dict[name] = parse_profile(raw_profile, f"{path}.{name}")

    return profiles_dict


def parse_config(data: dict[str, object]) -> RawConfig:
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


def _resolve_source(raw: str, dotfiles: Path, path: str) -> Path:
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        raise InvalidSourceError(path, raw)
    return dotfiles / p


def _resolve_dest(raw: str, home: Path, path: str) -> Path:
    if raw.startswith("~/"):
        return home / raw.removeprefix("~/")
    p = Path(raw)
    if not p.is_absolute():
        raise InvalidDestError(path, raw)
    return p


def _resolve_module(
    name: str, raw: RawModule, dotfiles: Path, home: Path, path: str
) -> Module:
    links: list[Link] = []
    for i, raw_link in enumerate(raw["links"]):
        link = Link(
            module=name,
            source=_resolve_source(
                raw_link["source"], dotfiles, f"{path}.links[{i}].source"
            ),
            dest=_resolve_dest(raw_link["dest"], home, f"{path}.links[{i}].dest"),
        )
        links.append(link)
    return Module(name=name, packages=tuple(raw["packages"]), links=tuple(links))


def _resolve_package_manager(raw: str, path: str) -> PackageManager:
    try:
        return PackageManager(raw)
    except ValueError:
        raise InvalidChoiceError(
            path, raw, [pm.value for pm in PackageManager]
        ) from None


def _resolve_profile(
    name: str, raw: RawProfile, modules: dict[str, Module], path: str
) -> Profile:
    found_modules: list[Module] = []
    for i, module_name in enumerate(raw["modules"]):
        module = modules.get(module_name)
        if not module:
            raise UnknownModuleError(f"{path}.modules[{i}]", module_name)
        found_modules.append(module)

    seen: dict[Path, Link] = {}
    for module in found_modules:
        for link in module.links:
            if link.dest in seen:
                raise DestConflictError(
                    path, str(link.dest), seen[link.dest].module, link.module
                )
            seen[link.dest] = link

    package_manager = _resolve_package_manager(
        raw["package_manager"], f"{path}.package_manager"
    )
    return Profile(
        name=name, package_manager=package_manager, modules=tuple(found_modules)
    )


def resolve_config(raw: RawConfig, dotfiles: Path, home: Path) -> Config:
    modules: dict[str, Module] = {}
    profiles: dict[str, Profile] = {}
    for name, raw_module in raw["modules"].items():
        modules[name] = _resolve_module(
            name, raw_module, dotfiles, home, f"toml.modules.{name}"
        )
    for name, raw_profile in raw["profiles"].items():
        profiles[name] = _resolve_profile(
            name, raw_profile, modules, f"toml.profiles.{name}"
        )
    return Config(modules=modules, profiles=profiles)


def load_config(path: Path, home: Path) -> Config:
    if not path.exists():
        raise ConfigFileNotFoundError(str(path))
    with open(path, "rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigSyntaxError(str(path), str(e)) from None
    return resolve_config(parse_config(data), path.parent, home)
