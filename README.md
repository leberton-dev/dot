# v1.0.0

First stable release of `dot`, a dotfiles manager driven by a single `dotfiles.toml`.

## Commands

| Command              | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `dot status`         | Show the state of every link: ok, broken, missing, modified                 |
| `dot install`        | Install packages and create links for the detected profile, with backups    |
| `dot add <file>`     | Move a file into the repo, link it back and register it in the toml         |
| `dot remove <module>`| Unlink a module and restore the real files                                  |
| `dot doctor`         | Report unlinked repo files, dead links and invalid toml                     |
| `dot undo`           | Restore the backups made by the last install                                |

Global options: `--dry-run`, `--verbose`, `--config <path>`, `--help`, `--version`

## Tasks

### Setup
- [x] Init project with uv (`pyproject.toml`, `src/dot/`, entry point `dot`)
- [x] CLI skeleton with subcommands and global options
- [ ] Define the `dotfiles.toml` format (profiles, modules, packages, links)
- [ ] Write an example `dotfiles.toml` matching the current `.dotfiles` repo

### Core
- [ ] Load and validate the toml (clear error messages)
- [ ] Path handling: expand `~`, resolve paths relative to the repo
- [ ] Link state detection: ok / missing / broken / wrong target / real file in place
- [ ] Profile detection (hostname, existing paths, OS)
- [ ] Package manager detection (dnf, apt, pacman, brew)

### Commands
- [ ] `status`: print the state of every link, grouped by module
- [ ] `install`: create links, back up existing files, idempotent
- [ ] `install`: install missing packages for the active profile
- [ ] `install`: record backups in a state file for `undo`
- [ ] `add`: move file into repo, create link, update the toml
- [ ] `remove`: delete links of a module, restore the real files
- [ ] `doctor`: list repo files not referenced in the toml
- [ ] `doctor`: list dead links and invalid toml entries
- [ ] `undo`: restore backups from the last install
- [ ] `--dry-run` support for every command that writes

### Quality
- [ ] Tests running in a temporary fake `$HOME`
- [ ] Test idempotence (install twice = no change)
- [ ] GitHub Actions CI (lint + tests)
- [ ] README: install, toml format, examples for each command

### Release
- [ ] Replace `install.sh` in `.dotfiles` with `dot install`
- [ ] Tag `v1.0.0`
