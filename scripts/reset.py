import shutil
from pathlib import Path

TEST_PATH: str = "/tmp/dot-test/"


def reset_home() -> None:
    home = Path(TEST_PATH + "home")
    if home.exists():
        shutil.rmtree(home)


def copy_to_home() -> None:
    home = Path(TEST_PATH + "home")
    dotfiles = Path(TEST_PATH + "dotfiles")

    if not dotfiles.exists():
        raise ValueError("error: dotfiles do not exists, cannot continue")

    home.mkdir(exist_ok=True)

    # skip .zshrc for missing state
    _ = shutil.copy(dotfiles / "git/config", home / ".gitconfig")  # conflict state
    # _ = (home / ".gitconfig.bak").write_text("OLD BACKUP")
    _ = shutil.copytree(dotfiles / "nvim", home / ".config/nvim")  # conflict state
    _ = Path(home / ".zprofile").symlink_to(
        dotfiles / "some/path/thatdoes/not/exists"
    )  # dangling state
    another_file_path = Path("/tmp/another_file.txt")
    _ = another_file_path.write_text(
        "Hello from another file, this is not the .gitmessage.txt"
    )  # wrong target state
    _ = Path(home / ".gitmessage.txt").symlink_to(another_file_path)
    _ = Path(home / ".config/i3").symlink_to(dotfiles / "i3")  # linked state


if __name__ == "__main__":
    reset_home()
    copy_to_home()
