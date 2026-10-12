from collections.abc import Callable

from dot.config import Link
from dot.context import Context


type MakeCtx = Callable[[list[Link]], Context]
