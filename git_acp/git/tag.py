"""Manage git tag operations."""
from git_acp.git.runner import run_git_command, GitError

def manage_tags(operation: str, tag_name: str, message: str = None, config=None) -> None:
    """
    Manage tags: create, delete, or push.
    
    Args:
        operation: "create", "delete", or "push".
        tag_name: The name of the tag.
        message: Tag message (for creation).
    """
    if operation == "create":
        if message:
            run_git_command(["git", "tag", "-a", tag_name, "-m", message], config)
        else:
            run_git_command(["git", "tag", tag_name], config)
    elif operation == "delete":
        run_git_command(["git", "tag", "-d", tag_name], config)
    elif operation == "push":
        run_git_command(["git", "push", "origin", tag_name], config) 