"""AI-powered commit message generation utilities.

This module provides functions for generating commit messages using AI models,
with support for both simple and advanced context-aware generation.
"""

import json
from collections import Counter
from typing import Dict, Any

from openai import OpenAI
from rich import print as rprint
import questionary
from rich.panel import Panel
from rich.progress import Progress

from git_acp.git import (
    GitError, run_git_command, get_recent_commits,
    get_diff,
    find_related_commits,
    analyze_commit_patterns
)
from git_acp.utils import (
    debug_header, debug_item, debug_preview,
    GitConfig, OptionalConfig, PromptType
)
from git_acp.config import (
    DEFAULT_AI_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_NUM_RECENT_COMMITS,
    DEFAULT_NUM_RELATED_COMMITS,
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    DEFAULT_PROMPT_TYPE,
    DEFAULT_AI_TIMEOUT,
    QUESTIONARY_STYLE,
    COLORS,
    TERMINAL_WIDTH
)

class AIClient:
    """Client for interacting with AI models via OpenAI package."""
    
    def __init__(self, config: OptionalConfig = None):
        """Initialize the AI client with configuration.
        
        Args:
            config: Optional configuration settings
        """
        self.config = config
        if self.config and self.config.verbose:
            debug_header("Initializing AI client")
            debug_item("Base URL", DEFAULT_BASE_URL)
            debug_item("Model", DEFAULT_AI_MODEL)
            debug_item("Temperature", str(DEFAULT_TEMPERATURE))
            debug_item("Timeout", str(DEFAULT_AI_TIMEOUT))
        
        try:
            self.client = OpenAI(
                base_url=DEFAULT_BASE_URL,
                api_key=DEFAULT_API_KEY,
                timeout=DEFAULT_AI_TIMEOUT
            )
        except ValueError as e:
            if self.config and self.config.verbose:
                debug_header("AI Client Initialization Failed")
                debug_item("Error Type", "ValueError")
                debug_item("Error Message", str(e))
            if "Invalid URL" in str(e):
                raise GitError("Invalid Ollama server URL. Please check your configuration.") from e
            raise GitError("Invalid AI configuration. Please verify your settings.") from e
        except ConnectionError:
            if self.config and self.config.verbose:
                debug_header("AI Client Connection Failed")
                debug_item("Error Type", "ConnectionError")
                debug_item("Base URL", DEFAULT_BASE_URL)
            raise GitError("Could not connect to Ollama server. Please ensure it's running.") from None
        except Exception as e:
            if self.config and self.config.verbose:
                debug_header("AI Client Initialization Failed")
                debug_item("Error Type", e.__class__.__name__)
                debug_item("Error Message", str(e))
            raise GitError("Failed to initialize AI client. Please check your configuration and try again.") from e

    def chat_completion(self, messages: list, **kwargs) -> str:
        """
        Create a chat completion request.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            kwargs: Additional configuration arguments.
            
        Returns:
            str: The generated response content.
            
        Raises:
            GitError: With specific error context for different failure scenarios
        """
        try:
            if self.config and self.config.verbose:
                debug_header("Sending chat completion request")
                debug_item("Messages count", str(len(messages)))
                debug_item("First message preview", messages[0]['content'][:100] + "...")
                debug_item("Timeout", f"{DEFAULT_AI_TIMEOUT}s")
            
            with Progress() as progress:
                # Create a task with 100 steps (for percentage-based progress)
                task = progress.add_task("Waiting for AI response...", total=100)
                
                # Start the request in a separate thread to allow progress updates
                from threading import Thread, Event
                from time import sleep
                
                response_event = Event()
                response_data = {"response": None, "error": None}
                
                # Add cancellation flag
                cancellation_flag = Event()
                
                def make_request():
                    try:
                        if cancellation_flag.is_set():
                            return
                        response_data["response"] = self.client.chat.completions.create(
                            model=DEFAULT_AI_MODEL,
                            messages=messages,
                            temperature=DEFAULT_TEMPERATURE,
                            timeout=DEFAULT_AI_TIMEOUT,
                            **kwargs
                        )
                    except Exception as e:
                        if not cancellation_flag.is_set():
                            response_data["error"] = e
                        response_event.set()
                
                thread = Thread(target=make_request)
                thread.start()
                
                # Update progress while waiting for response
                elapsed = 0
                while not response_event.is_set() and elapsed < DEFAULT_AI_TIMEOUT:
                    try:
                        progress.update(task, completed=int((elapsed / DEFAULT_AI_TIMEOUT) * 100))
                        sleep(0.1)
                        elapsed += 0.1
                    except KeyboardInterrupt:
                        cancellation_flag.set()
                        response_event.set()
                        raise
                
                # Complete the progress bar
                progress.update(task, completed=100)
                
                # Check for errors or timeout
                if response_data["error"]:
                    raise response_data["error"]
                if not response_event.is_set():
                    raise TimeoutError("Request timed out")
                
                response = response_data["response"]
                if not response or not response.choices:
                    raise GitError("AI model returned an empty response. Please try again.")
                    
                return response.choices[0].message.content
                
        except KeyboardInterrupt:
            if self.config and self.config.verbose:
                debug_header("AI Request Cancelled by User")
            raise GitError("AI generation cancelled by user") from None
        except TimeoutError:
            if self.config and self.config.verbose:
                debug_header("AI Request Timeout")
                debug_item("Timeout Value", str(DEFAULT_AI_TIMEOUT))
            raise GitError(
                f"AI request timed out after {DEFAULT_AI_TIMEOUT} seconds. "
                "Try increasing the timeout value in your configuration or check if Ollama is responding."
            ) from None
        except ConnectionError:
            if self.config and self.config.verbose:
                debug_header("AI Connection Failed")
                debug_item("Base URL", DEFAULT_BASE_URL)
                debug_item("Model", DEFAULT_AI_MODEL)
            raise GitError(
                "Could not connect to Ollama server. Please ensure:\n"
                "1. Ollama is running (run 'ollama serve')\n"
                "2. The model is installed (run 'ollama pull mevatron/diffsense:1.5b')\n"
                "3. The server URL is correct in your configuration"
            ) from None
        except ValueError as e:
            if self.config and self.config.verbose:
                debug_header("AI Request Parameter Error")
                debug_item("Error Message", str(e))
            if "model" in str(e).lower():
                raise GitError(
                    f"AI model '{DEFAULT_AI_MODEL}' not found. "
                    "Please run 'ollama pull mevatron/diffsense:1.5b' to install it."
                ) from e
            raise GitError(f"Invalid AI request parameters: {str(e)}") from e
        except Exception as e:
            if self.config and self.config.verbose:
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

def create_advanced_commit_message_prompt(context: Dict[str, Any], config: OptionalConfig = None) -> str:
    """Create an AI prompt for generating a commit message with repository context.

    Args:
        context: Dictionary containing git context information
        config: GitConfig instance containing configuration options
    
    Returns:
        str: Generated prompt for the AI model
    """
    # Get most common commit type from recent commits
    commit_types = context['commit_patterns']['types']
    common_type = max(commit_types.items(), key=lambda x: x[1])[0] if commit_types else "feat"
    
    # Format recent commit messages for context
    recent_messages = [c['message'] for c in context['recent_commits']]
    related_messages = [c['message'] for c in context['related_commits']]

    prompt = f"""Generate a concise and descriptive commit message for the following changes:

Changes to commit:
{context['staged_changes']}

Repository context:
- Most used commit type: {common_type}
- Recent commits:
{json.dumps(recent_messages, indent=2)}

Related commits:
{json.dumps(related_messages, indent=2) if related_messages else '[]'}

Requirements:
1. Follow the repository's commit style (type: description)
2. Be specific about what changed and why
3. Reference related work if relevant
4. Keep it concise but descriptive
"""
    if config and config.verbose:
        debug_header("Generated prompt preview:")
        debug_preview(prompt)

    return prompt

def get_commit_context(config: GitConfig) -> Dict[str, Any]:
    """
    Gather git context information for commit message generation.
    
    Args:
        config: GitConfig instance containing configuration options
    
    Returns:
        dict: Context information including staged changes, commit history, and patterns
        
    Raises:
        GitError: If unable to gather context information
    """
    try:
        if config and config.verbose:
            debug_header("Starting context gathering")
        
        # Get staged changes
        staged_changes = get_diff("staged", config)
        if not staged_changes:
            if config and config.verbose:
                debug_header("No staged changes, checking working directory")
            staged_changes = get_diff("unstaged", config)
        
        if config and config.verbose:
            debug_header("Fetching commit history")
        recent_commits = get_recent_commits(DEFAULT_NUM_RECENT_COMMITS, config)
        
        if config and config.verbose:
            debug_header("Validating commit data")
        
        # Analyze commit patterns
        commit_patterns = analyze_commit_patterns(recent_commits, config)
        
        if config and config.verbose:
            debug_header("Commit statistics:")
            debug_item("Recent commits", str(len(recent_commits)))
            debug_item("Common types", ", ".join(commit_patterns['types'].keys()))
            debug_item("Common scopes", ", ".join(commit_patterns['scopes'].keys()))
        
        if config and config.verbose:
            debug_header("Analyzing commit patterns")
        
        # Find related commits based on staged changes
        related_commits = find_related_commits(
            staged_changes,
            DEFAULT_NUM_RELATED_COMMITS,
            config
        )
        
        context = {
            'staged_changes': staged_changes,
            'recent_commits': recent_commits,
            'related_commits': related_commits,
            'commit_patterns': commit_patterns
        }
        
        if config and config.verbose:
            debug_header("Context preparation complete")
            debug_item("Context size", str(len(json.dumps(context))))
        
        return context
        
    except GitError as e:
        raise GitError(f"Failed to gather commit context: {str(e)}") from e

def create_simple_commit_message_prompt(context: Dict[str, Any], config: OptionalConfig = None) -> str:
    """Create a simple AI prompt for generating a commit message.
    
    Args:
        context: Dictionary containing git context information
        config: GitConfig instance containing configuration options
        
    Returns:
        str: Generated prompt for the AI model
    """
    prompt = f"""Generate a concise and descriptive commit message for the following changes:

{context['staged_changes']}

Requirements:
1. Follow conventional commit format (type: description)
2. Be specific about what changed
3. Keep it concise but descriptive
"""
    if config and config.verbose:
        debug_header("Generated simple prompt preview:")
        debug_preview(prompt)
    
    return prompt

def edit_commit_message(message: str, config: GitConfig) -> str:
    """Allow user to edit the AI-generated commit message.
    
    Args:
        message: The AI-generated commit message
        config: GitConfig instance containing configuration options
        
    Returns:
        str: The edited commit message
    """
    if not config.interactive:
        return message
        
    if config and config.verbose:
        debug_header("Editing commit message")
    
    # Show the message in a panel for review
    rprint(Panel(
        message,
        title="Generated Commit Message",
        border_style=COLORS['ai_message_border']
    ))
    
    # Ask if user wants to edit
    if questionary.confirm(
        "Would you like to edit this message?",
        style=questionary.Style(QUESTIONARY_STYLE)
    ).ask():
        # Let user edit the message
        edited = questionary.text(
            "Edit commit message:",
            default=message,
            style=questionary.Style(QUESTIONARY_STYLE)
        ).ask()
        
        if edited and edited.strip():
            if config and config.verbose:
                debug_header("Message edited")
                debug_preview(edited)
            return edited.strip()
    
    return message

def generate_commit_message(config: GitConfig) -> str:
    """Generate a commit message using AI.
    
    Args:
        config: GitConfig instance containing configuration options
        
    Returns:
        str: The generated commit message
        
    Raises:
        GitError: If message generation fails
    """
    try:
        if config and config.verbose:
            debug_header("Generating commit message with AI")
            debug_item("Prompt type", config.prompt_type)
        
        # Initialize AI client
        client = AIClient(config)
        
        if config and config.verbose:
            debug_header("Gathering repository context")
        context = get_commit_context(config)
        
        if config and config.verbose:
            debug_header("Creating AI prompt")
        
        # Create prompt based on configuration
        if config.prompt_type == "advanced":
            prompt = create_advanced_commit_message_prompt(context, config)
        else:
            prompt = create_simple_commit_message_prompt(context, config)
        
        # Send request to AI model
        messages = [{"role": "user", "content": prompt}]
        commit_message = client.chat_completion(messages)
        
        if config and config.verbose:
            debug_header("Generated commit message")
            debug_preview(commit_message)
        
        # Allow user to edit the message
        edited_message = edit_commit_message(commit_message, config)
        
        if config and config.verbose:
            debug_header("Edited commit message")
            debug_preview(edited_message)
        
        return edited_message
        
    except GitError as e:
        if config and config.verbose:
            debug_header("Error generating commit message")
            debug_item("Error", str(e))
        raise GitError(f"Failed to generate commit message: {str(e)}") from e
