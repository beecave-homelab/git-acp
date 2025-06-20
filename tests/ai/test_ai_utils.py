"""Tests for AI-powered commit message generation utilities.

This module contains tests for the AI utilities used in commit message generation,
including AI client initialization, context gathering, and message generation.
"""

import json
from unittest.mock import Mock, patch, MagicMock
import pytest
from openai import OpenAI
from rich.panel import Panel

from git_acp.ai.ai_utils import (
    AIClient,
    create_advanced_commit_message_prompt,
    create_simple_commit_message_prompt,
    get_commit_context,
    edit_commit_message,
    generate_commit_message,
)
from git_acp.git import GitError
from git_acp.utils import GitConfig, PromptType
from git_acp.config import DEFAULT_BASE_URL, DEFAULT_API_KEY, DEFAULT_AI_TIMEOUT


# Test fixtures
@pytest.fixture
def mock_config():
    """Create a mock GitConfig instance."""
    return GitConfig(
        files="test.py",
        message=None,
        branch="main",
        use_ollama=True,
        interactive=False,
        skip_confirmation=False,
        verbose=True,
        prompt_type="simple",
    )


@pytest.fixture
def mock_context():
    """Create a mock git context dictionary."""
    return {
        "staged_changes": "Modified: test.py\n+New line added",
        "recent_commits": [
            {"message": "feat: add new feature"},
            {"message": "fix: resolve bug"},
        ],
        "related_commits": [{"message": "feat: related change"}],
        "commit_patterns": {"types": {"feat": 2, "fix": 1}, "scopes": {}},
    }


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    mock_message = Mock()
    mock_message.content = "feat: test commit message"

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    return mock_response


# AIClient Tests
class TestAIClient:
    """Test suite for AIClient class."""

    def test_init_success(self, mock_config):
        """Test successful AIClient initialization."""
        with patch("git_acp.ai.ai_utils.OpenAI") as mock_openai:
            client = AIClient(mock_config)
            assert client.config == mock_config
            mock_openai.assert_called_once_with(
                base_url=DEFAULT_BASE_URL,
                api_key=DEFAULT_API_KEY,
                timeout=DEFAULT_AI_TIMEOUT,
            )

    def test_init_invalid_url(self, mock_config):
        """Test AIClient initialization with invalid URL."""
        with patch("git_acp.ai.ai_utils.OpenAI", side_effect=ValueError("Invalid URL")):
            with pytest.raises(GitError, match="Invalid Ollama server URL"):
                AIClient(mock_config)

    def test_init_connection_error(self, mock_config):
        """Test AIClient initialization with connection error."""
        with patch("git_acp.ai.ai_utils.OpenAI", side_effect=ConnectionError()):
            with pytest.raises(GitError, match="Could not connect to Ollama server"):
                AIClient(mock_config)

    def test_chat_completion_success(self, mock_config, mock_openai_response):
        """Test successful chat completion."""
        with patch("git_acp.ai.ai_utils.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai.return_value = mock_client

            client = AIClient(mock_config)
            messages = [{"role": "user", "content": "Test prompt"}]
            response = client.chat_completion(messages)

            assert response == "feat: test commit message"
            mock_client.chat.completions.create.assert_called_once()

    def test_chat_completion_timeout(self, mock_config):
        """Test chat completion timeout."""
        with patch("git_acp.ai.ai_utils.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = TimeoutError()
            mock_openai.return_value = mock_client

            client = AIClient(mock_config)
            messages = [{"role": "user", "content": "Test prompt"}]

            with pytest.raises(GitError, match="AI request timed out"):
                client.chat_completion(messages)


# Context Gathering Tests
def test_get_commit_context(mock_config):
    """Test commit context gathering."""
    with (
        patch("git_acp.ai.ai_utils.get_diff") as mock_get_diff,
        patch("git_acp.ai.ai_utils.get_recent_commits") as mock_get_commits,
        patch("git_acp.ai.ai_utils.find_related_commits") as mock_find_related,
        patch("git_acp.ai.ai_utils.analyze_commit_patterns") as mock_analyze,
    ):
        mock_get_diff.return_value = "Modified: test.py"
        mock_get_commits.return_value = [{"message": "feat: test"}]
        mock_find_related.return_value = [{"message": "fix: related"}]
        mock_analyze.return_value = {"types": {"feat": 1}, "scopes": {}}

        context = get_commit_context(mock_config)
        assert isinstance(context, dict)
        assert "staged_changes" in context
        assert "recent_commits" in context
        assert "related_commits" in context
        assert "commit_patterns" in context


def test_get_commit_context_error(mock_config):
    """Test commit context gathering with error."""
    with patch("git_acp.ai.ai_utils.get_diff", side_effect=GitError("Test error")):
        with pytest.raises(GitError, match="Failed to gather commit context"):
            get_commit_context(mock_config)


# Prompt Creation Tests
def test_create_advanced_prompt(mock_context, mock_config):
    """Test advanced commit message prompt creation."""
    prompt = create_advanced_commit_message_prompt(mock_context, mock_config)
    assert isinstance(prompt, str)
    assert "Changes to commit:" in prompt
    assert "Repository context:" in prompt
    assert "Most used commit type:" in prompt


def test_create_simple_prompt(mock_context, mock_config):
    """Test simple commit message prompt creation."""
    prompt = create_simple_commit_message_prompt(mock_context, mock_config)
    assert isinstance(prompt, str)
    assert "Generate a concise" in prompt
    assert mock_context["staged_changes"] in prompt


# Message Editing Tests
def test_edit_commit_message_non_interactive(mock_config):
    """Test commit message editing in non-interactive mode."""
    message = "feat: test message"
    assert edit_commit_message(message, mock_config) == message


def test_edit_commit_message_interactive():
    """Test commit message editing in interactive mode."""
    config = GitConfig(
        files="test.py",
        message=None,
        branch="main",
        use_ollama=True,
        interactive=True,
        skip_confirmation=False,
        verbose=False,
        prompt_type="simple",
    )

    with (
        patch("questionary.confirm") as mock_confirm,
        patch("questionary.text") as mock_text,
    ):
        mock_confirm.return_value.ask.return_value = True
        mock_text.return_value.ask.return_value = "feat: edited message"

        result = edit_commit_message("feat: original message", config)
        assert result == "feat: edited message"


# Message Generation Tests
def test_generate_commit_message(mock_config, mock_context, mock_openai_response):
    """Test complete commit message generation workflow."""
    with (
        patch("git_acp.ai.ai_utils.AIClient") as mock_client_class,
        patch("git_acp.ai.ai_utils.get_commit_context") as mock_get_context,
    ):
        mock_client = Mock()
        mock_client.chat_completion.return_value = "feat: generated message"
        mock_client_class.return_value = mock_client
        mock_get_context.return_value = mock_context

        message = generate_commit_message(mock_config)
        assert isinstance(message, str)
        assert message == "feat: generated message"


def test_generate_commit_message_error(mock_config):
    """Test commit message generation with error."""
    with patch("git_acp.ai.ai_utils.AIClient", side_effect=GitError("Test error")):
        with pytest.raises(GitError, match="Failed to generate commit message"):
            generate_commit_message(mock_config)
