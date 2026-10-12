import sys
import typing


class Reporter:
    def __init__(
        self,
        out: typing.TextIO | None = None,
        err: typing.TextIO | None = None,
        verbose: bool = False,
    ) -> None:
        self._out: typing.TextIO = out if out else sys.stdout
        self._err: typing.TextIO = err if err else sys.stderr
        self._verbose: bool = verbose

    def info(self, msg: str) -> None:
        _ = self._out.write(msg + "\n")

    def debug(self, msg: str) -> None:
        if self._verbose:
            _ = self._err.write("[debug] " + msg + "\n")

    def warn(self, msg: str) -> None:
        _ = self._err.write("dot: warning: " + msg + "\n")

    def error(self, msg: str) -> None:
        _ = self._err.write("dot: error: " + msg + "\n")
