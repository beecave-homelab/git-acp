"""Git stash operations."""

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command


def stash_changes(message: str = None, config=None) -> None:
    """Stash current changes.

    Args:
        message: Optional stash message
        config: Optional configuration

    Raises:
        GitError: If stashing changes fails
    """
    try:
        if message:
            run_git_command(["git", "stash", "save", message], config)
        else:
            run_git_command(["git", "stash"], config)
    except Exception as e:
        raise GitError(f"Failed to stash changes: {str(e)}") from e


def pop_stash(stash_id: str = None, config=None) -> None:
    """Pop changes from stash.

    Args:
        stash_id: Optional stash ID to pop
        config: Optional configuration

    Raises:
        GitError: If popping stash fails
    """
    try:
        if stash_id:
            run_git_command(["git", "stash", "pop", stash_id], config)
        else:
            run_git_command(["git", "stash", "pop"], config)
    except Exception as e:
        raise GitError(f"Failed to pop stash: {str(e)}") from e


def list_stashes(config=None) -> list:
    """List all stashes.

    Args:
        config: Optional configuration

    Returns:
        list: List of stash entries

    Raises:
        GitError: If listing stashes fails
    """
    try:
        stdout, _ = run_git_command(["git", "stash", "list"], config)
        return stdout.split("\n") if stdout else []
    except Exception as e:
        raise GitError(f"Failed to list stashes: {str(e)}") from e


def clear_stashes(config=None) -> None:
    """Clear all stashes.

    Args:
        config: Optional configuration

    Raises:
        GitError: If clearing stashes fails
    """
    try:
        run_git_command(["git", "stash", "clear"], config)
    except Exception as e:
        raise GitError(f"Failed to clear stashes: {str(e)}") from e
