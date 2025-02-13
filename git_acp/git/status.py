"""
Git status operations and file tracking.
"""

from typing import Dict, List
from collections import defaultdict

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command
from git_acp.config.settings import GIT_SETTINGS


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
        output, _ = run_git_command(
            ["git", "diff", "--name-status", f"{target}...{source}"], config=None
        )
        changes = {"added": [], "modified": [], "deleted": []}

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


def analyze_diff_hotspots(diff_text: str, top_n: int = 3) -> List[str]:
    """Analyze diff text to find most modified files.

    Args:
        diff_text: Raw diff output
        top_n: Number of top files to return

    Returns:
        List of file paths ordered by modification frequency
    """

    file_changes = defaultdict(int)

    current_file = None
    for line in diff_text.split("\n"):
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
        elif line.startswith("@@"):
            if current_file:
                file_changes[current_file] += 1

    return sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:top_n]
