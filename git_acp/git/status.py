"""
Git status operations and file tracking.
"""

from typing import Dict, List

from git_acp.git.runner import GitError, run_git_command
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


def get_name_status_changes(target: str, source: str) -> Dict[str, List[str]]:
    """Get name-status changes between two branches.

    Args:
        target: Target branch name
        source: Source branch name

    Returns:
        Dictionary with keys 'added', 'modified', and 'deleted',
        each containing a list of file paths

    Raises:
        GitError: If getting name-status changes fails
    """
    try:
        output, _ = run_git_command([
            "git", "diff", "--name-status",
            f"{target}...{source}"
        ], config=None)
        changes = {
            "added": [],
            "modified": [],
            "deleted": []
        }
        
        for line in output.split("\n"):
            if not line.strip():
                continue
                
            try:
                status, file_path = line.split(maxsplit=1)
                status = status.strip()
                file_path = file_path.strip()
                
                if status == "A":
                    changes["added"].append(file_path)
                elif status == "M":
                    changes["modified"].append(file_path)
                elif status == "D":
                    changes["deleted"].append(file_path)
            except ValueError:
                continue  # Skip malformed lines
                
        return changes
    except Exception as e:
        raise GitError(f"Failed to get name-status changes: {str(e)}") from e 