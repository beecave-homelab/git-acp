import pytest
from unittest.mock import patch, MagicMock
from git_acp.git import (
    GitError,
    run_git_command,
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    get_changed_files,
    unstage_files,
    get_diff,
    get_recent_commits,
    find_related_commits,
    analyze_commit_patterns
)

# Mock configuration class
class MockConfig:
    def __init__(self, verbose=False):
        self.verbose = verbose

@pytest.fixture
def mock_subprocess():
    with patch('git_acp.git_operations.subprocess') as mock:
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("success", "")
        process_mock.returncode = 0
        mock.Popen.return_value = process_mock
        yield mock

@pytest.fixture
def mock_console():
    with patch('git_acp.git_operations.console') as mock:
        yield mock

def test_run_git_command_success(mock_subprocess):
    stdout, stderr = run_git_command(["git", "status"])
    assert stdout == "success"
    assert stderr == ""
    mock_subprocess.Popen.assert_called_once()

def test_run_git_command_failure(mock_subprocess):
    mock_subprocess.Popen.return_value.returncode = 1
    mock_subprocess.Popen.return_value.communicate.return_value = ("", "error")
    
    with pytest.raises(GitError, match="Command failed: error"):
        run_git_command(["git", "status"])

def test_get_current_branch(mock_subprocess):
    mock_subprocess.Popen.return_value.communicate.return_value = ("main", "")
    branch = get_current_branch()
    assert branch == "main"

def test_git_add(mock_subprocess, mock_console):
    git_add("test.py")
    mock_subprocess.Popen.assert_called_with(
        ["git", "add", "test.py"],
        stdout=mock_subprocess.PIPE,
        stderr=mock_subprocess.PIPE,
        text=True
    )

def test_git_commit(mock_subprocess, mock_console):
    git_commit("test commit")
    mock_subprocess.Popen.assert_called_with(
        ["git", "commit", "-m", "test commit"],
        stdout=mock_subprocess.PIPE,
        stderr=mock_subprocess.PIPE,
        text=True
    )

def test_git_push(mock_subprocess, mock_console):
    git_push("main")
    mock_subprocess.Popen.assert_called_with(
        ["git", "push", "origin", "main"],
        stdout=mock_subprocess.PIPE,
        stderr=mock_subprocess.PIPE,
        text=True
    )

def test_get_changed_files(mock_subprocess):
    status_output = """
 M file1.py
?? file2.py
 M __pycache__/ignored.pyc
"""
    mock_subprocess.Popen.return_value.communicate.return_value = (status_output, "")
    config = MockConfig(verbose=True)
    
    files = get_changed_files(config)
    assert files == {"file1.py", "file2.py"}

def test_unstage_files(mock_subprocess):
    unstage_files()
    mock_subprocess.Popen.assert_called_with(
        ["git", "reset", "HEAD"],
        stdout=mock_subprocess.PIPE,
        stderr=mock_subprocess.PIPE,
        text=True
    )

def test_get_recent_commits(mock_subprocess):
    commit_output = """hash1
Initial commit
Author1
Date1
---
hash2
Second commit
Author2
Date2
---"""
    mock_subprocess.Popen.return_value.communicate.return_value = (commit_output, "")
    
    commits = get_recent_commits(2)
    assert len(commits) == 2
    assert commits[0]["hash"] == "hash1"
    assert commits[0]["message"] == "Initial commit"
    assert commits[0]["author"] == "Author1"
    assert commits[0]["date"] == "Date1"

def test_analyze_commit_patterns(mock_subprocess):
    commit_output = """hash1
feat: new feature
Author1
Date1
---
hash2
fix: bug fix
Author2
Date2
---"""
    mock_subprocess.Popen.return_value.communicate.return_value = (commit_output, "")
    
    patterns = analyze_commit_patterns()
    assert "commit_types" in patterns
    assert "message_length" in patterns
    assert "authors" in patterns

def test_find_related_commits(mock_subprocess):
    diff_content = """
+++ b/file1.py
--- a/file1.py
"""
    commit_output = """hash1
Related commit
Author1
Date1
---"""
    mock_subprocess.Popen.return_value.communicate.return_value = (commit_output, "")
    
    commits = find_related_commits(diff_content)
    assert len(commits) == 1
    assert commits[0]["hash"] == "hash1"
    assert commits[0]["message"] == "Related commit"

def test_git_error():
    error = GitError("test error")
    assert str(error) == "test error" 