"""Low-level Git command runner and error handler."""
import subprocess
import shlex
import signal
import sys
from typing import Optional
from git_acp.utils import debug_header, debug_item
from git_acp.config.settings import TERMINAL_SETTINGS

class GitError(Exception):
    """Custom exception for git-related errors.
    
    Attributes:
        message: The error message
        suggestion: Optional suggestion for fixing the error
        context: Optional context about where/why the error occurred
    """
    def __init__(self, message: str, suggestion: Optional[str] = None, context: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        self.context = context
        
        # Build the full error message
        parts = []
        
        # Add context and message
        if context:
            parts.append(f"{context}:")
        parts.append(message)
        
        # Add suggestion if provided, combining multiple suggestions with semicolons
        if suggestion:
            suggestions = suggestion.split('\n')
            formatted_suggestions = '; '.join(s.strip() for s in suggestions if s.strip())
            if formatted_suggestions:
                parts.append(f"\nSuggestion: {formatted_suggestions}")
        
        # Join all parts
        super().__init__('\n'.join(parts))

def run_git_command(command: list, config=None) -> tuple:
    """
    Execute a git command.
    
    Args:
        command: List of command parts.
        config: Optional configuration.
    
    Returns:
        Tuple of (stdout, stderr).
    
    Raises:
        GitError: On failure.
    """
    try:
        if config and config.verbose:
            debug_header("Executing Git command")
            debug_item("Command", ' '.join(command))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            # Common git errors with specific suggestions
            error_map = {
                "not a git repository": (
                    "Not a git repository.",
                    "Run 'git init' to create a new repository or ensure you're in the correct directory."
                ),
                "nothing to commit": (
                    "No changes to commit.",
                    "Stage some changes first with 'git add' or create new files."
                ),
                "permission denied": (
                    "Permission denied.",
                    "Check your file permissions and Git credentials."
                ),
                "branch .* not found": (
                    "Branch not found.",
                    "Create the branch first or check the branch name."
                ),
                "remote .* not found": (
                    "Remote not found.",
                    "Add the remote first with 'git remote add' or check the remote name."
                ),
                "pull request already exists": (
                    "Pull request already exists.",
                    "Check existing pull requests or create a new branch for your changes."
                ),
            }
            
            for pattern, (message, suggestion) in error_map.items():
                if pattern in stderr.lower():
                    raise GitError(message, suggestion=suggestion)
            
            # Generic git error
            raise GitError(
                f"Git command failed: {stderr.strip()}",
                suggestion="Check the error message above and ensure your Git configuration is correct."
            )
        return stdout.strip(), stderr.strip()
    except FileNotFoundError:
        raise GitError(
            "Git is not installed or not in PATH.",
            suggestion="Install Git or add it to your system PATH."
        )
    except Exception as e:
        raise GitError(
            f"Failed to execute git command: {str(e)}",
            suggestion="Check your Git installation and configuration."
        ) from e

def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful interruption."""
    def signal_handler(signum, frame):
        from git_acp.git.status import unstage_files
        unstage_files()
        print("Operation cancelled by user.")
        sys.exit(1)
    signal.signal(signal.SIGINT, signal_handler) 