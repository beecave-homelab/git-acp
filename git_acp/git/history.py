"""Git history and diff analysis functions."""
import json
from collections import Counter
from git_acp.git.runner import run_git_command, GitError
from git_acp.config.settings import GIT_SETTINGS
from git_acp.utils import debug_item

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