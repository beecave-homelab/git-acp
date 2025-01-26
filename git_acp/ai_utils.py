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

from git_acp.git_operations import (
    GitError, run_git_command, get_recent_commits,
    get_diff,
    find_related_commits
)
from git_acp.formatting import (
    debug_header, debug_item, debug_preview
)
from git_acp.constants import (
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
from git_acp.types import (
    GitConfig, OptionalConfig, PromptType
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
            debug_header("AI Client Initialization Failed")
            debug_item("Error Type", "ValueError")
            debug_item("Error Message", str(e))
            if "Invalid URL" in str(e):
                raise GitError("Invalid Ollama server URL. Please check your configuration.") from e
            raise GitError("Invalid AI configuration. Please verify your settings.") from e
        except ConnectionError:
            debug_header("AI Client Connection Failed")
            debug_item("Error Type", "ConnectionError")
            debug_item("Base URL", DEFAULT_BASE_URL)
            raise GitError("Could not connect to Ollama server. Please ensure it's running.") from None
        except Exception as e:
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
                task = progress.add_task("Waiting for AI response...", total=1)
                response = self.client.chat.completions.create(
                    model=DEFAULT_AI_MODEL,
                    messages=messages,
                    temperature=DEFAULT_TEMPERATURE,
                    timeout=DEFAULT_AI_TIMEOUT,
                    **kwargs
                )
                
                if not response or not response.choices:
                    raise GitError("AI model returned an empty response. Please try again.")
                    
                return response.choices[0].message.content
                
        except TimeoutError:
            debug_header("AI Request Timeout")
            debug_item("Timeout Value", str(DEFAULT_AI_TIMEOUT))
            raise GitError(
                f"AI request timed out after {DEFAULT_AI_TIMEOUT} seconds. "
                "Try increasing the timeout value in your configuration or check if Ollama is responding."
            ) from None
        except ConnectionError:
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
            debug_header("AI Request Parameter Error")
            debug_item("Error Message", str(e))
            if "model" in str(e).lower():
                raise GitError(
                    f"AI model '{DEFAULT_AI_MODEL}' not found. "
                    "Please run 'ollama pull mevatron/diffsense:1.5b' to install it."
                ) from e
            raise GitError(f"Invalid AI request parameters: {str(e)}") from e
        except Exception as e:
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
    if config.verbose:
        debug_header("Starting context gathering")

    # Get the staged changes for context
    staged_diff, _ = run_git_command(["git", "diff", "--staged"], config)
    if not staged_diff.strip():
        if config.verbose:
            debug_header("No staged changes, checking working directory")
        staged_diff, _ = run_git_command(["git", "diff"], config)

    if not staged_diff:
        raise GitError("No changes detected to generate commit message from.")

    if config.verbose:
        debug_header("Fetching commit history")

    # Get commit history context - fetch once and reuse
    recent_commit_history = get_recent_commits(DEFAULT_NUM_RECENT_COMMITS, config)
    related_commit_history = find_related_commits(staged_diff, DEFAULT_NUM_RELATED_COMMITS, config)

    if config.verbose:
        debug_header("Validating commit data")

    # Filter out any commits that don't have all required fields
    valid_recent_commits = [
        commit for commit in recent_commit_history
        if all(key in commit for key in ['hash', 'message', 'author', 'date'])
    ]
    valid_related_commits = [
        commit for commit in related_commit_history
        if all(key in commit for key in ['hash', 'message', 'author', 'date'])
    ]

    if config.verbose:
        debug_header("Commit statistics:")
        debug_item("Valid recent commits", str(len(valid_recent_commits)))
        debug_item("Valid related commits", str(len(valid_related_commits)))

    # Analyze commit patterns using the recent commits we already have
    if config.verbose:
        debug_header("Analyzing commit patterns")

    commit_patterns = {
        'commit_types': Counter(),
        'message_length': Counter(),
        'authors': Counter()
    }

    for commit in valid_recent_commits:
        message = commit['message']
        if ': ' in message:
            commit_type = message.split(': ')[0]
            commit_patterns['commit_types'][commit_type] += 1
            if config and config.verbose:
                debug_item("Found commit type", commit_type)

        message_length = len(message) // 10 * 10  # Group by tens
        commit_patterns['message_length'][message_length] += 1
        commit_patterns['authors'][commit['author']] += 1

    # Prepare context for the model
    commit_context = {
        "staged_changes": staged_diff,
        "recent_commits": valid_recent_commits,
        "commit_patterns": {
            "types": dict(commit_patterns['commit_types']),
            "typical_length": dict(commit_patterns['message_length']),
        },
        "related_commits": valid_related_commits
    }

    if config.verbose:
        debug_header("Context preparation complete")

    return commit_context

def create_simple_commit_message_prompt(staged_changes: str, config: OptionalConfig = None) -> str:
    """Create a simple AI prompt for generating a commit message from diff.

    Args:
        staged_changes: The git diff output
        config: GitConfig instance containing configuration options
    
    Returns:
        str: Generated prompt for the AI model
    """
    prompt = f"""Generate a concise and descriptive commit message for the following changes:

Changes to commit:
{staged_changes}

Requirements:
1. Follow the conventional commit format (type: description)
2. Be specific about what changed and why
3. Keep it concise but descriptive
"""
    if config and config.verbose:
        debug_header("Generated simple prompt preview:")
        debug_preview(prompt)

    return prompt

def generate_commit_message_with_ai(config: GitConfig) -> str:
    """
    Generate a commit message using AI.
    
    Args:
        config: GitConfig instance containing configuration options
        
    Returns:
        str: Generated commit message
    """
    if config.verbose:
        debug_header("Generating commit message with AI")
    
    try:
        client = AIClient(config)
        
        # Get repository context
        with Progress() as progress:
            task = progress.add_task("Gathering repository context...", total=1)
            context = get_commit_context(config)
        
        # Create prompt based on context
        with Progress() as progress:
            task = progress.add_task("Creating AI prompt...", total=1)
            if DEFAULT_PROMPT_TYPE == "advanced":
                prompt = create_advanced_commit_message_prompt(context, config)
            else:
                prompt = create_simple_commit_message_prompt(context['staged_changes'], config)
        
        # Generate commit message
        rprint(f"[{COLORS['bold']}]🤖 Generating commit message with AI...[/{COLORS['bold']}]")
        messages = [{"role": "user", "content": prompt}]
        
        try:
            commit_message = client.chat_completion(messages)
            rprint(f"[{COLORS['success']}]✓ Commit message generated successfully[/{COLORS['success']}]")
        except GitError as e:
            if "timed out" in str(e).lower():
                # If timeout occurs, try with a simpler prompt
                warning("AI request timed out. Trying with a simpler prompt...")
                prompt = create_simple_commit_message_prompt(context['staged_changes'], config)
                messages = [{"role": "user", "content": prompt}]
                commit_message = client.chat_completion(messages)
                rprint(f"[{COLORS['success']}]✓ Commit message generated with simpler prompt[/{COLORS['success']}]")
            else:
                raise
        
        if config.verbose:
            debug_header("Generated commit message")
            debug_item("Message", commit_message[:100] + "..." if len(commit_message) > 100 else commit_message)
        
        # Allow interactive editing if enabled
        if config.interactive:
            if not config.use_ollama:
                raise GitError("Interactive mode requires --ollama flag")
                
            # Calculate a fixed width for both panel and text input
            display_width = min(max(len(line) for line in commit_message.split('\n')) + 4, TERMINAL_WIDTH - 20)
                
            # Show the AI-generated message and allow editing
            rprint(f"\n[{COLORS['ai_message_header']}]AI-generated commit message:[/{COLORS['ai_message_header']}]")
            rprint(Panel.fit(
                commit_message,
                border_style=COLORS['ai_message_border'],
                width=display_width,
                padding=(0, 1)  # Add horizontal padding
            ))
            
            # Ask if user wants to edit
            if questionary.confirm(
                "Would you like to edit this commit message?",
                style=questionary.Style(QUESTIONARY_STYLE)
            ).ask():
                # Show editing instructions
                rprint(f"\n[{COLORS['instruction_text']}](Finish editing with [{COLORS['key_combination']}]'Alt+Enter'[/{COLORS['key_combination']}] or [{COLORS['key_combination']}]'Esc then Enter'[/{COLORS['key_combination']}])[/{COLORS['instruction_text']}]")
                
                # Use questionary text input with the AI message as default
                edited_message = questionary.text(
                    "Edit commit message:\n",  # Add newline to place input on next line
                    default=commit_message,
                    style=questionary.Style([
                        *QUESTIONARY_STYLE,
                        ('text', 'yellow'),  # Make input text yellow for better visibility
                        ('answer', 'yellow'),  # Make answer text yellow for consistency
                        ('question', '')  # Remove question styling to maximize width
                    ]),
                    multiline=True,
                    qmark='',  # Remove the question mark to maximize width
                    instruction='',  # Remove instruction to maximize width
                ).ask()
                
                if edited_message is not None:
                    commit_message = edited_message.strip()
                    if config.verbose:
                        debug_header("Edited commit message")
                        debug_item("Message", commit_message[:100] + "..." if len(commit_message) > 100 else commit_message)
        
        return commit_message
    
    except Exception as e:
        if config.verbose:
            debug_header("Error generating commit message")
            debug_item("Error", str(e))
        raise GitError(f"Failed to generate commit message: {str(e)}") from e
