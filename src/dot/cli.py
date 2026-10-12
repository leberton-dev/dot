import argparse

HELP: dict[str, str] = {
    "dry run": "see what would happen",
    "verbose": "log more output",
    "status": "show the state of every link",
    "install": "install packages and create links for the detected profile",
    "add": "move a file into the repo, link it back and register it in the toml",
    "add name": "name of dotfile",
    "remove": "unlink a module and restore the real files",
    "remove module": "module to unlink",
    "doctor": "report unlinked repo files, dead links and invalid toml",
    "undo": "restore the backups made by the last install",
    "config": "choose which config",
    "profile": "choose which profile",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dot", description="manage your dotfiles")

    common = argparse.ArgumentParser(add_help=False)
    _ = common.add_argument(
        "--dry-run", required=False, help=HELP["dry run"], action="store_true"
    )
    _ = common.add_argument(
        "--verbose", required=False, help=HELP["verbose"], action="store_true"
    )
    _ = common.add_argument(
        "--config", help=HELP["config"], default="~/.dotfiles/dotfiles.toml"
    )
    _ = common.add_argument("--profile", help=HELP["profile"], default="asahi")

    subparsers = parser.add_subparsers(dest="command", required=True)

    _ = subparsers.add_parser("status", help=HELP["status"], parents=[common])
    _ = subparsers.add_parser("install", help=HELP["install"], parents=[common])
    add =subparsers.add_parser("add", help=HELP["add"], parents=[common])
    _ = add.add_argument("path", help=HELP["add name"], metavar="FILE")
    remove = subparsers.add_parser("remove", help=HELP["remove"], parents=[common])
    _ = remove.add_argument("module", help=HELP["remove module"], metavar="MODULE")
    _ = subparsers.add_parser("doctor", help=HELP["doctor"], parents=[common])
    _ = subparsers.add_parser("undo", help=HELP["undo"], parents=[common])

    return parser
