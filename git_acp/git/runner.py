"""Low-level Git command runner and error handler."""
import subprocess
import shlex
import signal
import sys
from git_acp.utils import debug_header, debug_item
from git_acp.config.settings import TERMINAL_SETTINGS

class GitError(Exception):
    """Custom exception for git-related errors."""
    pass

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
            for pattern, message in {
                "not a git repository": "Not a git repository.",
                "nothing to commit": "No changes to commit.",
                "permission denied": "Permission denied.",
            }.items():
                if pattern in stderr.lower():
                    raise GitError(message)
            raise GitError(f"Git command failed: {stderr.strip()}")
        return stdout.strip(), stderr.strip()
    except FileNotFoundError:
        raise GitError("Git is not installed or not in PATH.")
    except Exception as e:
        raise GitError(f"Failed to execute git command: {str(e)}") from e

def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful interruption."""
    def signal_handler(signum, frame):
        from git_acp.git.status import unstage_files
        unstage_files()
        print("Operation cancelled by user.")
        sys.exit(1)
    signal.signal(signal.SIGINT, signal_handler) 