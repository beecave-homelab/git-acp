"""File category classification for the scoring commit classifier.

Separates file purpose (where files live) from commit type (what the
commit does). The two public functions feed into the signal collection
phase of the scoring classifier.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

from git_acp.config import EXCLUDED_PATTERNS, FILE_CATEGORY_PATTERNS


class FileCategory(Enum):
    """Classification of file purpose, separate from commit type.

    Used to weight signals in the scoring classifier: production files
    carry more weight than supporting files (tests, docs).
    """

    PRODUCTION = "production"
    TEST = "test"
    DOCS = "docs"
    CI = "ci"
    BUILD = "build"
    CONFIG = "config"
    DEPENDENCY = "dependency"
    GENERATED = "generated"
    STYLE = "style"
    UNKNOWN = "unknown"


def _normalize_path_separators(value: str) -> str:
    return re.sub(r"[\\/]+", "/", value)


def _match_file_path_pattern(file_path: str, pattern: str) -> bool:
    file_norm = _normalize_path_separators(file_path).strip("/")
    if not file_norm:
        return False

    file_segments = [seg.lower() for seg in file_norm.split("/") if seg]

    pattern_norm = _normalize_path_separators(pattern)
    if not pattern_norm:
        return False

    pattern_lower = pattern_norm.lower()
    if "/" in pattern_lower:
        is_dir_pattern = pattern_lower.endswith("/")
        pattern_segments = [seg for seg in pattern_lower.strip("/").split("/") if seg]
        if not pattern_segments:
            return False

        if is_dir_pattern and len(pattern_segments) == 1:
            target = pattern_segments[0]
            return any(seg == target for seg in file_segments)

        for i in range(0, len(file_segments) - len(pattern_segments) + 1):
            if file_segments[i : i + len(pattern_segments)] == pattern_segments:
                return True
        return False

    if re.fullmatch(r"[a-z0-9_]+", pattern_lower):
        regex = re.compile(rf"\b{re.escape(pattern_lower)}\b", flags=re.IGNORECASE)
        return any(bool(regex.search(seg)) for seg in file_segments)

    if pattern_lower.endswith("_"):
        return any(seg.startswith(pattern_lower) for seg in file_segments)

    if pattern_lower.startswith("_"):
        return any(seg.endswith(pattern_lower) for seg in file_segments)

    return any(pattern_lower in seg for seg in file_segments)


def is_file_excluded(file_path: str) -> bool:
    """Check whether *file_path* matches any ``EXCLUDED_PATTERNS`` entry.

    Uses :func:`_match_file_path_pattern` for consistent segment-aware
    matching, the same matcher used by file-category and commit-type
    classification. The ``/.env$`` pattern is special-cased because it
    represents an exact-basename match (``.env`` but not
    ``.env.example``) that cannot be expressed as a literal substring.

    Returns:
        ``True`` if the file path matches any exclusion pattern.
    """
    for pattern in EXCLUDED_PATTERNS:
        if pattern == "/.env$":
            if Path(file_path).name == ".env":
                return True
            continue
        if _match_file_path_pattern(file_path, pattern):
            return True
    return False


def classify_file_category(path: str) -> FileCategory:
    """Classify a single file path into a FileCategory.

    Uses ``FILE_CATEGORY_PATTERNS`` from constants. The match order is
    significant: STYLE is checked before CONFIG (STYLE ⊂ CONFIG), and
    DEPENDENCY/GENERATED are checked before other categories to ensure
    lockfiles and build artefacts are correctly categorised.

    Files that match no pattern are classified as ``PRODUCTION`` — this
    is the default for source code files that don't live in test/docs/etc
    directories.

    Args:
        path: Repository-relative file path.

    Returns:
        The matching FileCategory, or PRODUCTION for unmatched files.
    """
    # Order matters: more specific categories first.
    category_order = [
        "DEPENDENCY",
        "GENERATED",
        "STYLE",  # before CONFIG (STYLE ⊂ CONFIG)
        "CI",
        "TEST",
        "DOCS",
        "BUILD",
        "CONFIG",
    ]

    for category_name in category_order:
        patterns = FILE_CATEGORY_PATTERNS.get(category_name, [])
        for pattern in patterns:
            if _match_file_path_pattern(path, pattern):
                return FileCategory[category_name]

    return FileCategory.PRODUCTION


def categorize_changed_files(files: set[str]) -> dict[FileCategory, set[str]]:
    """Group a set of file paths by their FileCategory.

    Args:
        files: Set of repository-relative file paths.

    Returns:
        Dict mapping each FileCategory to the set of matching files.
        Only categories with matches are included.
    """
    result: dict[FileCategory, set[str]] = {}
    for path in files:
        category = classify_file_category(path)
        result.setdefault(category, set()).add(path)
    return result
