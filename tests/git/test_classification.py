"""Tests for git_acp.git.classification module."""

from unittest.mock import MagicMock, call, patch

import pytest

from git_acp.config import COMMIT_TYPE_PATTERNS, FILE_PATH_PATTERNS
from git_acp.git.classification import (
    CommitType,
    _classify_by_file_paths,
    classify_commit_type,
    get_changes,
)
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
    def test_no_changes_error(self, mock_get_diff, mock_get_files, mock_config):
        """Raise GitError when diff is empty."""
        mock_get_files.return_value = set()
        mock_get_diff.return_value = ""
        with pytest.raises(GitError):
            classify_commit_type(mock_config)

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
                call("Starting Commit Classification"),
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

    @patch("git_acp.git.classification.get_changed_files")
    def test_file_path_takes_priority_over_diff(self, mock_get_files, mock_config):
        """File path classification takes priority over diff keywords."""
        mock_get_files.return_value = {"tests/test_module.py"}
        # Even though message says "fix", file path should win
        result = classify_commit_type(mock_config, commit_message="fix something")
        assert result == CommitType.TEST

    @patch("git_acp.git.classification.get_changed_files")
    def test_message_prefix_takes_highest_priority(self, mock_get_files, mock_config):
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
        mock_debug_header.assert_any_call("No Specific Pattern Matched")
        mock_debug_item.assert_any_call("Default Type", "CHORE")

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
        """Log error details in verbose mode when GitError occurs."""
        mock_get_files.return_value = set()
        mock_get_diff.side_effect = GitError("no changes")

        with pytest.raises(GitError):
            classify_commit_type(verbose_config)

        mock_debug_header.assert_any_call("Commit Classification Failed")
        mock_debug_item.assert_any_call("Error Type", "GitError")

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

        mock_debug_header.assert_any_call("Invalid Commit Type")

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
        mock_debug_item.assert_any_call("Source", "file_paths")
