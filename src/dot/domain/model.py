from dataclasses import dataclass
from enum import auto, StrEnum
from pathlib import Path


class PackageManager(StrEnum):
    dnf = auto()
    apt = auto()
    pacman = auto()
    brew = auto()


@dataclass(frozen=True)
class Link:
    module: str
    source: Path
    dest: Path

@dataclass(frozen=True)
class Module:
    name: str
    packages: tuple[str, ...]
    links: tuple[Link, ...]

@dataclass(frozen=True)
class Profile:
    name: str
    package_manager: PackageManager
    modules: tuple[Module, ...]

    @property
    def links(self) -> tuple[Link, ...]:
        return tuple(link for module in self.modules for link in module.links)

@dataclass(frozen=True)
class Config:
    modules: dict[str, Module]
    profiles: dict[str, Profile]
