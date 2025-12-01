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
