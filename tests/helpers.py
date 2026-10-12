from collections.abc import Callable

from dot.infra.config_loader import RawLink
from dot.context import Context


type MakeCtx = Callable[[list[RawLink]], Context]
