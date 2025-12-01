"""Core git command execution and error handling."""

from __future__ import annotations

import subprocess

from git_acp.utils import OptionalConfig, debug_header, debug_item


class GitError(Exception):
    """Custom exception for git-related errors."""


def run_git_command(
    command: list[str], config: OptionalConfig = None
) -> tuple[str, str]:
    """Execute a git command and return its output.

    Args:
        command: List of command arguments to execute.
        config: Optional configuration for verbose output.

    Returns:
        tuple[str, str]: Tuple of (stdout, stderr) from the command.

    Raises:
        GitError: If the command fails or git is not available.
    """
    try:
        if config and config.verbose:
            debug_header("Git Command Execution")
            debug_item("Command", " ".join(command))

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            if config and config.verbose:
                debug_header("Git Command Failed")
                debug_item("Command", " ".join(command))
                debug_item("Exit Code", str(process.returncode))
                debug_item("Error Output", stderr.strip())

            error_patterns = {
                "not a git repository": (
                    "Not a git repository. Please run this command in a git repository."
                ),
                "did not match any files": (
                    "No files matched the specified pattern. "
                    "Please check the file paths."
                ),
                "nothing to commit": (
                    "No changes to commit. Working directory is clean."
                ),
                "permission denied": (
                    "Permission denied. Please check your repository permissions."
                ),
                "remote: repository not found": (
                    "Remote repository not found. "
                    "Please check the repository URL and your access rights."
                ),
                "failed to push": (
                    "Failed to push changes. "
                    "Please pull the latest changes and resolve any conflicts."
                ),
                "cannot lock ref": (
                    "Cannot lock ref. Another git process may be running."
                ),
                "refusing to merge unrelated histories": (
                    "Cannot merge unrelated histories. "
                    "Use --allow-unrelated-histories if intended."
                ),
                "your local changes would be overwritten": (
                    "Local changes would be overwritten. "
                    "Please commit or stash them first."
                ),
            }

            for pattern, message in error_patterns.items():
                if pattern in stderr.lower():
                    raise GitError(message)

            raise GitError(f"Git command failed: {stderr.strip()}")

        if config and config.verbose and stdout.strip():
            debug_item("Command Output", stdout.strip())

        return stdout.strip(), stderr.strip()

    except FileNotFoundError:
        if config and config.verbose:
            debug_header("Git Command Error")
            debug_item("Error Type", "FileNotFoundError")
        raise GitError(
            "Git is not installed or not in PATH. Please install git and try again."
        )
    except PermissionError:
        if config and config.verbose:
            debug_header("Git Command Error")
            debug_item("Error Type", "PermissionError")
            debug_item("Command", " ".join(command))
        raise GitError(
            "Permission denied while executing git command. "
            "Please check your permissions."
        )
    except Exception as e:
        if config and config.verbose:
            debug_header("Git Command Error")
            debug_item("Error Type", e.__class__.__name__)
            debug_item("Error Message", str(e))
            debug_item("Command", " ".join(command))
        raise GitError(f"Failed to execute git command: {str(e)}") from e
