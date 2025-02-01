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
    raise GitError("OpenAI package not installed. Please install it with: pip install openai")

class AIClient:
    def __init__(self, config=None):
        self.config = config
        if config and getattr(config, 'verbose', False):
            debug_header("Initializing AI client")
            debug_item("Base URL", AI_SETTINGS["base_url"])
            debug_item("Model", AI_SETTINGS["model"])
            debug_item("Temperature", str(AI_SETTINGS["temperature"]))
            debug_item("Timeout", str(AI_SETTINGS["timeout"]))
        try:
            self.client = OpenAI(
                base_url=AI_SETTINGS["base_url"],
                api_key=AI_SETTINGS["api_key"],
                timeout=AI_SETTINGS["timeout"]
            )
        except ValueError as e:
            if "Invalid URL" in str(e):
                raise GitError("Invalid Ollama server URL. Please check your configuration.") from e
            raise GitError("Invalid AI configuration. Please verify your settings.") from e
        except ConnectionError:
            raise GitError("Could not connect to Ollama server. Please ensure it's running.") from None
        except Exception as e:
            raise GitError(f"Failed to initialize AI client: {str(e)}") from e

    def chat_completion(self, messages: list, **kwargs) -> str:
        try:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("Sending chat completion request")
                debug_item("Messages count", str(len(messages)))
                debug_item("First message preview", messages[0]['content'][:100] + "...")
                debug_item("Timeout", f"{AI_SETTINGS['timeout']}s")
            
            with Progress() as progress:
                task = progress.add_task("Waiting for AI response...", total=100)
                response_event = Event()
                response_data = {"response": None, "error": None}
                
                def make_request():
                    try:
                        response_data["response"] = self.client.chat.completions.create(
                            model=AI_SETTINGS["model"],
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
                    raise GitError("AI model returned an empty response. Please try again.")
                    
                return response.choices[0].message.content
                
        except TimeoutError:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Request Timeout")
                debug_item("Timeout Value", str(AI_SETTINGS["timeout"]))
            raise GitError(
                f"AI request timed out after {AI_SETTINGS['timeout']} seconds. "
                "Try increasing the timeout value in your configuration or check if Ollama is responding."
            ) from None
        except ConnectionError:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Connection Failed")
                debug_item("Base URL", AI_SETTINGS["base_url"])
                debug_item("Model", AI_SETTINGS["model"])
            raise GitError(
                "Could not connect to Ollama server. Please ensure:\n"
                "1. Ollama is running (run 'ollama serve')\n"
                "2. The model is installed (run 'ollama pull mevatron/diffsense:1.5b')\n"
                "3. The server URL is correct in your configuration"
            ) from None
        except ValueError as e:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Request Parameter Error")
                debug_item("Error Message", str(e))
            if "model" in str(e).lower():
                raise GitError(
                    f"AI model '{AI_SETTINGS['model']}' not found. "
                    "Please run 'ollama pull mevatron/diffsense:1.5b' to install it."
                ) from e
            raise GitError(f"Invalid AI request parameters: {str(e)}") from e
        except Exception as e:
            if self.config and getattr(self.config, 'verbose', False):
                debug_header("AI Request Failed")
                debug_item("Error Type", e.__class__.__name__)
                debug_item("Error Message", str(e))
                if hasattr(e, 'response'):
                    debug_item("Response Status", str(getattr(e.response, 'status_code', 'N/A')))
                    debug_item("Response Text", str(getattr(e.response, 'text', 'N/A')))
            raise GitError(
                "AI request failed. Please ensure:\n"
                "1. Ollama server is running and responsive\n"
                "2. The required model is installed\n"
                "3. Your network connection is stable"
            ) from e 