import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from git_acp.cli.cli import main
from git_acp.utils import GitConfig  # For creating config objects if needed


class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        # This self.mock_config can be a template, but often config is implicitly created
        # by the CLI main function based on parameters. So, direct mocking of functions
        # that would receive a config might be more straightforward than preparing one here.

    @patch("git_acp.cli.cli.sys.exit")
    @patch("git_acp.cli.cli.git_push")
    @patch("git_acp.cli.cli.git_commit")
    @patch("git_acp.cli.cli.generate_commit_message")
    @patch("git_acp.git.get_changed_files")  # Mocking the one in .git module
    @patch("git_acp.cli.cli.git_add")
    @patch("glob.glob")
    def test_cli_add_path_has_changes(
        self,
        mock_glob,
        mock_git_add,
        mock_get_changed_files_git_module,
        mock_generate_commit_message,
        mock_git_commit,
        mock_git_push,
        mock_sys_exit,
    ):
        """Scenario 2.1: -a used, specified path has changes (files are staged)."""
        # Mock get_changed_files (called by CLI for -a check) to return staged files
        # This mock is for the call: get_changed_files(config, staged_only=True)
        mock_get_changed_files_git_module.return_value = {"folder/file1.py"}
        mock_glob.return_value = ["folder/file1.py"]

        # Mock generate_commit_message to return a dummy message
        mock_generate_commit_message.return_value = "AI generated commit message"

        # Mock get_current_branch used internally if no branch is specified
        with patch("git_acp.cli.cli.get_current_branch") as mock_get_current_branch:
            mock_get_current_branch.return_value = "main"

            self.runner.invoke(
                main, ["-a", "folder/*.py", "-o", "--no-confirm", "--verbose"]
            )

        mock_git_add.assert_called_once()  # Check if git_add was called
        # The config object is created inside main, so we check the first arg of git_add
        self.assertEqual(mock_git_add.call_args[0][0], "folder/file1.py")

        mock_generate_commit_message.assert_called()
        mock_git_commit.assert_called()
        mock_git_push.assert_called()
        # If an error occurred, result.exit_code would be non-zero.
        # If it exited due to "no changes", specific mocks downstream wouldn't be called.

    @patch("git_acp.cli.cli.sys.exit")
    @patch("git_acp.cli.cli.git_push")  # Order matters for decorators, bottom up
    @patch("git_acp.cli.cli.git_commit")
    @patch("git_acp.cli.cli.generate_commit_message")
    @patch("git_acp.git.get_changed_files")  # Mocking the one in .git module
    @patch("git_acp.cli.cli.git_add")
    @patch("glob.glob")
    def test_cli_add_path_no_changes(
        self,
        mock_glob,
        mock_git_add,
        mock_get_changed_files_git_module,
        mock_generate_commit_message,
        mock_git_commit,
        mock_git_push,
        mock_sys_exit,
    ):
        """Scenario 2.2: -a used, specified path has no files with changes."""
        # Mock get_changed_files (called by CLI for -a check) to return an empty set
        mock_get_changed_files_git_module.return_value = set()
        mock_glob.return_value = []

        # Mock get_current_branch used internally if no branch is specified
        with patch("git_acp.cli.cli.get_current_branch") as mock_get_current_branch:
            mock_get_current_branch.return_value = "main"  # Needed for config creation
            result = self.runner.invoke(main, ["-a", "folder/*.py", "--no-confirm"])

        mock_git_add.assert_not_called()

        self.assertIn(
            "didnotmatchanyfilesystempaths:folder/*.py", "".join(result.output.split())
        )
        mock_sys_exit.assert_any_call(0)  # Should exit with 0

        # Ensure downstream functions were not called
        mock_generate_commit_message.assert_not_called()
        mock_git_commit.assert_not_called()
        mock_git_push.assert_not_called()


if __name__ == "__main__":
    unittest.main()
