"""Branch management functions."""
from git_acp.git.runner import run_git_command, GitError
from git_acp.utils import debug_header, debug_item

def get_current_branch(config=None) -> str:
    """Retrieve the current git branch name."""
    stdout, _ = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], config)
    if not stdout:
        raise GitError("Failed to determine the current branch.")
    return stdout

def create_branch(branch_name: str, config=None) -> None:
    """Create a new branch."""
    run_git_command(["git", "checkout", "-b", branch_name], config)

def delete_branch(branch_name: str, force: bool = False, config=None) -> None:
    """Delete an existing branch."""
    if force:
        run_git_command(["git", "branch", "-D", branch_name], config)
    else:
        run_git_command(["git", "branch", "-d", branch_name], config)

def merge_branch(source_branch: str, config=None) -> None:
    """Merge a branch into the current branch."""
    run_git_command(["git", "merge", source_branch], config) 