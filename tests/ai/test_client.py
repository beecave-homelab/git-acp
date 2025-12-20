"""Tests for AIClient with dependency injection.

This module tests the AIClient class with injected dependencies,
enabling comprehensive testing without external API calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from git_acp.ai.client import AIClient
from git_acp.config import (
    DEFAULT_AI_MODEL,
    DEFAULT_BASE_URL,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_TEMPERATURE,
)
from git_acp.git import GitError
from git_acp.utils import GitConfig


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def mock_config() -> GitConfig:
    """Create a non-verbose GitConfig instance.

    Returns:
        GitConfig: Test configuration with verbose=False.
    """
    return GitConfig(
        files="test.py",
        message=None,
        branch="main",
        use_ollama=True,
        interactive=False,
        skip_confirmation=False,
        verbose=False,
        prompt_type="simple",
    )


@pytest.fixture
def verbose_config() -> GitConfig:
    """Create a verbose GitConfig instance.

    Returns:
        GitConfig: Test configuration with verbose=True.
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
def mock_openai_client() -> MagicMock:
    """Create a mock OpenAI client with chat.completions.create method.

    Returns:
        MagicMock: Mock client returning 'feat: test commit message'.
    """
    client = MagicMock()
    mock_message = Mock()
    mock_message.content = "feat: test commit message"

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    client.chat.completions.create.return_value = mock_response
    return client


@pytest.fixture
def mock_progress_factory() -> MagicMock:
    """Create a mock progress factory that returns a no-op progress context.

    Returns:
        MagicMock: Factory that produces mock Progress instances.
    """
    progress = MagicMock()
    progress.__enter__ = MagicMock(return_value=progress)
    progress.__exit__ = MagicMock(return_value=False)
    progress.add_task.return_value = 0

    factory = MagicMock(return_value=progress)
    return factory


# -----------------------------------------------------------------------------
# Tests for Dependency Injection
# -----------------------------------------------------------------------------
class TestAIClientInjection:
    """Test suite for AIClient dependency injection capability."""

    def test_init__uses_injected_client(
        self, mock_config: GitConfig, mock_openai_client: MagicMock
    ) -> None:
        """Use injected OpenAI client instead of creating a new one."""
        # This test should FAIL until we add injection support
        client = AIClient(mock_config, _openai_client=mock_openai_client)

        assert client.client is mock_openai_client

    def test_init__creates_default_client_when_not_injected(
        self, mock_config: GitConfig
    ) -> None:
        """Create default OpenAI client when none is injected."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai_class:
            mock_openai_class.return_value = MagicMock()
            client = AIClient(mock_config)

            mock_openai_class.assert_called_once()
            assert client.client is mock_openai_class.return_value

    def test_chat_completion__uses_injected_progress_factory(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Use injected progress factory instead of default rich.Progress."""
        # This test should FAIL until we add injection support
        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        messages = [{"role": "user", "content": "test"}]
        result = client.chat_completion(messages)

        assert result == "feat: test commit message"
        # Progress factory should have been called
        mock_progress_factory.assert_called_once()


# -----------------------------------------------------------------------------
# Tests for chat_completion with Injected Client
# -----------------------------------------------------------------------------
class TestChatCompletionWithInjection:
    """Test chat_completion using injected dependencies."""

    def test_chat_completion__returns_response_content(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Return the message content from AI response."""
        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        messages = [{"role": "user", "content": "Generate commit message"}]
        result = client.chat_completion(messages)

        assert result == "feat: test commit message"
        mock_openai_client.chat.completions.create.assert_called_once()

    def test_chat_completion__passes_model_and_temperature(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Pass correct model and temperature to OpenAI API."""
        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        messages = [{"role": "user", "content": "test"}]
        client.chat_completion(messages)

        call_kwargs = mock_openai_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == DEFAULT_AI_MODEL
        assert call_kwargs.kwargs["temperature"] == DEFAULT_TEMPERATURE

    def test_chat_completion__uses_config_model_override(
        self,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Use config-provided ai_model override."""
        config = GitConfig(
            files="test.py",
            message=None,
            branch="main",
            use_ollama=True,
            interactive=False,
            skip_confirmation=False,
            verbose=False,
            prompt_type="simple",
            ai_model="custom/model:latest",
        )

        client = AIClient(
            config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )
        client.chat_completion([{"role": "user", "content": "test"}])

        call_kwargs = mock_openai_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "custom/model:latest"

    def test_chat_completion__passes_num_ctx_for_local_ollama_endpoint(
        self,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Pass num_ctx via extra_body for localhost Ollama endpoints."""
        config = GitConfig(
            files="test.py",
            message=None,
            branch="main",
            use_ollama=True,
            interactive=False,
            skip_confirmation=False,
            verbose=False,
            prompt_type="simple",
            context_window=4096,
        )
        client = AIClient(
            config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        assert DEFAULT_BASE_URL
        client.chat_completion([{"role": "user", "content": "test"}])

        call_kwargs = mock_openai_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["extra_body"]["options"]["num_ctx"] == 4096

    def test_chat_completion__does_not_pass_num_ctx_for_non_local_endpoint(
        self,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Avoid sending num_ctx for strict OpenAI-compatible servers."""
        config = GitConfig(
            files="test.py",
            message=None,
            branch="main",
            use_ollama=True,
            interactive=False,
            skip_confirmation=False,
            verbose=False,
            prompt_type="simple",
            context_window=DEFAULT_CONTEXT_WINDOW,
        )
        client = AIClient(
            config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        client.base_url = "https://api.openai.com/v1"
        client.chat_completion([{"role": "user", "content": "test"}])

        call_kwargs = mock_openai_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["extra_body"] == {}

    def test_chat_completion__raises_on_empty_response(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Raise GitError when AI returns empty response."""
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[])

        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError, match="empty response"):
            client.chat_completion([{"role": "user", "content": "test"}])

    def test_chat_completion__raises_on_none_response(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Raise GitError when AI returns None response."""
        mock_openai_client.chat.completions.create.return_value = None

        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError, match="empty response"):
            client.chat_completion([{"role": "user", "content": "test"}])

    def test_chat_completion__handles_connection_error(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Raise GitError with helpful message on ConnectionError."""
        mock_openai_client.chat.completions.create.side_effect = ConnectionError(
            "Connection refused"
        )

        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError, match="Could not connect to Ollama"):
            client.chat_completion([{"role": "user", "content": "test"}])

    def test_chat_completion__handles_value_error_for_model(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Raise GitError when model is not found."""
        mock_openai_client.chat.completions.create.side_effect = ValueError(
            "model not found"
        )

        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError, match="model.*not found"):
            client.chat_completion([{"role": "user", "content": "test"}])

    def test_chat_completion__handles_generic_value_error(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Raise GitError with details on generic ValueError."""
        mock_openai_client.chat.completions.create.side_effect = ValueError(
            "invalid parameter"
        )

        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError, match="Invalid AI request parameters"):
            client.chat_completion([{"role": "user", "content": "test"}])

    def test_chat_completion__handles_generic_exception(
        self,
        mock_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Raise GitError with generic message on unexpected exception."""
        mock_openai_client.chat.completions.create.side_effect = RuntimeError(
            "Unexpected error"
        )

        client = AIClient(
            mock_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError, match="AI request failed"):
            client.chat_completion([{"role": "user", "content": "test"}])


# -----------------------------------------------------------------------------
# Tests for Verbose Mode with Injection
# -----------------------------------------------------------------------------
class TestVerboseModeWithInjection:
    """Test verbose debug output using injected dependencies."""

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_chat_completion__logs_request_details_verbose(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Log request details in verbose mode."""
        client = AIClient(
            verbose_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        client.chat_completion([{"role": "user", "content": "test message here"}])

        mock_debug_header.assert_any_call("Sending chat completion request")
        mock_debug_item.assert_any_call("Messages count", "1")

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_chat_completion__logs_connection_error_verbose(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Log connection error details in verbose mode."""
        mock_openai_client.chat.completions.create.side_effect = ConnectionError()

        client = AIClient(
            verbose_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError):
            client.chat_completion([{"role": "user", "content": "test"}])

        mock_debug_header.assert_any_call("AI Connection Failed")

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_chat_completion__logs_value_error_verbose(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Log ValueError details in verbose mode."""
        mock_openai_client.chat.completions.create.side_effect = ValueError("bad param")

        client = AIClient(
            verbose_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError):
            client.chat_completion([{"role": "user", "content": "test"}])

        mock_debug_header.assert_any_call("AI Request Parameter Error")

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_chat_completion__logs_generic_error_verbose(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Log generic error details in verbose mode."""
        error = RuntimeError("unexpected")
        mock_openai_client.chat.completions.create.side_effect = error

        client = AIClient(
            verbose_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError):
            client.chat_completion([{"role": "user", "content": "test"}])

        mock_debug_header.assert_any_call("AI Request Failed")
        mock_debug_item.assert_any_call("Error Type", "RuntimeError")


# -----------------------------------------------------------------------------
# Tests for Init Error Handling
# -----------------------------------------------------------------------------
class TestInitErrorHandling:
    """Test AIClient initialization error handling."""

    def test_init__raises_on_invalid_url(self, mock_config: GitConfig) -> None:
        """Raise GitError when URL is invalid."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = ValueError("Invalid URL")

            with pytest.raises(GitError, match="Invalid Ollama server URL"):
                AIClient(mock_config)

    def test_init__raises_on_generic_value_error(self, mock_config: GitConfig) -> None:
        """Raise GitError on generic ValueError during init."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = ValueError("Some other error")

            with pytest.raises(GitError, match="Invalid AI configuration"):
                AIClient(mock_config)

    def test_init__tries_fallback_on_connection_error(
        self, mock_config: GitConfig
    ) -> None:
        """Try fallback URL when primary connection fails."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            # First call fails, second succeeds
            mock_openai.side_effect = [ConnectionError(), MagicMock()]

            with patch(
                "git_acp.ai.client.DEFAULT_FALLBACK_BASE_URL", "http://fallback:11434"
            ):
                client = AIClient(mock_config)

                assert mock_openai.call_count == 2
                assert client.base_url == "http://fallback:11434"

    def test_init__raises_when_fallback_also_fails(
        self, mock_config: GitConfig
    ) -> None:
        """Raise GitError when both primary and fallback connections fail."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = [ConnectionError(), ConnectionError()]

            with patch(
                "git_acp.ai.client.DEFAULT_FALLBACK_BASE_URL", "http://fallback:11434"
            ):
                with pytest.raises(GitError, match="Could not connect to Ollama"):
                    AIClient(mock_config)

    def test_init__raises_without_fallback_on_connection_error(
        self, mock_config: GitConfig
    ) -> None:
        """Raise GitError when no fallback is configured."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = ConnectionError()

            with patch("git_acp.ai.client.DEFAULT_FALLBACK_BASE_URL", None):
                with pytest.raises(GitError, match="Could not connect to Ollama"):
                    AIClient(mock_config)

    def test_init__raises_on_generic_exception(self, mock_config: GitConfig) -> None:
        """Raise GitError on generic exception during init."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = RuntimeError("Unexpected")

            with pytest.raises(GitError, match="Failed to initialize AI client"):
                AIClient(mock_config)

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_init__logs_verbose_on_success(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log initialization details in verbose mode."""
        with patch("git_acp.ai.client.OpenAI"):
            AIClient(verbose_config)

            mock_debug_header.assert_any_call("Initializing AI client")
            mock_debug_item.assert_any_call("Base URL", DEFAULT_BASE_URL)

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_init__logs_verbose_on_fallback(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log fallback attempt in verbose mode."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = [ConnectionError(), MagicMock()]

            with patch(
                "git_acp.ai.client.DEFAULT_FALLBACK_BASE_URL", "http://fallback:11434"
            ):
                AIClient(verbose_config)

                mock_debug_header.assert_any_call(
                    "Primary AI server unavailable, trying fallback"
                )

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_init__logs_verbose_connection_error_no_fallback(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log connection error details when no fallback is configured."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = ConnectionError()

            with patch("git_acp.ai.client.DEFAULT_FALLBACK_BASE_URL", None):
                with pytest.raises(GitError):
                    AIClient(verbose_config)

                mock_debug_header.assert_any_call("AI Client Connection Failed")
                mock_debug_item.assert_any_call("Error Type", "ConnectionError")

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_init__logs_verbose_on_generic_exception(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log generic exception details during init in verbose mode."""
        with patch("git_acp.ai.client.OpenAI") as mock_openai:
            mock_openai.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(GitError):
                AIClient(verbose_config)

            mock_debug_header.assert_any_call("AI Client Initialization Failed")
            mock_debug_item.assert_any_call("Error Type", "RuntimeError")
            mock_debug_item.assert_any_call("Error Message", "Unexpected error")

    @patch("git_acp.ai.client.debug_header")
    @patch("git_acp.ai.client.debug_item")
    def test_chat_completion__logs_response_attrs_on_error(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        verbose_config: GitConfig,
        mock_openai_client: MagicMock,
        mock_progress_factory: MagicMock,
    ) -> None:
        """Log response attributes when error has response object."""
        error = RuntimeError("API error")
        error.response = MagicMock()
        error.response.status_code = 500
        error.response.text = "Internal Server Error"
        mock_openai_client.chat.completions.create.side_effect = error

        client = AIClient(
            verbose_config,
            _openai_client=mock_openai_client,
            _progress_factory=mock_progress_factory,
        )

        with pytest.raises(GitError):
            client.chat_completion([{"role": "user", "content": "test"}])

        mock_debug_item.assert_any_call("Response Status", "500")
        mock_debug_item.assert_any_call("Response Text", "Internal Server Error")
