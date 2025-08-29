from __future__ import annotations

from typing import Literal, Optional

from git_acp.utils import OptionalConfig, debug_header, debug_item
from git_acp.git.core import GitError


def create_branch(branch_name: str, config: OptionalConfig = None) -> None:
    """Create a new git branch."""
    try:
        from git_acp.git.git_operations import run_git_command
        if config and config.verbose:
            debug_header("Creating branch")
            debug_item("Creating branch", branch_name)
        run_git_command(["git", "checkout", "-b", branch_name], config)
    except GitError as e:
        raise GitError(f"Failed to create branch: {str(e)}") from e


def delete_branch(branch_name: str, force: bool = False, config: OptionalConfig = None) -> None:
    """Delete a git branch."""
    try:
        from git_acp.git.git_operations import run_git_command
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
    """Merge a branch into the current branch."""
    try:
        from git_acp.git.git_operations import run_git_command
        if config and config.verbose:
            debug_header("Merging branch")
            debug_item("Merging branch", source_branch)
        run_git_command(["git", "merge", source_branch], config)
    except GitError as e:
        raise GitError(f"Failed to merge branch: {str(e)}") from e


def manage_remote(
    operation: Literal["add", "remove", "set-url"],
    remote_name: str,
    url: Optional[str] = None,
    config: OptionalConfig = None,
) -> None:
    """Manage git remotes (add, remove, set-url)."""
    try:
        if config and config.verbose:
            debug_item(f"Remote operation: {operation}", f"{remote_name} {url or ''}")

        from git_acp.git.git_operations import run_git_command

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
    message: Optional[str] = None,
    config: OptionalConfig = None,
) -> None:
    """Manage git tags (create, delete, push)."""
    try:
        if config and config.verbose:
            debug_item(f"Tag operation: {operation}", tag_name)

        from git_acp.git.git_operations import run_git_command

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
    message: Optional[str] = None,
    stash_id: Optional[str] = None,
    config: OptionalConfig = None,
) -> Optional[str]:
    """Manage git stash operations."""
    try:
        if config and config.verbose:
            debug_item(f"Stash operation: {operation}", f"{message or ''} {stash_id or ''}")

        from git_acp.git.git_operations import run_git_command

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
