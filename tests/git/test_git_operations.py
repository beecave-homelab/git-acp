"""Tests for git_acp.git.git_operations helper functions."""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from git_acp.git.git_operations import (
    GitError,  # Added for testing exclusions
    get_changed_files,
    get_diff,
    git_push,
    run_git_command,
)
from git_acp.utils import GitConfig  # Added for creating config objects


class TestRunGitCommand:
    """Tests low-level git command execution behavior."""

    @patch("subprocess.Popen")
    def test_successful_command(self, mock_popen: MagicMock) -> None:
        """Run a successful git command and return stdout."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        stdout, stderr = run_git_command(["git", "status"])
        assert stdout == "output"

    @patch("subprocess.Popen")
    def test_error_handling(self, mock_popen: MagicMock) -> None:
        """Raise GitError when git command exits with non-zero status."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "fatal error")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError):
            run_git_command(["git", "invalid"])

    @patch("subprocess.Popen")
    def test_known_error_patterns(self, mock_popen: MagicMock) -> None:
        """Map known push errors to a helpful GitError message."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            "",
            "error: failed to push some refs to 'https://github.com/example.git'",
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(GitError) as exc:
            run_git_command(["git", "push"])
        assert "pull the latest changes" in str(exc.value)


class TestDiffOperations:
    """Tests for diff retrieval helpers."""

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff_staged(self, mock_run) -> None:
        """Return staged diff output from git diff --staged."""
        mock_run.return_value = ("diff output", "")
        result = get_diff("staged")
        assert result == "diff output"
        mock_run.assert_called_with(["git", "diff", "--staged"], None)

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff_unstaged(self, mock_run) -> None:
        """Return unstaged diff output from git diff."""
        mock_run.return_value = ("diff output", "")
        result = get_diff("unstaged")
        assert result == "diff output"
        mock_run.assert_called_with(["git", "diff"], None)


class TestChangedFiles:
    """Tests for get_changed_files helper."""

    @patch("git_acp.git.git_operations.run_git_command")
    def test_file_exclusion(self, mock_run) -> None:
        """Exclude __pycache__ files from changed file list."""
        mock_run.return_value = (
            "MM tests/__init__.py\n"
            "A  src/new_feature.py\n"
            "D  __pycache__/old.cpython-38.pyc",
            "",
        )
        files = get_changed_files()
        assert "__pycache__/old.cpython-38.pyc" not in files
        assert "src/new_feature.py" in files

    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files_staged_only_with_files(
        self, mock_run_git_command
    ) -> None:
        """Return staged files when staged_only=True."""
        mock_config = GitConfig(verbose=False)  # Create a minimal config
        mock_run_git_command.return_value = ("file1.py\nfolder/file2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        assert result == {"file1.py", "folder/file2.py"}

    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files_staged_only_no_files(self, mock_run_git_command) -> None:
        """Return empty set when no staged files exist."""
        mock_config = GitConfig(verbose=False)
        mock_run_git_command.return_value = ("", "")  # No output means no staged files

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        assert result == set()

    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files_staged_only_with_excluded_files(
        self, mock_run_git_command
    ) -> None:
        """Exclude __pycache__ files even when staged_only=True."""
        mock_config = GitConfig(verbose=False)
        # Ensure __pycache__ is in EXCLUDED_PATTERNS for this test to be meaningful.
        # If EXCLUDED_PATTERNS is dynamic, this test might need adjustment.
        mock_run_git_command.return_value = (
            "file1.py\n__pycache__/somefile.pyc\nfolder/file2.py",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        # Depending on the actual EXCLUDED_PATTERNS loaded by git_operations
        assert result == {"file1.py", "folder/file2.py"}


class TestPushOperations:
    """Tests for git push helper."""

    @patch("git_acp.git.staging.run_git_command")
    def test_push_success(self, mock_run):
        """Push to origin successfully."""
        mock_run.return_value = ("", "")
        git_push("main")
        mock_run.assert_called_with(["git", "push", "origin", "main"], None)

    @patch("git_acp.git.staging.run_git_command")
    def test_push_rejection(self, mock_run) -> None:
        """Raise GitError with helpful message on push rejection."""
        mock_run.side_effect = GitError("! [rejected]")
        with pytest.raises(GitError) as exc:
            git_push("feature")
        assert "Pull latest changes first" in str(exc.value)


class TestSignalHandlers:
    """Tests for signal handler setup."""

    @patch("git_acp.git.staging.unstage_files")
    @patch("git_acp.git.staging.rprint")
    def test_interrupt_handling(self, mock_rprint, mock_unstage) -> None:
        """Unstage files on SIGINT interrupt."""
        import signal

        from git_acp.git.staging import setup_signal_handlers

        # Set up the signal handler
        setup_signal_handlers()

        # Get the installed handler
        handler = signal.getsignal(signal.SIGINT)
        assert callable(handler), "SIGINT handler should be callable"

        # Call the handler and expect SystemExit
        with pytest.raises(SystemExit) as exc:
            handler(signal.SIGINT, None)

        assert exc.value.code == 1
        mock_unstage.assert_called_once()
        mock_rprint.assert_called_once()


class TestBranchOperations:
    """Tests for branch creation and deletion helpers."""

    @patch("git_acp.git.management.run_git_command")
    def test_create_branch(self, mock_run) -> None:
        """Create a new branch with git checkout -b."""
        from git_acp.git.git_operations import create_branch

        mock_config = GitConfig(verbose=False)
        create_branch(
            "new-feature", config=mock_config
        )  # Removed base_branch as it's not in signature
        mock_run.assert_called_with(
            ["git", "checkout", "-b", "new-feature"],  # Adjusted call
            mock_config,
        )

    @patch("git_acp.git.management.run_git_command")
    def test_delete_branch(self, mock_run) -> None:
        """Delete a branch with git branch -d."""
        from git_acp.git.git_operations import delete_branch

        mock_config = GitConfig(verbose=False)
        delete_branch("old-branch", config=mock_config)
        mock_run.assert_called_with(
            [
                "git",
                "branch",
                "-d",
                "old-branch",
            ],  # Assuming force delete for simplicity, or add force=True
            mock_config,
        )


class TestTagOperations:
    """Tests for tag management helpers."""

    @patch("git_acp.git.management.run_git_command")
    def test_create_annotated_tag(self, mock_run) -> None:
        """Create an annotated tag with git tag -a."""
        from git_acp.git.git_operations import manage_tags

        mock_config = GitConfig(verbose=False)
        manage_tags("create", "v0.5.0", message="Initial release", config=mock_config)
        mock_run.assert_called_with(
            ["git", "tag", "-a", "v0.5.0", "-m", "Initial release"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    def test_delete_tag(self, mock_run) -> None:
        """Delete a tag with git tag -d."""
        from git_acp.git.git_operations import manage_tags

        mock_config = GitConfig(verbose=False)
        manage_tags("delete", "v0.5.0", config=mock_config)
        mock_run.assert_called_with(["git", "tag", "-d", "v0.5.0"], mock_config)
        manage_tags("delete", "v0.5", config=mock_config)
        mock_run.assert_called_with(["git", "tag", "-d", "v0.5"], mock_config)


class TestCommitAnalysis:
    """Tests for commit pattern analysis."""

    def test_analyze_commit_patterns(self) -> None:
        """Parse conventional commit types and scopes."""
        from git_acp.git.git_operations import analyze_commit_patterns

        mock_config = GitConfig(verbose=False)
        test_commits = [
            {"message": "feat: add new module"},
            {"message": "fix(login): resolve auth issue"},
            {"message": "docs: update README"},
            {"message": "chore: update dependencies"},
            {"message": "invalid commit message"},
        ]

        patterns = analyze_commit_patterns(test_commits, config=mock_config)

        assert patterns["types"]["feat"] == 1
        assert patterns["types"]["fix"] == 1
        assert patterns["types"]["docs"] == 1
        assert patterns["scopes"]["login"] == 1


class TestProtectedBranches:
    """Tests for protected branch handling."""

    @patch("git_acp.git.management.run_git_command")
    def test_protected_branch_deletion(self, mock_run) -> None:
        """Raise GitError when deleting a protected branch."""
        from git_acp.git.git_operations import delete_branch

        mock_config = GitConfig(verbose=False)
        mock_run.side_effect = GitError("protected branch")

        with pytest.raises(GitError) as exc:
            delete_branch(
                "main", config=mock_config
            )  # Added force=True or handle default

        assert "protected branch" in str(exc.value)


class TestChangedFilesUnittest(
    unittest.TestCase
):  # Changed from 'class TestChangedFiles:'
    """Unittest-style tests for changed-files helper behavior."""

    @patch("git_acp.git.git_operations.run_git_command")
    def test_file_exclusion(self, mock_run) -> None:
        """Exclude __pycache__ files from changed file list (unittest style)."""
        mock_config = GitConfig(verbose=False)
        mock_run.return_value = (
            "MM tests/__init__.py\n"
            "A  src/new_feature.py\n"
            "D  __pycache__/old.cpython-38.pyc",
            "",
        )
        files = get_changed_files(config=mock_config)
        self.assertNotIn("__pycache__/old.cpython-38.pyc", files)
        self.assertIn("src/new_feature.py", files)

    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files_staged_only_with_files(
        self, mock_run_git_command
    ) -> None:
        """Return staged files when staged_only=True (unittest style)."""
        mock_config = GitConfig(verbose=False)
        mock_run_git_command.return_value = ("file1.py\nfolder/file2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, {"file1.py", "folder/file2.py"})

    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files_staged_only_no_files(self, mock_run_git_command) -> None:
        """Return empty set when no staged files exist (unittest style)."""
        mock_config = GitConfig(verbose=False)
        mock_run_git_command.return_value = ("", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, set())

    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files_staged_only_with_excluded_files(
        self, mock_run_git_command
    ) -> None:
        """Exclude __pycache__ files even when staged_only=True (unittest style)."""
        mock_config = GitConfig(verbose=False)
        # Assuming EXCLUDED_PATTERNS is available and includes "__pycache__"
        mock_run_git_command.return_value = (
            "file1.py\n__pycache__/somefile.pyc\nfolder/file2.py",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, {"file1.py", "folder/file2.py"})


class TestChangedFilesVerbose:
    """Tests for get_changed_files with verbose mode."""

    @patch("git_acp.git.git_operations.debug_item")
    @patch("git_acp.git.git_operations.debug_header")
    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files__verbose_staged_only(
        self, mock_run, mock_debug_header, mock_debug_item
    ) -> None:
        """Log debug output for staged files in verbose mode."""
        mock_config = GitConfig(verbose=True)
        mock_run.return_value = ("file.py", "")

        get_changed_files(config=mock_config, staged_only=True)

        mock_debug_header.assert_called_once()
        mock_debug_item.assert_called()

    @patch("git_acp.git.git_operations.debug_item")
    @patch("git_acp.git.git_operations.debug_header")
    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files__verbose_status_mode(
        self, mock_run, mock_debug_header, mock_debug_item
    ) -> None:
        """Log debug output for status mode in verbose mode."""
        mock_config = GitConfig(verbose=True)
        mock_run.return_value = (" M file.py", "")

        get_changed_files(config=mock_config, staged_only=False)

        mock_debug_header.assert_called_once()
        assert mock_debug_item.call_count >= 2

    @patch("git_acp.git.git_operations.debug_item")
    @patch("git_acp.git.git_operations.debug_header")
    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files__verbose_with_rename(
        self, mock_run, mock_debug_header, mock_debug_item
    ) -> None:
        """Handle renamed files with arrow notation in verbose mode."""
        mock_config = GitConfig(verbose=True)
        mock_run.return_value = ("R  old.py -> new.py", "")

        result = get_changed_files(config=mock_config, staged_only=False)

        assert "new.py" in result
        assert "old.py" not in result
        mock_debug_item.assert_called()

    @patch("git_acp.git.git_operations.debug_item")
    @patch("git_acp.git.git_operations.debug_header")
    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files__verbose_exclusion(
        self, mock_run, mock_debug_header, mock_debug_item
    ) -> None:
        """Log exclusion in verbose mode."""
        mock_config = GitConfig(verbose=True)
        mock_run.return_value = (" M __pycache__/file.pyc", "")

        get_changed_files(config=mock_config, staged_only=False)

        # Should have logged exclusion
        exclusion_logged = any(
            "Excluding" in str(call) for call in mock_debug_item.call_args_list
        )
        assert exclusion_logged

    @patch("git_acp.git.git_operations.run_git_command")
    def test_get_changed_files__empty_line_handling(self, mock_run) -> None:
        """Skip empty lines in status output."""
        mock_config = GitConfig(verbose=False)
        mock_run.return_value = (" M file1.py\n\n   \n M file2.py", "")

        result = get_changed_files(config=mock_config, staged_only=False)

        assert result == {"file1.py", "file2.py"}
