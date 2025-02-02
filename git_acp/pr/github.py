"""
GitHub API integration for creating pull requests.
"""

import os
from typing import Dict, Optional

import requests

from git_acp.git.runner import GitError


def get_github_token() -> str:
    """Get GitHub token from environment variables.

    Returns:
        GitHub token string

    Raises:
        GitError: If GitHub token is not found
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitError("GitHub token not found. Please set GITHUB_TOKEN environment variable.")
    return token


def get_repo_info() -> tuple[str, str]:
    """Extract repository owner and name from git remote URL.

    Returns:
        Tuple of (owner, repo_name)

    Raises:
        GitError: If repository information cannot be extracted
    """
    try:
        # Get the remote URL
        from git_acp.git.runner import run_git_command
        remote_url, _ = run_git_command(["git", "remote", "get-url", "origin"])
        
        # Extract owner and repo from URL
        # Handles both HTTPS and SSH URLs:
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        if remote_url.startswith("https://"):
            parts = remote_url.split("/")
            owner = parts[-2]
            repo = parts[-1]
        else:
            # Handle SSH URL format
            parts = remote_url.split(":")
            owner_repo = parts[-1]
            owner, repo = owner_repo.split("/")
            
        # Remove .git suffix if present
        repo = repo.rstrip(".git")
        
        return owner, repo
    except Exception as e:
        raise GitError(f"Failed to extract repository information: {str(e)}") from e


def create_pull_request(
    base: str,
    head: str,
    title: str,
    body: str,
    draft: bool = False
) -> Dict:
    """Create a pull request on GitHub.

    Args:
        base: Target branch name
        head: Source branch name
        title: PR title
        body: PR description in markdown format
        draft: Whether to create as draft PR

    Returns:
        Dictionary containing PR information including URL

    Raises:
        GitError: If PR creation fails
    """
    token = get_github_token()
    owner, repo = get_repo_info()
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
        "draft": draft
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise GitError(f"Failed to create pull request: {str(e)}") from e


def list_pull_requests(state: str = "open") -> list[Dict]:
    """List pull requests from GitHub.

    Args:
        state: PR state to filter by ('open', 'closed', 'all')

    Returns:
        List of dictionaries containing PR information

    Raises:
        GitError: If PR listing fails
    """
    token = get_github_token()
    owner, repo = get_repo_info()
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "state": state
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
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
    token = get_github_token()
    owner, repo = get_repo_info()
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.patch(url, headers=headers, json={"state": "closed"})
        response.raise_for_status()
    except Exception as e:
        raise GitError(f"Failed to delete pull request: {str(e)}") from e 