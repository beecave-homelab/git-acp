"""Tests for git_acp.git.diff module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_acp.git.core import GitError
from git_acp.git.diff import get_changed_files, get_diff
from git_acp.utils import GitConfig


class TestGetChangedFiles:
    """Tests for get_changed_files function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__staged_only_returns_staged_files(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return staged files when staged_only is True."""
        mock_run.return_value = ("file1.py\nfile2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        assert result == {"file1.py", "file2.py"}

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__staged_only_empty(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return empty set when no staged files exist."""
        mock_run.return_value = ("", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        assert result == set()

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__status_mode_parses_porcelain(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Parse porcelain status output correctly."""
        mock_run.return_value = (
            " M modified.py\nA  added.py\n?? untracked.py\nMM both_modified.py",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=False)

        assert "modified.py" in result
        assert "added.py" in result
        assert "untracked.py" in result
        assert "both_modified.py" in result

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__handles_rename_arrow(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Handle renamed files with arrow notation."""
        mock_run.return_value = ("R  old_name.py -> new_name.py", "")

        result = get_changed_files(config=mock_config, staged_only=False)

        assert "new_name.py" in result
        assert "old_name.py" not in result

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__excludes_pycache(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Exclude __pycache__ files from results."""
        mock_run.return_value = (
            " M valid.py\n"
            " M __pycache__/module.cpython-39.pyc\n"
            " M src/__pycache__/other.pyc",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=False)

        assert "valid.py" in result
        assert "__pycache__/module.cpython-39.pyc" not in result
        assert "src/__pycache__/other.pyc" not in result

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__skips_empty_lines(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Skip empty lines in status output."""
        mock_run.return_value = (
            " M file1.py\n\n   \n M file2.py",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=False)

        assert result == {"file1.py", "file2.py"}

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_header")
    @patch("git_acp.git.diff.debug_item")
    def test_get_changed_files__verbose_mode_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = (" M file.py", "")

        get_changed_files(config=verbose_config, staged_only=False)

        mock_debug_header.assert_called()
        mock_debug_item.assert_called()

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_header")
    @patch("git_acp.git.diff.debug_item")
    def test_get_changed_files__staged_verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output for staged files in verbose mode."""
        mock_run.return_value = ("staged.py", "")

        get_changed_files(config=verbose_config, staged_only=True)

        mock_debug_header.assert_called()
        mock_debug_item.assert_called()

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_item")
    def test_get_changed_files__verbose_logs_exclusion(
        self,
        mock_debug_item: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log file exclusion in verbose mode."""
        mock_run.return_value = (" M __pycache__/file.pyc", "")

        get_changed_files(config=verbose_config, staged_only=False)

        # Should have logged exclusion
        exclusion_logged = any(
            "Excluding" in str(call) for call in mock_debug_item.call_args_list
        )
        assert exclusion_logged

    def test_get_changed_files__no_config(self) -> None:
        """Work without a config object."""
        with patch("git_acp.git.diff.run_git_command") as mock_run:
            mock_run.return_value = (" M file.py", "")

            result = get_changed_files(config=None, staged_only=False)

            assert result == {"file.py"}


class TestGetDiff:
    """Tests for get_diff function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__staged_returns_staged_diff(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return staged diff output."""
        mock_run.return_value = ("diff --staged output", "")

        result = get_diff(diff_type="staged", config=mock_config)

        mock_run.assert_called_once_with(["git", "diff", "--staged"], mock_config)
        assert result == "diff --staged output"

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__unstaged_returns_unstaged_diff(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return unstaged diff output."""
        mock_run.return_value = ("diff output", "")

        result = get_diff(diff_type="unstaged", config=mock_config)

        mock_run.assert_called_once_with(["git", "diff"], mock_config)
        assert result == "diff output"

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__default_is_staged(self, mock_run: MagicMock) -> None:
        """Default to staged diff when no type specified."""
        mock_run.return_value = ("staged diff", "")

        result = get_diff()

        mock_run.assert_called_once_with(["git", "diff", "--staged"], None)
        assert result == "staged diff"

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__raises_git_error_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when diff command fails."""
        mock_run.side_effect = GitError("git diff failed")

        with pytest.raises(GitError) as exc:
            get_diff(diff_type="staged", config=mock_config)

        assert "Failed to get staged diff" in str(exc.value)

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_header")
    @patch("git_acp.git.diff.debug_item")
    def test_get_diff__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("diff content", "")

        get_diff(diff_type="staged", config=verbose_config)

        mock_debug_header.assert_called_with("Getting staged diff")
        mock_debug_item.assert_called_with("Diff length", "12")

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__returns_empty_string_on_no_diff(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return empty string when no diff exists."""
        mock_run.return_value = ("", "")

        result = get_diff(diff_type="staged", config=mock_config)

        assert result == ""
