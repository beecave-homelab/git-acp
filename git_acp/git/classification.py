"""Commit type classification and change analysis utilities.

This module provides functionality for classifying commit types and analyzing
changes in the repository to suggest appropriate commit types.

Classification Priority:
    1. Message prefix (e.g., "feat:", "fix:") - highest priority
    2. File path patterns - deterministic and highly accurate
    3. Message keyword matching - medium priority
    4. Diff-based keyword matching - fallback
    5. Default to CHORE - lowest priority
"""

import re
from enum import Enum

from git_acp.config import COMMIT_TYPE_PATTERNS, COMMIT_TYPES, FILE_PATH_PATTERNS
from git_acp.git.git_operations import GitError, get_changed_files, get_diff
from git_acp.utils import debug_header, debug_item


class CommitType(Enum):
    """Enumeration of conventional commit types with emojis."""

    FEAT = COMMIT_TYPES["FEAT"]
    FIX = COMMIT_TYPES["FIX"]
    DOCS = COMMIT_TYPES["DOCS"]
    STYLE = COMMIT_TYPES["STYLE"]
    REFACTOR = COMMIT_TYPES["REFACTOR"]
    TEST = COMMIT_TYPES["TEST"]
    CHORE = COMMIT_TYPES["CHORE"]
    REVERT = COMMIT_TYPES["REVERT"]

    @classmethod
    def from_str(cls, type_str: str) -> "CommitType":
        """Convert a string to a CommitType enum value.

        Args:
            type_str: The commit type string to convert

        Returns:
            CommitType: The corresponding enum value

        Raises:
            GitError: If the type string is invalid
        """
        try:
            return cls[type_str.upper()]
        except KeyError:
            valid_types = [t.name.lower() for t in cls]
            raise GitError(
                f"Invalid commit type: {type_str}. "
                f"Valid types are: {', '.join(valid_types)}"
            )


def get_changes() -> str:
    """Retrieve the staged or unstaged changes in the repository.

    Returns:
        str: The changes as a diff string

    Raises:
        GitError: If unable to get changes or if no changes are found
    """
    try:
        # First try staged changes
        diff = get_diff("staged")
        if not diff:
            # If no staged changes, get unstaged changes
            diff = get_diff("unstaged")

        if not diff:
            raise GitError("No changes detected in the repository.")

        return diff
    except GitError as e:
        msg = "Failed to retrieve changes. Ensure you have a valid Git repo."
        raise GitError(msg) from e


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


def _classify_by_file_paths(
    changed_files: set[str],
    config,
) -> CommitType | None:
    """Classify commit type based on changed file paths.

    Args:
        changed_files: Set of changed file paths.
        config: GitConfig instance for verbose logging.

    Returns:
        CommitType if a match is found, None otherwise.
    """
    if not changed_files:
        return None

    # Count matches for each type
    type_scores: dict[str, int] = {}

    for file_path in changed_files:
        for commit_type, patterns in FILE_PATH_PATTERNS.items():
            for pattern in patterns:
                if _match_file_path_pattern(file_path, pattern):
                    type_scores[commit_type] = type_scores.get(commit_type, 0) + 1
                    break  # One match per file per type is enough

    if not type_scores:
        return None

    # Check if all files match a single type (strong signal)
    total_files = len(changed_files)
    for commit_type, count in sorted(type_scores.items(), key=lambda x: -x[1]):
        # If majority of files match this type, use it
        if count >= total_files * 0.5 or count == total_files:
            if config.verbose:
                debug_header("Commit Classification Result")
                debug_item("Selected Type", commit_type.upper())
                debug_item("Source", "file_paths")
                debug_item("Matched Files", f"{count}/{total_files}")
            try:
                return CommitType[commit_type.upper()]
            except KeyError:
                continue

    return None


def _check_keyword_pattern(
    keywords: list[str],
    text: str,
    *,
    use_word_boundaries: bool,
    config,
) -> list[str]:
    """Return the list of matched keywords.

    Args:
        keywords: Keywords to search for.
        text: Text to search in.
        use_word_boundaries: Whether to apply word boundary matching.
        config: GitConfig instance for verbose logging.

    Returns:
        List of matched keywords.
    """
    lowered = text.lower()
    matches: list[str] = []

    for keyword in keywords:
        key = keyword.lower()
        if not key:
            continue

        is_plain_word = bool(re.fullmatch(r"[a-z0-9]+(?: [a-z0-9]+)*", key))
        if use_word_boundaries and is_plain_word:
            pattern = rf"\b{re.escape(key)}\b"
            if re.search(pattern, lowered):
                matches.append(keyword)
        elif key in lowered:
            matches.append(keyword)

    if matches and config.verbose:
        debug_item("Matched Keywords", ", ".join(matches))
    return matches


def _parse_message_prefix(commit_title: str, config) -> CommitType | None:
    """Parse a conventional commit type from the message prefix.

    This supports prefixes like:
        - ``feat: ...``
        - ``feat(scope): ...``
        - ``feat ✨: ...``
        - ``feat(scope) ✨: ...``

    Args:
        commit_title: First line of the commit message.
        config: GitConfig instance for verbose logging.

    Returns:
        Parsed commit type, or None if no valid prefix is present.
    """
    if ":" not in commit_title:
        return None

    prefix = commit_title.split(":", maxsplit=1)[0].strip()
    if not prefix:
        return None

    match = re.match(r"^(?P<type>[a-z]+)(?P<rest>.*)$", prefix, flags=re.IGNORECASE)
    if not match:
        return None

    type_str = match.group("type")
    rest = match.group("rest").strip()

    # Strip optional (scope)
    if rest.startswith("("):
        scope_match = re.match(r"^\([^\)]+\)", rest)
        if not scope_match:
            return None
        rest = rest[scope_match.end() :].strip()

    # Remaining characters (if any) must be non-alphanumeric. This prevents
    # false positives like "feat update: ...".
    if rest and re.search(r"[A-Za-z0-9_]", rest):
        return None

    try:
        parsed_type = CommitType.from_str(type_str)
    except GitError:
        return None

    if config.verbose:
        debug_header("Commit Classification Result")
        debug_item("Selected Type", type_str.lower())
        debug_item("Source", "message_prefix")

    return parsed_type


def classify_commit_type(config, commit_message: str | None = None) -> CommitType:
    """Classify the commit type based on file paths, message, and diff content.

    Classification priority:
        1. Message prefix (e.g., "feat:", "fix:") - explicit intent
        2. File path patterns - deterministic and highly accurate
        3. Message keyword matching - semantic hints
        4. Diff-based keyword matching - fallback
        5. Default to CHORE

    Args:
        config: GitConfig instance containing configuration options.
        commit_message: The generated (and possibly edited) commit message.

    Returns:
        CommitType: The classified commit type.

    Raises:
        GitError: If unable to classify commit type or if changes cannot be retrieved.
    """
    try:
        if config.verbose:
            debug_header("Starting Commit Classification")

        # Priority 1: Check for explicit type prefix in commit message
        commit_title = (commit_message or "").strip()
        commit_title = commit_title.split("\n", maxsplit=1)[0].strip()
        if commit_title:
            parsed_type = _parse_message_prefix(commit_title, config)
            if parsed_type is not None:
                return parsed_type

        # Priority 2: Classify by file paths (most reliable heuristic)
        try:
            changed_files = get_changed_files(config, staged_only=True)
            if not changed_files:
                changed_files = get_changed_files(config, staged_only=False)
        except GitError:
            changed_files = set()

        if changed_files:
            file_based_type = _classify_by_file_paths(changed_files, config)
            if file_based_type is not None:
                return file_based_type

        # Priority 3: Message keyword matching
        if commit_message and commit_message.strip():
            for commit_type, keywords in COMMIT_TYPE_PATTERNS.items():
                try:
                    matches = _check_keyword_pattern(
                        keywords,
                        commit_message,
                        use_word_boundaries=True,
                        config=config,
                    )
                    if matches:
                        if config.verbose:
                            debug_header("Commit Classification Result")
                            debug_item("Selected Type", commit_type.upper())
                            debug_item("Source", "commit_message")
                        return CommitType[commit_type.upper()]
                except KeyError as e:
                    if config.verbose:
                        debug_header("Invalid Commit Type")
                        debug_item("Type", commit_type)
                        debug_item("Error", str(e))
                    msg = (
                        f"Invalid commit type pattern: {commit_type}. "
                        "Check commit type definitions."
                    )
                    raise GitError(msg) from e

        # Priority 4: Diff-based keyword matching (fallback)
        diff = get_changes()

        for commit_type, keywords in COMMIT_TYPE_PATTERNS.items():
            try:
                matches = _check_keyword_pattern(
                    keywords, diff, use_word_boundaries=False, config=config
                )
                if matches:
                    if config.verbose:
                        debug_header("Commit Classification Result")
                        debug_item("Selected Type", commit_type.upper())
                        debug_item("Source", "git_diff")
                    return CommitType[commit_type.upper()]
            except KeyError as e:
                if config.verbose:
                    debug_header("Invalid Commit Type")
                    debug_item("Type", commit_type)
                    debug_item("Error", str(e))
                msg = (
                    f"Invalid commit type pattern: {commit_type}. "
                    "Check commit type definitions."
                )
                raise GitError(msg) from e

        # Priority 5: Default to CHORE
        if config.verbose:
            debug_header("No Specific Pattern Matched")
            debug_item("Default Type", "CHORE")
        return CommitType.CHORE

    except GitError as e:
        if config.verbose:
            debug_header("Commit Classification Failed")
            debug_item("Error Type", "GitError")
            debug_item("Error Message", str(e))
        raise GitError(f"Failed to classify commit type: {str(e)}") from e
    except Exception as e:
        if config.verbose:
            debug_header("Unexpected Classification Error")
            debug_item("Error Type", e.__class__.__name__)
            debug_item("Error Message", str(e))
        raise GitError(
            "An unexpected error occurred during commit classification."
        ) from e
