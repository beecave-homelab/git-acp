"""Commit type classification and change analysis utilities.

This module provides functionality for classifying commit types and analyzing
changes in the repository to suggest appropriate commit types.

Recognized Commit Types:
    FEAT, FIX, DOCS, STYLE, REFACTOR, TEST, CHORE, REVERT, BUILD, CI, PERF.

Classification Priority:
    1. Message prefix (e.g., "feat:", "fix:") - highest priority
    2. File path patterns - deterministic and highly accurate
    3. Message keyword matching - medium priority
    4. Diff-based keyword matching - fallback
    5. Default to CHORE - lowest priority
"""

import re
import shlex
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from git_acp.config import (
    COMMIT_TYPE_PATTERNS,
    COMMIT_TYPES,
    EXCLUDED_PATTERNS,
    FILE_PATH_PATTERNS,
    SIGNAL_LAYER_WEIGHTS,
)
from git_acp.git.diff import extract_added_lines, get_numstat
from git_acp.git.file_classifier import (
    FileCategory,
    _match_file_path_pattern,
    _normalize_path_separators,
    categorize_changed_files,
)
from git_acp.git.git_operations import GitError, get_changed_files, get_diff
from git_acp.utils import OptionalConfig, debug_header, debug_item
from git_acp.utils.file_filter import filter_files_by_scope


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
    BUILD = COMMIT_TYPES["BUILD"]
    CI = COMMIT_TYPES["CI"]
    PERF = COMMIT_TYPES["PERF"]

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
        normalized = type_str.strip().lower()
        for commit_type in cls:
            if normalized == commit_type.name.lower():
                return commit_type
            value = commit_type.value.strip().lower()
            if normalized == value:
                return commit_type
            value_prefix = value.split()[0] if value else value
            if normalized == value_prefix:
                return commit_type

        valid_types = [t.name.lower() for t in cls]
        raise GitError(
            f"Invalid commit type: {type_str}. "
            f"Valid types are: {', '.join(valid_types)}"
        )


@dataclass(frozen=True)
class ClassificationResult:
    """Rich result from the scoring classifier.

    Attributes:
        commit_type: The winning commit type.
        confidence: Score margin ratio between winner and runner-up,
            clamped to [0.0, 1.0].
        scores: Raw score per commit type for debugging.
        is_mixed: True when the commit contains unrelated file groups.
    """

    commit_type: CommitType
    confidence: float
    scores: dict[CommitType, float]
    is_mixed: bool


def get_changes(config: OptionalConfig = None) -> str:
    """Retrieve the staged or unstaged changes in the repository.

    When ``config`` is provided and specifies particular files, the
    unstaged diff is scoped to those files only so that unrelated
    working-directory changes do not influence classification.

    Args:
        config: Optional configuration for scoping and verbose output.

    Returns:
        str: The changes as a diff string

    Raises:
        GitError: If unable to get changes or if no changes are found
    """
    try:
        # First try staged changes
        diff = get_diff("staged", config)
        if not diff:
            # If no staged changes, get unstaged changes scoped to
            # the user's selected files when applicable.
            selected_files: list[str] | None = None
            if (
                config
                and isinstance(config.files, str)
                and config.files
                and config.files != "."
            ):
                selected_files = shlex.split(config.files)
            diff = get_diff("unstaged", config, files=selected_files)

        if not diff:
            raise GitError("No changes detected in the repository.")

        return diff
    except GitError as e:
        msg = "Failed to retrieve changes. Ensure you have a valid Git repo."
        raise GitError(msg) from e


def group_changed_files(
    files: set[str], *, max_non_type_groups: int | None = None
) -> list[list[str]]:
    """Group changed files into deterministic, focused commit batches.

    The grouping algorithm is designed to be pure and deterministic:

    - Commit-type grouping comes first, using ``FILE_PATH_PATTERNS`` and the
      existing ``_match_file_path_pattern()`` matcher.
    - Unmatched files fall back to grouping by a stable directory prefix
      (2-3 levels deep).
    - Unmatched root-level files (no directory) are grouped by file extension.

    Ordering guarantees:

    - Files are sorted alphabetically within each returned group.
    - Groups are ordered by:
        1) Commit-type priority: ``docs``, ``test``, ``perf``, ``style``,
           ``build``, ``ci``, ``chore``.
        2) Directory prefix groups (lexicographic).
        3) Root-level extension groups (lexicographic).

    The input set is filtered using ``EXCLUDED_PATTERNS``.

    Args:
        files: Set of repository-relative file paths.
        max_non_type_groups: Optional maximum number of non commit-type groups
            (directory/extension groups). When provided, the algorithm merges
            the closest groups deterministically until the limit is met.

    Returns:
        A list of file-path groups (each a sorted list of paths).

    Examples:
        >>> group_changed_files({"docs/intro.md", "tests/test_core.py"})
        [['docs/intro.md'], ['tests/test_core.py']]

    Notes:
        ``FILE_PATH_PATTERNS`` and ``EXCLUDED_PATTERNS`` come from
        ``git_acp.config.constants``.
    """
    commit_type_priority = ["docs", "test", "perf", "style", "build", "ci", "chore"]

    def is_excluded(file_path: str) -> bool:
        for pattern in EXCLUDED_PATTERNS:
            # Special case for exact .env matching as defined in EXCLUDED_PATTERNS.
            # This is hardcoded to match the "/.env$" pattern in constants.py.
            if pattern == "/.env$":
                if Path(file_path).name == ".env":
                    return True
                continue
            if pattern in file_path:
                return True
        return False

    remaining = sorted({f for f in files if f and not is_excluded(f)})
    if not remaining:
        return []

    type_groups: dict[str, list[str]] = {t: [] for t in commit_type_priority}
    unmatched: list[str] = []

    for file_path in remaining:
        matched_type: str | None = None
        for commit_type in commit_type_priority:
            for pattern in FILE_PATH_PATTERNS.get(commit_type, []):
                if _match_file_path_pattern(file_path, pattern):
                    matched_type = commit_type
                    break
            if matched_type is not None:
                break

        if matched_type is None:
            unmatched.append(file_path)
        else:
            type_groups[matched_type].append(file_path)

    directory_groups: dict[str, list[str]] = defaultdict(list)
    root_files: list[str] = []
    for file_path in unmatched:
        norm = _normalize_path_separators(file_path).strip("/")
        parts = [p for p in norm.split("/") if p]
        if len(parts) <= 1:
            root_files.append(file_path)
            continue

        # Prefer 2-3 directory levels when available, but fall back to a
        # single directory level when the path is only one level deep.
        max_dir_depth = len(parts) - 1
        depth = min(3, max_dir_depth)
        if max_dir_depth >= 2:
            depth = max(2, depth)
        else:
            depth = 1
        key = "/".join(parts[:depth])
        directory_groups[key].append(file_path)

    extension_groups: dict[str, list[str]] = defaultdict(list)

    def extension_key(file_path: str) -> str:
        suffix = Path(file_path).suffix.lower().lstrip(".")
        return suffix or "no_ext"

    for file_path in root_files:
        extension_groups[extension_key(file_path)].append(file_path)

    non_type_groups: list[tuple[str, str, list[str]]] = []
    for key in sorted(directory_groups):
        non_type_groups.append(("dir", key, sorted(directory_groups[key])))
    for key in sorted(extension_groups):
        non_type_groups.append(("ext", key, sorted(extension_groups[key])))

    def key_segments(kind: str, key: str) -> list[str]:
        if kind == "ext":
            return ["__ext__", key]
        if not key:
            return []
        return [seg for seg in key.split("/") if seg]

    def common_prefix_len(a: list[str], b: list[str]) -> int:
        count = 0
        for left, right in zip(a, b, strict=False):
            if left != right:
                break
            count += 1
        return count

    def merge_non_type_groups(
        groups: list[tuple[str, str, list[str]]], *, max_groups: int
    ) -> list[tuple[str, str, list[str]]]:
        merged = list(groups)
        while len(merged) > max_groups:
            best_pair: tuple[int, int] | None = None
            best_score: tuple[bool, int, int, str, str] | None = None

            for i in range(len(merged) - 1):
                kind_i, key_i, files_i = merged[i]
                seg_i = key_segments(kind_i, key_i)
                for j in range(i + 1, len(merged)):
                    kind_j, key_j, files_j = merged[j]
                    seg_j = key_segments(kind_j, key_j)
                    same_kind = kind_i == kind_j
                    prefix = common_prefix_len(seg_i, seg_j)
                    combined_size = len(files_i) + len(files_j)
                    a_key, b_key = sorted((key_i, key_j))
                    score = (not same_kind, -prefix, combined_size, a_key, b_key)
                    if best_score is None or score < best_score:
                        best_score = score
                        best_pair = (i, j)

            if best_pair is None or best_score is None:
                break

            i, j = best_pair
            kind_i, key_i, files_i = merged[i]
            kind_j, key_j, files_j = merged[j]

            seg_i = key_segments(kind_i, key_i)
            seg_j = key_segments(kind_j, key_j)
            prefix = common_prefix_len(seg_i, seg_j)

            new_kind = kind_i if kind_i == kind_j else "mixed"
            if new_kind == "ext":
                prefix = 0

            if prefix > 0 and new_kind != "ext":
                new_key = "/".join(seg_i[:prefix])
            else:
                new_key = min(key_i, key_j)

            new_files = sorted({*files_i, *files_j})

            for idx in sorted((i, j), reverse=True):
                merged.pop(idx)
            merged.append((new_kind, new_key, new_files))

            merged.sort(key=lambda item: (item[0], item[1]))

        return merged

    if max_non_type_groups is not None and max_non_type_groups > 0:
        non_type_groups = merge_non_type_groups(
            non_type_groups, max_groups=max_non_type_groups
        )

    result: list[list[str]] = []

    for commit_type in commit_type_priority:
        group_files = type_groups[commit_type]
        if group_files:
            result.append(sorted(group_files))

    kind_order = {"dir": 0, "mixed": 1, "ext": 2}
    for _, _, group_files in sorted(
        non_type_groups, key=lambda item: (kind_order.get(item[0], 99), item[1])
    ):
        result.append(sorted(group_files))

    return result


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
        if count >= total_files * 0.5:
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


def strip_conventional_prefix(title: str) -> str:
    """Strip a conventional-commit prefix from a title when present.

    Supported prefixes include:
        - ``type: ...``
        - ``type(scope): ...``
        - ``type emoji: ...``
        - ``type(scope) emoji: ...``

    Args:
        title: Candidate commit title.

    Returns:
        Title without the leading conventional prefix, or the original title if
        no valid conventional prefix is present.
    """
    if not title:
        return title

    commit_type_pattern = "|".join(
        commit_type.name.lower() for commit_type in CommitType
    )
    _emojis = {
        part for ct in CommitType for part in ct.value.split() if not part.isascii()
    }
    emoji_pattern = "|".join(re.escape(e) for e in sorted(_emojis))
    pattern = re.compile(
        rf"^\s*(?:{emoji_pattern})?\s*(?:{commit_type_pattern})(?:\s+(?:{emoji_pattern}))?\s*"
        rf"(?:\([^)]+\))?(?:\s+(?:{emoji_pattern}))?\s*"
        r"(?P<breaking>!?):\s*(?P<body>.+)$",
        flags=re.IGNORECASE,
    )
    match = pattern.match(title)
    if not match:
        return title
    return match.group("body").lstrip()


# Categories whose files should NOT contribute keyword evidence —
# generated output and lockfiles can fire false keyword matches.
_KEYWORD_EXCLUDED_CATEGORIES: frozenset[FileCategory] = frozenset({
    FileCategory.GENERATED,
    FileCategory.DEPENDENCY,
})


def _collect_signals(
    config,
    commit_message: str | None,
    changed_files: set[str],
) -> dict:
    """Gather raw signals from all sources for the scoring classifier.

    Returns:
        A dict with keys:
            prefix_type: CommitType | None — explicit prefix result
            file_categories: dict[FileCategory, set[str]] — grouped files
            numstat: dict[str, tuple[int, int]] — line counts per file
            message_keyword_hits: dict[str, list[str]] — type → matched keywords
            diff_text: str | None — raw diff (for keyword matching)
    """
    prefix_type: CommitType | None = None
    commit_title = (commit_message or "").strip()
    commit_title = commit_title.split("\n", maxsplit=1)[0].strip()
    if commit_title:
        prefix_type = _parse_message_prefix(commit_title, config)

    if config.verbose:
        debug_header("Signal Collection")
        debug_item("Prefix type", prefix_type.name if prefix_type else "None")

    # File categories
    file_categories = categorize_changed_files(changed_files) if changed_files else {}

    if config.verbose and file_categories:
        debug_item(
            "File categories",
            ", ".join(f"{cat.name}({len(f)})" for cat, f in file_categories.items()),
        )

    # Numstat (line impact)
    numstat: dict[str, tuple[int, int]] = {}
    try:
        numstat = get_numstat(config)
    except (GitError, Exception):
        pass

    if config.verbose and numstat:
        debug_item("Numstat files", str(len(numstat)))

    # Message keyword hits
    message_keyword_hits: dict[str, list[str]] = {}
    if commit_message and commit_message.strip():
        for type_name, keywords in COMMIT_TYPE_PATTERNS.items():
            matches = _check_keyword_pattern(
                keywords, commit_message, use_word_boundaries=True, config=config
            )
            if matches:
                message_keyword_hits[type_name] = matches

    # Diff text for keyword matching
    diff_text: str | None = None
    try:
        diff_text = get_changes(config)
    except GitError:
        pass

    return {
        "prefix_type": prefix_type,
        "file_categories": file_categories,
        "numstat": numstat,
        "message_keyword_hits": message_keyword_hits,
        "diff_text": diff_text,
    }


def _score_commit_types(
    signals: dict,
    config,
) -> tuple[dict[CommitType, float], float, bool]:
    """Calculate aggregate scores, confidence, and mixed-change detection.

    Args:
        signals: Output of _collect_signals().
        config: For verbose logging.

    Returns:
        (scores, confidence, is_mixed)

    Raises:
        GitError: If an invalid commit type pattern is encountered.
    """
    scores: dict[CommitType, float] = {ct: 0.0 for ct in CommitType}
    file_categories: dict[FileCategory, set[str]] = signals["file_categories"]
    numstat: dict[str, tuple[int, int]] = signals["numstat"]

    # --- File category signals ---
    # Map FileCategory → contributing CommitType(s)
    category_to_type: dict[FileCategory, CommitType] = {
        FileCategory.TEST: CommitType.TEST,
        FileCategory.DOCS: CommitType.DOCS,
        FileCategory.CI: CommitType.CI,
        FileCategory.BUILD: CommitType.BUILD,
        FileCategory.CONFIG: CommitType.CHORE,
        FileCategory.STYLE: CommitType.STYLE,
        FileCategory.DEPENDENCY: CommitType.CHORE,
    }

    has_production = FileCategory.PRODUCTION in file_categories
    production_types = {
        CommitType.FEAT,
        CommitType.FIX,
        CommitType.REFACTOR,
        CommitType.PERF,
    }

    # Supporting-file logic: when PRODUCTION has changes, TEST and DOCS
    # categories contribute to production-type scores instead of winning
    # independently.
    supporting_categories = {FileCategory.TEST, FileCategory.DOCS}

    for category, files in file_categories.items():
        # Calculate line-impact weight
        total_lines = 0
        for f in files:
            if f in numstat:
                total_lines += numstat[f][0] + numstat[f][1]
        weight = max(total_lines, len(files))  # fallback to file count

        if category in category_to_type:
            target_type = category_to_type[category]
            if has_production and category in supporting_categories:
                # Supporting files boost production-type scores
                for pt in production_types:
                    scores[pt] += weight * SIGNAL_LAYER_WEIGHTS["file_category"] * 0.5
            else:
                scores[target_type] += weight * SIGNAL_LAYER_WEIGHTS["file_category"]

        elif category == FileCategory.PRODUCTION:
            # Distribute production weight across production types
            for pt in production_types:
                scores[pt] += weight * SIGNAL_LAYER_WEIGHTS["file_category"]

    # --- Single-purpose fast paths ---
    # When only one category has files (and no production), give high weight
    if len(file_categories) == 1 and not has_production:
        sole_cat = next(iter(file_categories))
        if sole_cat in category_to_type:
            scores[category_to_type[sole_cat]] += 10.0  # strong boost

    # --- Message keyword signals ---
    for type_name, _matches in signals["message_keyword_hits"].items():
        try:
            ct = CommitType[type_name.upper()]
            scores[ct] += len(_matches) * SIGNAL_LAYER_WEIGHTS["message_keyword"]
        except KeyError:
            msg = (
                f"Invalid commit type pattern: {type_name}. "
                "Check commit type definitions."
            )
            raise GitError(msg)

    # --- Diff keyword signals ---
    diff_text = signals["diff_text"]
    if diff_text:
        # Exclude generated/dependency file added lines from keyword matching.
        excluded_files: set[str] = set()
        for cat in _KEYWORD_EXCLUDED_CATEGORIES:
            excluded_files.update(file_categories.get(cat, set()))

        added_lines = extract_added_lines(diff_text, excluded_files)
        # Fall back to raw text when extract_added_lines returns nothing
        # (e.g. the input is not in unified diff format)
        keyword_text = added_lines if added_lines else diff_text

        for type_name, keywords in COMMIT_TYPE_PATTERNS.items():
            matches = _check_keyword_pattern(
                keywords, keyword_text, use_word_boundaries=False, config=config
            )
            if matches:
                try:
                    ct = CommitType[type_name.upper()]
                    scores[ct] += len(matches) * SIGNAL_LAYER_WEIGHTS["diff_keyword"]
                except KeyError:
                    msg = (
                        f"Invalid commit type pattern: {type_name}. "
                        "Check commit type definitions."
                    )
                    raise GitError(msg)

    # --- Remove REVERT from scoring (only via explicit prefix) ---
    scores[CommitType.REVERT] = 0.0

    # --- Calculate confidence ---
    sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
    top_type, top_score = sorted_scores[0]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

    if top_score == 0:
        confidence = 0.0
    elif second_score == 0:
        confidence = 1.0
    else:
        confidence = min((top_score - second_score) / top_score, 1.0)

    # --- Tiebreaker: alphabetical CommitType name ---
    if top_score == second_score and second_score > 0:
        # Re-sort equal-top by name for deterministic results
        equal_top = [(ct, s) for ct, s in sorted_scores if s == top_score]
        equal_top.sort(key=lambda x: x[0].name)
        top_type = equal_top[0][0]

    # --- Mixed change detection ---
    is_mixed = False
    if has_production and len(file_categories) >= 3:
        # Production + 2+ other distinct categories = likely mixed
        non_prod_cats = {k for k in file_categories if k != FileCategory.PRODUCTION}
        supporting_count = len(non_prod_cats & supporting_categories)
        if len(non_prod_cats) - supporting_count >= 1:
            is_mixed = True

    if config.verbose:
        debug_header("Scoring Results")
        debug_item("Top type", top_type.name)
        debug_item("Confidence", f"{confidence:.2f}")
        debug_item("Is mixed", str(is_mixed))
        debug_item(
            "Scores",
            ", ".join(f"{ct.name}:{s:.1f}" for ct, s in sorted_scores[:5] if s > 0),
        )

    return scores, confidence, is_mixed


def classify_commit(config, commit_message: str | None = None) -> ClassificationResult:
    """Classify commit type using the weighted scoring system.

    Orchestrates the full flow:
        1. Explicit prefix check (short-circuits)
        2. Signal collection
        3. Scoring with confidence and mixed detection
        4. Result assembly

    Args:
        config: GitConfig instance.
        commit_message: Optional commit message for keyword signals.

    Returns:
        ClassificationResult with commit_type, confidence, scores, is_mixed.

    Raises:
        GitError: If an unexpected error occurs during classification.
    """
    try:
        if config.verbose:
            debug_header("Starting Commit Classification (Scoring)")

        # Get changed files (with file-scoping to user selection)
        try:
            changed_files = get_changed_files(config, staged_only=True)
            if not changed_files:
                changed_files = get_changed_files(config, staged_only=False)
            if (
                changed_files
                and isinstance(config.files, str)
                and config.files
                and config.files != "."
            ):
                changed_files = filter_files_by_scope(changed_files, config.files)
        except GitError:
            changed_files = set()

        signals = _collect_signals(config, commit_message, changed_files)

        # Short-circuit: explicit prefix wins
        if signals["prefix_type"] is not None:
            result = ClassificationResult(
                commit_type=signals["prefix_type"],
                confidence=1.0,
                scores={ct: 0.0 for ct in CommitType},
                is_mixed=False,
            )
            result.scores[signals["prefix_type"]] = 1.0
            if config.verbose:
                debug_header("Commit Classification Result")
                debug_item("Selected Type", signals["prefix_type"].name)
                debug_item("Source", "message_prefix (short-circuit)")
            return result

        # Score everything
        scores, confidence, is_mixed = _score_commit_types(signals, config)

        # Pick winner (default to CHORE when no signal matched)
        sorted_scores = sorted(scores.items(), key=lambda x: (-x[1], x[0].name))
        top_score = sorted_scores[0][1] if sorted_scores else 0.0
        winner = sorted_scores[0][0] if top_score > 0 else CommitType.CHORE

        if config.verbose:
            debug_header("Commit Classification Result")
            debug_item("Selected Type", winner.name)
            debug_item("Confidence", f"{confidence:.2f}")
            debug_item("Source", "scoring")

        return ClassificationResult(
            commit_type=winner,
            confidence=confidence,
            scores=scores,
            is_mixed=is_mixed,
        )

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


def classify_commit_type(config, commit_message: str | None = None) -> CommitType:
    """Classify the commit type based on file paths, message, and diff content.

    This is the backward-compatible API that delegates to the weighted
    scoring classifier (:func:`classify_commit`) and returns only the
    commit type.

    Args:
        config: GitConfig instance containing configuration options.
        commit_message: The generated (and possibly edited) commit message.

    Returns:
        CommitType: The classified commit type.
    """
    result = classify_commit(config, commit_message)
    return result.commit_type
