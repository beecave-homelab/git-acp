import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from git_acp.cli.cli import main
from git_acp.utils import GitConfig # For creating config objects if needed

class TestCli(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        # This self.mock_config can be a template, but often config is implicitly created
        # by the CLI main function based on parameters. So, direct mocking of functions
        # that would receive a config might be more straightforward than preparing one here.

    @patch('git_acp.cli.cli.sys.exit')
    @patch('git_acp.cli.cli.git_push')
    @patch('git_acp.cli.cli.git_commit')
    @patch('git_acp.cli.cli.generate_commit_message')
    @patch('git_acp.git.get_changed_files') # Mocking the one in .git module
    @patch('git_acp.cli.cli.git_add')
    def test_cli_add_path_has_changes(self, mock_git_add, mock_get_changed_files_git_module,
                                       mock_generate_commit_message, mock_git_commit,
                                       mock_git_push, mock_sys_exit):
        """Scenario 2.1: -a used, specified path has changes (files are staged)."""
        # Mock get_changed_files (called by CLI for -a check) to return staged files
        # This mock is for the call: get_changed_files(config, staged_only=True)
        mock_get_changed_files_git_module.return_value = {"folder/file1.py"}

        # Mock generate_commit_message to return a dummy message
        mock_generate_commit_message.return_value = "AI generated commit message"

        # Mock get_current_branch used internally if no branch is specified
        with patch('git_acp.cli.cli.get_current_branch') as mock_get_current_branch:
            mock_get_current_branch.return_value = "main"

            result = self.runner.invoke(main, ['-a', 'folder/*.py', '-o', '--no-confirm', '--verbose'])

        print(f"Output: {result.output}") # For debugging test
        print(f"Exception: {result.exception}")
        print(f"Exit code: {result.exit_code}")


        mock_git_add.assert_called_once() # Check if git_add was called
        # The config object is created inside main, so we check the first arg of git_add
        self.assertEqual(mock_git_add.call_args[0][0], "folder/*.py")


        # Check that get_changed_files was called for the -a check, with staged_only=True
        # The first call to get_changed_files might be with staged_only=False if add is None
        # The second call (if add is not None) should have staged_only=True
        found_staged_only_call = False
        for call_args in mock_get_changed_files_git_module.call_args_list:
            # call_args is a tuple: (args, kwargs)
            # args is a tuple of positional arguments, config is the first one
            # kwargs is a dict of keyword arguments
            if call_args[1].get('staged_only') is True:
                found_staged_only_call = True
                break
        self.assertTrue(found_staged_only_call, "get_changed_files with staged_only=True was not called")


        self.assertNotIn("No files with changes found in the specified path", result.output)
        # Check that sys.exit(0) was not called prematurely
        # if sys_exit was called with 0, it means the "no changes" path was taken.
        # We expect it to proceed, so if it exits, it would be with 1 (error) or 0 (after success)
        # For this test, we primarily care it didn't exit due to "no changes".
        # A successful run will also call sys.exit(0) at the very end if not for mocks.
        # Here, since we mock downstream, a normal exit_code of 0 is fine.
        # The key is that mock_sys_exit wasn't called with 0 *because* of the "no changes" check.
        # This is implicitly checked by asserting "No files with changes" is not in output.
        # And asserting that commit/push were called.
        mock_generate_commit_message.assert_called()
        mock_git_commit.assert_called()
        mock_git_push.assert_called()
        # If an error occurred, result.exit_code would be non-zero.
        # If it exited due to "no changes", specific mocks downstream wouldn't be called.


    @patch('git_acp.cli.cli.sys.exit')
    @patch('git_acp.cli.cli.git_push') # Order matters for decorators, bottom up
    @patch('git_acp.cli.cli.git_commit')
    @patch('git_acp.cli.cli.generate_commit_message')
    @patch('git_acp.git.get_changed_files') # Mocking the one in .git module
    @patch('git_acp.cli.cli.git_add')
    def test_cli_add_path_no_changes(self, mock_git_add, mock_get_changed_files_git_module,
                                     mock_generate_commit_message, mock_git_commit,
                                     mock_git_push, mock_sys_exit):
        """Scenario 2.2: -a used, specified path has no files with changes."""
        # Mock get_changed_files (called by CLI for -a check) to return an empty set
        mock_get_changed_files_git_module.return_value = set()

        # Mock get_current_branch used internally if no branch is specified
        with patch('git_acp.cli.cli.get_current_branch') as mock_get_current_branch:
            mock_get_current_branch.return_value = "main" # Needed for config creation
            result = self.runner.invoke(main, ['-a', 'folder/*.py', '--no-confirm'])

        print(f"Output for no_changes: {result.output}")
        print(f"Exception for no_changes: {result.exception}")


        mock_git_add.assert_called_once()
        self.assertEqual(mock_git_add.call_args[0][0], "folder/*.py")

        # Check that get_changed_files was called correctly for the -a check
        found_staged_only_call = False
        for call_args in mock_get_changed_files_git_module.call_args_list:
            if call_args[1].get('staged_only') is True:
                found_staged_only_call = True
                # We also need to check the config object passed if it's complex
                # For now, just checking staged_only=True is sufficient
                break
        self.assertTrue(found_staged_only_call, "get_changed_files with staged_only=True was not called")

        self.assertIn("No files with changes found in the specified path: folder/*.py", result.output)
        mock_sys_exit.assert_called_once_with(0) # Should exit with 0

        # Ensure downstream functions were not called
        mock_generate_commit_message.assert_not_called()
        mock_git_commit.assert_not_called()
        mock_git_push.assert_not_called()

if __name__ == '__main__':
    unittest.main()
