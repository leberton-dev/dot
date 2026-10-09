import tomllib
from typing import TypedDict, cast


class LinkDict(TypedDict):
    source: str
    dest: str


class ModuleDict(TypedDict):
    packages: list[str]
    links: list[LinkDict]


class ProfileDict(TypedDict):
    modules: list[str]
    package_manager: str


Name = str


class DotfilesDict(TypedDict):
    modules: dict[Name, ModuleDict]
    profiles: dict[Name, ProfileDict]


TYPES_PYTHON_TOML: dict[type, str] = {
    str: "string",
    int: "integer",
    bool: "boolean",
    list: "array",
    dict: "table",
}


class DotfilesDictError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: str = message


class DotfilesDictWrongTypeError(DotfilesDictError):
    """Raised when a value has not the correct type"""

    def __init__(self, name: str, expected: type, got: type) -> None:
        self.name: str = name
        self.expected: type = expected
        self.got: type = got
        message = f"{name}: expected {TYPES_PYTHON_TOML.get(expected, expected.__name__)}, got {TYPES_PYTHON_TOML.get(got, got.__name__)}"
        super().__init__(message)


class DotfilesDictMissingKeyError(DotfilesDictError):
    """Raised when a key is missing"""

    def __init__(self, name: str, missing: str) -> None:
        self.name: str = name
        self.missing: str = missing
        message = f"{name}: missing key '{missing}'"
        super().__init__(message)


class DotfilesDictUnknownKeyError(DotfilesDictError):
    """Raised when a key is unknown"""

    def __init__(self, name: str, unknown: set[str]) -> None:
        self.name: str = name
        self.unknown: set[str] = unknown
        keys = ", ".join(f"'{k}'" for k in sorted(unknown))
        label = "key" if len(unknown) == 1 else "keys"
        message = f"{name}: unknown {label} {keys}"
        super().__init__(message)


def check_link(raw: object, path: str) -> LinkDict:
    if not isinstance(raw, dict):
        raise DotfilesDictWrongTypeError(f"{path}", dict, type(raw))
    link = cast(dict[str, object], raw)

    allowed_keys = {"source", "dest"}
    diff = set(link) - allowed_keys
    if len(diff) != 0:
        raise DotfilesDictUnknownKeyError(path, diff)

    raw_source = link.get("source")
    if raw_source is None:
        raise DotfilesDictMissingKeyError(path, "source")
    if not isinstance(raw_source, str):
        raise DotfilesDictWrongTypeError(f"{path}.source", str, type(raw_source))

    raw_dest = link.get("dest")
    if raw_dest is None:
        raise DotfilesDictMissingKeyError(path, "dest")
    if not isinstance(raw_dest, str):
        raise DotfilesDictWrongTypeError(f"{path}.dest", str, type(raw_dest))

    link_dict: LinkDict = {"source": raw_source, "dest": raw_dest}

    return link_dict


def check_links(raw: dict[str, object], path: str) -> list[LinkDict]:
    raw_links = raw.get("links")
    if raw_links is None:
        raise DotfilesDictMissingKeyError(path, "links")
    if not isinstance(raw_links, list):
        raise DotfilesDictWrongTypeError(f"{path}.links", list, type(raw_links))
    links = cast(list[object], raw_links)

    linkdict_list: list[LinkDict] = []
    for i, raw_link in enumerate(links):
        linkdict_list.append(check_link(raw_link, f"{path}.links[{i}]"))

    return linkdict_list


def check_packages(raw: dict[str, object], path: str) -> list[str]:
    raw_packages = raw.get("packages")
    if raw_packages is None:
        raise DotfilesDictMissingKeyError(path, "packages")
    if not isinstance(raw_packages, list):
        raise DotfilesDictWrongTypeError(f"{path}.packages", list, type(raw_packages))
    packages = cast(list[object], raw_packages)

    packages_list: list[str] = []
    for i, raw_package in enumerate(packages):
        if not isinstance(raw_package, str):
            raise DotfilesDictWrongTypeError(
                f"{path}.packages[{i}]", str, type(raw_package)
            )
        packages_list.append(raw_package)

    return packages_list


def check_modules(raw: dict[str, object], path: str) -> dict[Name, ModuleDict]:
    modules_dict: dict[Name, ModuleDict] = {}
    for name, raw_module in raw.items():
        module_path = f"{path}.{name}"

        if not isinstance(raw_module, dict):
            raise DotfilesDictWrongTypeError(module_path, dict, type(raw_module))
        module = cast(dict[str, object], raw_module)

        allowed_keys = {"packages", "links"}
        diff = set(module) - allowed_keys
        if len(diff) != 0:
            raise DotfilesDictUnknownKeyError(module_path, diff)

        modules_dict[name] = {
            "packages": check_packages(module, module_path),
            "links": check_links(module, module_path),
        }

    return modules_dict


def check_profile_modules(raw: dict[str, object], path: str) -> list[str]:
    raw_modules = raw.get("modules")
    if raw_modules is None:
        raise DotfilesDictMissingKeyError(path, "modules")
    if not isinstance(raw_modules, list):
        raise DotfilesDictWrongTypeError(f"{path}.modules", list, type(raw_modules))
    modules = cast(list[object], raw_modules)

    modules_list: list[str] = []
    for i, module in enumerate(modules):
        if not isinstance(module, str):
            raise DotfilesDictWrongTypeError(f"{path}.modules[{i}]", str, type(module))
        modules_list.append(module)

    return modules_list


def check_package_manager(raw: dict[str, object], path: str) -> str:
    raw_pm = raw.get("package_manager")
    if raw_pm is None:
        raise DotfilesDictMissingKeyError(path, "package_manager")
    if not isinstance(raw_pm, str):
        raise DotfilesDictWrongTypeError(f"{path}.package_manager", str, type(raw_pm))

    return raw_pm


def check_profile(raw: object, path: str) -> ProfileDict:
    if not isinstance(raw, dict):
        raise DotfilesDictWrongTypeError(path, dict, type(raw))
    profile = cast(dict[str, object], raw)

    allowed_keys = {"modules", "package_manager"}
    diff = set(profile) - allowed_keys
    if len(diff) != 0:
        raise DotfilesDictUnknownKeyError(path, diff)

    profile_dict: ProfileDict = {
        "modules": check_profile_modules(profile, path),
        "package_manager": check_package_manager(profile, path),
    }

    return profile_dict


def check_profiles(raw: dict[str, object], path: str) -> dict[Name, ProfileDict]:
    profiles_dict: dict[Name, ProfileDict] = {}

    for name, raw_profile in raw.items():
        profiles_dict[name] = check_profile(raw_profile, f"{path}.{name}")

    return profiles_dict


def check_data_is_dotfiles_dict(data: dict[str, object]) -> DotfilesDict:
    path = "toml"

    allowed_keys = {"modules", "profiles"}
    diff = set(data) - allowed_keys
    if len(diff) != 0:
        raise DotfilesDictUnknownKeyError(path, diff)

    modules = data.get("modules")
    if modules is None:
        raise DotfilesDictMissingKeyError(path, "modules")
    if not isinstance(modules, dict):
        raise DotfilesDictWrongTypeError(f"{path}.modules", dict, type(modules))
    modules = cast(dict[str, object], modules)

    profiles = data.get("profiles")
    if profiles is None:
        raise DotfilesDictMissingKeyError(path, "profiles")
    if not isinstance(profiles, dict):
        raise DotfilesDictWrongTypeError(f"{path}.profiles", dict, type(profiles))
    profiles = cast(dict[str, object], profiles)

    return {
        "modules": check_modules(modules, f"{path}.modules"),
        "profiles": check_profiles(profiles, f"{path}.profiles"),
    }


def load_dotfiles(config_path: str = "examples/dotfiles.toml") -> DotfilesDict:
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    return check_data_is_dotfiles_dict(data)
