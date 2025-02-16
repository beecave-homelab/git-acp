"""Core Git operations and utilities."""

import subprocess
from typing import Tuple

from git_acp.utils import debug_header, debug_item
from git_acp.git.exceptions import GitError


def run_git_command(command: list, config=None) -> Tuple[str, str]:
    """
    Execute a git command.

    Args:
        command: List of command parts.
        config: Optional configuration.

    Returns:
        Tuple of (stdout, stderr).

    Raises:
        GitError: On failure.
    """
    try:
        if config and config.verbose:
            debug_header("Executing Git command")
            debug_item(config, "Command", " ".join(command))
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            # Common git errors with specific suggestions
            error_map = {
                "not a git repository": (
                    "Not a git repository.",
                    "Run 'git init' or check directory",
                ),
                "nothing to commit": (
                    "No changes to commit.",
                    "Stage some changes first with 'git add' or create new files.",
                ),
                "permission denied": (
                    "Permission denied.",
                    "Check your file permissions and Git credentials.",
                ),
                "branch .* not found": (
                    "Branch not found.",
                    "Create the branch first or check the branch name.",
                ),
                "remote .* not found": (
                    "Remote not found.",
                    "Add the remote first with 'git remote add' or check the remote "
                    "name.",
                ),
                "pull request already exists": (
                    "Pull request already exists.",
                    "Check existing pull requests or create a new branch for your "
                    "changes.",
                ),
            }

            for pattern, (message, suggestion) in error_map.items():
                if pattern in stderr.lower():
                    raise GitError(message, suggestion=suggestion)

            # Generic git error with actual output
            error_msg = (
                f"Git command failed:\n"
                f"Command: {' '.join(command)}\n"
                f"Exit code: {process.returncode}\n"
                f"Stdout: {stdout}\n"
                f"Stderr: {stderr}"
            )
            if config and config.verbose:
                debug_item(config, "Error Details", error_msg)
            raise GitError(
                error_msg,
                suggestion=(
                    "Check the error message above and ensure your Git "
                    "configuration is correct."
                ),
            )
        return stdout.strip(), stderr.strip()
    except FileNotFoundError as exc:
        raise GitError(
            "Git is not installed or not in PATH.",
            suggestion="Install Git or add it to your system PATH.",
        ) from exc
    except Exception as e:
        raise GitError(
            f"Failed to execute git command: {str(e)}",
            suggestion="Check your Git installation and configuration.",
        ) from e
