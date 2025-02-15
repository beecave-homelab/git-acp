"""AI client for interacting with AI models."""

from threading import Thread, Event
from time import sleep
from typing import Optional, Callable

import openai
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from git_acp.git import GitError
from git_acp.config import AI_SETTINGS
from git_acp.utils import (
    debug_header,
    debug_item,
)

try:
    from openai import OpenAI
except ImportError as exc:
    raise GitError(
        "OpenAI package not installed.",
        suggestion="Install it with: pip install openai",
    ) from exc

# Maximum number of retries for transient errors
MAX_RETRIES = 3
# Delay between retries (in seconds)
RETRY_DELAY = 2


class AIClient:
    """Client for interacting with AI models via OpenAI's API.

    Handles model initialization, verification, and chat completions with proper
    error handling and progress tracking. Supports both commit message and PR
    generation models.
    """

    def __init__(self, config=None, use_pr_model=False):
        """Initialize the AI client.

        Args:
            config: GitConfig object containing AI configuration
            use_pr_model: Whether to use the PR model instead of commit model
        """
        self.config = config
        # Use model from config if available, otherwise use default
        self._model = (
            config.ai_config.model
            if config and config.ai_config and config.ai_config.model
            else (AI_SETTINGS["pr_model"] if use_pr_model else AI_SETTINGS["model"])
        )

        if config and getattr(config, "verbose", False):
            debug_header("Initializing AI client")
            debug_item(config, "Base URL", AI_SETTINGS["base_url"])
            debug_item(config, "Model", self._model)
            debug_item(
                config,
                "Model Source",
                (
                    "User override"
                    if config.ai_config.model
                    else ("Default PR" if use_pr_model else "Default commit")
                ),
            )
            debug_item(config, "Temperature", str(AI_SETTINGS["temperature"]))
            debug_item(config, "Timeout", str(AI_SETTINGS["timeout"]))

        try:
            # Use the configuration from AIConfig if available
            timeout = (
                config.ai_config.timeout
                if config and hasattr(config, "ai_config")
                else AI_SETTINGS["timeout"]
            )
            self.client = OpenAI(
                base_url=AI_SETTINGS["base_url"],
                api_key=AI_SETTINGS["api_key"],
                timeout=timeout,
            )
            # Verify model availability immediately
            if config and getattr(self.config, "verbose", False):
                debug_header("Verifying model availability")
                debug_item(config, "Model", self._model)
            self._verify_model()
        except ValueError as e:
            if "Invalid URL" in str(e):
                raise GitError(
                    "Invalid Ollama server URL.",
                    suggestion="Check your configuration and ensure the URL"
                    "is correct.",
                    context="AI Configuration Error",
                ) from e
            raise GitError(
                "Invalid AI configuration.",
                suggestion="Verify your settings in ~/.config/git-acp/.env",
                context="AI Configuration Error",
            ) from e
        except ConnectionError:
            raise GitError(
                "Could not connect to Ollama server.",
                suggestion=(
                    "1. Ensure Ollama is running (run 'ollama serve')\n"
                    "2. Check if server is responsive "
                    "(curl http://localhost:11434/api/tags)\n"
                    "3. Verify your network connection"
                ),
                context="AI Connection Error",
            ) from None
        except Exception as e:
            if "model" in str(e).lower() and "not found" in str(e).lower():
                model_type = (
                    "PR" if self._model == AI_SETTINGS["pr_model"] else "commit message"
                )
                raise GitError(
                    f"The {model_type} model '{self._model}' "
                    "is not available in Ollama.",
                    suggestion=(
                        f"Run 'ollama pull {self._model}' "
                        "to install the required model"
                    ),
                    context="AI Model Error",
                ) from e
            raise GitError(
                f"Failed to initialize AI client: {str(e)}",
                suggestion="Check your Ollama installation and configuration",
                context="AI Initialization Error",
            ) from e

    def _verify_model(self) -> None:
        """Verify that the model is available in Ollama."""
        try:
            # Try a simple completion to verify model availability
            self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "test"}],
                temperature=0,
                max_tokens=1,
                timeout=AI_SETTINGS["timeout"],
            )
        except openai.APIConnectionError as e:
            raise GitError(
                "Could not connect to Ollama server.",
                suggestion=(
                    "1. Ensure Ollama is running (run 'ollama serve')\n"
                    "2. Check if server is responsive "
                    "(curl http://localhost:11434/api/tags)\n"
                    "3. Verify your network connection"
                ),
                context="AI Connection Error",
            ) from e
        except openai.NotFoundError as e:
            raise GitError(
                f"The model '{self._model}' is not available in Ollama.",
                suggestion=f"Run 'ollama pull {self._model}' to install it",
                context="AI Model Error",
            ) from e
        except openai.APIError as e:
            raise GitError(
                f"Model verification failed: {str(e)}",
                suggestion="Check Ollama server logs",
                context="AI Model Error",
            ) from e

    @property
    def model(self) -> str:
        """Get the current model name."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the model name to use for requests."""
        if value != self._model:
            self._model = value
            if self.config and getattr(self.config, "verbose", False):
                debug_header("Model changed")
                debug_item(self.config, "New model", value)
            # Verify the new model is available
            self._verify_model()

    def is_reasoning_llm(self, text: str) -> bool:
        """Check if the AI model is a reasoning LLM by looking for thinking tags.

        Args:
            text: The text to check for thinking tags

        Returns:
            True if thinking tags are found, indicating a reasoning LLM
        """
        return "<think>" in text.lower() and "</think>" in text.lower()

    def extract_thinking_blocks(self, text: str) -> list[tuple[str, str]]:
        """Extract thinking blocks from text while preserving their positions.

        Args:
            text: The text to extract thinking blocks from

        Returns:
            List of tuples containing (thinking content, position in text)
            where position is 'before', 'middle', or 'after' the main content
        """
        thinking_blocks = []
        cleaned_text = text

        while "<think>" in cleaned_text.lower() and "</think>" in cleaned_text.lower():
            start = cleaned_text.lower().find("<think>")
            end = cleaned_text.lower().find("</think>") + len("</think>")

            # Extract the thinking block with tags
            thinking_block = cleaned_text[start:end]

            # Determine position based on location in text
            if start == 0:
                position = "before"
            elif end == len(cleaned_text):
                position = "after"
            else:
                position = "middle"

            thinking_blocks.append((thinking_block, position))
            cleaned_text = cleaned_text[:start] + cleaned_text[end:]

        return thinking_blocks

    def clean_thinking_tags(self, text: str) -> str:
        """Remove thinking tags and their content from the text.

        Args:
            text: The text to clean

        Returns:
            Text with thinking tags and their content removed
        """
        cleaned_text = text
        while "<think>" in cleaned_text.lower() and "</think>" in cleaned_text.lower():
            start = cleaned_text.lower().find("<think>")
            end = cleaned_text.lower().find("</think>") + len("</think>")
            cleaned_text = cleaned_text[:start] + cleaned_text[end:]
        return cleaned_text.strip()

    def _handle_ai_request(self, messages: list, **kwargs) -> dict:
        """Handle the actual AI request in a separate thread.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments for the API

        Returns:
            dict: Response data containing either response or error
        """
        response_data = {"response": None, "error": None}
        try:
            # Use the configuration from AIConfig if available
            temperature = (
                self.config.ai_config.temperature
                if self.config and hasattr(self.config, "ai_config")
                else AI_SETTINGS["temperature"]
            )
            timeout = (
                self.config.ai_config.timeout
                if self.config and hasattr(self.config, "ai_config")
                else AI_SETTINGS["timeout"]
            )
            # Set a slightly shorter timeout for the API call
            api_timeout = max(5, timeout - 5)
            if self.config and getattr(self.config, "verbose", False):
                debug_item(self.config, "API timeout", f"{api_timeout}s")
                debug_item(self.config, "Total timeout", f"{timeout}s")
            response_data["response"] = self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                timeout=api_timeout,
                **kwargs,
            )
        except openai.APITimeoutError as e:
            if self.config and getattr(self.config, "verbose", False):
                debug_item(self.config, "Error", "API timeout")
                debug_item(self.config, "Details", str(e))
            response_data["error"] = GitError(
                "AI request timed out.",
                suggestion=(
                    "1. Check network connection to Ollama server\n"
                    "2. Try increasing timeout in ~/.config/git-acp/.env\n"
                    "3. Consider using --context-type commits for faster processing"
                ),
                context="AI Timeout Error",
            )
        except (openai.APIError, openai.BadRequestError, openai.NotFoundError) as e:
            if self.config and getattr(self.config, "verbose", False):
                debug_item(self.config, "Error", str(type(e).__name__))
                debug_item(self.config, "Details", str(e))
            response_data["error"] = GitError(str(e), context="AI API Error")
        return response_data

    def _handle_response_error(self, response_data: dict) -> None:
        """Handle response errors by raising appropriate exceptions.

        Args:
            response_data: Dictionary containing response and error information

        Raises:
            GitError: With appropriate context based on the error type
        """
        if response_data.get("error"):
            error = response_data["error"]
            if isinstance(error, GitError):
                raise error
            raise GitError(str(error))

    def _handle_retry_logic(self, e: Exception, retries: int) -> bool:
        """Handle retry logic for transient errors.

        Args:
            e: The exception that occurred
            retries: Current number of retries

        Returns:
            bool: True if should retry, False otherwise

        Raises:
            GitError: If max retries reached
        """
        # Early return for non-retryable errors
        if not isinstance(
            e, (openai.APIError, openai.APIConnectionError, TimeoutError)
        ):
            return False

        # Return True if we should retry
        if retries < MAX_RETRIES:
            sleep(RETRY_DELAY)
            return True

        # At this point, we've exhausted retries, raise appropriate error
        error_msg = (
            f"Failed to get AI response after {MAX_RETRIES} retries: " f"{str(e)}"
            if isinstance(e, (openai.APIError, openai.APIConnectionError))
            else (f"AI request timed out after " f"{AI_SETTINGS['timeout']} seconds")
        )
        suggestion = (
            "Check your network connection and Ollama server status"
            if isinstance(e, (openai.APIError, openai.APIConnectionError))
            else "Try again or adjust the timeout in your configuration"
        )
        context = (
            "AI Communication Error"
            if isinstance(e, (openai.APIError, openai.APIConnectionError))
            else "AI Timeout Error"
        )

        raise GitError(
            error_msg,
            suggestion=suggestion,
            context=context,
        ) from (
            e if isinstance(e, (openai.APIError, openai.APIConnectionError)) else None
        )

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        progress_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """Generate a chat completion response from the AI model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            progress_callback: Optional callback function to update progress status
            **kwargs: Additional arguments to pass to the completion API

        Returns:
            str: The AI model's response text

        Raises:
            GitError: For various AI-related errors including timeouts,
                    connection issues, or invalid configurations
        """
        if self.config and getattr(self.config, "verbose", False):
            debug_header("Sending chat completion request")
            debug_item(self.config, "Messages count", str(len(messages)))
            debug_item(
                self.config,
                "First message preview",
                messages[0]["content"][:100] + "...",
            )
            debug_item(self.config, "Model", self._model)
            debug_item(self.config, "Timeout", f"{AI_SETTINGS['timeout']}s")

        response_event = Event()
        response_data: dict = {"response": None, "error": None}

        for retry_count in range(MAX_RETRIES):
            try:
                def make_request() -> None:
                    nonlocal response_data
                    response_data = self._handle_ai_request(messages, **kwargs)
                    response_event.set()

                # Start request in a separate thread
                request_thread = Thread(target=make_request)
                request_thread.start()

                # Wait for response or timeout
                if not response_event.wait(timeout=AI_SETTINGS["timeout"]):
                    raise TimeoutError("Request timed out")

                # Handle any errors from the request
                self._handle_response_error(response_data)

                response = response_data.get("response")
                if not response or not response.choices:
                    raise GitError("Empty response from AI model")

                return response.choices[0].message.content.strip()

            except (openai.APIError, openai.APIConnectionError, TimeoutError) as e:
                # On last retry, raise the error
                if retry_count == MAX_RETRIES - 1:
                    error_msg = (
                        f"Failed to get AI response after {MAX_RETRIES} retries: "
                        f"{str(e)}"
                        if isinstance(e, (openai.APIError, openai.APIConnectionError))
                        else (
                            f"AI request timed out after "
                            f"{AI_SETTINGS['timeout']} seconds"
                        )
                    )
                    suggestion = (
                        "Check your network connection and Ollama server status"
                        if isinstance(e, (openai.APIError, openai.APIConnectionError))
                        else "Try again or adjust the timeout in your configuration"
                    )
                    context = (
                        "AI Communication Error"
                        if isinstance(e, (openai.APIError, openai.APIConnectionError))
                        else "AI Timeout Error"
                    )
                    raise GitError(
                        error_msg,
                        suggestion=suggestion,
                        context=context,
                    ) from e
                # Otherwise sleep and continue to next retry
                sleep(RETRY_DELAY)
                continue

            except ValueError as e:
                if self.config and getattr(self.config, "verbose", False):
                    debug_header("AI Request Parameter Error")
                    debug_item(self.config, "Error Message", str(e))
                if "model" in str(e).lower():
                    model_type = (
                        "PR"
                        if self._model == AI_SETTINGS["pr_model"]
                        else "commit message"
                    )
                    raise GitError(
                        f"{model_type} model '{self._model}' is not available "
                        "in Ollama.",
                        suggestion=(
                            f"Run 'ollama pull {self._model}' to install the "
                            "required model"
                        ),
                        context="AI Model Error",
                    ) from e
                raise GitError(
                    f"Invalid AI request parameters: {str(e)}",
                    suggestion="Check your configuration settings",
                    context="AI Parameter Error",
                ) from e
            except Exception as e:
                raise GitError(
                    f"Failed to generate AI response: {str(e)}",
                    suggestion="Check your configuration and try again",
                    context="AI Generation Error",
                ) from e

        # This line should never be reached due to the error handling above
        raise GitError(
            "Failed to get AI response after exhausting all retries",
            suggestion="Check your network connection and try again",
            context="AI Communication Error",
        )
