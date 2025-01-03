"""AI utilities module for git-acp package."""

import json
from collections import Counter
from typing import Dict, Optional, Any, TypeVar, cast

from ollama import chat, pull, ChatResponse
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

GitConfig = TypeVar('GitConfig')

def create_commit_message_prompt(context: Dict[str, Any], config: Optional[GitConfig] = None) -> str:
    """
    Create a prompt for generating a commit message.
    
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
    recent_commit_history = get_recent_commits(5, config)  # Get 5 most recent commits
    related_commit_history = find_related_commits(staged_diff, 3, config)  # Find 3 most relevant commits

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

def pull_ollama_model(model_name: str, config: Optional[GitConfig] = None) -> bool:
    """
    Pull an Ollama model after user confirmation.
    
    Args:
        model_name: Name of the model to pull
        config: GitConfig instance containing configuration options
        
    Returns:
        bool: True if model was pulled successfully, False otherwise
    """
    try:
        if config and config.verbose:
            debug_header("Model not found, asking for confirmation to pull")
        
        if not Confirm.ask(f"Model '{model_name}' not found. Would you like to pull it now?"):
            return False
            
        with status(f"Pulling model {model_name}..."):
            current_digest, bars = '', {}
            for progress in pull(model_name, stream=True):
                digest = progress.get('digest', '')
                if digest != current_digest and current_digest in bars:
                    bars[current_digest].close()

                if not digest:
                    if status_msg := progress.get('status'):
                        if config and config.verbose:
                            debug_item("Status", status_msg)
                    continue

                if digest not in bars and (total := progress.get('total')):
                    bars[digest] = tqdm(total=total, desc=f'Pulling {digest[7:19]}', unit='B', unit_scale=True)

                if completed := progress.get('completed'):
                    bars[digest].update(completed - bars[digest].n)

                current_digest = digest

            # Close any remaining progress bars
            for bar in bars.values():
                bar.close()

            success(f"Model {model_name} pulled successfully")
            return True
            
    except Exception as e:
        raise GitError(f"Failed to pull model: {str(e)}") from e

def generate_commit_message_with_ollama(config: Any) -> str:
    """
    Generate a commit message using Ollama AI.
    
    Args:
        config: GitConfig instance containing configuration options
        
    Returns:
        str: The generated commit message
        
    Raises:
        GitError: If unable to generate commit message
    """
    MODEL_NAME = 'mevatron/diffsense:1.5b'
    
    try:
        if config.verbose:
            debug_header("\nStarting commit message generation")

        context = get_commit_context(config)

        if config.verbose:
            debug_header("Creating AI prompt")
        prompt = create_commit_message_prompt(context, config)

        if config.verbose:
            debug_header("Sending request to Ollama")
            debug_item("Model", MODEL_NAME)

        try:
            response: ChatResponse = chat(
                model=MODEL_NAME,
                messages=[{'role': 'user', 'content': prompt}]
            )
            with status("Generating commit message with Ollama..."):
                message = response.message.content.strip()

                if config.verbose:
                    debug_header("Received response from Ollama")
                    debug_item("Generated message")
                    debug_preview(message)

                return message
        except Exception as e:
            error_msg = str(e).lower()
            if "model not found" in error_msg or "try pulling it first" in error_msg:
                # Try to pull the model if not found
                if pull_ollama_model(MODEL_NAME, config):
                    # Retry the request after pulling the model
                    response: ChatResponse = chat(
                        model=MODEL_NAME,
                        messages=[{'role': 'user', 'content': prompt}]
                    )
                    with status("Generating commit message with Ollama..."):
                        message = response.message.content.strip()
                        return message
                else:
                    raise GitError("Model not available and user declined to pull it")
            raise GitError(f"Ollama failed: {str(e)}") from e

    except GitError as e:
        raise GitError(f"Failed to generate commit message: {e}") from e
