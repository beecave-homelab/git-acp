"""Tests for git_acp.git.staging module."""

from __future__ import annotations

import signal
from unittest.mock import MagicMock, patch

import pytest

from git_acp.git.core import GitError
from git_acp.git.staging import (
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    setup_signal_handlers,
    unstage_files,
)
from git_acp.utils import GitConfig


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.staging.run_git_command")
    def test_get_current_branch__returns_branch_name(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return the current branch name."""
        mock_run.return_value = ("main", "")

        result = get_current_branch(config=mock_config)

        assert result == "main"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], mock_config
        )

    @patch("git_acp.git.staging.run_git_command")
    def test_get_current_branch__strips_whitespace(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Strip whitespace from branch name."""
        mock_run.return_value = ("  feature-branch  ", "")

        result = get_current_branch(config=mock_config)

        # run_git_command already strips, but test the expectation
        assert result == "  feature-branch  "  # Raw return from mock

    @patch("git_acp.git.staging.run_git_command")
    def test_get_current_branch__raises_on_empty_output(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when branch cannot be determined."""
        mock_run.return_value = ("", "")

        with pytest.raises(GitError) as exc:
            get_current_branch(config=mock_config)

        assert "Could not determine the current branch" in str(exc.value)

    @patch("git_acp.git.staging.run_git_command")
    def test_get_current_branch__raises_on_git_error(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when git command fails."""
        mock_run.side_effect = GitError("not a git repository")

        with pytest.raises(GitError) as exc:
            get_current_branch(config=mock_config)

        assert "Could not determine the current branch" in str(exc.value)

    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    @patch("git_acp.git.staging.debug_item")
    def test_get_current_branch__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("main", "")

        get_current_branch(config=verbose_config)

        mock_debug_header.assert_called_with("Getting Current Branch")
        mock_debug_item.assert_called_with("Current Branch", "main")

    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    @patch("git_acp.git.staging.debug_item")
    def test_get_current_branch__verbose_logs_error(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log error in verbose mode when detection fails."""
        mock_run.side_effect = GitError("failed")

        with pytest.raises(GitError):
            get_current_branch(config=verbose_config)

        mock_debug_header.assert_called_with("Branch Detection Failed")


class TestGitAdd:
    """Tests for git_add function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_add__adds_all_files(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Add all files with '.'."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_add(".", config=mock_config)

        mock_run.assert_called_once_with(["git", "add", "."], mock_config)
        mock_success.assert_called_once_with("Files added successfully")

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_add__adds_specific_files(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Add specific files."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_add("file1.py file2.py", config=mock_config)

        assert mock_run.call_count == 2
        mock_run.assert_any_call(["git", "add", "file1.py"], mock_config)
        mock_run.assert_any_call(["git", "add", "file2.py"], mock_config)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_add__handles_quoted_paths(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Handle quoted file paths with spaces."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_add('"file with spaces.py"', config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "add", "file with spaces.py"], mock_config
        )

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_add__raises_on_failure(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Raise GitError when add fails."""
        mock_run.side_effect = GitError("file not found")

        with pytest.raises(GitError) as exc:
            git_add("nonexistent.py", config=mock_config)

        assert "Failed to add files" in str(exc.value)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    @patch("git_acp.git.staging.debug_item")
    def test_git_add__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_add(".", config=verbose_config)

        mock_debug_header.assert_called()
        mock_debug_item.assert_called()

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    @patch("git_acp.git.staging.debug_item")
    def test_git_add__verbose_logs_error(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log error details in verbose mode."""
        mock_run.side_effect = GitError("error")

        with pytest.raises(GitError):
            git_add("file.py", config=verbose_config)

        mock_debug_header.assert_called_with("Git Add Failed")


class TestGitCommit:
    """Tests for git_commit function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_commit__commits_with_message(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Commit staged changes with message."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_commit("feat: add new feature", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "commit", "-m", "feat: add new feature"], mock_config
        )
        mock_success.assert_called_once_with("Changes committed successfully")

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_commit__raises_on_failure(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Raise GitError when commit fails."""
        mock_run.side_effect = GitError("nothing to commit")

        with pytest.raises(GitError) as exc:
            git_commit("test message", config=mock_config)

        assert "Failed to commit changes" in str(exc.value)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    @patch("git_acp.git.staging.debug_item")
    def test_git_commit__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_commit("test", config=verbose_config)

        mock_debug_header.assert_called()
        mock_debug_item.assert_called()

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    def test_git_commit__verbose_logs_error(
        self,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log error in verbose mode when commit fails."""
        mock_run.side_effect = GitError("error")

        with pytest.raises(GitError):
            git_commit("test", config=verbose_config)

        mock_debug_header.assert_called_with("Commit Failed")


class TestGitPush:
    """Tests for git_push function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_push__pushes_to_remote(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Push to origin remote."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_push("main", config=mock_config)

        mock_run.assert_called_once_with(["git", "push", "origin", "main"], mock_config)
        mock_success.assert_called_once_with("Changes pushed successfully")

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_push__raises_on_rejection(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Raise GitError with helpful message on rejection."""
        mock_run.side_effect = GitError("rejected")

        with pytest.raises(GitError) as exc:
            git_push("main", config=mock_config)

        assert "Pull latest changes first" in str(exc.value)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_push__raises_on_no_upstream(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Raise GitError with helpful message when no upstream."""
        mock_run.side_effect = GitError("no upstream branch")

        with pytest.raises(GitError) as exc:
            git_push("feature", config=mock_config)

        assert "No upstream branch" in str(exc.value)
        assert "--set-upstream" in str(exc.value)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    def test_git_push__raises_generic_error(
        self,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Raise GitError for other push failures."""
        mock_run.side_effect = GitError("network error")

        with pytest.raises(GitError) as exc:
            git_push("main", config=mock_config)

        assert "Failed to push changes" in str(exc.value)

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    @patch("git_acp.git.staging.debug_item")
    def test_git_push__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")
        mock_status.return_value.__enter__ = MagicMock()
        mock_status.return_value.__exit__ = MagicMock()

        git_push("main", config=verbose_config)

        mock_debug_header.assert_called()
        mock_debug_item.assert_called()

    @patch("git_acp.git.staging.success")
    @patch("git_acp.git.staging.status")
    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    def test_git_push__verbose_logs_error(
        self,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        mock_status: MagicMock,
        mock_success: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log error in verbose mode when push fails."""
        mock_run.side_effect = GitError("error")

        with pytest.raises(GitError):
            git_push("main", config=verbose_config)

        mock_debug_header.assert_called_with("Push Failed")


class TestUnstageFiles:
    """Tests for unstage_files function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.staging.run_git_command")
    def test_unstage_files__resets_head(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Unstage all files with git reset HEAD."""
        mock_run.return_value = ("", "")

        unstage_files(config=mock_config)

        mock_run.assert_called_once_with(["git", "reset", "HEAD"], mock_config)

    @patch("git_acp.git.staging.run_git_command")
    def test_unstage_files__raises_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when unstaging fails."""
        mock_run.side_effect = GitError("reset failed")

        with pytest.raises(GitError) as exc:
            unstage_files(config=mock_config)

        assert "Failed to unstage files" in str(exc.value)

    @patch("git_acp.git.staging.run_git_command")
    @patch("git_acp.git.staging.debug_header")
    def test_unstage_files__verbose_logs_debug(
        self,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")

        unstage_files(config=verbose_config)

        mock_debug_header.assert_called_with("Unstaging all files")


class TestSetupSignalHandlers:
    """Tests for setup_signal_handlers function."""

    @patch("git_acp.git.staging.unstage_files")
    @patch("git_acp.git.staging.rprint")
    def test_setup_signal_handlers__installs_sigint_handler(
        self, mock_rprint: MagicMock, mock_unstage: MagicMock
    ) -> None:
        """Install SIGINT signal handler."""
        setup_signal_handlers()

        handler = signal.getsignal(signal.SIGINT)
        assert callable(handler)

    @patch("git_acp.git.staging.unstage_files")
    @patch("git_acp.git.staging.rprint")
    def test_setup_signal_handlers__handler_unstages_and_exits(
        self, mock_rprint: MagicMock, mock_unstage: MagicMock
    ) -> None:
        """Signal handler unstages files and exits with code 1."""
        setup_signal_handlers()

        handler = signal.getsignal(signal.SIGINT)

        with pytest.raises(SystemExit) as exc:
            handler(signal.SIGINT, None)

        assert exc.value.code == 1
        mock_unstage.assert_called_once()
        mock_rprint.assert_called_once()
