"""AI client for interacting with AI models."""
import json
from threading import Thread, Event
from time import sleep
from rich.progress import Progress
from git_acp.git import GitError
from git_acp.config.settings import AI_SETTINGS
from git_acp.utils import debug_header, debug_item

try:
    from openai import OpenAI
except ImportError:
    raise GitError(
        "OpenAI package not installed.",
        suggestion="Install it with: pip install openai"
    )

class AIClient:
    def __init__(self, config=None, use_pr_model=False):
        self.config = config
        # Initialize with PR model if requested, otherwise use default model
        self._model = AI_SETTINGS["pr_model"] if use_pr_model else AI_SETTINGS["model"]
        
        if config and getattr(config, 'verbose', False):
            debug_header("Initializing AI client")
            debug_item("Base URL", AI_SETTINGS["base_url"])
            debug_item("Model", self._model)
            debug_item("Model Type", "PR" if use_pr_model else "Commit")
            debug_item("Temperature", str(AI_SETTINGS["temperature"]))
            debug_item("Timeout", str(AI_SETTINGS["timeout"]))
        try:
            self.client = OpenAI(
                base_url=AI_SETTINGS["base_url"],
                api_key=AI_SETTINGS["api_key"],
                timeout=AI_SETTINGS["timeout"]
            )
            # Verify model availability immediately
            if config and getattr(self.config, 'verbose', False):
                debug_header("Verifying model availability")
                debug_item("Model", self._model)
            self._verify_model()
        except ValueError as e:
            if "Invalid URL" in str(e):
                raise GitError(
                    "Invalid Ollama server URL.",
                    suggestion="Check your configuration and ensure the URL is correct.",
                    context="AI Configuration Error"
                ) from e
            raise GitError(
                "Invalid AI configuration.",
                suggestion="Verify your settings in ~/.config/git-acp/.env",
                context="AI Configuration Error"
            ) from e
        except ConnectionError:
            raise GitError(
                "Could not connect to Ollama server.",
                suggestion="Ensure Ollama is running with 'ollama serve'",
                context="AI Connection Error"
            ) from None
        except Exception as e:
            if "model" in str(e).lower() and "not found" in str(e).lower():
                model_type = "PR" if self._model == AI_SETTINGS["pr_model"] else "commit message"
                raise GitError(
                    f"The {model_type} model '{self._model}' is not available in Ollama.",
                    suggestion=f"Run 'ollama pull {self._model}' to install the required model",
                    context="AI Model Error"
                ) from e
            raise GitError(
                f"Failed to initialize AI client: {str(e)}",
                suggestion="Check your Ollama installation and configuration",
                context="AI Initialization Error"
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
                timeout=5  # Short timeout for verification
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "model" in error_msg and "not found" in error_msg:
                model_type = "PR" if self._model == AI_SETTINGS["pr_model"] else "commit message"
                raise GitError(
                    f"The {model_type} model '{self._model}' is not available in Ollama.",
                    suggestion=f"Run 'ollama pull {self._model}' to install the required model",
                    context="AI Model Error"
                ) from e
            elif "connection" in error_msg:
                raise GitError(
                    "Could not connect to Ollama server.",
                    suggestion="1. Ensure Ollama is running (run 'ollama serve')\n"
                             "2. Check if server is responsive (try 'curl http://localhost:11434/api/tags')\n"
                             "3. Verify your network connection",
                    context="AI Connection Error"
                ) from e
            else:
                raise GitError(
                    f"Failed to verify model availability: {str(e)}",
                    suggestion="Check Ollama server logs for more details",
                    context="AI Model Verification Error"
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
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("Model changed")
                debug_item("New model", value)
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

    def chat_completion(self, messages: list, **kwargs) -> str:
        try:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("Sending chat completion request")
                debug_item("Messages count", str(len(messages)))
                debug_item("First message preview", messages[0]['content'][:100] + "...")
                debug_item("Model", self._model)  # Log the actual model being used
                debug_item("Timeout", f"{AI_SETTINGS['timeout']}s")
            
            with Progress() as progress:
                task = progress.add_task("Waiting for AI response...", total=100)
                response_event = Event()
                response_data = {"response": None, "error": None}
                
                def make_request():
                    try:
                        response_data["response"] = self.client.chat.completions.create(
                            model=self._model,  # Use instance model instead of settings
                            messages=messages,
                            temperature=AI_SETTINGS["temperature"],
                            timeout=AI_SETTINGS["timeout"],
                            **kwargs
                        )
                    except Exception as e:
                        response_data["error"] = e
                    finally:
                        response_event.set()

                thread = Thread(target=make_request)
                thread.start()
                
                elapsed = 0
                while not response_event.is_set() and elapsed < AI_SETTINGS["timeout"]:
                    progress.update(task, completed=int((elapsed / AI_SETTINGS["timeout"]) * 100))
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
                        "AI model returned an empty response.",
                        suggestion="Try the request again or check if the model is functioning correctly",
                        context="AI Response Error"
                    )
                    
                content = response.choices[0].message.content
                
                # Check if this is a reasoning LLM
                if self.is_reasoning_llm(content):
                    if self.config and getattr(self.config, 'verbose', False):
                        debug_header("Reasoning LLM detected")
                        debug_item("Original response", content)
                        
                        # Extract and display thinking blocks in verbose mode
                        thinking_blocks = self.extract_thinking_blocks(content)
                        if thinking_blocks:
                            debug_header("Thinking Process")
                            for block, position in thinking_blocks:
                                # Extract the actual thinking content without tags
                                thinking_content = block[block.lower().find("<think>") + 7:block.lower().find("</think>")].strip()
                                debug_item(f"Thinking ({position})", thinking_content)
                
                    # Clean the content for actual use
                    content = self.clean_thinking_tags(content)
                    
                    if self.config and getattr(self.config, 'verbose', False):
                        debug_item("Cleaned response", content)
                
                return content
                
        except TimeoutError:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Request Timeout")
                debug_item("Timeout Value", str(AI_SETTINGS["timeout"]))
            raise GitError(
                f"AI request timed out after {AI_SETTINGS['timeout']} seconds.",
                suggestion="Try increasing the timeout value in your configuration or check if Ollama is responding",
                context="AI Timeout Error"
            ) from None
        except ConnectionError:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Connection Failed")
                debug_item("Base URL", AI_SETTINGS["base_url"])
                debug_item("Model", self._model)
            raise GitError(
                "Could not connect to Ollama server.",
                suggestion="1. Ensure Ollama is running (run 'ollama serve')\n"
                         "2. Check if server is responsive (try 'curl http://localhost:11434/api/tags')\n"
                         "3. Verify your network connection",
                context="AI Connection Error"
            ) from None
        except ValueError as e:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Request Parameter Error")
                debug_item("Error Message", str(e))
            if "model" in str(e).lower():
                model_type = "PR" if self._model == AI_SETTINGS["pr_model"] else "commit message"
                raise GitError(
                    f"The {model_type} model '{self._model}' is not available in Ollama.",
                    suggestion=f"Run 'ollama pull {self._model}' to install the required model",
                    context="AI Model Error"
                ) from e
            raise GitError(
                f"Invalid AI request parameters: {str(e)}",
                suggestion="Check your configuration settings",
                context="AI Parameter Error"
            ) from e
        except Exception as e:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Request Failed")
                debug_item("Error Type", e.__class__.__name__)
                debug_item("Error Message", str(e))
                if hasattr(e, 'response'):
                    debug_item("Response Status", str(getattr(e.response, 'status_code', 'N/A')))
                    debug_item("Response Text", str(getattr(e.response, 'text', 'N/A')))
            if "model" in str(e).lower() and "not found" in str(e).lower():
                model_type = "PR" if self._model == AI_SETTINGS["pr_model"] else "commit message"
                raise GitError(
                    f"The {model_type} model '{self._model}' is not available in Ollama.",
                    suggestion=f"Run 'ollama pull {self._model}' to install the required model",
                    context="AI Model Error"
                ) from e
            raise GitError(
                "AI request failed.",
                suggestion="1. Ensure Ollama server is running and responsive\n"
                         "2. Verify the required model is installed\n"
                         "3. Check your network connection",
                context="AI Request Error"
            ) from e 