import pytest
from unittest.mock import patch, MagicMock, call
from git_acp.git.git_operations import (
    run_git_command,
    get_diff,
    get_changed_files,
    git_push,
    GitError
)
from subprocess import CalledProcessError

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
            handler = signal.getsignal(signal.SIGINT)
            handler(signal.SIGINT, None)
            mock_unstage.assert_called()

class TestBranchOperations:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_create_branch(self, mock_run):
        from git_acp.git.git_operations import create_branch
        create_branch('new-feature', 'main')
        mock_run.assert_called_with(
            ['git', 'checkout', '-b', 'new-feature', 'main'],
            None
        )

    @patch('git_acp.git.git_operations.run_git_command')
    def test_delete_branch(self, mock_run):
        from git_acp.git.git_operations import delete_branch
        delete_branch('old-branch')
        mock_run.assert_called_with(
            ['git', 'branch', '-D', 'old-branch'],
            None
        )

class TestTagOperations:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_create_annotated_tag(self, mock_run):
        from git_acp.git.git_operations import manage_tags
        manage_tags('create', 'v1.0', 'Initial release')
        mock_run.assert_called_with(
            ['git', 'tag', '-a', 'v1.0', '-m', 'Initial release'],
            None
        )

    @patch('git_acp.git.git_operations.run_git_command')
    def test_delete_tag(self, mock_run):
        from git_acp.git.git_operations import manage_tags
        manage_tags('delete', 'v0.5')
        mock_run.assert_called_with(
            ['git', 'tag', '-d', 'v0.5'],
            None
        )

class TestCommitAnalysis:
    def test_analyze_commit_patterns(self):
        from git_acp.git.git_operations import analyze_commit_patterns
        test_commits = [
            {'message': 'feat: add new module'},
            {'message': 'fix(login): resolve auth issue'},
            {'message': 'docs: update README'},
            {'message': 'chore: update dependencies'},
            {'message': 'invalid commit message'}
        ]
        
        patterns = analyze_commit_patterns(test_commits)
        
        assert patterns['types']['feat'] == 1
        assert patterns['types']['fix'] == 1
        assert patterns['types']['docs'] == 1
        assert patterns['scopes']['login'] == 1

class TestProtectedBranches:
    @patch('git_acp.git.git_operations.run_git_command')
    def test_protected_branch_deletion(self, mock_run):
        from git_acp.git.git_operations import delete_branch
        mock_run.side_effect = GitError("protected branch")
        
        with pytest.raises(GitError) as exc:
            delete_branch('main')
        
        assert "protected branch" in str(exc.value)
