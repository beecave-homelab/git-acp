"""
CLI command for PR workflow.
"""

import click
from typing import Optional

from git_acp.config.settings import GIT_SETTINGS
from git_acp.config.constants import DEFAULT_PR_AI_MODEL
from git_acp.git.history import get_commit_messages, get_diff_between_branches
from git_acp.git.status import get_name_status_changes
from git_acp.pr.builder import (
    build_pr_markdown,
    generate_pr_title,
    generate_pr_summary,
    generate_code_changes,
    generate_reason_for_changes,
    generate_test_plan,
    generate_additional_notes
)
from git_acp.pr.github import create_pull_request
from git_acp.utils.formatting import debug_header, debug_item


@click.command()
@click.option(
    "--source",
    required=True,
    help="Feature branch name"
)
@click.option(
    "--target",
    default=GIT_SETTINGS["default_branch"],
    help="Target (base) branch"
)
@click.option(
    "-o",
    "--ollama",
    is_flag=True,
    help="Use Ollama AI to generate PR description (uses a larger model than commit messages)"
)
@click.option(
    "--draft",
    is_flag=True,
    help="Create as draft PR"
)
def pr(source: str, target: str, ollama: bool, draft: bool) -> None:
    """Create a pull request with an AI-generated description.

    \b
    This command:
    1. Analyzes commits and changes between branches
    2. Generates a comprehensive PR description (with AI if --ollama is used)
    3. Creates a pull request on GitHub

    \b
    The AI-generated description includes:
    - Summary of changes
    - Detailed code analysis
    - Testing recommendations
    - Additional notes and considerations
    """
    debug_header("Creating Pull Request")
    debug_item("Source branch", source)
    debug_item("Target branch", target)
    debug_item("AI enabled", str(ollama))
    debug_item("Draft PR", str(draft))
    if ollama:
        debug_item("AI Model", DEFAULT_PR_AI_MODEL)

    # 1. Gather git data
    commit_messages_list = get_commit_messages(target, source)
    commit_messages = "\n".join(f"- {msg}" for msg in commit_messages_list)
    diff_text = get_diff_between_branches(target, source)
    changes = get_name_status_changes(target, source)
    
    added_files = "\n".join(f"- {f}" for f in changes.get("added", []))
    modified_files = "\n".join(f"- {f}" for f in changes.get("modified", []))
    deleted_files = "\n".join(f"- {f}" for f in changes.get("deleted", []))

    # 2. Generate PR sections
    if ollama:
        debug_header("Generating PR Content with AI")
        git_data = {
            "commit_messages": commit_messages_list,
            "diff": diff_text,
            "model": DEFAULT_PR_AI_MODEL  # Use PR-specific model
        }
        
        title = generate_pr_title(git_data)
        summary = generate_pr_summary(diff_text, commit_messages_list)
        code_changes = generate_code_changes(diff_text)
        reason = generate_reason_for_changes(commit_messages_list, diff_text)
        test_plan = generate_test_plan(diff_text)
        additional_notes = generate_additional_notes(commit_messages_list, diff_text)
    else:
        debug_header("Using Basic PR Content")
        title = f"PR: {commit_messages_list[0]}" if commit_messages_list else "Pull Request"
        summary = "Summary derived from commit messages."
        code_changes = diff_text[:500] + "\n...[diff excerpt]"
        reason = "Reason derived from commit messages."
        test_plan = "Describe your test plan here..."
        additional_notes = "Additional notes here..."

    # 3. Build PR markdown
    pr_markdown = build_pr_markdown(
        title=title,
        summary=summary,
        commit_messages=commit_messages,
        added_files=added_files,
        modified_files=modified_files,
        deleted_files=deleted_files,
        code_changes=code_changes,
        reason_for_changes=reason,
        test_plan=test_plan,
        additional_notes=additional_notes
    )

    # 4. Create PR on GitHub
    debug_header("Creating PR on GitHub")
    try:
        pr_response = create_pull_request(
            base=target,
            head=source,
            title=title,
            body=pr_markdown,
            draft=draft
        )
        click.echo(f"\nPull Request created successfully: {pr_response.get('html_url')}")
    except Exception as e:
        click.echo(f"\nError creating pull request: {str(e)}", err=True) 