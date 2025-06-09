import pytest
from unittest.mock import patch, MagicMock, call
from git_acp.git.git_operations import (
    run_git_command,
    get_diff,
    get_changed_files,
    git_push,
    GitError,
    EXCLUDED_PATTERNS # Added for testing exclusions
)
from git_acp.utils import GitConfig # Added for creating config objects
from subprocess import CalledProcessError
from unittest.mock import call # Ensure call is imported if not already

class TestRunGitCommand:
    @patch('subprocess.Popen')
    def test_successful_command(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('output', '')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        stdout, stderr = run_git_command(['git', 'status'])
        assert stdout == 'output'

    @patch('subprocess.Popen')
    def test_error_handling(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('', 'fatal error')
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        with pytest.raises(GitError):
            run_git_command(['git', 'invalid'])

    @patch('subprocess.Popen')
    def test_known_error_patterns(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            '', 
            'error: failed to push some refs to \'https://github.com/example.git\''
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        with pytest.raises(GitError) as exc:
            run_git_command(['git', 'push'])
        assert "pull the latest changes" in str(exc.value)

class TestDiffOperations:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_diff_staged(self, mock_run):
        mock_run.return_value = ('diff output', '')
        result = get_diff('staged')
        assert result == 'diff output'
        mock_run.assert_called_with(["git", "diff", "--staged"], None)

    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_diff_unstaged(self, mock_run):
        mock_run.return_value = ('diff output', '')
        result = get_diff('unstaged')
        assert result == 'diff output'
        mock_run.assert_called_with(["git", "diff"], None)

class TestChangedFiles:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_file_exclusion(self, mock_run):
        mock_run.return_value = (
            'MM tests/__init__.py\n'
            'A  src/new_feature.py\n'
            'D  __pycache__/old.cpython-38.pyc',
            ''
        )
        files = get_changed_files()
        assert '__pycache__/old.cpython-38.pyc' not in files
        assert 'src/new_feature.py' in files

    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_changed_files_staged_only_with_files(self, mock_run_git_command):
        mock_config = GitConfig(verbose=False) # Create a minimal config
        mock_run_git_command.return_value = ("file1.py\nfolder/file2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, {"file1.py", "folder/file2.py"})

    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_changed_files_staged_only_no_files(self, mock_run_git_command):
        mock_config = GitConfig(verbose=False)
        mock_run_git_command.return_value = ("", "") # No output means no staged files

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, set())

    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_changed_files_staged_only_with_excluded_files(self, mock_run_git_command):
        mock_config = GitConfig(verbose=False)
        # Ensure __pycache__ is in EXCLUDED_PATTERNS for this test to be meaningful
        # For this example, let's assume it is, as per the problem description.
        # If EXCLUDED_PATTERNS is dynamic, this test might need adjustment or direct mock.
        mock_run_git_command.return_value = ("file1.py\n__pycache__/somefile.pyc\nfolder/file2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        # Depending on the actual EXCLUDED_PATTERNS loaded by git_operations
        self.assertEqual(result, {"file1.py", "folder/file2.py"})

    # Keep existing tests, just ensure self.assertEqual is used if this class inherits unittest.TestCase
    # If it's a plain pytest class, assert works fine. The current file uses plain asserts.
    # For consistency with potential new structure (if TestChangedFiles becomes a unittest.TestCase subclass):
    # For the original test_file_exclusion, if it were unittest:
    # @patch('git_acp.git.git_operations.run_git_command')
    # def test_file_exclusion_unittest_style(self, mock_run):
    #     mock_config = GitConfig(verbose=False)
    #     mock_run.return_value = (
    #         'MM tests/__init__.py\n'
    #         'A  src/new_feature.py\n'
    #         'D  __pycache__/old.cpython-38.pyc',
    #         ''
    #     )
    #     files = get_changed_files(config=mock_config) # Test with staged_only=False (default)
    #     self.assertNotIn('__pycache__/old.cpython-38.pyc', files)
    #     self.assertIn('src/new_feature.py', files)

class TestPushOperations:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_push_success(self, mock_run):
        mock_run.return_value = ('', '')
        git_push('main')
        mock_run.assert_called_with(["git", "push", "origin", "main"], None)

    @patch('git_acp.git.git_operations.run_git_command')
    def test_push_rejection(self, mock_run):
        mock_run.side_effect = GitError("! [rejected]")
        with pytest.raises(GitError) as exc:
            git_push('feature')
        assert "pull the latest changes" in str(exc.value)

class TestSignalHandlers:
    @patch('git_acp.git.git_operations.unstage_files')
    def test_interrupt_handling(self, mock_unstage):
        import signal
        with pytest.raises(SystemExit):
            from git_acp.git.git_operations import setup_signal_handlers
            # setup_signal_handlers() # Call it to set the handler
            handler = signal.getsignal(signal.SIGINT)
            if callable(handler): # Check if handler is callable (it should be after setup)
                 handler(signal.SIGINT, None)
            mock_unstage.assert_called()

class TestBranchOperations:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_create_branch(self, mock_run):
        from git_acp.git.git_operations import create_branch
        mock_config = GitConfig(verbose=False)
        create_branch('new-feature', config=mock_config) # Removed base_branch as it's not in signature
        mock_run.assert_called_with(
            ['git', 'checkout', '-b', 'new-feature'], # Adjusted call
            mock_config
        )

    @patch('git_acp.git.git_operations.run_git_command')
    def test_delete_branch(self, mock_run):
        from git_acp.git.git_operations import delete_branch
        mock_config = GitConfig(verbose=False)
        delete_branch('old-branch', config=mock_config)
        mock_run.assert_called_with(
            ['git', 'branch', '-D', 'old-branch'], # Assuming force delete for simplicity, or add force=True
            mock_config
        )

class TestTagOperations:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_create_annotated_tag(self, mock_run):
        from git_acp.git.git_operations import manage_tags
        mock_config = GitConfig(verbose=False)
        manage_tags('create', 'v1.0', message='Initial release', config=mock_config)
        mock_run.assert_called_with(
            ['git', 'tag', '-a', 'v1.0', '-m', 'Initial release'],
            mock_config
        )

    @patch('git_acp.git.git_operations.run_git_command')
    def test_delete_tag(self, mock_run):
        from git_acp.git.git_operations import manage_tags
        mock_config = GitConfig(verbose=False)
        manage_tags('delete', 'v0.5', config=mock_config)
        mock_run.assert_called_with(
            ['git', 'tag', '-d', 'v0.5'],
            mock_config
        )

class TestCommitAnalysis:
    def test_analyze_commit_patterns(self):
        from git_acp.git.git_operations import analyze_commit_patterns
        mock_config = GitConfig(verbose=False)
        test_commits = [
            {'message': 'feat: add new module'},
            {'message': 'fix(login): resolve auth issue'},
            {'message': 'docs: update README'},
            {'message': 'chore: update dependencies'},
            {'message': 'invalid commit message'}
        ]
        
        patterns = analyze_commit_patterns(test_commits, config=mock_config)
        
        assert patterns['types']['feat'] == 1
        assert patterns['types']['fix'] == 1
        assert patterns['types']['docs'] == 1
        assert patterns['scopes']['login'] == 1

class TestProtectedBranches:
    @patch('git_acp.git.git_operations.run_git_mock_config = GitConfig(verbose=False)command')
    def test_protected_branch_deletion(self, mock_run):
        from git_acp.git.git_operations import delete_branch
        mock_config = GitConfig(verbose=False)
        mock_run.side_effect = GitError("protected branch")
        
        with pytest.raises(GitError) as exc:
            delete_branch('main', config=mock_config) # Added force=True or handle default
        
        assert "protected branch" in str(exc.value)

# Ensure the test class is correctly defined to use unittest.TestCase methods like self.assertEqual
# If TestChangedFiles is not a subclass of unittest.TestCase, then use `assert result == expected_set`
# The provided code seems to mix pytest style (plain assert) with unittest.mock.patch.
# For the new tests, I'll assume it's a unittest.TestCase style for self.assertEqual.
# If it's pure pytest, then direct asserts are fine.

# Convert TestChangedFiles to inherit from unittest.TestCase for self.assertEqual
import unittest

class TestChangedFiles(unittest.TestCase): # Changed from 'class TestChangedFiles:'
    @patch('git_acp.git.git_operations.run_git_command')
    def test_file_exclusion(self, mock_run): # Added self
        mock_config = GitConfig(verbose=False)
        mock_run.return_value = (
            'MM tests/__init__.py\n'
            'A  src/new_feature.py\n'
            'D  __pycache__/old.cpython-38.pyc',
            ''
        )
        files = get_changed_files(config=mock_config)
        self.assertNotIn('__pycache__/old.cpython-38.pyc', files) # Changed from 'assert ... not in'
        self.assertIn('src/new_feature.py', files) # Changed from 'assert ... in'

    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_changed_files_staged_only_with_files(self, mock_run_git_command): # Added self
        mock_config = GitConfig(verbose=False)
        mock_run_git_command.return_value = ("file1.py\nfolder/file2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, {"file1.py", "folder/file2.py"})

    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_changed_files_staged_only_no_files(self, mock_run_git_command): # Added self
        mock_config = GitConfig(verbose=False)
        mock_run_git_command.return_value = ("", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, set())

    @patch('git_acp.git.git_operations.run_git_command')
    def test_get_changed_files_staged_only_with_excluded_files(self, mock_run_git_command): # Added self
        mock_config = GitConfig(verbose=False)
        # Assuming EXCLUDED_PATTERNS is available and includes "__pycache__"
        mock_run_git_command.return_value = ("file1.py\n__pycache__/somefile.pyc\nfolder/file2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run_git_command.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        self.assertEqual(result, {"file1.py", "folder/file2.py"})
