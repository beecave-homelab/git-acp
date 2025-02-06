"""Manage git stash operations."""

from git_acp.git.runner import run_git_command, GitError


def manage_stash(
    operation: str, message: str = None, stash_id: str = None, config=None
) -> str:
    """
    Manage stash operations.

    Args:
        operation: "save", "pop", "apply", "drop", or "list".
        message: Stash message for save.
        stash_id: Identifier for pop, apply, or drop.

    Returns:
        The output for the "list" operation, otherwise None.
    """
    if operation == "save":
        cmd = ["git", "stash", "push"]
        if message:
            cmd.extend(["-m", message])
        run_git_command(cmd, config)
    elif operation == "pop":
        cmd = ["git", "stash", "pop"]
        if stash_id:
            cmd.append(stash_id)
        run_git_command(cmd, config)
    elif operation == "apply":
        cmd = ["git", "stash", "apply"]
        if stash_id:
            cmd.append(stash_id)
        run_git_command(cmd, config)
    elif operation == "drop":
        if not stash_id:
            raise GitError("Stash ID is required for drop operation.")
        run_git_command(["git", "stash", "drop", stash_id], config)
    elif operation == "list":
        stdout, _ = run_git_command(["git", "stash", "list"], config)
        return stdout
    return ""
