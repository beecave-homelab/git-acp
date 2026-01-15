"""File filtering utilities for scoped file selection."""

from __future__ import annotations

# Use Path.match for consistent glob semantics (including **/ handling).
import shlex
from pathlib import Path


def filter_files_by_scope(files: set[str], add_patterns: str | None) -> set[str]:
    """Filter files based on raw -a scope patterns.

    Args:
        files: Set of repository-relative file paths.
        add_patterns: Raw -a patterns string (or None).

    Returns:
        Filtered set of files within the provided scope patterns.
    """
    if add_patterns is None:
        return set(files)

    stripped = add_patterns.strip()
    if stripped in {".", "./"}:
        return set(files)

    targets = shlex.split(add_patterns)
    if any(target in {".", "./"} for target in targets):
        return set(files)
    if not targets:
        return set()

    filtered: set[str] = set()
    for path in files:
        for target in targets:
            if not target:
                continue
            normalized = target.strip()
            if normalized.startswith("./"):
                normalized = normalized[2:]
            normalized = normalized.rstrip("/")
            if not normalized:
                continue
            if path == normalized or path.startswith(f"{normalized}/"):
                filtered.add(path)
                break
            if "*" in normalized or "?" in normalized or "[" in normalized:
                if "/" not in normalized and "*" not in normalized and "/" in path:
                    continue
                if "/" in normalized:
                    patterns = [normalized]
                    if "**/" in normalized:
                        patterns.append(normalized.replace("**/", ""))
                elif "*" in normalized:
                    patterns = [normalized, f"**/{normalized}"]
                else:
                    patterns = [normalized]
                if any(Path(path).match(pattern) for pattern in patterns):
                    filtered.add(path)
                    break

    return filtered
