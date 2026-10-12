TOML_TYPE_NAMES: dict[type, str] = {
    str: "string",
    int: "integer",
    bool: "boolean",
    list: "array",
    dict: "table",
}


def _type_name(t: type) -> str:
    return TOML_TYPE_NAMES.get(t, t.__name__)


class DotError(Exception):
    """Base error for dot program"""

    exit_code: int = 1

    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(message)


class ConfigError(DotError):
    """Parent class for config errors"""


class ConfigFileNotFoundError(ConfigError):
    """Raised when the config file was not found"""

    def __init__(self, path: str) -> None:
        self.path: str = path
        super().__init__(f"config file not found: {path}")


class ConfigTypeError(ConfigError):
    """Raised when a value has not the correct type"""

    def __init__(self, path: str, expected: type, got: type) -> None:
        self.path: str = path
        self.expected: type = expected
        self.got: type = got
        super().__init__(
            f"{path}: expected {_type_name(expected)}, got {_type_name(got)}"
        )


class ConfigMissingKeyError(ConfigError):
    """Raised when a key is missing"""

    def __init__(self, path: str, missing: str) -> None:
        self.path: str = path
        self.missing: str = missing
        message = f"{path}: missing key '{missing}'"
        super().__init__(message)


class ConfigUnknownKeyError(ConfigError):
    """Raised when a key is unknown"""

    def __init__(self, path: str, unknown: set[str]) -> None:
        self.path: str = path
        self.unknown: set[str] = unknown
        keys = ", ".join(f"'{k}'" for k in sorted(unknown))
        label = "key" if len(unknown) == 1 else "keys"
        message = f"{path}: unknown {label} {keys}"
        super().__init__(message)


class StateFileError(DotError):
    """Parent class for state file errors"""


class StateFileWrongTypeError(StateFileError):
    """Raised when a value has not the correct type"""

    def __init__(self, path: str, expected: type, got: type) -> None:
        self.path: str = path
        self.expected: type = expected
        self.got: type = got
        super().__init__(
            f"{path}: expected {_type_name(expected)}, got {_type_name(got)}"
        )


class StateFileMissingKeyError(StateFileError):
    """Raised when a key is missing"""

    def __init__(self, path: str, missing: str) -> None:
        self.path: str = path
        self.missing: str = missing
        message = f"{path}: missing key '{missing}'"
        super().__init__(message)


class StateFileUnknownActionError(StateFileError):
    """Raised when an action is unknown"""

    def __init__(self, path: str, action: str) -> None:
        self.path: str = path
        self.action: str = action
        super().__init__(f"{path}: unknown action '{action}'")


class ProfileNotFoundError(DotError):
    """Raised when a profile is absent from the config"""

    exit_code: int = 2

    def __init__(self, name: str, available: list[str]) -> None:
        self.name: str = name
        self.available: list[str] = available
        super().__init__(
            f"profile '{name}' not found (available: {', '.join(available)})"
        )


class CommandNotImplementedError(DotError):
    """Raised when a command is not implemented"""

    exit_code: int = 2

    def __init__(self, command: str) -> None:
        super().__init__(f"command '{command}' is not implemented yet")
