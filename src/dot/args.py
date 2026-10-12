import argparse


class CliArgs(argparse.Namespace):
    command: str = ""
    name: str | None = None
    dry_run: bool = False
    verbose: bool = False
    config: str = ""
    module: str | None = None
    profile: str = ""
