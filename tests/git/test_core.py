"""Tests for git_acp.git.core module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_acp.git.core import GitError, run_git_command
from git_acp.utils import GitConfig


class TestGitError:
    """Tests for GitError exception class."""

    def test_git_error__is_exception(self) -> None:
        """GitError is a subclass of Exception."""
        assert issubclass(GitError, Exception)

    def test_git_error__can_be_raised(self) -> None:
        """GitError can be raised and caught.

        Raises:
            GitError: Always raises GitError with "test error".
        """
        with pytest.raises(GitError) as exc:
            raise GitError("test error")

        assert str(exc.value) == "test error"

    def test_git_error__preserves_message(self) -> None:
        """GitError preserves the error message."""
        error = GitError("custom message")
        assert str(error) == "custom message"


class TestRunGitCommand:
    """Tests for run_git_command function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("subprocess.Popen")
    def test_run_git_command__returns_stdout_stderr(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return tuple of stdout and stderr."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        stdout, stderr = run_git_command(["git", "status"], mock_config)

        assert stdout == "output"
        assert stderr == ""

    @patch("subprocess.Popen")
    def test_run_git_command__strips_output(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Strip whitespace from stdout and stderr."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("  output  \n", "  error  \n")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        stdout, stderr = run_git_command(["git", "status"], mock_config)

        assert stdout == "output"
        assert stderr == "error"

    @patch("subprocess.Popen")
    def test_run_git_command__raises_on_nonzero_exit(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError on non-zero exit code."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "error message")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "invalid"], mock_config)

        assert "error message" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__not_a_git_repository(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'not a git repository' error to helpful message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "fatal: not a git repository",
        )
        mock_process.returncode = 128
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "status"], mock_config)

        assert "Not a git repository" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__did_not_match_any_files(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'did not match any files' error to helpful message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "error: pathspec 'foo' did not match any files",
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "add", "foo"], mock_config)

        assert "No files matched" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__nothing_to_commit(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'nothing to commit' error to helpful message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "nothing to commit")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "commit"], mock_config)

        assert "No changes to commit" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__permission_denied(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'permission denied' error to helpful message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "fatal: permission denied")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "push"], mock_config)

        assert "Permission denied" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__remote_not_found(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'remote: Repository not found' error to helpful message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "remote: Repository not found",
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "push"], mock_config)

        assert "Remote repository not found" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__failed_to_push(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'failed to push' error to helpful message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "error: failed to push some refs",
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "push"], mock_config)

        assert "Failed to push changes" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__cannot_lock_ref(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'cannot lock ref' error to helpful message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "error: cannot lock ref",
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "checkout"], mock_config)

        assert "Cannot lock ref" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__unrelated_histories(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'refusing to merge unrelated histories' error."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "fatal: refusing to merge unrelated histories",
        )
        mock_process.returncode = 128
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "merge"], mock_config)

        assert "unrelated histories" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__local_changes_overwritten(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Map 'local changes would be overwritten' error."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "error: Your local changes would be overwritten by merge",
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "pull"], mock_config)

        assert "Local changes would be overwritten" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__file_not_found_error(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when git is not installed."""
        mock_popen.side_effect = FileNotFoundError("git not found")

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "status"], mock_config)

        assert "Git is not installed" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__permission_error_exception(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError on PermissionError."""
        mock_popen.side_effect = PermissionError("permission denied")

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "status"], mock_config)

        assert "Permission denied while executing" in str(exc.value)

    @patch("subprocess.Popen")
    def test_run_git_command__generic_exception(
        self, mock_popen: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError on generic exceptions."""
        mock_popen.side_effect = OSError("unexpected error")

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "status"], mock_config)

        assert "Failed to execute git command" in str(exc.value)

    @patch("subprocess.Popen")
    @patch("git_acp.git.core.debug_header")
    @patch("git_acp.git.core.debug_item")
    def test_run_git_command__verbose_logs_command(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_popen: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log command execution in verbose mode."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        run_git_command(["git", "status"], verbose_config)

        mock_debug_header.assert_called_with("Git Command Execution")
        mock_debug_item.assert_any_call("Command", "git status")

    @patch("subprocess.Popen")
    @patch("git_acp.git.core.debug_header")
    @patch("git_acp.git.core.debug_item")
    def test_run_git_command__verbose_logs_output(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_popen: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log command output in verbose mode."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("command output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        run_git_command(["git", "status"], verbose_config)

        mock_debug_item.assert_any_call("Command Output", "command output")

    @patch("subprocess.Popen")
    @patch("git_acp.git.core.debug_header")
    @patch("git_acp.git.core.debug_item")
    def test_run_git_command__verbose_logs_error_details(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_popen: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log error details in verbose mode."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "error occurred")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError):
            run_git_command(["git", "invalid"], verbose_config)

        mock_debug_header.assert_any_call("Git Command Failed")
        mock_debug_item.assert_any_call("Exit Code", "1")
        mock_debug_item.assert_any_call("Error Output", "error occurred")

    @patch("subprocess.Popen")
    @patch("git_acp.git.core.debug_header")
    @patch("git_acp.git.core.debug_item")
    def test_run_git_command__verbose_logs_file_not_found(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_popen: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log FileNotFoundError in verbose mode."""
        mock_popen.side_effect = FileNotFoundError("git not found")

        with pytest.raises(GitError):
            run_git_command(["git", "status"], verbose_config)

        mock_debug_header.assert_called_with("Git Command Error")
        mock_debug_item.assert_any_call("Error Type", "FileNotFoundError")

    @patch("subprocess.Popen")
    @patch("git_acp.git.core.debug_header")
    @patch("git_acp.git.core.debug_item")
    def test_run_git_command__verbose_logs_permission_error(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_popen: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log PermissionError in verbose mode."""
        mock_popen.side_effect = PermissionError("denied")

        with pytest.raises(GitError):
            run_git_command(["git", "status"], verbose_config)

        mock_debug_header.assert_called_with("Git Command Error")
        mock_debug_item.assert_any_call("Error Type", "PermissionError")

    @patch("subprocess.Popen")
    @patch("git_acp.git.core.debug_header")
    @patch("git_acp.git.core.debug_item")
    def test_run_git_command__verbose_logs_generic_error(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_popen: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log generic errors in verbose mode."""
        mock_popen.side_effect = OSError("unexpected")

        with pytest.raises(GitError):
            run_git_command(["git", "status"], verbose_config)

        mock_debug_header.assert_called_with("Git Command Error")
        mock_debug_item.assert_any_call("Error Type", "OSError")

    @patch("subprocess.Popen")
    def test_run_git_command__no_config(self, mock_popen: MagicMock) -> None:
        """Work without a config object."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        stdout, stderr = run_git_command(["git", "status"])

        assert stdout == "output"
