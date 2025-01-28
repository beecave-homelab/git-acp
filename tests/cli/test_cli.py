#!/usr/bin/env python3
"""
Test suite for git_acp/cli/cli.py functionality
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from git_acp.cli import cli
from git_acp.utils import GitConfig
from git_acp.git import GitError, CommitType

runner = CliRunner()

# Fixtures
@pytest.fixture
def mock_git_operations(mocker):
    """Mock Git operations"""
    mocker.patch('git_acp.git.git_add')
    mocker.patch('git_acp.git.git_commit')
    mocker.patch('git_acp.git.git_push')
    mocker.patch('git_acp.git.get_current_branch', return_value='main')
    mocker.patch('git_acp.git.get_changed_files', return_value={'file1.txt', 'file2.py'})
    mocker.patch('git_acp.git.classify_commit_type', return_value=CommitType.FEAT)

@pytest.fixture
def mock_ai_operations(mocker):
    """Mock AI operations"""
    mocker.patch('git_acp.ai.generate_commit_message', return_value="AI generated message")

@pytest.fixture
def mock_user_prompts(mocker):
    """Mock user interactions"""
    mocker.patch('questionary.checkbox', return_value=MagicMock(ask=lambda: ['file1.txt']))
    mocker.patch('questionary.confirm', return_value=MagicMock(ask=lambda: True))

# Core CLI Command Tests
def test_cli_successful_workflow(mock_git_operations, mock_ai_operations):
    """Test complete successful workflow with AI generation"""
    result = runner.invoke(
        cli.main,
        ['-a', 'file1.txt', '-o', '-nc']
    )
    assert result.exit_code == 0
    assert "✓ Commit type selected successfully" in result.output
    assert "Pushing changes to branch: main" in result.output

def test_interactive_file_selection(mock_git_operations, mock_ai_operations):
    """Test interactive file selection workflow"""
    with patch('questionary.checkbox') as mock_checkbox:
        mock_checkbox.return_value.ask.return_value = ['file1.txt']
        result = runner.invoke(cli.main, ['-o', '-nc'])
        assert "Select files to commit" in result.output
        assert "Adding files:" in result.output

def test_commit_type_selection(mock_git_operations, mock_ai_operations):
    """Test commit type selection logic"""
    with patch('questionary.checkbox') as mock_commit_type:
        mock_commit_type.return_value.ask.return_value = [CommitType.FIX]
        result = runner.invoke(cli.main, ['-a', '.', '-o', '-nc'])
        assert "feat (suggested)" in result.output
        assert "✓ Commit type selected successfully" in result.output

# Error Handling Tests
def test_git_add_failure(mocker, mock_ai_operations):
    """Test handling of git add failure"""
    mocker.patch('git_acp.git.git_add', side_effect=GitError("Add failed"))
    result = runner.invoke(cli.main, ['-a', 'missing.txt', '-o', '-nc'])
    assert result.exit_code == 1
    assert "Git Add Failed" in result.output
    assert "Check file paths" in result.output

def test_ai_generation_failure(mocker, mock_git_operations):
    """Test AI generation failure handling"""
    mocker.patch('git_acp.ai.generate_commit_message', side_effect=GitError("AI timeout"))
    result = runner.invoke(cli.main, ['-a', '.', '-o', '-nc'])
    assert "AI Generation Failed" in result.output
    assert "Check Ollama server" in result.output

# User Interaction Tests
def test_user_cancellation_file_selection(mocker, mock_git_operations):
    """Test user cancellation during file selection"""
    mocker.patch('questionary.checkbox', return_value=MagicMock(ask=lambda: None))
    result = runner.invoke(cli.main, ['-o'])
    assert result.exit_code == 1
    assert "Operation cancelled by user" in result.output

def test_commit_confirmation_cancel(mock_git_operations, mock_ai_operations):
    """Test commit confirmation cancellation"""
    with patch('rich.prompt.Confirm.ask', return_value=False):
        result = runner.invoke(cli.main, ['-a', '.', '-o'])
        assert result.exit_code == 0
        assert "Operation cancelled by user" in result.output

# Formatting Tests
def test_commit_message_formatting():
    """Test conventional commits message formatting"""
    from git_acp.cli.cli import format_commit_message
    formatted = format_commit_message(CommitType.FIX, "Fix critical bug\nDetails here")
    assert formatted.startswith("fix: Fix critical bug")
    assert "\n\nDetails here" in formatted

# Configuration Tests
def test_git_config_initialization():
    """Test GitConfig dataclass initialization"""
    config = GitConfig(
        files=".",
        message="Test",
        branch="main",
        use_ollama=True,
        interactive=False,
        skip_confirmation=True,
        verbose=True,
        prompt_type="advanced"
    )
    assert config.use_ollama is True
    assert config.skip_confirmation is True

# Edge Case Tests
def test_no_changes_detected(mocker):
    """Test handling of no changes scenario"""
    mocker.patch('git_acp.git.get_changed_files', return_value=set())
    result = runner.invoke(cli.main, ['-o'])
    assert result.exit_code == 1
    assert "No changes detected" in result.output

def test_all_files_selection(mock_git_operations, mock_ai_operations):
    """Test 'All files' selection handling"""
    with patch('questionary.checkbox') as mock_checkbox:
        mock_checkbox.return_value.ask.return_value = ["All files"]
        result = runner.invoke(cli.main, ['-o', '-nc'])
        assert "Adding all files" in result.output
        cli.git_add.assert_called_with(".")
