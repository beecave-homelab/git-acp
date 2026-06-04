"""File category classification for the scoring commit classifier.

Separates file purpose (where files live) from commit type (what the
commit does). The two public functions feed into the signal collection
phase of the scoring classifier.
"""

from __future__ import annotations

from git_acp.config import FILE_CATEGORY_PATTERNS
from git_acp.git.classification import FileCategory, _match_file_path_pattern


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
                return FileCategory(category_name)

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
