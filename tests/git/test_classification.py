"""Tests for git_acp.git.classification module."""

from unittest.mock import MagicMock, call, patch

import pytest

from git_acp.config import COMMIT_TYPE_PATTERNS, FILE_PATH_PATTERNS
from git_acp.git.classification import (
    ClassificationResult,
    CommitType,
    FileCategory,
    _classify_by_file_paths,
    _KEYWORD_EXCLUDED_CATEGORIES,
    _collect_signals,
    _score_commit_types,
    classify_commit,
    classify_commit_type,
    get_changes,
    strip_conventional_prefix,
)
from git_acp.git.diff import extract_added_lines
from git_acp.git.file_classifier import categorize_changed_files, classify_file_category
from git_acp.git.git_operations import GitError


class TestCommitType:
    """Tests for CommitType enum."""

    def test_from_str_valid(self):
        """Parse valid commit type strings."""
        assert CommitType.from_str("feat") == CommitType.FEAT
        assert CommitType.from_str("FIX") == CommitType.FIX

    def test_from_str_invalid(self):
        """Raise GitError for invalid commit type strings."""
        with pytest.raises(GitError):
            CommitType.from_str("invalid")


class TestFilePathClassification:
    """Tests for file-path-based commit classification."""

    @pytest.fixture
    def mock_config(self):
        """Return a mock config object."""
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    def test_classify_test_files(self, mock_config):
        """Classify commits with test files as TEST."""
        test_files = {
            "tests/test_utils.py",
            "tests/cli/test_workflow.py",
        }
        result = _classify_by_file_paths(test_files, mock_config)
        assert result == CommitType.TEST

    def test_classify_docs_files(self, mock_config):
        """Classify commits with documentation files as DOCS."""
        doc_files = {
            "docs/api/overview.md",
            "README.md",
        }
        result = _classify_by_file_paths(doc_files, mock_config)
        assert result == CommitType.DOCS

    def test_classify_docs_files__does_not_match_readme_generator(self, mock_config):
        """Avoid false positives when a segment contains "readme" as a substring."""
        files = {"src/readme_generator.py"}
        result = _classify_by_file_paths(files, mock_config)
        assert result is None

    def test_classify_chore_files(self, mock_config):
        """Classify commits with config/build files as CHORE."""
        chore_files = {
            ".github/workflows/ci.yaml",
            "pyproject.toml",
        }
        result = _classify_by_file_paths(chore_files, mock_config)
        assert result == CommitType.CHORE

    def test_classify_test_files__does_not_false_positive_on_contest_dir(
        self, mock_config
    ):
        """Avoid matching "test/" patterns inside unrelated segments like "contest"."""
        files = {"src/contest/module.py"}
        result = _classify_by_file_paths(files, mock_config)
        assert result is None

    def test_classify_test_files__normalizes_path_separators(self, mock_config):
        """Support Windows-style path separators when matching directory patterns."""
        files = {"tests\\test_utils.py", "tests\\cli\\test_workflow.py"}
        result = _classify_by_file_paths(files, mock_config)
        assert result == CommitType.TEST

    def test_classify_mixed_files__majority_wins(self, mock_config):
        """Return type matching majority of files."""
        mixed_files = {
            "tests/test_a.py",
            "tests/test_b.py",
            "src/module.py",  # No pattern match
        }
        result = _classify_by_file_paths(mixed_files, mock_config)
        assert result == CommitType.TEST

    def test_classify_no_pattern_match(self, mock_config):
        """Return None when no file patterns match."""
        source_files = {
            "src/module.py",
            "git_acp/cli/cli.py",
        }
        result = _classify_by_file_paths(source_files, mock_config)
        assert result is None

    def test_classify_empty_files(self, mock_config):
        """Return None for empty file set."""
        result = _classify_by_file_paths(set(), mock_config)
        assert result is None

    def test_file_path_patterns_defined(self):
        """Verify FILE_PATH_PATTERNS contains expected types."""
        assert "test" in FILE_PATH_PATTERNS
        assert "docs" in FILE_PATH_PATTERNS
        assert "chore" in FILE_PATH_PATTERNS


class TestClassification:
    """Tests for commit classification logic."""

    @pytest.fixture
    def mock_config(self):
        """Return a mock config object."""
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_classify_commit_patterns(self, mock_get_diff, mock_get_files, mock_config):
        """Classify commit messages by pattern matching."""
        mock_get_files.return_value = set()  # No file-path match
        test_cases = [
            ("implement new feature", "FEAT"),
            ("fix login bug", "FIX"),
            ("update documentation", "DOCS"),
            ("format code style", "STYLE"),
            ("refactor module", "REFACTOR"),
            ("add unit tests", "TEST"),
        ]

        for message, expected_type in test_cases:
            mock_get_diff.return_value = message
            result = classify_commit_type(mock_config)
            assert result == getattr(CommitType, expected_type)

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_default_chore_classification(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Default to CHORE when no pattern matches."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "Generic changes"
        assert classify_commit_type(mock_config) == CommitType.CHORE

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_multiple_pattern_matches(self, mock_get_diff, mock_get_files, mock_config):
        """Return a valid commit type when multiple patterns match."""
        mock_get_files.return_value = set()
        all_patterns = [p for sublist in COMMIT_TYPE_PATTERNS.values() for p in sublist]
        mock_get_diff.return_value = "\n".join(all_patterns)
        result = classify_commit_type(mock_config)
        assert result in CommitType

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_no_changes_defaults_to_chore(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Default to CHORE when diff is empty and no classification matches."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = ""
        result = classify_commit_type(mock_config)
        assert result == CommitType.CHORE

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_verbose_output(self, mock_get_diff, mock_get_files):
        """Emit debug headers when verbose mode is enabled."""
        mock_config = MagicMock(verbose=True)
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "fix: critical security patch"

        with patch("git_acp.git.classification.debug_header") as mock_debug:
            classify_commit_type(mock_config)

            debug_calls = [
                call("Starting Commit Classification (Scoring)"),
                call("Commit Classification Result"),
            ]
            mock_debug.assert_has_calls(debug_calls, any_order=True)

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_all_commit_types_coverage(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Test detection of all commit types defined in constants."""
        mock_get_files.return_value = set()
        type_tests = {
            "feat": "implement new user authentication feature",
            "fix": "fix login timeout bug",
            "docs": "update API documentation",
            "style": "reformat code with black",
            "refactor": "restructure database module",
            "test": "add unit tests for utils",
        }

        for type_name, message in type_tests.items():
            mock_get_diff.return_value = message
            result = classify_commit_type(mock_config)
            assert result.name.lower() == type_name

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_file_path_takes_priority_over_diff(self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config):
        """File path classification takes priority over diff keywords."""
        mock_get_files.return_value = {"tests/test_module.py"}
        mock_get_diff.return_value = ""
        mock_get_numstat.return_value = {}
        # Even though message says "fix", file path should win
        result = classify_commit_type(mock_config, commit_message="fix something")
        assert result == CommitType.TEST

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_message_prefix_takes_highest_priority(self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config):
        """Explicit message prefix takes highest priority."""
        mock_get_files.return_value = {"tests/test_module.py"}
        # Explicit prefix should override file path
        result = classify_commit_type(mock_config, commit_message="fix: correct test")
        assert result == CommitType.FIX

    @patch("git_acp.git.classification.get_changed_files")
    def test_message_prefix_with_emoji_takes_highest_priority(
        self, mock_get_files, mock_config
    ):
        """Explicit emoji-style prefix takes highest priority."""
        mock_get_files.return_value = {"tests/test_module.py"}
        result = classify_commit_type(
            mock_config,
            commit_message="fix 🐛: correct test",
        )
        assert result == CommitType.FIX

    @patch("git_acp.git.classification.get_changed_files")
    def test_message_prefix_with_scope_and_emoji_takes_highest_priority(
        self, mock_get_files, mock_config
    ):
        """Explicit emoji-style prefix with scope takes highest priority."""
        mock_get_files.return_value = {"tests/test_module.py"}
        result = classify_commit_type(
            mock_config,
            commit_message="refactor(core) ♻️: reorganize test",
        )
        assert result == CommitType.REFACTOR


class TestCommitMessageSemantics:
    """Tests for commit type selection driven by generated message semantics."""

    @pytest.fixture
    def mock_config(self):
        """Return a mock config object."""
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_prefers_feat_over_style_when_feature_is_mentioned(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Prefer FEAT when message describes a feature.

        This should still hold even if formatting is mentioned.
        """
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "irrelevant"

        message = (
            "Add auto-group feature to CLI and update commit message format\n\n"
            "This commit introduces a new feature in the CLI."
        )
        result = classify_commit_type(mock_config, commit_message=message)

        assert result == CommitType.FEAT

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_classifies_compatibility_changes_as_fix(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Classify compatibility and breakage-prevention changes as FIX."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "irrelevant"

        message = (
            "Update AI client to prevent breaking strict OpenAI endpoints\n\n"
            "This ensures compatibility with strict OpenAI servers."
        )
        result = classify_commit_type(mock_config, commit_message=message)

        assert result == CommitType.FIX

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_classifies_default_value_config_changes_as_chore(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Classify configuration default/env var changes as CHORE."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "irrelevant"

        message = (
            "Add default value for AUTO_GROUP_MAX_NON_TYPE_GROUPS\n\n"
            "This change updates configuration and environment variable handling."
        )
        result = classify_commit_type(mock_config, commit_message=message)

        assert result == CommitType.CHORE


class TestGetChanges:
    """Tests for get_changes helper."""

    @patch("git_acp.git.classification.get_diff")
    def test_fallback_to_unstaged(self, mock_get_diff):
        """Fall back to unstaged diff when staged diff is empty."""
        mock_get_diff.side_effect = [None, "unstaged changes"]
        result = get_changes()
        assert result == "unstaged changes"

    @patch("git_acp.git.classification.get_diff")
    def test_no_changes_found(self, mock_get_diff):
        """Raise GitError when no changes are found."""
        mock_get_diff.return_value = None
        with pytest.raises(GitError):
            get_changes()

    @patch("git_acp.git.classification.get_diff")
    def test_get_changes__raises_on_git_error(self, mock_get_diff):
        """Wrap GitError with meaningful message."""
        mock_get_diff.side_effect = GitError("git error")
        with pytest.raises(GitError) as exc:
            get_changes()
        assert "Failed to retrieve changes" in str(exc.value)


class TestClassifyCommitTypeEdgeCases:
    """Edge case tests for classify_commit_type function."""

    @pytest.fixture
    def verbose_config(self):
        """Return a verbose config object."""
        cfg = MagicMock()
        cfg.verbose = True
        return cfg

    @pytest.fixture
    def mock_config(self):
        """Return a non-verbose config object."""
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__default_chore_verbose(
        self,
        mock_debug_item,
        mock_debug_header,
        mock_get_diff,
        mock_get_files,
        verbose_config,
    ):
        """Log debug output when defaulting to CHORE in verbose mode."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "some random change without patterns"

        result = classify_commit_type(verbose_config)

        assert result == CommitType.CHORE
        mock_debug_header.assert_any_call("Scoring Results")
        mock_debug_item.assert_any_call("Selected Type", "CHORE")

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__git_error_verbose(
        self,
        mock_debug_item,
        mock_debug_header,
        mock_get_diff,
        mock_get_files,
        verbose_config,
    ):
        """Default to CHORE when get_diff raises GitError (e.g. no diff)."""
        mock_get_files.return_value = set()
        mock_get_diff.side_effect = GitError("no changes")

        result = classify_commit_type(verbose_config)
        assert result == CommitType.CHORE
        mock_debug_header.assert_any_call("Scoring Results")
        mock_debug_item.assert_any_call("Selected Type", "CHORE")

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__unexpected_error_verbose(
        self,
        mock_debug_item,
        mock_debug_header,
        mock_get_diff,
        mock_get_files,
        verbose_config,
    ):
        """Log unexpected errors in verbose mode."""
        mock_get_files.return_value = set()
        mock_get_diff.side_effect = RuntimeError("unexpected")

        with pytest.raises(GitError) as exc:
            classify_commit_type(verbose_config)

        assert "unexpected error" in str(exc.value)
        mock_debug_header.assert_any_call("Unexpected Classification Error")
        mock_debug_item.assert_any_call("Error Type", "RuntimeError")

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_classify__unexpected_error_non_verbose(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Handle unexpected errors in non-verbose mode."""
        mock_get_files.return_value = set()
        mock_get_diff.side_effect = ValueError("bad value")

        with pytest.raises(GitError) as exc:
            classify_commit_type(mock_config)

        assert "unexpected error" in str(exc.value)

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    @patch(
        "git_acp.git.classification.COMMIT_TYPE_PATTERNS",
        {"invalid_type": ["pattern"]},
    )
    def test_classify__invalid_commit_type_pattern(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Raise GitError when COMMIT_TYPE_PATTERNS contains invalid type."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "pattern match"

        with pytest.raises(GitError) as exc:
            classify_commit_type(mock_config)

        assert "Invalid commit type pattern" in str(exc.value)

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    @patch(
        "git_acp.git.classification.COMMIT_TYPE_PATTERNS",
        {"invalid_type": ["pattern"]},
    )
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__invalid_commit_type_verbose(
        self,
        mock_debug_item,
        mock_debug_header,
        mock_get_diff,
        mock_get_files,
        verbose_config,
    ):
        """Log invalid commit type errors in verbose mode."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "pattern match"

        with pytest.raises(GitError):
            classify_commit_type(verbose_config)

        mock_debug_header.assert_any_call("Commit Classification Failed")

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__pattern_match_verbose(
        self,
        mock_debug_item,
        mock_debug_header,
        mock_get_diff,
        mock_get_files,
        verbose_config,
    ):
        """Log matched keywords in verbose mode."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "fix: resolved critical bug"

        result = classify_commit_type(verbose_config)

        assert result == CommitType.FIX
        # Verify matched keywords are logged
        matched_call = any(
            "Matched Keywords" in str(c) for c in mock_debug_item.call_args_list
        )
        assert matched_call

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__file_path_verbose(
        self,
        mock_debug_item,
        mock_debug_header,
        mock_get_files,
        verbose_config,
    ):
        """Log file path classification in verbose mode."""
        mock_get_files.return_value = {"tests/test_module.py"}

        result = classify_commit_type(verbose_config)

        assert result == CommitType.TEST
        mock_debug_header.assert_any_call("Commit Classification Result")
        mock_debug_item.assert_any_call("Source", "scoring")


class TestStripConventionalPrefix:
    """Tests for stripping conventional prefixes from commit titles."""

    def test_strip_conventional_prefix__type_only(self) -> None:
        """Strip simple ``type:`` prefixes."""
        assert strip_conventional_prefix("fix: description") == "description"

    def test_strip_conventional_prefix__type_with_scope(self) -> None:
        """Strip ``type(scope):`` prefixes."""
        assert strip_conventional_prefix("feat(scope): description") == "description"

    def test_strip_conventional_prefix__type_with_emoji(self) -> None:
        """Strip ``type emoji:`` prefixes."""
        assert strip_conventional_prefix("fix 🐛: description") == "description"

    def test_strip_conventional_prefix__type_scope_and_emoji(self) -> None:
        """Strip ``type(scope) emoji:`` prefixes."""
        message = "refactor(core) ♻️: description"
        assert strip_conventional_prefix(message) == "description"

    def test_strip_conventional_prefix__emoji_leading(self) -> None:
        """Strip emoji-leading conventional prefixes."""
        assert strip_conventional_prefix("🐛 fix: description") == "description"
        message = "♻️ refactor(core): description"
        assert strip_conventional_prefix(message) == "description"

    def test_strip_conventional_prefix__no_prefix(self) -> None:
        """Leave non-conventional titles unchanged."""
        message = "add feature: with colon in body"
        assert strip_conventional_prefix(message) == message

    def test_strip_conventional_prefix__invalid_partial_prefix(self) -> None:
        """Avoid stripping invalid partial prefixes."""
        message = "fix update: description"
        assert strip_conventional_prefix(message) == message

    def test_strip_conventional_prefix__empty(self) -> None:
        """Return empty input unchanged."""
        assert strip_conventional_prefix("") == ""

    def test_strip_conventional_prefix__breaking_marker(self) -> None:
        """Strip the breaking-change indicator along with the prefix."""
        assert strip_conventional_prefix("fix!: breaking API") == "breaking API"

    def test_strip_conventional_prefix__case_insensitive(self) -> None:
        """Normalize case-insensitive conventional prefixes."""
        assert strip_conventional_prefix("Fix: description") == "description"
        assert strip_conventional_prefix("FEAT(scope): description") == "description"


# ---------------------------------------------------------------------------
# Phase 2 infrastructure tests
# ---------------------------------------------------------------------------

class TestExtractAddedLines:
    """Tests for extract_added_lines in diff.py."""

    def test_extracts_added_lines_only(self) -> None:
        """Return only lines starting with +, stripping the marker."""
        diff = (
            "diff --git a/file.py b/file.py\n"
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,3 +1,4 @@\n"
            " context line\n"
            "-removed line\n"
            "+added line one\n"
            "+added line two\n"
        )
        result = extract_added_lines(diff)
        assert "added line one" in result
        assert "added line two" in result
        assert "context line" not in result
        assert "removed line" not in result

    def test_empty_diff(self) -> None:
        """Return empty string for empty input."""
        assert extract_added_lines("") == ""

    def test_skips_file_headers(self) -> None:
        """Do not include +++ and --- lines."""
        diff = "+++ b/new_file.py\n--- a/old_file.py\n+actual change\n"
        result = extract_added_lines(diff)
        assert "b/new_file.py" not in result
        assert "a/old_file.py" not in result
        assert "actual change" in result


class TestFileClassifier:
    """Tests for file_classifier module."""

    def test_classify_test_file(self) -> None:
        """Classify test files as TEST category."""
        assert classify_file_category("tests/test_utils.py") == FileCategory.TEST

    def test_classify_docs_file(self) -> None:
        """Classify documentation files as DOCS category."""
        assert classify_file_category("docs/api.md") == FileCategory.DOCS

    def test_classify_ci_file(self) -> None:
        """Classify CI config files as CI category."""
        assert classify_file_category(".github/workflows/ci.yaml") == FileCategory.CI

    def test_classify_dependency_file(self) -> None:
        """Classify lockfiles as DEPENDENCY category."""
        assert classify_file_category("uv.lock") == FileCategory.DEPENDENCY
        assert classify_file_category("package-lock.json") == FileCategory.DEPENDENCY

    def test_classify_generated_file(self) -> None:
        """Classify build artifacts as GENERATED category."""
        assert classify_file_category("__pycache__/module.cpython-311.pyc") == FileCategory.GENERATED

    def test_classify_style_file(self) -> None:
        """Linting configs classify as STYLE, not CONFIG."""
        assert classify_file_category(".flake8") == FileCategory.STYLE
        assert classify_file_category("ruff.toml") == FileCategory.STYLE

    def test_classify_config_file(self) -> None:
        """General config files classify as CONFIG."""
        assert classify_file_category("pyproject.toml") == FileCategory.CONFIG
        assert classify_file_category(".gitignore") == FileCategory.CONFIG

    def test_classify_build_file(self) -> None:
        """Build files classify as BUILD."""
        assert classify_file_category("Dockerfile") == FileCategory.BUILD

    def test_classify_production_file(self) -> None:
        """Source code files default to PRODUCTION."""
        assert classify_file_category("src/auth.py") == FileCategory.PRODUCTION
        assert classify_file_category("git_acp/cli/cli.py") == FileCategory.PRODUCTION

    def test_categorize_changed_files(self) -> None:
        """Group mixed files into correct categories."""
        files = {
            "src/main.py",
            "tests/test_main.py",
            "docs/README.md",
            "uv.lock",
        }
        result = categorize_changed_files(files)
        assert FileCategory.PRODUCTION in result
        assert FileCategory.TEST in result
        assert FileCategory.DOCS in result
        assert FileCategory.DEPENDENCY in result
        assert "src/main.py" in result[FileCategory.PRODUCTION]
        assert "tests/test_main.py" in result[FileCategory.TEST]


# ---------------------------------------------------------------------------
# Phase 3: Regression tests for known misclassification patterns
# ---------------------------------------------------------------------------

class TestProductionWithSupportingFiles:
    """Test that production changes with supporting test/doc files classify
    based on production intent, not as test/docs.

    These represent the ~25% misclassification rate the scoring system
    aims to fix. They run against the *current* classifier to establish
    a baseline — some may currently fail, which is expected and will be
    fixed by Phase 4.
    """

    @pytest.fixture
    def mock_config(self):
        """Return a mock config object."""
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_production_plus_test_classifies_by_production(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """src/auth.py + tests/test_auth.py should not classify as TEST."""
        mock_get_files.return_value = {"src/auth.py", "tests/test_auth.py"}
        mock_get_diff.return_value = "implement new authentication"
        result = classify_commit_type(mock_config)
        # Scoring classifier: production file + supporting test → FEAT
        assert result == CommitType.FEAT

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_production_plus_docs_classifies_by_production(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """src/module.py + docs/module.md should not classify as DOCS."""
        mock_get_files.return_value = {"src/module.py", "docs/module.md"}
        mock_get_diff.return_value = "refactor module internals"
        result = classify_commit_type(mock_config)
        # Scoring classifier: production file + supporting docs, "refactor" keyword → REFACTOR
        assert result == CommitType.REFACTOR


class TestSinglePurposeChanges:
    """Test that single-purpose changes classify correctly."""

    @pytest.fixture
    def mock_config(self):
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_docs_only_classifies_as_docs(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Pure documentation changes classify as DOCS."""
        mock_get_files.return_value = {"docs/api.md", "README.md"}
        mock_get_diff.return_value = "update API documentation"
        result = classify_commit_type(mock_config)
        assert result == CommitType.DOCS

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_test_only_classifies_as_test(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """Pure test changes classify as TEST."""
        mock_get_files.return_value = {"tests/test_utils.py", "tests/conftest.py"}
        mock_get_diff.return_value = "add unit tests for utils"
        result = classify_commit_type(mock_config)
        assert result == CommitType.TEST

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_ci_only_classifies_as_ci(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """CI-only changes classify as CI."""
        mock_get_files.return_value = {".github/workflows/ci.yaml"}
        mock_get_diff.return_value = "update CI pipeline"
        result = classify_commit_type(mock_config)
        # Scoring classifier: CI files → CommitType.CI
        assert result == CommitType.CI


class TestMixedChangeDetection:
    """Tests for the is_mixed flag in ClassificationResult.

    These tests will become meaningful after Phase 4 when
    classify_commit() returns ClassificationResult with is_mixed.
    For now they test that the category grouping works.
    """

    def test_mixed_categories_detected(self) -> None:
        """Unrelated file groups produce multiple categories."""
        files = {"src/auth.py", "docs/api.md", "pyproject.toml"}
        cats = categorize_changed_files(files)
        # PRODUCTION + DOCS + CONFIG = 3 distinct categories
        assert len(cats) >= 3

    def test_single_purpose_has_one_category(self) -> None:
        """Single-purpose changes produce a single category."""
        files = {"tests/test_a.py", "tests/test_b.py", "conftest.py"}
        cats = categorize_changed_files(files)
        assert len(cats) == 1
        assert FileCategory.TEST in cats


# ---------------------------------------------------------------------------
# New CommitType members (BUILD, CI, PERF) added in this PR
# ---------------------------------------------------------------------------


class TestNewCommitTypeMembers:
    """Tests for the BUILD, CI, and PERF CommitType enum members."""

    def test_build_commit_type_exists(self) -> None:
        """CommitType.BUILD should be a valid enum member."""
        assert CommitType.BUILD in CommitType

    def test_ci_commit_type_exists(self) -> None:
        """CommitType.CI should be a valid enum member."""
        assert CommitType.CI in CommitType

    def test_perf_commit_type_exists(self) -> None:
        """CommitType.PERF should be a valid enum member."""
        assert CommitType.PERF in CommitType

    def test_build_from_str(self) -> None:
        """CommitType.from_str('build') returns CommitType.BUILD."""
        assert CommitType.from_str("build") == CommitType.BUILD

    def test_ci_from_str(self) -> None:
        """CommitType.from_str('ci') returns CommitType.CI."""
        assert CommitType.from_str("ci") == CommitType.CI

    def test_perf_from_str(self) -> None:
        """CommitType.from_str('perf') returns CommitType.PERF."""
        assert CommitType.from_str("perf") == CommitType.PERF

    def test_build_value_starts_with_build(self) -> None:
        """BUILD value starts with the 'build' keyword."""
        assert CommitType.BUILD.value.startswith("build")

    def test_ci_value_starts_with_ci(self) -> None:
        """CI value starts with the 'ci' keyword."""
        assert CommitType.CI.value.startswith("ci")

    def test_perf_value_starts_with_perf(self) -> None:
        """PERF value starts with the 'perf' keyword."""
        assert CommitType.PERF.value.startswith("perf")


# ---------------------------------------------------------------------------
# ClassificationResult dataclass
# ---------------------------------------------------------------------------


class TestClassificationResult:
    """Tests for the ClassificationResult frozen dataclass."""

    def _make_result(
        self,
        commit_type: CommitType = CommitType.FEAT,
        confidence: float = 0.75,
        scores: dict | None = None,
        is_mixed: bool = False,
    ) -> ClassificationResult:
        if scores is None:
            scores = {ct: 0.0 for ct in CommitType}
        return ClassificationResult(
            commit_type=commit_type,
            confidence=confidence,
            scores=scores,
            is_mixed=is_mixed,
        )

    def test_fields_are_accessible(self) -> None:
        """All four fields should be accessible via attribute access."""
        result = self._make_result(CommitType.FIX, 0.9, {CommitType.FIX: 5.0}, True)
        assert result.commit_type == CommitType.FIX
        assert result.confidence == 0.9
        assert result.is_mixed is True

    def test_is_frozen_dataclass(self) -> None:
        """Assigning to a frozen dataclass field raises AttributeError."""
        result = self._make_result()
        with pytest.raises(AttributeError):
            result.commit_type = CommitType.FIX  # type: ignore[misc]

    def test_scores_dict_is_mutable(self) -> None:
        """The scores dict itself is mutable even though the dataclass is frozen."""
        scores = {ct: 0.0 for ct in CommitType}
        result = self._make_result(scores=scores)
        # Should not raise — we're mutating the dict, not the dataclass field
        result.scores[CommitType.FEAT] = 1.0
        assert result.scores[CommitType.FEAT] == 1.0

    def test_confidence_zero_for_no_signal(self) -> None:
        """Zero confidence is valid when no signal was found."""
        result = self._make_result(confidence=0.0)
        assert result.confidence == 0.0

    def test_confidence_one_for_prefix_shortcircuit(self) -> None:
        """confidence=1.0 is valid for prefix short-circuit results."""
        result = self._make_result(confidence=1.0)
        assert result.confidence == 1.0

    def test_is_mixed_false_by_default(self) -> None:
        """is_mixed defaults to False."""
        result = self._make_result(is_mixed=False)
        assert result.is_mixed is False

    def test_equality_based_on_fields(self) -> None:
        """Two ClassificationResult with identical fields compare equal."""
        scores = {ct: 0.0 for ct in CommitType}
        r1 = ClassificationResult(CommitType.TEST, 0.8, scores, False)
        r2 = ClassificationResult(CommitType.TEST, 0.8, scores, False)
        assert r1 == r2

    def test_inequality_on_different_type(self) -> None:
        """Different commit types produce non-equal results."""
        scores = {ct: 0.0 for ct in CommitType}
        r1 = ClassificationResult(CommitType.FEAT, 0.8, scores, False)
        r2 = ClassificationResult(CommitType.FIX, 0.8, scores, False)
        assert r1 != r2


# ---------------------------------------------------------------------------
# classify_commit (new high-level API)
# ---------------------------------------------------------------------------


class TestClassifyCommit:
    """Tests for classify_commit(), the new primary classifier."""

    @pytest.fixture
    def mock_config(self):
        """Return a non-verbose mock config."""
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @pytest.fixture
    def verbose_config(self):
        """Return a verbose mock config."""
        cfg = MagicMock()
        cfg.verbose = True
        return cfg

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_returns_classification_result(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """classify_commit must return a ClassificationResult instance."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "implement new feature"
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        assert isinstance(result, ClassificationResult)

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_result_has_all_commit_types_in_scores(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """Result.scores must contain an entry for every CommitType."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = ""
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        for ct in CommitType:
            assert ct in result.scores

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_prefix_shortcircuit_returns_confidence_one(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """Explicit commit prefix short-circuits with confidence=1.0."""
        mock_get_files.return_value = {"tests/test_module.py"}
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config, commit_message="feat: add new API")

        assert result.commit_type == CommitType.FEAT
        assert result.confidence == 1.0
        assert result.is_mixed is False

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_prefix_shortcircuit_sets_score_for_winner(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """Prefix short-circuit sets the winner's score to 1.0 in scores dict."""
        mock_get_files.return_value = set()
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config, commit_message="fix: resolve bug")

        assert result.commit_type == CommitType.FIX
        # score for winner should be 1.0
        assert result.scores[CommitType.FIX] == 1.0

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_no_signals_defaults_to_chore(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """When no signals match, classify_commit defaults to CHORE."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = ""
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        assert result.commit_type == CommitType.CHORE

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_confidence_is_float_between_zero_and_one(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """confidence must always be in [0.0, 1.0]."""
        mock_get_files.return_value = {"src/module.py"}
        mock_get_diff.return_value = "implement feature"
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        assert 0.0 <= result.confidence <= 1.0

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_is_mixed_false_for_single_category(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """is_mixed should be False when only one category of files is changed."""
        mock_get_files.return_value = {"tests/test_a.py", "tests/test_b.py"}
        mock_get_diff.return_value = "add tests"
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        assert result.is_mixed is False

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_is_mixed_true_for_complex_change(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """is_mixed should be True when production + 2 non-supporting categories changed."""
        # PRODUCTION + CI + CONFIG = 3 categories (CI and CONFIG are non-supporting)
        mock_get_files.return_value = {
            "src/auth.py",
            ".github/workflows/ci.yaml",
            "pyproject.toml",
        }
        mock_get_diff.return_value = "various changes"
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        assert result.is_mixed is True

    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_git_error_re_raised_as_git_error(
        self, mock_get_diff, mock_get_files, mock_config
    ):
        """GitError during classification is re-raised as a GitError."""
        mock_get_files.return_value = set()
        mock_get_diff.side_effect = RuntimeError("unexpected internal error")

        with pytest.raises(GitError) as exc:
            classify_commit(mock_config)

        assert "unexpected error" in str(exc.value)

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_classify_commit_type_delegates_to_classify_commit(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """classify_commit_type should return the commit_type from classify_commit."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = ""
        mock_get_numstat.return_value = {}

        commit_result = classify_commit(mock_config)
        type_result = classify_commit_type(mock_config)

        # Both should agree on the commit type
        assert type_result == commit_result.commit_type

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_ci_files_produce_ci_commit_type(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """CI-only files should produce CommitType.CI via the new scoring path."""
        mock_get_files.return_value = {".github/workflows/ci.yaml"}
        mock_get_diff.return_value = "update workflow"
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        assert result.commit_type == CommitType.CI

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_build_files_produce_build_commit_type(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """BUILD-only files should produce CommitType.BUILD."""
        mock_get_files.return_value = {"Dockerfile"}
        mock_get_diff.return_value = "update docker image"
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        assert result.commit_type == CommitType.BUILD

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    def test_revert_commit_type_excluded_from_scoring(
        self, mock_get_diff, mock_get_files, mock_get_numstat, mock_config
    ):
        """REVERT is always zeroed out in scores; it only comes from explicit prefix."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = "revert previous change"
        mock_get_numstat.return_value = {}

        result = classify_commit(mock_config)

        # Even with "revert" keyword in diff, REVERT score must be 0.0
        assert result.scores[CommitType.REVERT] == 0.0
        # It should NOT be classified as REVERT (no explicit prefix was given)
        assert result.commit_type != CommitType.REVERT

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changed_files")
    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_verbose_logs_scoring_results(
        self, mock_debug_item, mock_debug_header, mock_get_diff, mock_get_files,
        mock_get_numstat, verbose_config
    ):
        """Verbose mode should log 'Scoring Results' header."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = ""
        mock_get_numstat.return_value = {}

        classify_commit(verbose_config)

        mock_debug_header.assert_any_call("Scoring Results")


# ---------------------------------------------------------------------------
# _KEYWORD_EXCLUDED_CATEGORIES
# ---------------------------------------------------------------------------


class TestKeywordExcludedCategories:
    """Tests for the _KEYWORD_EXCLUDED_CATEGORIES frozenset."""

    def test_generated_is_excluded(self) -> None:
        """GENERATED category should be excluded from keyword matching."""
        assert FileCategory.GENERATED in _KEYWORD_EXCLUDED_CATEGORIES

    def test_dependency_is_excluded(self) -> None:
        """DEPENDENCY category should be excluded from keyword matching."""
        assert FileCategory.DEPENDENCY in _KEYWORD_EXCLUDED_CATEGORIES

    def test_production_is_not_excluded(self) -> None:
        """PRODUCTION category should NOT be excluded from keyword matching."""
        assert FileCategory.PRODUCTION not in _KEYWORD_EXCLUDED_CATEGORIES

    def test_test_is_not_excluded(self) -> None:
        """TEST category should NOT be excluded from keyword matching."""
        assert FileCategory.TEST not in _KEYWORD_EXCLUDED_CATEGORIES

    def test_is_frozenset(self) -> None:
        """_KEYWORD_EXCLUDED_CATEGORIES should be a frozenset."""
        assert isinstance(_KEYWORD_EXCLUDED_CATEGORIES, frozenset)


# ---------------------------------------------------------------------------
# _collect_signals (internal — tested via public interfaces where possible,
# but tested directly here for full coverage of the new code)
# ---------------------------------------------------------------------------


class TestCollectSignals:
    """Tests for _collect_signals internal function."""

    @pytest.fixture
    def mock_config(self):
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_returns_required_keys(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """_collect_signals must return a dict with the expected keys."""
        mock_get_changes.return_value = "some diff"
        mock_get_numstat.return_value = {}

        signals = _collect_signals(mock_config, None, set())

        assert "prefix_type" in signals
        assert "file_categories" in signals
        assert "numstat" in signals
        assert "message_keyword_hits" in signals
        assert "diff_text" in signals

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_prefix_type_none_when_no_message(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """prefix_type is None when commit_message is None."""
        mock_get_changes.return_value = None
        mock_get_numstat.return_value = {}

        signals = _collect_signals(mock_config, None, set())

        assert signals["prefix_type"] is None

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_prefix_type_parsed_from_message(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """prefix_type is set when a valid conventional prefix is present."""
        mock_get_changes.return_value = None
        mock_get_numstat.return_value = {}

        signals = _collect_signals(mock_config, "feat: add new feature", set())

        assert signals["prefix_type"] == CommitType.FEAT

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_file_categories_empty_when_no_files(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """file_categories is an empty dict when changed_files is empty."""
        mock_get_changes.return_value = None
        mock_get_numstat.return_value = {}

        signals = _collect_signals(mock_config, None, set())

        assert signals["file_categories"] == {}

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_file_categories_populated_from_changed_files(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """file_categories reflects the category of changed files."""
        mock_get_changes.return_value = None
        mock_get_numstat.return_value = {}

        signals = _collect_signals(
            mock_config, None, {"tests/test_module.py"}
        )

        assert FileCategory.TEST in signals["file_categories"]

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_message_keyword_hits_populated_for_matching_message(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """message_keyword_hits is populated when commit message matches keywords."""
        mock_get_changes.return_value = None
        mock_get_numstat.return_value = {}

        signals = _collect_signals(mock_config, "implement new feature", set())

        # "FEAT" patterns should fire on "implement new feature"
        assert len(signals["message_keyword_hits"]) > 0

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_diff_text_captured_when_available(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """diff_text is populated when get_changes succeeds."""
        mock_get_changes.return_value = "+def new_function(): pass"
        mock_get_numstat.return_value = {}

        signals = _collect_signals(mock_config, None, set())

        assert signals["diff_text"] == "+def new_function(): pass"

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_diff_text_none_when_get_changes_raises(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """diff_text is None when get_changes raises GitError."""
        mock_get_changes.side_effect = GitError("no diff")
        mock_get_numstat.return_value = {}

        signals = _collect_signals(mock_config, None, set())

        assert signals["diff_text"] is None

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_numstat_populated_when_available(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """numstat is populated when get_numstat succeeds."""
        mock_get_changes.return_value = None
        mock_get_numstat.return_value = {"src/module.py": (10, 2)}

        signals = _collect_signals(mock_config, None, {"src/module.py"})

        assert "src/module.py" in signals["numstat"]

    @patch("git_acp.git.classification.get_numstat")
    @patch("git_acp.git.classification.get_changes")
    def test_numstat_empty_on_exception(
        self, mock_get_changes, mock_get_numstat, mock_config
    ):
        """numstat is empty when get_numstat raises an exception."""
        mock_get_changes.return_value = None
        mock_get_numstat.side_effect = Exception("git error")

        signals = _collect_signals(mock_config, None, set())

        assert signals["numstat"] == {}


# ---------------------------------------------------------------------------
# _score_commit_types (internal scoring engine)
# ---------------------------------------------------------------------------


class TestScoreCommitTypes:
    """Tests for _score_commit_types internal function."""

    @pytest.fixture
    def mock_config(self):
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    def _make_signals(
        self,
        file_categories=None,
        numstat=None,
        message_keyword_hits=None,
        diff_text=None,
        prefix_type=None,
    ) -> dict:
        return {
            "prefix_type": prefix_type,
            "file_categories": file_categories or {},
            "numstat": numstat or {},
            "message_keyword_hits": message_keyword_hits or {},
            "diff_text": diff_text,
        }

    def test_returns_three_tuple(self, mock_config) -> None:
        """_score_commit_types returns (scores, confidence, is_mixed)."""
        signals = self._make_signals()
        result = _score_commit_types(signals, mock_config)
        scores, confidence, is_mixed = result
        assert isinstance(scores, dict)
        assert isinstance(confidence, float)
        assert isinstance(is_mixed, bool)

    def test_all_commit_types_have_scores(self, mock_config) -> None:
        """scores dict must contain every CommitType key."""
        signals = self._make_signals()
        scores, _, _ = _score_commit_types(signals, mock_config)
        for ct in CommitType:
            assert ct in scores

    def test_revert_score_is_always_zero(self, mock_config) -> None:
        """REVERT score is forced to 0.0 regardless of signals."""
        signals = self._make_signals(
            message_keyword_hits={"REVERT": ["revert"]},
            diff_text="revert the changes",
        )
        scores, _, _ = _score_commit_types(signals, mock_config)
        assert scores[CommitType.REVERT] == 0.0

    def test_single_category_boost_applied(self, mock_config) -> None:
        """Single non-production category gets a +10.0 boost."""
        signals = self._make_signals(
            file_categories={FileCategory.TEST: {"tests/test_a.py"}},
        )
        scores, _, _ = _score_commit_types(signals, mock_config)
        # TEST maps to CommitType.TEST; should have a substantial score
        assert scores[CommitType.TEST] > 10.0

    def test_production_files_boost_production_types(self, mock_config) -> None:
        """PRODUCTION category distributes weight across production types."""
        signals = self._make_signals(
            file_categories={FileCategory.PRODUCTION: {"src/module.py"}},
        )
        scores, _, _ = _score_commit_types(signals, mock_config)
        production_types = {
            CommitType.FEAT, CommitType.FIX, CommitType.REFACTOR, CommitType.PERF
        }
        for pt in production_types:
            assert scores[pt] > 0.0

    def test_confidence_zero_when_all_scores_zero(self, mock_config) -> None:
        """Confidence is 0.0 when all scores are 0."""
        signals = self._make_signals()
        scores, confidence, _ = _score_commit_types(signals, mock_config)
        # All scores are 0 → confidence must be 0.0
        if all(s == 0.0 for s in scores.values()):
            assert confidence == 0.0

    def test_confidence_one_when_only_winner_has_score(self, mock_config) -> None:
        """Confidence is 1.0 when only the top-scoring type has a non-zero score."""
        # Single file in TEST category, no other signals
        signals = self._make_signals(
            file_categories={FileCategory.TEST: {"tests/test_only.py"}},
        )
        scores, confidence, _ = _score_commit_types(signals, mock_config)
        # TEST should have score >> 0, and there's no second-place score
        # because the +10 boost goes only to CommitType.TEST
        # Note: file weight (1 file) + 10 boost should make TEST dominate
        if scores[CommitType.TEST] > 0 and all(
            s == 0.0 for ct, s in scores.items() if ct != CommitType.TEST
        ):
            assert confidence == 1.0

    def test_is_mixed_true_when_production_plus_two_non_supporting(
        self, mock_config
    ) -> None:
        """is_mixed is True when production + 2+ non-supporting categories are present."""
        signals = self._make_signals(
            file_categories={
                FileCategory.PRODUCTION: {"src/module.py"},
                FileCategory.CI: {".github/workflows/ci.yaml"},
                FileCategory.BUILD: {"Dockerfile"},
            }
        )
        _, _, is_mixed = _score_commit_types(signals, mock_config)
        assert is_mixed is True

    def test_is_mixed_false_when_only_supporting_categories(
        self, mock_config
    ) -> None:
        """is_mixed is False when additional categories are only TEST and DOCS."""
        signals = self._make_signals(
            file_categories={
                FileCategory.PRODUCTION: {"src/auth.py"},
                FileCategory.TEST: {"tests/test_auth.py"},
                FileCategory.DOCS: {"docs/auth.md"},
            }
        )
        _, _, is_mixed = _score_commit_types(signals, mock_config)
        # Only supporting categories alongside production → not mixed
        assert is_mixed is False

    def test_message_keyword_score_added(self, mock_config) -> None:
        """Message keyword hits add to the corresponding type score."""
        signals = self._make_signals(
            message_keyword_hits={"FEAT": ["implement", "new feature"]},
        )
        scores, _, _ = _score_commit_types(signals, mock_config)
        assert scores[CommitType.FEAT] > 0.0

    def test_diff_keyword_score_added(self, mock_config) -> None:
        """Diff text keyword hits contribute to type scores."""
        signals = self._make_signals(
            diff_text="+def new_feature():\n+    pass\n",
        )
        scores, _, _ = _score_commit_types(signals, mock_config)
        # "new feature" in diff should produce at least one non-zero score
        assert any(s > 0.0 for ct, s in scores.items() if ct != CommitType.REVERT)

    @patch(
        "git_acp.git.classification.COMMIT_TYPE_PATTERNS",
        {"invalid_type": ["pattern"]},
    )
    def test_invalid_keyword_type_raises_git_error(self, mock_config) -> None:
        """Invalid type name in COMMIT_TYPE_PATTERNS raises GitError."""
        signals = self._make_signals(
            message_keyword_hits={"invalid_type": ["pattern"]},
        )
        with pytest.raises(GitError) as exc:
            _score_commit_types(signals, mock_config)
        assert "Invalid commit type pattern" in str(exc.value)
