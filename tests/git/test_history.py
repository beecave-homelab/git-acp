"""Tests for git_acp.git.history module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_acp.git.core import GitError
from git_acp.git.history import (
    analyze_commit_patterns,
    find_related_commits,
    get_recent_commits,
)
from git_acp.utils import GitConfig


class TestGetRecentCommits:
    """Tests for get_recent_commits function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.history.run_git_command")
    def test_get_recent_commits__returns_parsed_commits(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Parse and return commit history as list of dicts."""
        json_line_1 = (
            '{"hash":"abc1234","message":"feat: add feature",'
            '"author":"Dev","date":"2024-01-01"}'
        )
        json_line_2 = (
            '{"hash":"def5678","message":"fix: bug fix",'
            '"author":"Dev","date":"2024-01-02"}'
        )
        mock_run.return_value = (f"{json_line_1}\n{json_line_2}", "")

        result = get_recent_commits(num_commits=5, config=mock_config)

        assert len(result) == 2
        assert result[0]["hash"] == "abc1234"
        assert result[0]["message"] == "feat: add feature"
        assert result[1]["hash"] == "def5678"

    @patch("git_acp.git.history.run_git_command")
    def test_get_recent_commits__returns_empty_list_on_no_commits(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return empty list when no commits exist."""
        mock_run.return_value = ("", "")

        result = get_recent_commits(config=mock_config)

        assert result == []

    @patch("git_acp.git.history.run_git_command")
    def test_get_recent_commits__skips_invalid_json(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Skip lines that cannot be parsed as JSON."""
        valid_1 = (
            '{"hash":"abc1234","message":"valid","author":"Dev","date":"2024-01-01"}'
        )
        valid_2 = (
            '{"hash":"def5678","message":"also valid",'
            '"author":"Dev","date":"2024-01-02"}'
        )
        mock_run.return_value = (
            f"{valid_1}\ninvalid json line\n{valid_2}",
            "",
        )

        result = get_recent_commits(config=mock_config)

        assert len(result) == 2

    @patch("git_acp.git.history.run_git_command")
    def test_get_recent_commits__raises_on_git_error(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when git log fails."""
        mock_run.side_effect = GitError("not a git repository")

        with pytest.raises(GitError) as exc:
            get_recent_commits(config=mock_config)

        assert "Failed to get recent commits" in str(exc.value)

    @patch("git_acp.git.history.run_git_command")
    @patch("git_acp.git.history.debug_header")
    @patch("git_acp.git.history.debug_item")
    def test_get_recent_commits__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = (
            '{"hash":"abc","message":"test","author":"Dev","date":"2024-01-01"}',
            "",
        )

        get_recent_commits(config=verbose_config)

        mock_debug_header.assert_called_with("Getting recent commits")
        mock_debug_item.assert_called()

    @patch("git_acp.git.history.run_git_command")
    def test_get_recent_commits__uses_default_num_commits(
        self, mock_run: MagicMock
    ) -> None:
        """Use default number of commits when not specified."""
        mock_run.return_value = ("", "")

        get_recent_commits()

        # Check that the command includes the default num_commits
        call_args = mock_run.call_args[0][0]
        assert any("-" in arg for arg in call_args)  # e.g., "-10"


class TestFindRelatedCommits:
    """Tests for find_related_commits function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.history.run_git_command")
    @patch("git_acp.git.history.get_recent_commits")
    def test_find_related_commits__finds_commits_with_matching_files(
        self,
        mock_get_recent: MagicMock,
        mock_run: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Find commits that modified the same files as the diff."""
        mock_get_recent.return_value = [
            {"hash": "abc123", "message": "feat: add file"},
            {"hash": "def456", "message": "fix: update file"},
        ]
        # First call for abc123 returns src/file.py
        # Second call for def456 returns different file
        mock_run.side_effect = [
            ("src/file.py", ""),
            ("other/file.py", ""),
        ]

        diff_content = "+++ b/src/file.py\n--- a/src/file.py"
        result = find_related_commits(diff_content, num_commits=5, config=mock_config)

        assert len(result) == 1
        assert result[0]["hash"] == "abc123"

    @patch("git_acp.git.history.run_git_command")
    @patch("git_acp.git.history.get_recent_commits")
    def test_find_related_commits__returns_empty_when_no_matches(
        self,
        mock_get_recent: MagicMock,
        mock_run: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return empty list when no commits match."""
        mock_get_recent.return_value = [
            {"hash": "abc123", "message": "feat: unrelated"},
        ]
        mock_run.return_value = ("unrelated/file.py", "")

        diff_content = "+++ b/src/file.py\n--- a/src/file.py"
        result = find_related_commits(diff_content, config=mock_config)

        assert result == []

    @patch("git_acp.git.history.run_git_command")
    @patch("git_acp.git.history.get_recent_commits")
    def test_find_related_commits__limits_results(
        self,
        mock_get_recent: MagicMock,
        mock_run: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Limit results to requested number of commits."""
        mock_get_recent.return_value = [
            {"hash": "abc", "message": "one"},
            {"hash": "def", "message": "two"},
            {"hash": "ghi", "message": "three"},
        ]
        mock_run.return_value = ("src/file.py", "")

        diff_content = "+++ b/src/file.py"
        result = find_related_commits(diff_content, num_commits=2, config=mock_config)

        assert len(result) == 2

    @patch("git_acp.git.history.run_git_command")
    @patch("git_acp.git.history.get_recent_commits")
    def test_find_related_commits__skips_dev_null(
        self,
        mock_get_recent: MagicMock,
        mock_run: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Ignore /dev/null in diff paths."""
        mock_get_recent.return_value = [
            {"hash": "abc", "message": "delete file"},
        ]
        mock_run.return_value = ("", "")

        diff_content = "+++ b/src/file.py\n--- a//dev/null"
        result = find_related_commits(diff_content, config=mock_config)

        # Only src/file.py should be considered
        assert "/dev/null" not in str(result)

    @patch("git_acp.git.history.run_git_command")
    @patch("git_acp.git.history.get_recent_commits")
    def test_find_related_commits__handles_git_error_gracefully(
        self,
        mock_get_recent: MagicMock,
        mock_run: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Continue on git show errors for individual commits."""
        mock_get_recent.return_value = [
            {"hash": "abc", "message": "one"},
            {"hash": "def", "message": "two"},
        ]
        # First commit fails, second succeeds
        mock_run.side_effect = [
            GitError("commit not found"),
            ("src/file.py", ""),
        ]

        diff_content = "+++ b/src/file.py"
        result = find_related_commits(diff_content, config=mock_config)

        assert len(result) == 1
        assert result[0]["hash"] == "def"

    @patch("git_acp.git.history.get_recent_commits")
    def test_find_related_commits__raises_on_get_recent_error(
        self, mock_get_recent: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when getting recent commits fails."""
        mock_get_recent.side_effect = GitError("not a repository")

        with pytest.raises(GitError) as exc:
            find_related_commits("diff", config=mock_config)

        assert "Failed to find related commits" in str(exc.value)

    @patch("git_acp.git.history.run_git_command")
    @patch("git_acp.git.history.get_recent_commits")
    @patch("git_acp.git.history.debug_header")
    @patch("git_acp.git.history.debug_json")
    def test_find_related_commits__verbose_logs_debug(
        self,
        mock_debug_json: MagicMock,
        mock_debug_header: MagicMock,
        mock_get_recent: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_get_recent.return_value = [
            {"hash": "abc", "message": "test"},
        ]
        mock_run.return_value = ("src/file.py", "")

        find_related_commits("+++ b/src/file.py", config=verbose_config)

        mock_debug_header.assert_called()
        mock_debug_json.assert_called()


class TestAnalyzeCommitPatterns:
    """Tests for analyze_commit_patterns function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    def test_analyze_commit_patterns__extracts_types(
        self, mock_config: GitConfig
    ) -> None:
        """Extract commit types from conventional commit messages."""
        commits = [
            {"message": "feat: add new feature"},
            {"message": "fix: resolve bug"},
            {"message": "feat: another feature"},
            {"message": "docs: update readme"},
        ]

        result = analyze_commit_patterns(commits, config=mock_config)

        assert result["types"]["feat"] == 2
        assert result["types"]["fix"] == 1
        assert result["types"]["docs"] == 1

    def test_analyze_commit_patterns__extracts_scopes(
        self, mock_config: GitConfig
    ) -> None:
        """Extract scopes from conventional commit messages."""
        commits = [
            {"message": "feat(api): add endpoint"},
            {"message": "fix(api): resolve issue"},
            {"message": "feat(ui): add button"},
        ]

        result = analyze_commit_patterns(commits, config=mock_config)

        assert result["scopes"]["api"] == 2
        assert result["scopes"]["ui"] == 1

    def test_analyze_commit_patterns__handles_missing_type(
        self, mock_config: GitConfig
    ) -> None:
        """Handle messages without conventional commit format."""
        commits = [
            {"message": "Updated the code"},
            {"message": "Random change"},
        ]

        result = analyze_commit_patterns(commits, config=mock_config)

        assert len(result["types"]) == 0
        assert len(result["scopes"]) == 0

    def test_analyze_commit_patterns__handles_empty_messages(
        self, mock_config: GitConfig
    ) -> None:
        """Handle commits with empty messages."""
        commits = [
            {"message": ""},
            {"message": None},  # type: ignore[typeddict-item]
            {},
        ]

        result = analyze_commit_patterns(commits, config=mock_config)

        assert len(result["types"]) == 0
        assert len(result["scopes"]) == 0

    def test_analyze_commit_patterns__handles_complex_type_format(
        self, mock_config: GitConfig
    ) -> None:
        """Handle types with scope and breaking change indicators."""
        commits = [
            {"message": "feat(api)!: breaking change"},
            {"message": "fix(core): bug fix"},
        ]

        result = analyze_commit_patterns(commits, config=mock_config)

        assert result["types"]["feat"] == 1
        assert result["types"]["fix"] == 1

    def test_analyze_commit_patterns__lowercase_types_and_scopes(
        self, mock_config: GitConfig
    ) -> None:
        """Normalize types and scopes to lowercase."""
        commits = [
            {"message": "FEAT: uppercase type"},
            {"message": "Fix(API): mixed case"},
        ]

        result = analyze_commit_patterns(commits, config=mock_config)

        assert result["types"]["feat"] == 1
        assert result["types"]["fix"] == 1
        assert result["scopes"]["api"] == 1

    def test_analyze_commit_patterns__empty_commit_list(
        self, mock_config: GitConfig
    ) -> None:
        """Return empty counters for empty commit list."""
        result = analyze_commit_patterns([], config=mock_config)

        assert len(result["types"]) == 0
        assert len(result["scopes"]) == 0

    @patch("git_acp.git.history.debug_header")
    @patch("git_acp.git.history.debug_item")
    def test_analyze_commit_patterns__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        commits = [
            {"message": "feat(api): test"},
        ]

        analyze_commit_patterns(commits, config=verbose_config)

        mock_debug_header.assert_called_with("Analyzing commit patterns")
        mock_debug_item.assert_called()
