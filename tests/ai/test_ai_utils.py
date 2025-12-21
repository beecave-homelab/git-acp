"""Tests for AI-powered commit message generation utilities.

This module contains tests for the AI utilities used in commit message generation,
including AI client initialization, context gathering, and message generation.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from git_acp.ai.ai_utils import (
    AIClient,
    calculate_context_budget,
    create_structured_advanced_commit_message_prompt,
    create_structured_simple_commit_message_prompt,
    edit_commit_message,
    estimate_tokens,
    generate_commit_message,
    get_commit_context,
    truncate_context_for_window,
)
from git_acp.config import (
    DEFAULT_AI_TIMEOUT,
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_FALLBACK_BASE_URL,
)
from git_acp.git import GitError
from git_acp.utils import GitConfig


# Test fixtures
@pytest.fixture
def mock_config():
    """Create a mock GitConfig instance.

    Returns:
        A GitConfig object with test defaults.
    """
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
    """Create a mock git context dictionary.

    Returns:
        A dictionary with staged_changes, recent_commits, etc.
    """
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
    """Create a mock OpenAI API response.

    Returns:
        A mock response object with choices.
    """
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
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            client = AIClient(mock_config)
            assert client.config == mock_config
            mock_openai.assert_called_once_with(
                base_url=DEFAULT_BASE_URL,
                api_key=DEFAULT_API_KEY,
                timeout=DEFAULT_AI_TIMEOUT,
            )

    def test_init_invalid_url(self, mock_config):
        """Test AIClient initialization with invalid URL."""
        with patch("git_acp.ai.client.OpenAI", side_effect=ValueError("Invalid URL")):
            with pytest.raises(GitError, match="Invalid Ollama server URL"):
                AIClient(mock_config)

    def test_init_connection_error(self, mock_config):
        """Test AIClient initialization with connection error."""
        with patch("git_acp.ai.client.OpenAI", side_effect=ConnectionError()):
            with pytest.raises(GitError, match="Could not connect to Ollama server"):
                AIClient(mock_config)

    def test_init_fallback_url(self, mock_config):
        """Test AIClient uses fallback URL when primary fails."""
        with patch(
            "git_acp.ai.client.OpenAI",
            side_effect=[ConnectionError(), MagicMock()],
        ) as mock_openai:
            client = AIClient(mock_config)
            assert mock_openai.call_count == 2
            assert client.base_url == DEFAULT_FALLBACK_BASE_URL
            first_call = mock_openai.call_args_list[0]
            second_call = mock_openai.call_args_list[1]
            assert first_call.kwargs["base_url"] == DEFAULT_BASE_URL
            assert second_call.kwargs["base_url"] == DEFAULT_FALLBACK_BASE_URL

    def test_chat_completion_success(self, mock_config, mock_openai_response):
        """Test successful chat completion."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
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
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
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
    prompt = create_structured_advanced_commit_message_prompt(mock_context, mock_config)
    assert isinstance(prompt, str)
    assert "<task>" in prompt
    assert "<repository_context>" in prompt
    assert "<changes>" in prompt
    assert "<requirements>" in prompt
    assert "<output_format>" in prompt


def test_create_simple_prompt(mock_context, mock_config):
    """Test simple commit message prompt creation."""
    prompt = create_structured_simple_commit_message_prompt(mock_context, mock_config)
    assert isinstance(prompt, str)
    assert "<task>" in prompt
    assert "<changes>" in prompt
    assert "<requirements>" in prompt
    assert "<output_format>" in prompt
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


# Context Management Tests
class TestContextManagement:
    """Test suite for context window management functions."""

    def test_estimate_tokens(self):
        """Test token estimation function."""
        # Test basic cases
        assert estimate_tokens("") == 1  # Minimum 1 token
        assert estimate_tokens("test") == 1  # 4 chars = 1 token
        assert estimate_tokens("test test test test") == 4  # 16 chars = 4 tokens
        assert estimate_tokens("a" * 100) == 25  # 100 chars = 25 tokens

    def test_calculate_context_budget_simple(self):
        """Test context budget calculation for simple prompts."""
        max_tokens, reserved_tokens = calculate_context_budget(8192, "simple")

        # Simple uses 65% of context window
        expected_max = int(8192 * 0.65)
        expected_reserved = 8192 - expected_max

        assert max_tokens == expected_max
        assert reserved_tokens == expected_reserved

    def test_calculate_context_budget_advanced(self):
        """Test context budget calculation for advanced prompts."""
        max_tokens, reserved_tokens = calculate_context_budget(8192, "advanced")

        # Advanced uses 80% of context window
        expected_max = int(8192 * 0.80)
        expected_reserved = 8192 - expected_max

        assert max_tokens == expected_max
        assert reserved_tokens == expected_reserved

    def test_calculate_context_budget_custom_window(self):
        """Test context budget with custom window size."""
        max_tokens, reserved_tokens = calculate_context_budget(4096, "simple")

        expected_max = int(4096 * 0.65)
        expected_reserved = 4096 - expected_max

        assert max_tokens == expected_max
        assert reserved_tokens == expected_reserved

    def test_truncate_context_for_window_no_truncation_needed(self):
        """Test context truncation when no truncation is needed."""
        context = {
            "staged_changes": "small change",
            "recent_commits": [{"message": "feat: test"}],
            "related_commits": [],
            "commit_patterns": {"types": {"feat": 1}, "scopes": {}},
        }

        # Large enough budget to fit everything
        result = truncate_context_for_window(context, 10000, "simple")

        # Should return unchanged context
        assert result == context

    def test_truncate_context_for_window_simple_mode(self):
        """Test context truncation in simple mode."""
        # Create a large context that needs truncation
        large_change = "change\n" * 1000  # Large staged changes
        many_commits = [{"message": f"feat: commit {i}"} for i in range(20)]

        context = {
            "staged_changes": large_change,
            "recent_commits": many_commits,
            "related_commits": many_commits,
            "commit_patterns": {
                "types": {f"type_{i}": i for i in range(10)},
                "scopes": {f"scope_{i}": i for i in range(10)},
            },
        }

        # Small budget that requires truncation
        result = truncate_context_for_window(context, 1000, "simple")

        # Should preserve staged changes but truncate others
        assert "staged_changes" in result
        assert len(result["related_commits"]) < len(context["related_commits"])
        assert len(result["recent_commits"]) < len(context["recent_commits"])

        # Simple mode should be more aggressive (higher min_changes)
        assert len(result["commit_patterns"]["types"]) <= 5

    def test_truncate_context_for_window_advanced_mode(self):
        """Test context truncation in advanced mode."""
        # Create a large context
        large_change = "change\n" * 1000
        many_commits = [{"message": f"feat: commit {i}"} for i in range(20)]

        context = {
            "staged_changes": large_change,
            "recent_commits": many_commits,
            "related_commits": many_commits,
            "commit_patterns": {
                "types": {f"type_{i}": i for i in range(10)},
                "scopes": {f"scope_{i}": i for i in range(10)},
            },
        }

        # Small budget
        result = truncate_context_for_window(context, 1000, "advanced")

        # Advanced mode should preserve more context
        assert "staged_changes" in result

        # Advanced mode should be less restrictive
        assert len(result["commit_patterns"]["types"]) <= 5

    def test_truncate_context_for_window_preserves_minimum_changes(self):
        """Test that truncation preserves minimum required changes context."""
        large_change = "change\n" * 1000

        context = {
            "staged_changes": large_change,
            "recent_commits": [],
            "related_commits": [],
            "commit_patterns": {"types": {}, "scopes": {}},
        }

        # Very small budget that would normally truncate changes too much
        result = truncate_context_for_window(context, 500, "simple")

        # Should still have some staged changes content
        assert "staged_changes" in result
        assert len(result["staged_changes"]) > 0

        # Should have truncation indicator if actually truncated
        if "[truncated" in result["staged_changes"]:
            assert "truncated" in result["staged_changes"]


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


def test_generate_commit_message__uses_prompt_override(mock_context) -> None:
    """Use explicit prompt override instead of simple/advanced templates."""
    override_prompt = "Write a commit message for these changes."
    config = GitConfig(
        files="test.py",
        message=None,
        branch="main",
        use_ollama=True,
        interactive=False,
        skip_confirmation=False,
        verbose=False,
        prompt=override_prompt,
        prompt_type="advanced",
    )

    with (
        patch("git_acp.ai.ai_utils.AIClient") as mock_client_class,
        patch("git_acp.ai.ai_utils.get_commit_context") as mock_get_context,
        patch(
            "git_acp.ai.ai_utils.create_structured_advanced_commit_message_prompt"
        ) as mock_adv,
        patch(
            "git_acp.ai.ai_utils.create_structured_simple_commit_message_prompt"
        ) as mock_simple,
    ):
        mock_client = Mock()
        mock_client.chat_completion.return_value = "feat: generated message"
        mock_client_class.return_value = mock_client
        mock_get_context.return_value = mock_context

        result = generate_commit_message(config)

        assert result == "feat: generated message"
        mock_adv.assert_not_called()
        mock_simple.assert_not_called()

        call_args = mock_client.chat_completion.call_args
        assert call_args.args[0][0]["content"] == override_prompt


def test_generate_commit_message_error(mock_config):
    """Test commit message generation with error."""
    with patch("git_acp.ai.ai_utils.AIClient", side_effect=GitError("Test error")):
        with pytest.raises(GitError, match="Failed to generate commit message"):
            generate_commit_message(mock_config)


# Verbose Mode Tests
class TestVerboseMode:
    """Tests for verbose mode debugging output."""

    @pytest.fixture
    def verbose_config(self):
        """Create a verbose GitConfig instance.

        Returns:
            GitConfig: A verbose GitConfig instance.
        """
        return GitConfig(
            files="test.py",
            message=None,
            branch="main",
            use_ollama=True,
            interactive=False,
            skip_confirmation=False,
            verbose=True,
            prompt_type="advanced",
        )

    @pytest.fixture
    def mock_context(self):
        """Create a mock git context dictionary.

        Returns:
            dict: A mock git context dictionary.
        """
        return {
            "staged_changes": "Modified: test.py",
            "recent_commits": [{"message": "feat: test"}],
            "related_commits": [{"message": "fix: related"}],
            "commit_patterns": {"types": {"feat": 1}, "scopes": {"api": 1}},
        }

    @patch("git_acp.ai.ai_utils.debug_preview")
    @patch("git_acp.ai.ai_utils.debug_header")
    def test_create_advanced_prompt__verbose_logs(
        self, mock_header, mock_preview, verbose_config, mock_context
    ):
        """Log debug output when creating advanced prompt in verbose mode."""
        create_structured_advanced_commit_message_prompt(mock_context, verbose_config)

        mock_header.assert_called()
        mock_preview.assert_called()

    @patch("git_acp.ai.ai_utils.debug_preview")
    @patch("git_acp.ai.ai_utils.debug_header")
    def test_create_simple_prompt__verbose_logs(
        self, mock_header, mock_preview, verbose_config, mock_context
    ):
        """Log debug output when creating simple prompt in verbose mode."""
        create_structured_simple_commit_message_prompt(mock_context, verbose_config)

        mock_header.assert_called()
        mock_preview.assert_called()

    @patch("git_acp.ai.ai_utils.debug_item")
    @patch("git_acp.ai.ai_utils.debug_header")
    @patch("git_acp.ai.ai_utils.find_related_commits")
    @patch("git_acp.ai.ai_utils.analyze_commit_patterns")
    @patch("git_acp.ai.ai_utils.get_recent_commits")
    @patch("git_acp.ai.ai_utils.get_diff")
    def test_get_commit_context__verbose_logs_all_steps(
        self,
        mock_diff,
        mock_commits,
        mock_analyze,
        mock_related,
        mock_header,
        mock_item,
        verbose_config,
    ):
        """Log all context gathering steps in verbose mode."""
        mock_diff.return_value = "diff content"
        mock_commits.return_value = [{"message": "feat: test"}]
        mock_analyze.return_value = {"types": {"feat": 1}, "scopes": {"api": 1}}
        mock_related.return_value = []

        get_commit_context(verbose_config)

        # Should have multiple debug header calls
        assert mock_header.call_count >= 4
        assert mock_item.call_count >= 3

    @patch("git_acp.ai.ai_utils.debug_header")
    @patch("git_acp.ai.ai_utils.find_related_commits")
    @patch("git_acp.ai.ai_utils.analyze_commit_patterns")
    @patch("git_acp.ai.ai_utils.get_recent_commits")
    @patch("git_acp.ai.ai_utils.get_diff")
    def test_get_commit_context__fallback_to_unstaged(
        self,
        mock_diff,
        mock_commits,
        mock_analyze,
        mock_related,
        mock_header,
        verbose_config,
    ):
        """Fall back to unstaged diff when staged is empty in verbose mode."""
        # First call returns empty (staged), second returns content (unstaged)
        mock_diff.side_effect = ["", "unstaged content"]
        mock_commits.return_value = []
        mock_analyze.return_value = {"types": {}, "scopes": {}}
        mock_related.return_value = []

        context = get_commit_context(verbose_config)

        assert context["staged_changes"] == "unstaged content"
        # Should have logged the fallback (message says "working directory")
        header_calls = [str(call) for call in mock_header.call_args_list]
        assert any("working directory" in call.lower() for call in header_calls)

    @patch("git_acp.ai.ai_utils.debug_preview")
    @patch("git_acp.ai.ai_utils.debug_header")
    @patch("git_acp.ai.ai_utils.edit_commit_message")
    @patch("git_acp.ai.ai_utils.get_commit_context")
    @patch("git_acp.ai.ai_utils.AIClient")
    def test_generate_commit_message__verbose_logs(
        self,
        mock_client_class,
        mock_context,
        mock_edit,
        mock_header,
        mock_preview,
        verbose_config,
    ):
        """Log all generation steps in verbose mode."""
        mock_client = MagicMock()
        mock_client.chat_completion.return_value = "feat: test"
        mock_client_class.return_value = mock_client
        mock_context.return_value = {
            "staged_changes": "diff",
            "recent_commits": [],
            "related_commits": [],
            "commit_patterns": {"types": {}, "scopes": {}},
        }
        mock_edit.return_value = "feat: test"

        generate_commit_message(verbose_config)

        assert mock_header.call_count >= 3
        assert mock_preview.call_count >= 1

    @patch("git_acp.ai.ai_utils.debug_item")
    @patch("git_acp.ai.ai_utils.debug_header")
    @patch("git_acp.ai.ai_utils.AIClient")
    def test_generate_commit_message__verbose_logs_error(
        self, mock_client_class, mock_header, mock_item, verbose_config
    ):
        """Log error details in verbose mode when generation fails."""
        mock_client_class.side_effect = GitError("connection failed")

        with pytest.raises(GitError):
            generate_commit_message(verbose_config)

        # Should have logged the error
        header_calls = [str(call) for call in mock_header.call_args_list]
        assert any("error" in call.lower() for call in header_calls)


class TestEditCommitMessageVerbose:
    """Tests for edit_commit_message with verbose mode."""

    @pytest.fixture
    def interactive_verbose_config(self):
        """Create an interactive verbose GitConfig instance.

        Returns:
            GitConfig: An interactive verbose GitConfig instance.
        """
        return GitConfig(
            files="test.py",
            message=None,
            branch="main",
            use_ollama=True,
            interactive=True,
            skip_confirmation=False,
            verbose=True,
            prompt_type="simple",
        )

    @patch("git_acp.ai.ai_utils.debug_preview")
    @patch("git_acp.ai.ai_utils.debug_header")
    @patch("questionary.text")
    @patch("questionary.confirm")
    def test_edit_commit_message__verbose_logs_edit(
        self,
        mock_confirm,
        mock_text,
        mock_header,
        mock_preview,
        interactive_verbose_config,
    ):
        """Log editing in verbose mode."""
        mock_confirm.return_value.ask.return_value = True
        mock_text.return_value.ask.return_value = "feat: edited"

        edit_commit_message("feat: original", interactive_verbose_config)

        mock_header.assert_called()
        mock_preview.assert_called()

    @patch("questionary.confirm")
    def test_edit_commit_message__no_edit_returns_original(
        self, mock_confirm, interactive_verbose_config
    ):
        """Return original message when user declines to edit."""
        mock_confirm.return_value.ask.return_value = False

        result = edit_commit_message("feat: original", interactive_verbose_config)

        assert result == "feat: original"

    @patch("questionary.text")
    @patch("questionary.confirm")
    def test_edit_commit_message__empty_edit_returns_original(
        self, mock_confirm, mock_text, interactive_verbose_config
    ):
        """Return original message when edit is empty."""
        mock_confirm.return_value.ask.return_value = True
        mock_text.return_value.ask.return_value = ""

        result = edit_commit_message("feat: original", interactive_verbose_config)

        assert result == "feat: original"
