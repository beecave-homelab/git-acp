"""Git diff and changed files operations."""

from __future__ import annotations

from pathlib import Path

from git_acp.config import EXCLUDED_PATTERNS
from git_acp.utils import DiffType, OptionalConfig, debug_header, debug_item

from .core import GitError, run_git_command

# Default line count assigned to binary files in numstat output
# (shown as "-" in git diff --numstat).
_BINARY_LINE_COUNT: int = 10


def get_changed_files(
    config: OptionalConfig = None, staged_only: bool = False
) -> set[str]:
    """Get list of changed files.

    Args:
        config: Optional configuration for verbose output.
        staged_only: If True, only return staged files.

    Returns:
        set[str]: Set of changed file paths.
    """
    files: set[str] = set()
    if config and config.verbose:
        debug_header(f"Getting {'staged ' if staged_only else ''}changed files")

    if staged_only:
        stdout_staged_only, _ = run_git_command(
            ["git", "diff", "--staged", "--name-only"], config
        )
        if config and config.verbose:
            debug_item("Raw git diff --staged --name-only output", stdout_staged_only)
        files = set(stdout_staged_only.splitlines())
    else:
        stdout_status, _ = run_git_command(
            ["git", "status", "--porcelain", "-uall"], config
        )
        if config and config.verbose:
            debug_item("Raw git status --porcelain -uall output", stdout_status)

        def process_status_line(line: str) -> str | None:
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
                if pattern == "/.env$":
                    if Path(f).name == ".env":
                        if config and config.verbose:
                            debug_item(
                                "Excluding file based on pattern",
                                f"Pattern '{pattern}' matched '{f}'",
                            )
                        excluded_files.add(f)
                        break
                    continue

                if pattern in f:
                    if config and config.verbose:
                        debug_item(
                            "Excluding file based on pattern",
                            f"Pattern '{pattern}' matched '{f}'",
                        )
                    excluded_files.add(f)
                    break
        files -= excluded_files

    if config and config.verbose:
        debug_item("Final file set after exclusion", str(files))

    return files


def get_diff(
    diff_type: DiffType = "staged",
    config: OptionalConfig = None,
    files: list[str] | None = None,
) -> str:
    """Get the git diff output for staged or unstaged changes.

    Args:
        diff_type: Type of diff to retrieve ('staged' or 'unstaged').
        config: Optional configuration for verbose output.
        files: Optional list of file paths to scope the diff to.
            When provided, only changes to these files are included.

    Returns:
        str: The diff output as a string.

    Raises:
        GitError: If the diff command fails.
    """
    try:
        if config and config.verbose:
            debug_header(f"Getting {diff_type} diff")

        cmd: list[str] = (
            ["git", "diff", "--staged"] if diff_type == "staged" else ["git", "diff"]
        )
        if files:
            cmd.append("--")
            cmd.extend(files)

        stdout, _ = run_git_command(cmd, config)

        if config and config.verbose:
            debug_item("Diff length", str(len(stdout)))

        return stdout

    except GitError as e:
        raise GitError(f"Failed to get {diff_type} diff: {str(e)}") from e


def get_numstat(config: OptionalConfig = None) -> dict[str, tuple[int, int]]:
    """Get line-level change statistics per file via ``git diff --numstat``.

    Tries staged changes first, falls back to unstaged if no output.

    Args:
        config: Optional configuration for verbose output.

    Returns:
        Dict mapping file paths to ``(added, removed)`` line counts.
        Binary files receive ``(_BINARY_LINE_COUNT, 0)``.
        Files matching ``EXCLUDED_PATTERNS`` are filtered out.
    """
    stdout: str | None = None
    for flag in ("--staged", None):
        cmd = ["git", "diff"]
        if flag:
            cmd.append(flag)
        cmd.append("--numstat")
        try:
            out, _ = run_git_command(cmd, config)
            if out.strip():
                stdout = out
                break
        except GitError:
            continue

    if not stdout or not stdout.strip():
        return {}

    if config and config.verbose:
        debug_header("Parsing numstat output")

    result: dict[str, tuple[int, int]] = {}
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue

        added_str, removed_str, filepath = parts
        added = _BINARY_LINE_COUNT if added_str == "-" else int(added_str)
        removed = 0 if removed_str == "-" else int(removed_str)

        # Apply exclusion filter
        excluded = False
        for pattern in EXCLUDED_PATTERNS:
            if pattern == "/.env$" and Path(filepath).name == ".env":
                excluded = True
                break
            if pattern in filepath:
                excluded = True
                break
        if excluded:
            continue

        result[filepath] = (added, removed)

    if config and config.verbose:
        debug_item("Numstat entries", str(len(result)))

    return result


def extract_added_lines(
    diff: str, excluded_files: set[str] | None = None
) -> str:
    """Extract only added lines from a unified diff.

    Strips the leading ``+`` from each added line. Skips ``+++ `` file
    headers and hunk metadata (lines starting with ``@@``). Lines from
    files in *excluded_files* are skipped so that generated/dependency
    content does not pollute keyword matching.

    Args:
        diff: Raw unified diff output.
        excluded_files: Optional set of file paths whose added lines
            should be skipped. Paths are matched against the ``b/``
            component of the ``+++ b/path`` header.

    Returns:
        Concatenated added lines as a single string.
    """
    skip = excluded_files or set()
    added: list[str] = []
    current_file = ""
    for line in diff.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            if line.startswith("+++ "):
                path = line[4:].strip()
                # Strip the leading "b/" that git prepends.
                current_file = path[2:] if path.startswith("b/") else path
            continue
        if line.startswith("@@"):
            continue
        if line.startswith("+") and current_file not in skip:
            added.append(line[1:])
    return "\n".join(added)
