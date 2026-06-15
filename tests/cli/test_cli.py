"""Tests for git_acp.cli.cli module."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from git_acp import __version__
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

    @patch("git_acp.cli.cli.sys.exit")
    @patch("git_acp.cli.workflow.git_push")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.generate_commit_message")
    @patch("git_acp.cli.workflow.get_changed_files")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("glob.glob")
    def test_cli_add_dot_lists_files(
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
        """Scenario 2.3: -a . used, lists individual files being staged."""
        mock_get_changed_files.return_value = {
            "README.md",
            "VERSIONS.md",
            "project-overview.md",
        }
        mock_glob.return_value = [
            "README.md",
            "VERSIONS.md",
            "project-overview.md",
        ]
        mock_generate_commit_message.return_value = "AI generated commit message"
        mock_classify.return_value = CommitType.DOCS

        with patch("git_acp.cli.workflow.get_current_branch") as mock_branch:
            mock_branch.return_value = "main"

            result = self.runner.invoke(
                main, ["-a", ".", "-o", "--no-confirm", "--verbose"]
            )

        output = result.output
        self.assertIn("Adding files:", output)
        self.assertIn("  - README.md", output)
        self.assertIn("  - VERSIONS.md", output)
        self.assertIn("  - project-overview.md", output)

        mock_git_add.assert_called_once()
        mock_generate_commit_message.assert_called()
        mock_git_commit.assert_called()
        mock_git_push.assert_called()

    def test_cli_version_flag(self) -> None:
        """Test that --version flag displays the correct version."""
        result = self.runner.invoke(main, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("git-acp, version", result.output)
        self.assertIn(__version__, result.output)

    @patch("git_acp.config.run_setup", return_value=0)
    def test_cli_setup_flag(self, mock_setup: MagicMock) -> None:
        """Should call run_setup when --setup is passed."""
        result = self.runner.invoke(main, ["--setup"])
        assert result.exit_code == 0
        mock_setup.assert_called_once_with(force=False)

    @patch("git_acp.config.run_setup", return_value=0)
    def test_cli_setup_with_force(self, mock_setup: MagicMock) -> None:
        """Should call run_setup with force=True when both flags passed."""
        result = self.runner.invoke(main, ["--setup", "--force"])
        assert result.exit_code == 0
        mock_setup.assert_called_once_with(force=True)

    def test_cli_type__accepts_build(self) -> None:
        """The -t flag should accept 'build' as a valid commit type."""
        result = self.runner.invoke(main, ["-t", "build", "--dry-run"])
        # Click.Choice validation fails with exit code 2; we expect it to
        # proceed past argument parsing (any non-2 exit is fine here).
        self.assertNotEqual(result.exit_code, 2)
        self.assertNotIn("Invalid value", result.output)

    def test_cli_type__accepts_ci(self) -> None:
        """The -t flag should accept 'ci' as a valid commit type."""
        result = self.runner.invoke(main, ["-t", "ci", "--dry-run"])
        self.assertNotEqual(result.exit_code, 2)
        self.assertNotIn("Invalid value", result.output)

    def test_cli_type__accepts_perf(self) -> None:
        """The -t flag should accept 'perf' as a valid commit type."""
        result = self.runner.invoke(main, ["-t", "perf", "--dry-run"])
        self.assertNotEqual(result.exit_code, 2)
        self.assertNotIn("Invalid value", result.output)

    def test_cli_type__rejects_invalid(self) -> None:
        """The -t flag should reject invalid commit types."""
        result = self.runner.invoke(main, ["-t", "invalid_type", "--dry-run"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Invalid value", result.output)


if __name__ == "__main__":
    unittest.main()
