"""AI utilities module for git-acp package."""

import json
from ollama import chat, ChatResponse
from git_acp.git_operations import (
    GitError, run_git_command, get_recent_commits,
    analyze_commit_patterns, find_related_commits
)
from rich.console import Console

console = Console()

def generate_commit_message_with_ollama(config) -> str:
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
        with console.status("[bold green]Generating commit message with Ollama..."):
            # Get the diff for context
            stdout, _ = run_git_command(["git", "diff", "--staged"])
            if not stdout.strip():
                stdout, _ = run_git_command(["git", "diff"])
            
            if not stdout:
                raise GitError("No changes detected to generate commit message from.")
            
            # Get commit history context
            recent_commits = get_recent_commits(5)  # Get 5 most recent commits
            patterns = analyze_commit_patterns()
            related_commits = find_related_commits(stdout, 3, config)  # Find 3 most relevant commits
            
            # Filter out any commits that don't have all required fields
            recent_commits = [c for c in recent_commits if all(k in c for k in ['hash', 'message', 'author', 'date'])]
            related_commits = [c for c in related_commits if all(k in c for k in ['hash', 'message', 'author', 'date'])]
            
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
            
            # Create a prompt that includes the context
            prompt = f"""Based on the following context, generate a concise and descriptive commit message:

1. Changes made (git diff):
{context['diff']}

2. Recent commit messages for context:
{json.dumps([c['message'] for c in context['recent_commits']], indent=2)}

3. Common commit patterns in this repository:
- Most used commit types: {json.dumps(dict(list(context['commit_patterns']['types'].items())[:3]), indent=2)}
- Typical message length: {list(context['commit_patterns']['typical_length'].keys())[0]} characters

4. Related commits to these changes:
{json.dumps([c['message'] for c in context['related_commits']], indent=2) if context['related_commits'] else '[]'}

Generate a commit message that:
1. Follows the existing commit message style
2. Is consistent with the repository's patterns
3. References related work if relevant
4. Is concise but descriptive
"""
            
            try:
                response: ChatResponse = chat(
                    model='mevatron/diffsense:1.5b',
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response.message.content.strip()
            except Exception as e:
                raise GitError(f"Ollama failed: {str(e)}")
            
    except GitError as e:
        raise GitError(f"Failed to generate commit message: {e}") 