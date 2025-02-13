"""Git tag operations."""

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command


def create_tag(tag_name: str, message: str = None, config=None) -> None:
    """Create a new tag.

    Args:
        tag_name: Name of the tag
        message: Optional tag message
        config: Optional configuration

    Raises:
        GitError: If creating tag fails
    """
    try:
        if message:
            run_git_command(["git", "tag", "-a", tag_name, "-m", message], config)
        else:
            run_git_command(["git", "tag", tag_name], config)
    except Exception as e:
        raise GitError(f"Failed to create tag: {str(e)}") from e


def delete_tag(tag_name: str, config=None) -> None:
    """Delete a tag.

    Args:
        tag_name: Name of the tag to delete
        config: Optional configuration

    Raises:
        GitError: If deleting tag fails
    """
    try:
        run_git_command(["git", "tag", "-d", tag_name], config)
    except Exception as e:
        raise GitError(f"Failed to delete tag: {str(e)}") from e


def list_tags(config=None) -> list:
    """List all tags.

    Args:
        config: Optional configuration

    Returns:
        list: List of tag names

    Raises:
        GitError: If listing tags fails
    """
    try:
        stdout, _ = run_git_command(["git", "tag", "--list"], config)
        return stdout.split("\n") if stdout else []
    except Exception as e:
        raise GitError(f"Failed to list tags: {str(e)}") from e
