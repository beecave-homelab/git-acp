"""Git history and diff analysis functions."""
import json
from collections import Counter
from git_acp.git.runner import run_git_command, GitError
from git_acp.config.settings import GIT_SETTINGS
from git_acp.utils import debug_item
from typing import List

def get_recent_commits(num_commits: int = None, config=None) -> list:
    """Get recent commit history."""
    if num_commits is None:
        num_commits = GIT_SETTINGS["num_recent_commits"]
    stdout, _ = run_git_command([
        "git", "log", f"-{num_commits}",
        "--pretty=format:{\"hash\":\"%h\",\"message\":\"%s\",\"author\":\"%an\",\"date\":\"%ad\"}",
        "--date=short"
    ], config)
    commits = []
    for line in stdout.splitlines():
        try:
            commits.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return commits

def get_diff(diff_type: str = "staged", config=None) -> str:
    """Retrieve git diff output."""
    if diff_type == "staged":
        stdout, _ = run_git_command(["git", "diff", "--staged"], config)
    else:
        stdout, _ = run_git_command(["git", "diff"], config)
    return stdout

def find_related_commits(diff_content: str, config=None) -> list:
    """Find commits related to the current diff."""
    all_commits = get_recent_commits(config=config)
    related_commits = []
    current_files = {line[6:] for line in diff_content.splitlines() if line.startswith(("+++ b/", "--- a/")) and "/dev/null" not in line}
    for commit in all_commits:
        try:
            stdout, _ = run_git_command(["git", "show", "--name-only", "--pretty=format:", commit["hash"]], config)
            commit_files = set(stdout.splitlines())
            if current_files & commit_files:
                related_commits.append(commit)
        except GitError:
            continue
    return related_commits

def analyze_commit_patterns(commits: list, config=None) -> dict:
    """Analyze commit messages for pattern frequency."""
    patterns = {'types': Counter(), 'scopes': Counter()}
    for commit in commits:
        message = commit.get('message', '')
        if ':' in message:
            type_part = message.split(':', 1)[0].strip().split(' ')[0]
            patterns['types'][type_part.lower()] += 1
        if '(' in message and ')' in message:
            scope = message[message.find('(') + 1:message.find(')')].strip()
            if scope:
                patterns['scopes'][scope.lower()] += 1
    return patterns

def get_commit_messages(target: str, source: str) -> dict:
    """Get commit messages between two branches.

    Args:
        target: Target branch name
        source: Source branch name

    Returns:
        Dictionary containing:
            - messages: List of clean commit messages for title generation
            - messages_with_details: List of detailed commit messages including body for display

    Raises:
        GitError: If getting commit messages fails
    """
    try:
        # First get just the messages for title generation
        output, _ = run_git_command([
            "git", "log",
            "--pretty=format:%s",  # Subject line only
            "--no-merges",
            f"{target}...{source}"
        ])
        # Clean up the messages for title generation
        messages = []
        for msg in output.splitlines():  # Split on newlines since we only have subject lines
            if msg.strip():
                # Remove any conventional commit prefixes
                if ': ' in msg:
                    msg = msg.split(': ', 1)[1]
                messages.append(msg)
        
        # Then get the full format for display, including commit body
        output_with_details, _ = run_git_command([
            "git", "log",
            "--pretty=format:%h - %B",  # Full format with hash and full message (including body)
            "--no-merges",
            f"{target}...{source}"
        ])
        messages_with_details = []
        current_message = []
        
        # Process the detailed output to handle multi-line commit messages
        for line in output_with_details.split("\n"):
            if line.startswith(tuple("0123456789abcdef")):  # New commit starts
                if current_message:  # Save previous message if exists
                    messages_with_details.append("\n".join(current_message))
                current_message = [line.strip()]
            elif line.strip():  # Add non-empty lines to current message
                current_message.append(line.strip())
        
        # Add the last message
        if current_message:
            messages_with_details.append("\n".join(current_message))
        
        # Store both versions
        return {
            "messages": messages,  # Clean messages for title generation
            "messages_with_details": messages_with_details  # Detailed messages for display
        }
    except Exception as e:
        raise GitError(f"Failed to get commit messages: {str(e)}") from e

def get_diff_between_branches(target: str, source: str) -> str:
    """Get diff between two branches.

    Args:
        target: Target branch name
        source: Source branch name

    Returns:
        Diff text

    Raises:
        GitError: If getting diff fails
    """
    try:
        stdout, _ = run_git_command([
            "git", "--no-pager", "diff",
            f"{target}...{source}"
        ])
        return stdout
    except Exception as e:
        raise GitError(f"Failed to get diff between branches: {str(e)}") from e 