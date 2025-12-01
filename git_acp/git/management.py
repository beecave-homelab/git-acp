"""Git branch, tag, remote, and stash management operations."""

from __future__ import annotations

from typing import Literal

from git_acp.utils import OptionalConfig, debug_header, debug_item

from .core import GitError, run_git_command


def create_branch(branch_name: str, config: OptionalConfig = None) -> None:
    """Create a new git branch.

    Args:
        branch_name: Name of the branch to create.
        config: Optional configuration for verbose output.

    Raises:
        GitError: If branch creation fails.
    """
    try:
        if config and config.verbose:
            debug_header("Creating branch")
            debug_item("Creating branch", branch_name)
        run_git_command(["git", "checkout", "-b", branch_name], config)
    except GitError as e:
        raise GitError(f"Failed to create branch: {str(e)}") from e


def delete_branch(
    branch_name: str, force: bool = False, config: OptionalConfig = None
) -> None:
    """Delete a git branch.

    Args:
        branch_name: Name of the branch to delete.
        force: If True, force delete even if not merged.
        config: Optional configuration for verbose output.

    Raises:
        GitError: If branch deletion fails.
    """
    try:
        if config and config.verbose:
            debug_header("Deleting branch")
            debug_item("Deleting branch", branch_name)
        if force:
            run_git_command(["git", "branch", "-D", branch_name], config)
        else:
            run_git_command(["git", "branch", "-d", branch_name], config)
    except GitError as e:
        raise GitError(f"Failed to delete branch: {str(e)}") from e


def merge_branch(source_branch: str, config: OptionalConfig = None) -> None:
    """Merge a branch into the current branch.

    Args:
        source_branch: Name of the branch to merge from.
        config: Optional configuration for verbose output.

    Raises:
        GitError: If merge fails.
    """
    try:
        if config and config.verbose:
            debug_header("Merging branch")
            debug_item("Merging branch", source_branch)
        run_git_command(["git", "merge", source_branch], config)
    except GitError as e:
        raise GitError(f"Failed to merge branch: {str(e)}") from e


def manage_remote(
    operation: Literal["add", "remove", "set-url"],
    remote_name: str,
    url: str | None = None,
    config: OptionalConfig = None,
) -> None:
    """Manage git remotes (add, remove, set-url).

    Args:
        operation: The remote operation to perform.
        remote_name: Name of the remote.
        url: URL for the remote (required for 'add' and 'set-url').
        config: Optional configuration for verbose output.

    Raises:
        GitError: If the remote operation fails.
    """
    try:
        if config and config.verbose:
            debug_item(f"Remote operation: {operation}", f"{remote_name} {url or ''}")

        if operation == "add":
            if not url:
                raise GitError("URL is required for adding a remote")
            run_git_command(["git", "remote", "add", remote_name, url], config)
        elif operation == "remove":
            run_git_command(["git", "remote", "remove", remote_name], config)
        elif operation == "set-url":
            if not url:
                raise GitError("URL is required for setting remote URL")
            run_git_command(["git", "remote", "set-url", remote_name, url], config)
    except GitError as e:
        raise GitError(f"Failed to {operation} remote: {str(e)}") from e


def manage_tags(
    operation: Literal["create", "delete", "push"],
    tag_name: str,
    message: str | None = None,
    config: OptionalConfig = None,
) -> None:
    """Manage git tags (create, delete, push).

    Args:
        operation: The tag operation to perform.
        tag_name: Name of the tag.
        message: Optional message for annotated tags.
        config: Optional configuration for verbose output.

    Raises:
        GitError: If the tag operation fails.
    """
    try:
        if config and config.verbose:
            debug_item(f"Tag operation: {operation}", tag_name)

        if operation == "create":
            if message:
                run_git_command(["git", "tag", "-a", tag_name, "-m", message], config)
            else:
                run_git_command(["git", "tag", tag_name], config)
        elif operation == "delete":
            run_git_command(["git", "tag", "-d", tag_name], config)
        elif operation == "push":
            run_git_command(["git", "push", "origin", tag_name], config)
    except GitError as e:
        raise GitError(f"Failed to {operation} tag: {str(e)}") from e


def manage_stash(
    operation: Literal["save", "pop", "apply", "drop", "list"],
    message: str | None = None,
    stash_id: str | None = None,
    config: OptionalConfig = None,
) -> str | None:
    """Manage git stash operations.

    Args:
        operation: The stash operation to perform.
        message: Optional message for 'save' operation.
        stash_id: Stash identifier for 'pop', 'apply', 'drop' operations.
        config: Optional configuration for verbose output.

    Returns:
        str | None: Stash list output for 'list' operation, None otherwise.

    Raises:
        GitError: If the stash operation fails.
    """
    try:
        if config and config.verbose:
            debug_item(
                f"Stash operation: {operation}", f"{message or ''} {stash_id or ''}"
            )

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
                raise GitError("Stash ID is required for drop operation")
            run_git_command(["git", "stash", "drop", stash_id], config)
        elif operation == "list":
            stdout, _ = run_git_command(["git", "stash", "list"], config)
            return stdout
    except GitError as e:
        raise GitError(f"Failed to {operation} stash: {str(e)}") from e
    return None
