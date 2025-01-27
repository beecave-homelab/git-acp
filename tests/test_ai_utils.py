"""Tests for the AI utilities module."""

import json
import pytest
from unittest.mock import patch, MagicMock
from git_acp.ai import generate_commit_message
from git_acp.git import (
    run_git_command, get_recent_commits,
    analyze_commit_patterns, find_related_commits
)

@pytest.mark.describe("System prompt generation")
def test_generate_commit_message(request, capsys):
    """Test the commit message generation with actual git operations."""
    # Get actual git diff
    stdout, _ = run_git_command(["git", "diff", "--staged"])
    if not stdout.strip():
        stdout, _ = run_git_command(["git", "diff"])
    
    # Get actual commit history and patterns
    recent_commits = get_recent_commits(5)
    patterns = analyze_commit_patterns()
    related_commits = find_related_commits(stdout, 3)
    
    # Mock only the Ollama chat
    with patch('git_acp.ai_utils.chat') as mock_chat:
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.message.content = "feat: add docstring and positive number filtering"
        mock_chat.return_value = mock_response
        
        # Generate commit message
        message = generate_commit_message({})
        
        # Verify we got a commit message back
        assert message.strip()
        assert len(message) > 10  # Reasonable minimum length
        
        # Verify the mock was called
        mock_chat.assert_called_once()
        # Get the prompt from the first call's arguments
        call_args = mock_chat.call_args
        assert call_args is not None
        messages = call_args[1]['messages']
        assert messages
        prompt = messages[0]['content']
        
        # Print the prompt in verbose mode
        if request.config.getoption('verbose') > 0:
            print("\n=== System Prompt ===\n")
            print(prompt)
            print("\n===================\n")
            out, _ = capsys.readouterr()  # Capture output for pytest reporting
            pytest.fail(out)  # Use fail to show output in verbose mode
        
        # The prompt should contain all sections
        assert "Changes made (git diff):" in prompt
        assert "Recent commit messages for context:" in prompt
        assert "Common commit patterns" in prompt
        assert "Related commits to these changes:" in prompt 