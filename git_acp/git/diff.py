from __future__ import annotations

import shlex
from typing import Optional, Set

from git_acp.config import EXCLUDED_PATTERNS
from git_acp.utils import DiffType, OptionalConfig, debug_header, debug_item
from git_acp.git.core import GitError


def get_changed_files(config: OptionalConfig = None, staged_only: bool = False) -> Set[str]:
    """Get list of changed files."""
    from git_acp.git.git_operations import run_git_command

    files: Set[str] = set()
    if config and config.verbose:
        debug_header(f"Getting {'staged ' if staged_only else ''}changed files")

    if staged_only:
        stdout_staged_only, _ = run_git_command(["git", "diff", "--staged", "--name-only"], config)
        if config and config.verbose:
            debug_item("Raw git diff --staged --name-only output", stdout_staged_only)
        files = set(stdout_staged_only.splitlines())
    else:
        stdout_status, _ = run_git_command(["git", "status", "--porcelain", "-uall"], config)
        if config and config.verbose:
            debug_item("Raw git status --porcelain -uall output", stdout_status)

        def process_status_line(line: str) -> Optional[str]:
            if not line.strip():
                return None
            if config and config.verbose:
                debug_item("Processing status line", line)
            if " -> " in line:
                path = line.split(" -> ")[-1].strip()
            else:
                path = line[2:].lstrip()
            if config and config.verbose:
                debug_item("Extracted path from status", path)
            return path

        for line in stdout_status.splitlines():
            path = process_status_line(line)
            if path:
                files.add(path)

    if files:
        excluded_files = set()
        for f in files:
            for pattern in EXCLUDED_PATTERNS:
                if pattern in f:
                    if config and config.verbose:
                        debug_item("Excluding file based on pattern", f"Pattern '{pattern}' matched '{f}'")
                    excluded_files.add(f)
                    break
        files -= excluded_files

    if config and config.verbose:
        debug_item("Final file set after exclusion", str(files))

    return files


def get_diff(diff_type: DiffType = "staged", config: OptionalConfig = None) -> str:
    """Get the git diff output for staged or unstaged changes."""
    from git_acp.git.git_operations import run_git_command
    try:
        if config and config.verbose:
            debug_header(f"Getting {diff_type} diff")

        if diff_type == "staged":
            stdout, _ = run_git_command(["git", "diff", "--staged"], config)
        else:
            stdout, _ = run_git_command(["git", "diff"], config)

        if config and config.verbose:
            debug_item("Diff length", str(len(stdout)))

        return stdout

    except GitError as e:
        raise GitError(f"Failed to get {diff_type} diff: {str(e)}") from e
