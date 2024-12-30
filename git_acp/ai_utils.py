"""AI utilities module for git-acp package."""

import json
from collections import Counter
from typing import Dict, Optional, Any

from ollama import chat, ChatResponse

from git_acp.git_operations import (
    GitError, run_git_command, get_recent_commits,
    find_related_commits
)
from git_acp.formatting import (
    debug_header, debug_item, debug_json, debug_preview,
    status
)

def create_commit_message_prompt(context: Dict[str, Any], config: Optional[Any] = None) -> str:
    """
    Create a prompt for the AI model to generate a commit message.
    
    Args:
        context: Dictionary containing git context information:
                - diff: Current changes
                - recent_commits: List of recent commits
                - commit_patterns: Dictionary of commit patterns
                - related_commits: List of related commits
        config: Configuration object with verbose flag
    
    Returns:
        str: The formatted prompt for the AI model
    """
    if config and config.verbose:
        debug_header("Creating commit message prompt:")
        debug_item("Recent commits found", str(len(context['recent_commits'])))
        debug_item("Related commits found", str(len(context['related_commits'])))
        debug_header("Commit patterns:")
        debug_json(context['commit_patterns'])

    # Get the most common commit type for reference
    common_types = list(context['commit_patterns']['types'].items())
    common_types.sort(key=lambda x: x[1], reverse=True)
    common_type = common_types[0][0] if common_types else "feat"

    # Format recent commits more concisely
    recent_messages = [c['message'] for c in context['recent_commits']]
    related_messages = [c['message'] for c in context['related_commits']]

    prompt = f"""Generate a concise and descriptive commit message for the following changes:

Changes to commit:
{context['diff']}

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

def get_commit_context(config: Any) -> Dict[str, Any]:
    """
    Gather git context information for commit message generation.
    
    Args:
        config: GitConfig instance containing configuration options
    
    Returns:
        dict: Context information including diff, commits, and patterns
        
    Raises:
        GitError: If unable to gather context information
    """
    if config.verbose:
        debug_header("Starting context gathering")

    # Get the diff for context
    stdout, _ = run_git_command(["git", "diff", "--staged"], config)
    if not stdout.strip():
        if config.verbose:
            debug_header("No staged changes, checking working directory")
        stdout, _ = run_git_command(["git", "diff"], config)

    if not stdout:
        raise GitError("No changes detected to generate commit message from.")

    if config.verbose:
        debug_header("Fetching commit history")

    # Get commit history context - fetch once and reuse
    recent_commits = get_recent_commits(5, config)  # Get 5 most recent commits
    related_commits = find_related_commits(stdout, 3, config)  # Find 3 most relevant commits

    if config.verbose:
        debug_header("Validating commit data")

    # Filter out any commits that don't have all required fields
    recent_commits = [
        c for c in recent_commits
        if all(k in c for k in ['hash', 'message', 'author', 'date'])
    ]
    related_commits = [
        c for c in related_commits
        if all(k in c for k in ['hash', 'message', 'author', 'date'])
    ]

    if config.verbose:
        debug_header("Commit statistics:")
        debug_item("Valid recent commits", str(len(recent_commits)))
        debug_item("Valid related commits", str(len(related_commits)))

    # Analyze commit patterns using the recent commits we already have
    if config.verbose:
        debug_header("Analyzing commit patterns")

    patterns = {
        'commit_types': Counter(),
        'message_length': Counter(),
        'authors': Counter()
    }

    for commit in recent_commits:
        message = commit['message']
        if ': ' in message:
            commit_type = message.split(': ')[0]
            patterns['commit_types'][commit_type] += 1
            if config and config.verbose:
                debug_item("Found commit type", commit_type)

        length_category = len(message) // 10 * 10  # Group by tens
        patterns['message_length'][length_category] += 1
        patterns['authors'][commit['author']] += 1

    # Prepare context for the model
    context = {
        "diff": stdout,
        "recent_commits": recent_commits,
        "commit_patterns": {
            "types": dict(patterns['commit_types']),
            "typical_length": dict(patterns['message_length']),
        },
        "related_commits": related_commits
    }

    if config.verbose:
        debug_header("Context preparation complete")

    return context

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
    try:
        with status("Generating commit message with Ollama..."):
            if config.verbose:
                debug_header("\nStarting commit message generation")

            context = get_commit_context(config)

            if config.verbose:
                debug_header("Creating AI prompt")
            prompt = create_commit_message_prompt(context, config)

            if config.verbose:
                debug_header("Sending request to Ollama")
                debug_item("Model", "mevatron/diffsense:1.5b")

            try:
                response: ChatResponse = chat(
                    model='mevatron/diffsense:1.5b',
                    messages=[{'role': 'user', 'content': prompt}]
                )
                message = response.message.content.strip()

                if config.verbose:
                    debug_header("Received response from Ollama")
                    debug_item("Generated message")
                    debug_preview(message)

                return message
            except Exception as e:
                raise GitError(f"Ollama failed: {str(e)}") from e

    except GitError as e:
        raise GitError(f"Failed to generate commit message: {e}") from e
