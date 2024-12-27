"""AI utilities module for git-acp package."""

import subprocess
from git_acp.git_operations import GitError, run_git_command
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
            
            process = subprocess.Popen(
                ["ollama", "run", "mevatron/diffsense:1.5b"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=stdout)
            if process.returncode != 0:
                raise GitError(f"Ollama failed: {stderr}")
            return stdout.strip()
    except (subprocess.SubprocessError, GitError) as e:
        raise GitError(f"Failed to generate commit message: {e}") 