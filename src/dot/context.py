from dataclasses import dataclass
from pathlib import Path

from dot.domain.model import Config, Profile
from dot.infra.reporter import Reporter


@dataclass(frozen=True)
class Context:
    config: Config
    profile: Profile
    path_dotfiles: Path
    path_home: Path
    path_state: Path
    reporter: Reporter
