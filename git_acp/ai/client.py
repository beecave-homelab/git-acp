"""AI client for interacting with language models.

This module provides the :class:`AIClient` which handles communication with
OpenAI-compatible endpoints. It is responsible solely for network interaction
and leaves prompt construction and message handling to other modules.
"""

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
    DEFAULT_FALLBACK_BASE_URL,
    DEFAULT_TEMPERATURE,
)
from git_acp.git import GitError
from git_acp.utils import OptionalConfig, debug_header, debug_item


class AIClient:
    """Client for interacting with AI models via the OpenAI package."""

    def __init__(self, config: OptionalConfig = None) -> None:
        """Initialize the AI client.

        Args:
            config (OptionalConfig | None): Optional configuration settings.

        Raises:
            GitError: If connection to AI server fails or configuration is invalid.
        """
        self.config = config
        self.base_url = DEFAULT_BASE_URL
        if self.config and self.config.verbose:
            debug_header("Initializing AI client")
            debug_item("Base URL", self.base_url)
            debug_item("Model", DEFAULT_AI_MODEL)
            debug_item("Temperature", str(DEFAULT_TEMPERATURE))
            debug_item("Timeout", str(DEFAULT_AI_TIMEOUT))

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
                    msg = "Could not connect to Ollama. Ensure it's running."
                    raise GitError(msg) from None
            else:
                if self.config and self.config.verbose:
                    debug_header("AI Client Connection Failed")
                    debug_item("Error Type", "ConnectionError")
                    debug_item("Base URL", self.base_url)
                msg = "Could not connect to Ollama. Ensure it's running."
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
                debug_item("Timeout", f"{DEFAULT_AI_TIMEOUT}s")

            with Progress() as progress:
                task = progress.add_task(
                    "Waiting for AI response...",
                    total=100,
                )

                response_event = Event()
                response_data = {"response": None, "error": None}

                def make_request():
                    try:
                        response_data["response"] = self.client.chat.completions.create(
                            model=DEFAULT_AI_MODEL,
                            messages=messages,
                            temperature=DEFAULT_TEMPERATURE,
                            timeout=DEFAULT_AI_TIMEOUT,
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
                debug_item("Model", DEFAULT_AI_MODEL)
            raise GitError(
                "Could not connect to Ollama server. Please ensure:\n"
                "1. Ollama is running (run 'ollama serve')\n"
                "2. The model is installed (run "
                "'ollama pull mevatron/diffsense:1.5b')\n"
                "3. The server URL is correct in your configuration"
            ) from None
        except ValueError as e:
            if self.config and self.config.verbose:
                debug_header("AI Request Parameter Error")
                debug_item("Error Message", str(e))
            if "model" in str(e).lower():
                raise GitError(
                    f"AI model '{DEFAULT_AI_MODEL}' not found. "
                    "Please run 'ollama pull mevatron/diffsense:1.5b' to "
                    "install it."
                ) from e
            raise GitError(f"Invalid AI request parameters: {str(e)}") from e
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
