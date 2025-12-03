"""Tests for git_acp.git.classification module."""

from unittest.mock import MagicMock, call, patch

import pytest

from git_acp.config import COMMIT_TYPE_PATTERNS
from git_acp.git.classification import CommitType, classify_commit_type, get_changes
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


class TestClassification:
    """Tests for commit classification logic."""

    @pytest.fixture
    def mock_config(self):
        """Return a mock config object."""
        cfg = MagicMock()
        cfg.verbose = False
        return cfg

    @patch("git_acp.git.classification.get_diff")
    def test_classify_commit_patterns(self, mock_get_diff, mock_config):
        """Classify commit messages by pattern matching."""
        test_cases = [
            ("Added new feature", "FEAT"),
            ("Fixed login bug", "FIX"),
            ("Updated documentation", "DOCS"),
            ("Code style fixes", "STYLE"),
            ("Refactored module", "REFACTOR"),
            ("Added unit tests", "TEST"),
        ]

        for message, expected_type in test_cases:
            mock_get_diff.return_value = message
            result = classify_commit_type(mock_config)
            assert result == getattr(CommitType, expected_type)

    @patch("git_acp.git.classification.get_diff")
    def test_default_chore_classification(self, mock_get_diff, mock_config):
        """Default to CHORE when no pattern matches."""
        mock_get_diff.return_value = "Generic changes"
        assert classify_commit_type(mock_config) == CommitType.CHORE

    @patch("git_acp.git.classification.get_diff")
    def test_multiple_pattern_matches(self, mock_get_diff, mock_config):
        """Return a valid commit type when multiple patterns match."""
        all_patterns = [p for sublist in COMMIT_TYPE_PATTERNS.values() for p in sublist]
        mock_get_diff.return_value = "\n".join(all_patterns)
        result = classify_commit_type(mock_config)
        assert result in CommitType

    @patch("git_acp.git.classification.get_diff")
    def test_no_changes_error(self, mock_get_diff, mock_config):
        """Raise GitError when diff is empty."""
        mock_get_diff.return_value = ""
        with pytest.raises(GitError):
            classify_commit_type(mock_config)

    @patch("git_acp.git.classification.get_diff")
    def test_verbose_output(self, mock_get_diff):
        """Emit debug headers when verbose mode is enabled."""
        mock_config = MagicMock(verbose=True)
        mock_get_diff.return_value = "fix: critical security patch"

        with patch("git_acp.git.classification.debug_header") as mock_debug:
            classify_commit_type(mock_config)

            debug_calls = [
                call("Starting Commit Classification"),
                call("Commit Classification Result"),
            ]
            mock_debug.assert_has_calls(debug_calls, any_order=True)

    @patch("git_acp.git.classification.get_diff")
    def test_all_commit_types_coverage(self, mock_get_diff, mock_config):
        """Test detection of all commit types defined in constants."""
        type_tests = {
            "feat": "add new user authentication feature",
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

    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__default_chore_verbose(
        self, mock_debug_item, mock_debug_header, mock_get_diff, verbose_config
    ):
        """Log debug output when defaulting to CHORE in verbose mode."""
        mock_get_diff.return_value = "some random change without patterns"

        result = classify_commit_type(verbose_config)

        assert result == CommitType.CHORE
        mock_debug_header.assert_any_call("No Specific Pattern Matched")
        mock_debug_item.assert_any_call("Default Type", "CHORE")

    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__git_error_verbose(
        self, mock_debug_item, mock_debug_header, mock_get_diff, verbose_config
    ):
        """Log error details in verbose mode when GitError occurs."""
        mock_get_diff.side_effect = GitError("no changes")

        with pytest.raises(GitError):
            classify_commit_type(verbose_config)

        mock_debug_header.assert_any_call("Commit Classification Failed")
        mock_debug_item.assert_any_call("Error Type", "GitError")

    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__unexpected_error_verbose(
        self, mock_debug_item, mock_debug_header, mock_get_diff, verbose_config
    ):
        """Log unexpected errors in verbose mode."""
        mock_get_diff.side_effect = RuntimeError("unexpected")

        with pytest.raises(GitError) as exc:
            classify_commit_type(verbose_config)

        assert "unexpected error" in str(exc.value)
        mock_debug_header.assert_any_call("Unexpected Classification Error")
        mock_debug_item.assert_any_call("Error Type", "RuntimeError")

    @patch("git_acp.git.classification.get_diff")
    def test_classify__unexpected_error_non_verbose(self, mock_get_diff, mock_config):
        """Handle unexpected errors in non-verbose mode."""
        mock_get_diff.side_effect = ValueError("bad value")

        with pytest.raises(GitError) as exc:
            classify_commit_type(mock_config)

        assert "unexpected error" in str(exc.value)

    @patch("git_acp.git.classification.get_diff")
    @patch(
        "git_acp.git.classification.COMMIT_TYPE_PATTERNS", {"invalid_type": ["pattern"]}
    )
    def test_classify__invalid_commit_type_pattern(self, mock_get_diff, mock_config):
        """Raise GitError when COMMIT_TYPE_PATTERNS contains invalid type."""
        mock_get_diff.return_value = "pattern match"

        with pytest.raises(GitError) as exc:
            classify_commit_type(mock_config)

        assert "Invalid commit type pattern" in str(exc.value)

    @patch("git_acp.git.classification.get_diff")
    @patch(
        "git_acp.git.classification.COMMIT_TYPE_PATTERNS", {"invalid_type": ["pattern"]}
    )
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__invalid_commit_type_verbose(
        self, mock_debug_item, mock_debug_header, mock_get_diff, verbose_config
    ):
        """Log invalid commit type errors in verbose mode."""
        mock_get_diff.return_value = "pattern match"

        with pytest.raises(GitError):
            classify_commit_type(verbose_config)

        mock_debug_header.assert_any_call("Invalid Commit Type")

    @patch("git_acp.git.classification.get_diff")
    @patch("git_acp.git.classification.debug_header")
    @patch("git_acp.git.classification.debug_item")
    def test_classify__pattern_match_verbose(
        self, mock_debug_item, mock_debug_header, mock_get_diff, verbose_config
    ):
        """Log matched keywords in verbose mode."""
        mock_get_diff.return_value = "fix: resolved critical bug"

        result = classify_commit_type(verbose_config)

        assert result == CommitType.FIX
        # Verify matched keywords are logged
        matched_call = any(
            "Matched Keywords" in str(call) for call in mock_debug_item.call_args_list
        )
        assert matched_call
