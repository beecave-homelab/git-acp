"""
GitHub API integration for creating pull requests.
"""

import re
from typing import Dict

import requests

from git_acp.git.exceptions import GitError
from git_acp.git.core import run_git_command
from git_acp.config import GITHUB_TOKEN, DEFAULT_AI_TIMEOUT


def get_repo_info() -> Dict[str, str]:
    """Get repository information from remote URL.

    Returns:
        Dict with owner and repo name

    Raises:
        GitError: If getting repo info fails
    """
    try:
        stdout, _ = run_git_command(["git", "remote", "get-url", "origin"])
        url = stdout.strip()

        # Parse SSH or HTTPS URL
        if url.startswith("git@"):
            pattern = r"git@github\.com:([^/]+)/(.+)\.git"
        else:
            pattern = r"https://github\.com/([^/]+)/(.+)\.git"

        match = re.match(pattern, url)
        if not match:
            raise GitError(
                "Invalid GitHub repository URL",
                suggestion="Ensure remote 'origin' points to a GitHub repository",
            )

        return {"owner": match.group(1), "repo": match.group(2)}
    except Exception as e:
        raise GitError(f"Failed to get repository information: {str(e)}") from e


def create_pull_request(
    title: str,
    body: str,
    base_branch: str,
    head_branch: str,
    draft: bool = False,
) -> str:
    """Create a pull request on GitHub.

    Args:
        title: PR title
        body: PR description
        base_branch: Target branch
        head_branch: Source branch
        draft: Whether to create as draft

    Returns:
        URL of created PR

    Raises:
        GitError: If creating PR fails
    """
    if not GITHUB_TOKEN:
        raise GitError(
            "GitHub token not found",
            suggestion="Set GITHUB_TOKEN environment variable",
        )

    try:
        repo_info = get_repo_info()
        api_url = (
            f"https://api.github.com/repos/"
            f"{repo_info['owner']}/{repo_info['repo']}/pulls"
        )

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "draft": draft,
        }

        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            timeout=DEFAULT_AI_TIMEOUT,
        )
        if response.status_code == 201:
            pr_data = response.json()
            return pr_data["html_url"]
        else:
            error_msg = response.json().get("message", "Unknown error")
            raise GitError(
                f"Failed to create PR: {error_msg}",
                suggestion="Check your GitHub token and repository permissions",
            )
    except requests.exceptions.RequestException as e:
        raise GitError(f"Network error creating PR: {str(e)}") from e
    except Exception as e:
        raise GitError(f"Error creating PR: {str(e)}") from e


def list_pull_requests(state: str = "open") -> list[Dict]:
    """List pull requests from GitHub.

    Args:
        state: PR state to filter by ('open', 'closed', 'all')

    Returns:
        List of dictionaries containing PR information

    Raises:
        GitError: If PR listing fails
    """
    token = GITHUB_TOKEN
    if not token:
        raise GitError(
            "GitHub token not found",
            suggestion="Set GITHUB_TOKEN environment variable",
        )

    try:
        repo_info = get_repo_info()
        api_url = (
            f"https://api.github.com/repos/"
            f"{repo_info['owner']}/{repo_info['repo']}/pulls"
        )
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        params = {"state": state}

        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise GitError(f"Failed to list pull requests: {str(e)}") from e


def delete_pull_request(pr_number: int) -> None:
    """Delete a pull request on GitHub.

    Args:
        pr_number: The PR number to delete

    Raises:
        GitError: If PR deletion fails
    """
    token = GITHUB_TOKEN
    if not token:
        raise GitError(
            "GitHub token not found",
            suggestion="Set GITHUB_TOKEN environment variable",
        )

    try:
        repo_info = get_repo_info()
        api_url = (
            f"https://api.github.com/repos/"
            f"{repo_info['owner']}/{repo_info['repo']}/pulls/{pr_number}"
        )
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.patch(
            api_url, headers=headers, json={"state": "closed"}, timeout=30
        )
        response.raise_for_status()
    except Exception as e:
        raise GitError(f"Failed to delete pull request: {str(e)}") from e
