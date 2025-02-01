"""Git status operations: retrieving changed files and unstaging."""
from git_acp.git.runner import run_git_command, GitError
from git_acp.config.settings import GIT_SETTINGS
from git_acp.utils import debug_item

def get_changed_files(config=None) -> set:
    """Retrieve the set of changed files."""
    stdout, _ = run_git_command(["git", "status", "--porcelain", "-uall"], config)
    files = set()
    for line in stdout.splitlines():
        if not line.strip():
            continue
        if " -> " in line:
            path = line.split(" -> ")[-1].strip()
        else:
            path = line[2:].lstrip()
        if any(pattern in path for pattern in GIT_SETTINGS["excluded_patterns"]):
            continue
        files.add(path)
    return files

def unstage_files(config=None) -> None:
    """Unstage all files."""
    try:
        run_git_command(["git", "reset", "HEAD"], config)
    except GitError as e:
        raise GitError(f"Failed to unstage files: {str(e)}") from e 