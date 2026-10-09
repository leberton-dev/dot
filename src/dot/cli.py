import argparse


class DotArgs(argparse.Namespace):
    action: str = ""
    name: str | None = None
    dry_run: bool = False
    verbose: bool = False
    config: str = ""


HELP_MSG: dict[str, str] = {
    "dry run": "see what would happen",
    "verbose": "log more output",
    "status": "show the state of every link",
    "install": "install packages and create links for the detected profile",
    "add": "move a file into the repo, link it back and register it in the toml",
    "add_name": "name of dotfile",
    "remove": "unlink a module and restore the real files",
    "remove_module": "module to unlink",
    "doctor": "report unlinked repo files, dead links and invalid toml",
    "undo": "restore the backups made by the last install",
    "config": "choose which config",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dot", description="manage your dotfiles")

    commun = argparse.ArgumentParser(add_help=False)
    _ = commun.add_argument(
        "--dry-run", required=False, help=HELP_MSG["dry run"], action="store_true"
    )
    _ = commun.add_argument(
        "--verbose", required=False, help=HELP_MSG["verbose"], action="store_true"
    )
    _ = commun.add_argument(
        "--config", help=HELP_MSG["config"], default="~/.dotfiles/dotfiles.toml"
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    _ = subparsers.add_parser("status", help=HELP_MSG["status"], parents=[commun])
    _ = subparsers.add_parser("install", help=HELP_MSG["install"], parents=[commun])
    add = subparsers.add_parser("add", help=HELP_MSG["add"], parents=[commun])
    _ = add.add_argument("name", help=HELP_MSG["add_name"], metavar="NAME")
    remove = subparsers.add_parser("remove", help=HELP_MSG["remove"], parents=[commun])
    _ = remove.add_argument("module", help=HELP_MSG["remove_module"], metavar="MODULE")
    _ = subparsers.add_parser("doctor", help=HELP_MSG["doctor"], parents=[commun])
    _ = subparsers.add_parser("undo", help=HELP_MSG["undo"], parents=[commun])

    return parser
