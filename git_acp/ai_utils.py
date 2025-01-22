"""AI utilities module for git-acp package."""

import json
from collections import Counter
from typing import Dict, Optional, Any, TypeVar, cast

from openai import OpenAI
from rich.prompt import Confirm
from tqdm import tqdm

from git_acp.git_operations import (
    GitError, run_git_command, get_recent_commits,
    find_related_commits
)
from git_acp.formatting import (
    debug_header, debug_item, debug_json, debug_preview,
    status, success
)
from git_acp.constants import (
    DEFAULT_AI_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_NUM_RECENT_COMMITS,
    DEFAULT_NUM_RELATED_COMMITS,
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    DEFAULT_PROMPT_TYPE
)

GitConfig = TypeVar('GitConfig')

class AIClient:
    """Client for interacting with AI models via OpenAI package."""
    
    def __init__(self, config: Optional[GitConfig] = None):
        """Initialize the AI client with configuration."""
        self.config = config
        
        if self.config and self.config.verbose:
            debug_header("Initializing AI client")
            debug_item("Base URL", DEFAULT_BASE_URL)
            debug_item("Model", DEFAULT_AI_MODEL)
            debug_item("Temperature", str(DEFAULT_TEMPERATURE))
        
        try:
            self.client = OpenAI(
                base_url=DEFAULT_BASE_URL,
                api_key=DEFAULT_API_KEY,
                timeout=30.0  # Add explicit timeout
            )
        except Exception as e:
            if self.config and self.config.verbose:
                debug_header("Error initializing AI client")
                debug_item("Error", str(e))
            raise GitError(f"Failed to initialize AI client: {str(e)}") from e

    def chat_completion(self, messages: list, **kwargs) -> str:
        """
        Create a chat completion request.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            kwargs: Additional configuration arguments.
            
        Returns:
            str: The generated response content.
        """
        try:
            if self.config and self.config.verbose:
                debug_header("Sending chat completion request")
                debug_item("Messages count", str(len(messages)))
                debug_item("First message preview", messages[0]['content'][:100] + "...")
            
            response = self.client.chat.completions.create(
                model=DEFAULT_AI_MODEL,
                messages=messages,
                temperature=DEFAULT_TEMPERATURE,
                timeout=30.0,  # Add explicit timeout
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            if self.config and self.config.verbose:
                debug_header("Error in chat completion")
                debug_item("Error type", e.__class__.__name__)
                debug_item("Error message", str(e))
                if hasattr(e, 'response'):
                    debug_item("Response status", str(getattr(e.response, 'status_code', 'N/A')))
                    debug_item("Response text", str(getattr(e.response, 'text', 'N/A')))
            raise GitError(f"AI request failed: {e.__class__.__name__}: {str(e)}") from e

def create_advanced_commit_message_prompt(context: Dict[str, Any], config: Optional[GitConfig] = None) -> str:
    """
    Create a prompt for generating a commit message with advanced repository context.
    
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

def get_commit_context(config: 'GitConfig') -> Dict[str, Any]:
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

def create_simple_commit_message_prompt(staged_changes: str, config: Optional[GitConfig] = None) -> str:
    """
    Create a simple prompt for generating a commit message using just the diff.
    
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

def generate_commit_message_with_ai(config: Any) -> str:
    """
    Generate a commit message using AI.
    
    Args:
        config: GitConfig instance containing configuration options
        
    Returns:
        str: The generated commit message
        
    Raises:
        GitError: If unable to generate commit message
    """
    try:
        if config.verbose:
            debug_header("\nStarting commit message generation")

        context = get_commit_context(config)
        prompt_type = DEFAULT_PROMPT_TYPE.lower()

        if config.verbose:
            debug_header("Creating AI prompt")
            debug_item("Prompt type", prompt_type)

        # Select prompt based on configuration
        if prompt_type == "simple":
            prompt = create_simple_commit_message_prompt(context['staged_changes'], config)
        else:  # "advanced" is the default
            prompt = create_advanced_commit_message_prompt(context, config)

        if config.verbose:
            debug_header("Sending request to AI service")
            debug_item("Model", DEFAULT_AI_MODEL)

        ai_client = AIClient(config)
        with status("Generating commit message..."):
            message = ai_client.chat_completion(
                messages=[{'role': 'user', 'content': prompt}]
            )

            if config.verbose:
                debug_header("Received response from AI service")
                debug_item("Generated message")
                debug_preview(message)

            return message.strip()

    except GitError as e:
        raise GitError(f"Failed to generate commit message: {e}") from e
