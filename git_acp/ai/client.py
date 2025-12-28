"""AI client for interacting with language models.

This module provides the :class:`AIClient` which handles communication with
OpenAI-compatible endpoints. It is responsible solely for network interaction
and leaves prompt construction and message handling to other modules.
"""

from collections.abc import Callable
from threading import Event, Thread
from time import sleep
from typing import Any

from openai import OpenAI
from rich.progress import Progress

from git_acp.config import (
    DEFAULT_AI_MODEL,
    DEFAULT_AI_TIMEOUT,
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_FALLBACK_BASE_URL,
    DEFAULT_TEMPERATURE,
)
from git_acp.git import GitError
from git_acp.utils import OptionalConfig, debug_header, debug_item

# Type alias for progress factory injection
ProgressFactory = Callable[[], Progress]


class AIClient:
    """Client for interacting with AI models via the OpenAI package."""

    def __init__(
        self,
        config: OptionalConfig = None,
        *,
        _openai_client: OpenAI | None = None,
        _progress_factory: ProgressFactory | None = None,
    ) -> None:
        """Initialize the AI client.

        Args:
            config: Optional configuration settings.
            _openai_client: Injected OpenAI client for testing. When provided,
                skips default client creation.
            _progress_factory: Injected factory for Progress instances. Defaults
                to ``rich.progress.Progress``.

        Raises:
            GitError: If connection to AI server fails or configuration is invalid.
        """
        self.config = config
        self.base_url = DEFAULT_BASE_URL
        self._progress_factory = _progress_factory or Progress

        self.model = (
            self.config.ai_model
            if self.config is not None and self.config.ai_model
            else DEFAULT_AI_MODEL
        )
        self.context_window = (
            self.config.context_window
            if self.config is not None and self.config.context_window is not None
            else DEFAULT_CONTEXT_WINDOW
        )

        # Use injected client if provided (for testing)
        if _openai_client is not None:
            self.client = _openai_client
            return

        if self.config and self.config.verbose:
            debug_header("Initializing AI client")
            debug_item("Base URL", self.base_url)
            debug_item("Model", self.model)
            debug_item("Temperature", str(DEFAULT_TEMPERATURE))
            debug_item("Timeout", str(DEFAULT_AI_TIMEOUT))
            debug_item("Context window", str(self.context_window))

        try:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=DEFAULT_API_KEY,
                timeout=DEFAULT_AI_TIMEOUT,
            )
        except ValueError as e:
            if self.config and self.config.verbose:
                debug_header("AI Client Initialization Failed")
                debug_item("Error Type", "ValueError")
                debug_item("Error Message", str(e))
            if "Invalid URL" in str(e):
                raise GitError(
                    "Invalid Ollama server URL. Please check your configuration."
                ) from e
            raise GitError(
                "Invalid AI configuration. Please verify your settings."
            ) from e
        except ConnectionError:
            # Attempt fallback URL if configured
            if (
                DEFAULT_FALLBACK_BASE_URL
                and DEFAULT_FALLBACK_BASE_URL != DEFAULT_BASE_URL
            ):
                if self.config and self.config.verbose:
                    debug_header("Primary AI server unavailable, trying fallback")
                    debug_item("Fallback URL", DEFAULT_FALLBACK_BASE_URL)
                try:
                    self.base_url = DEFAULT_FALLBACK_BASE_URL
                    self.client = OpenAI(
                        base_url=self.base_url,
                        api_key=DEFAULT_API_KEY,
                        timeout=DEFAULT_AI_TIMEOUT,
                    )
                except Exception:
                    if self.config and self.config.verbose:
                        debug_header("Fallback AI Client Connection Failed")
                        debug_item("Base URL", DEFAULT_FALLBACK_BASE_URL)
                    msg = "Could not connect to Ollama server."
                    raise GitError(msg) from None
            else:
                if self.config and self.config.verbose:
                    debug_header("AI Client Connection Failed")
                    debug_item("Error Type", "ConnectionError")
                    debug_item("Base URL", self.base_url)
                msg = "Could not connect to Ollama server."
                raise GitError(msg) from None
        except Exception as e:
            if self.config and self.config.verbose:
                debug_header("AI Client Initialization Failed")
                debug_item("Error Type", e.__class__.__name__)
                debug_item("Error Message", str(e))
            raise GitError(
                "Failed to initialize AI client. Please check your "
                "configuration and try again."
            ) from e

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Create a chat completion request.

        Args:
            messages (list[dict[str, str]]): Message dictionaries with ``role``
                and ``content`` keys.
            kwargs (Any): Additional configuration arguments.

        Returns:
            str: The generated response content.

        Raises:
            GitError: With specific error context for failure scenarios.
            TimeoutError: If the request exceeds the configured timeout.
        """
        try:
            if self.config and self.config.verbose:
                debug_header("Sending chat completion request")
                debug_item("Messages count", str(len(messages)))
                debug_item(
                    "First message preview",
                    messages[0]["content"][:100] + "...",
                )
                debug_item("Base URL", self.base_url)
                debug_item("Model", self.model)
                debug_item("Timeout", f"{DEFAULT_AI_TIMEOUT}s")

            extra_body = kwargs.pop("extra_body", None)
            if extra_body is None:
                extra_body = {}

            # Only send num_ctx to endpoints that are expected to tolerate
            # Ollama-style ``extra_body`` fields.
            #
            # We treat strict OpenAI endpoints as incompatible and avoid sending
            # unknown fields there.
            is_strict_openai_endpoint = any(
                host in self.base_url for host in ("api.openai.com", "openai.com")
            )
            is_ollama_endpoint = not is_strict_openai_endpoint
            if is_ollama_endpoint and self.context_window:
                extra_body = {
                    **extra_body,
                    "options": {
                        **extra_body.get("options", {}),
                        "num_ctx": self.context_window,
                    },
                }

            with self._progress_factory() as progress:
                task = progress.add_task(
                    "Waiting for AI response...",
                    total=100,
                )

                response_event = Event()
                response_data = {"response": None, "error": None}

                def make_request():
                    try:
                        response_data["response"] = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=DEFAULT_TEMPERATURE,
                            timeout=DEFAULT_AI_TIMEOUT,
                            extra_body=extra_body,
                            **kwargs,
                        )
                    except Exception as e:  # pragma: no cover
                        response_data["error"] = e
                    finally:
                        response_event.set()

                thread = Thread(target=make_request)
                thread.start()

                elapsed = 0
                while not response_event.is_set() and elapsed < DEFAULT_AI_TIMEOUT:
                    progress.update(
                        task,
                        completed=int((elapsed / DEFAULT_AI_TIMEOUT) * 100),
                    )
                    sleep(0.1)
                    elapsed += 0.1

                progress.update(task, completed=100)

                if response_data["error"]:
                    raise response_data["error"]
                if not response_event.is_set():
                    raise TimeoutError("Request timed out")

                response = response_data["response"]
                if not response or not response.choices:
                    raise GitError(
                        "AI model returned an empty response. Please try again."
                    )

                return response.choices[0].message.content

        except TimeoutError:
            if self.config and self.config.verbose:
                debug_header("AI Request Timeout")
                debug_item("Timeout Value", str(DEFAULT_AI_TIMEOUT))
            raise GitError(
                f"AI request timed out after {DEFAULT_AI_TIMEOUT} seconds. "
                "Try increasing the timeout value in your configuration or "
                "check if Ollama is responding."
            ) from None
        except ConnectionError:
            if self.config and self.config.verbose:
                debug_header("AI Connection Failed")
                debug_item("Base URL", self.base_url)
                debug_item("Model", self.model)
            raise GitError(
                "Could not connect to Ollama server. Please ensure:\n"
                "1. Ollama is running (run 'ollama serve')\n"
                "2. The model is installed (run "
                f"'ollama pull {self.model}')\n"
                "3. The server URL is correct in your configuration"
            ) from None
        except ValueError as e:
            if self.config and self.config.verbose:
                debug_header("AI Request Parameter Error")
                debug_item("Error Message", str(e))
            if "model" in str(e).lower():
                raise GitError(
                    f"AI model '{self.model}' not found. "
                    f"Please run 'ollama pull {self.model}' to "
                    "install it."
                ) from e
            raise GitError(f"Invalid AI request parameters: {str(e)}") from e
        except GitError:
            # Re-raise GitError without wrapping (e.g., empty response error)
            raise
        except Exception as e:
            if self.config and self.config.verbose:
                debug_header("AI Request Failed")
                debug_item("Error Type", e.__class__.__name__)
                debug_item("Error Message", str(e))
                if hasattr(e, "response"):
                    debug_item(
                        "Response Status",
                        str(getattr(e.response, "status_code", "N/A")),
                    )
                    debug_item(
                        "Response Text",
                        str(getattr(e.response, "text", "N/A")),
                    )
            raise GitError(
                "AI request failed. Please ensure:\n"
                "1. Ollama server is running and responsive\n"
                "2. The required model is installed\n"
                "3. Your network connection is stable"
            ) from e
