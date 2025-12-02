"""Tests for git_acp.cli.cli module."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from git_acp.cli.cli import main
from git_acp.git import CommitType


class TestCli(unittest.TestCase):
    """Tests for the CLI entry point."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("git_acp.cli.cli.sys.exit")
    @patch("git_acp.cli.workflow.git_push")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.generate_commit_message")
    @patch("git_acp.cli.workflow.get_changed_files")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("glob.glob")
    def test_cli_add_path_has_changes(
        self,
        mock_glob: MagicMock,
        mock_classify: MagicMock,
        mock_git_add: MagicMock,
        mock_get_changed_files: MagicMock,
        mock_generate_commit_message: MagicMock,
        mock_git_commit: MagicMock,
        mock_git_push: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Scenario 2.1: -a used, specified path has changes (files are staged)."""
        mock_get_changed_files.return_value = {"folder/file1.py"}
        mock_glob.return_value = ["folder/file1.py"]
        mock_generate_commit_message.return_value = "AI generated commit message"
        mock_classify.return_value = CommitType.FEAT

        with patch("git_acp.cli.workflow.get_current_branch") as mock_branch:
            mock_branch.return_value = "main"

            self.runner.invoke(
                main, ["-a", "folder/*.py", "-o", "--no-confirm", "--verbose"]
            )

        mock_git_add.assert_called_once()
        mock_generate_commit_message.assert_called()
        mock_git_commit.assert_called()
        mock_git_push.assert_called()

    @patch("git_acp.cli.cli.sys.exit")
    @patch("glob.glob")
    def test_cli_add_path_no_changes(
        self,
        mock_glob: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Scenario 2.2: -a used, specified path has no files with changes."""
        mock_glob.return_value = []

        result = self.runner.invoke(main, ["-a", "folder/*.py", "--no-confirm"])

        self.assertIn(
            "didnotmatchanyfilesystempaths:folder/*.py", "".join(result.output.split())
        )
        mock_sys_exit.assert_any_call(0)


if __name__ == "__main__":
    unittest.main()
