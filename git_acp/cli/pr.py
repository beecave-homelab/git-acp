"""
CLI command for PR workflow.
"""

import click
import sys
from typing import Optional
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from git_acp.config.settings import GIT_SETTINGS
from git_acp.config.constants import (
    DEFAULT_PR_AI_MODEL,
    QUESTIONARY_STYLE,
    COLORS,
    TERMINAL_WIDTH,
    DEFAULT_BRANCH  # Import directly without alias
)
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
from git_acp.pr.github import create_pull_request, list_pull_requests, delete_pull_request
from git_acp.utils.formatting import debug_header, debug_item
from git_acp.utils.types import GitConfig

console = Console(width=TERMINAL_WIDTH)

@click.command()
@click.option(
    "-s",
    "--source",
    help="Feature branch name"
)
@click.option(
    "-t",
    "--target",
    help=f"Target (base) branch (default: {DEFAULT_BRANCH}, from GIT_ACP_DEFAULT_BRANCH)",
    default=DEFAULT_BRANCH,
)
@click.option(
    "-o",
    "--ollama",
    is_flag=True,
    help=f"Use Ollama AI to generate PR description (default model: {DEFAULT_PR_AI_MODEL}, from GIT_ACP_PR_AI_MODEL)",
)
@click.option(
    "-d",
    "--draft",
    is_flag=True,
    help="Create as draft PR"
)
@click.option(
    "-ld",
    "--list-drafts",
    is_flag=True,
    help="List all draft PRs"
)
@click.option(
    "-rd",
    "--remove-draft",
    is_flag=True,
    help="Interactively select and remove draft PRs"
)
@click.option(
    "-nc",
    "--no-confirm",
    is_flag=True,
    help="Skip all confirmation prompts and proceed automatically"
)
def pr(source: Optional[str], target: str, ollama: bool, draft: bool, list_drafts: bool, remove_draft: bool, no_confirm: bool) -> None:
    """Create or manage pull requests.
    
    This command helps you create and manage pull requests with optional AI-assisted description generation.
    """

    # Create config object to match main.py pattern
    config = GitConfig(
        files="",  # Not used in PR command
        message="",  # Not used in PR command
        branch=source,  # Use source branch
        use_ollama=ollama,
        interactive=False,  # Not used in PR command
        skip_confirmation=no_confirm,
        verbose=False,  # We don't use verbose in PR command yet
        prompt_type="advanced"  # Not used in PR command
    )

    try:
        if list_drafts or remove_draft:
            prs = list_pull_requests("open")
            draft_prs = [pr for pr in prs if pr.get("draft", False)]
            
            if not draft_prs:
                rprint(Panel(
                    "No draft pull requests found.",
                    title="No Drafts",
                    border_style=COLORS['warning'],
                    width=TERMINAL_WIDTH
                ))
                return
            
            if list_drafts:
                debug_header("Draft Pull Requests")
                for pr in draft_prs:
                    # Show PR header
                    rprint(Panel(
                        f"[{COLORS['status']}]#{pr['number']} - {pr['title']}[/{COLORS['status']}]",
                        border_style=COLORS['ai_message_border'],
                        width=TERMINAL_WIDTH
                    ))
                    
                    # Show PR details and content
                    rprint(Panel(
                        f"[{COLORS['debug_value']}]Created by: {pr['user']['login']}\n"
                        f"URL: {pr['html_url']}[/{COLORS['debug_value']}]\n\n"
                        f"[{COLORS['bold']}]Description:[/{COLORS['bold']}]\n"
                        f"{pr['body'] if pr['body'] else '(No description)'}",
                        border_style=COLORS['ai_message_border'],
                        width=TERMINAL_WIDTH
                    ))
                    rprint()  # Add spacing between PRs
            
            if remove_draft:
                debug_header("Delete Draft Pull Requests")
                choices = [
                    f"#{pr['number']} - {pr['title']}"
                    for pr in draft_prs
                ]
                selected = questionary.checkbox(
                    "Select draft PRs to delete:",
                    choices=choices,
                    style=Style(QUESTIONARY_STYLE)
                ).ask()
                
                if not selected:
                    rprint(Panel(
                        "No drafts selected for deletion.",
                        title="No Selection",
                        border_style=COLORS['warning'],
                        width=TERMINAL_WIDTH
                    ))
                    return
                
                # Create a mapping of selection string to PR data for easy lookup
                pr_map = {f"#{pr['number']} - {pr['title']}": pr for pr in draft_prs}
                
                for selection in selected:
                    pr_data = pr_map[selection]
                    pr_number = pr_data['number']
                    
                    # Display PR content
                    debug_header(f"Preview PR #{pr_number}")
                    rprint(Panel(
                        f"[{COLORS['status']}]Title: {pr_data['title']}[/{COLORS['status']}]\n"
                        f"Created by: [{COLORS['debug_value']}]{pr_data['user']['login']}[/{COLORS['debug_value']}]\n"
                        f"URL: [{COLORS['debug_value']}]{pr_data['html_url']}[/{COLORS['debug_value']}]\n\n"
                        f"[{COLORS['bold']}]Description:[/{COLORS['bold']}]\n"
                        f"{pr_data['body'] if pr_data['body'] else '(No description)'}",
                        title=f"[{COLORS['ai_message_header']}]PR Content[/{COLORS['ai_message_header']}]",
                        border_style=COLORS['ai_message_border'],
                        width=TERMINAL_WIDTH
                    ))
                    
                    # Ask for confirmation unless skip_confirmation is True
                    if not config.skip_confirmation:
                        try:
                            confirm = questionary.confirm(
                                f"Are you sure you want to delete PR #{pr_number}?",
                                style=Style(QUESTIONARY_STYLE)
                            ).ask()
                            
                            if not confirm:
                                rprint(f"[{COLORS['warning']}]Skipped deletion of PR #{pr_number}[/{COLORS['warning']}]")
                                continue
                        except KeyboardInterrupt:
                            rprint(Panel(
                                f"[{COLORS['error']}]Operation interrupted[/{COLORS['error']}]\n\n"
                                "Suggestion: Run the command again when ready.",
                                title="Operation Cancelled",
                                border_style=COLORS['warning'],
                                width=TERMINAL_WIDTH
                            ))
                            sys.exit(1)
                    
                    try:
                        delete_pull_request(pr_number)
                        rprint(f"[{COLORS['success']}]✓ Deleted PR #{pr_number}[/{COLORS['success']}]")
                    except Exception as e:
                        rprint(Panel(
                            f"[{COLORS['error']}]Failed to delete PR #{pr_number}:[/{COLORS['error']}]\n{str(e)}\n\n"
                            "Suggestion: Check your permissions and try again.",
                            title="Deletion Failed",
                            border_style=COLORS['error'],
                            width=TERMINAL_WIDTH
                        ))
                    rprint()
            
            return

        if not source:
            rprint(Panel(
                f"[{COLORS['error']}]Error: --source is required when creating a pull request[/{COLORS['error']}]\n\n"
                "Suggestion: Specify the source branch using --source option.",
                title="Missing Source Branch",
                border_style=COLORS['error'],
                width=TERMINAL_WIDTH
            ))
            return

        debug_header("Creating Pull Request")
        debug_item("Source branch", source)
        debug_item("Target branch", target)
        debug_item("AI enabled", str(ollama))
        debug_item("Draft PR", str(draft))
        if ollama:
            debug_item("AI Model", DEFAULT_PR_AI_MODEL)

        # 1. Gather git data
        try:
            commit_messages_list = get_commit_messages(target, source)
            commit_messages = "\n".join(f"- {msg}" for msg in commit_messages_list)
            diff_text = get_diff_between_branches(target, source)
            changes = get_name_status_changes(target, source)
        except KeyboardInterrupt:
            rprint(Panel(
                f"[{COLORS['error']}]Git data gathering interrupted[/{COLORS['error']}]\n\n"
                "Suggestion: Run the command again when ready.",
                title="Operation Cancelled",
                border_style=COLORS['warning'],
                width=TERMINAL_WIDTH
            ))
            sys.exit(1)
        
        added_files = "\n".join(f"- {f}" for f in changes.get("added", []))
        modified_files = "\n".join(f"- {f}" for f in changes.get("modified", []))
        deleted_files = "\n".join(f"- {f}" for f in changes.get("deleted", []))

        # 2. Generate PR sections
        if ollama:
            debug_header("Generating PR Content with AI")
            git_data = {
                "commit_messages": commit_messages_list,
                "diff": diff_text,
                "model": DEFAULT_PR_AI_MODEL
            }
            
            try:
                title = generate_pr_title(git_data)
                summary = generate_pr_summary(diff_text, commit_messages_list)
                code_changes = generate_code_changes(diff_text)
                reason = generate_reason_for_changes(commit_messages_list, diff_text)
                test_plan = generate_test_plan(diff_text)
                additional_notes = generate_additional_notes(commit_messages_list, diff_text)
            except KeyboardInterrupt:
                rprint(Panel(
                    f"[{COLORS['error']}]AI content generation interrupted[/{COLORS['error']}]\n\n"
                    "Suggestion: Try again with --ollama flag, or create PR without AI by omitting the flag.",
                    title="AI Generation Cancelled",
                    border_style=COLORS['warning'],
                    width=TERMINAL_WIDTH
                ))
                sys.exit(1)
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

        # Show preview and ask for confirmation unless skip_confirmation is True
        debug_header("Preview Pull Request")
        rprint(Panel(
            f"[{COLORS['status']}]Title: {title}[/{COLORS['status']}]\n"
            f"[{COLORS['debug_value']}]Source: {source}\n"
            f"Target: {target}\n"
            f"Draft: {str(draft)}[/{COLORS['debug_value']}]\n\n"
            f"[{COLORS['bold']}]Content:[/{COLORS['bold']}]\n"
            f"{pr_markdown}",
            title=f"[{COLORS['ai_message_header']}]Pull Request Preview[/{COLORS['ai_message_header']}]",
            border_style=COLORS['ai_message_border'],
            width=TERMINAL_WIDTH
        ))

        if not config.skip_confirmation:
            try:
                confirm = questionary.confirm(
                    "Do you want to create this pull request?",
                    style=Style(QUESTIONARY_STYLE)
                ).ask()

                if not confirm:
                    rprint(Panel(
                        "Pull request creation cancelled.",
                        title="Cancelled",
                        border_style=COLORS['warning'],
                        width=TERMINAL_WIDTH
                    ))
                    return
            except KeyboardInterrupt:
                rprint(Panel(
                    f"[{COLORS['error']}]Operation interrupted[/{COLORS['error']}]\n\n"
                    "Suggestion: Run the command again when ready.",
                    title="Operation Cancelled",
                    border_style=COLORS['warning'],
                    width=TERMINAL_WIDTH
                ))
                sys.exit(1)

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
            rprint(Panel(
                f"[{COLORS['success']}]✓ Pull Request created successfully![/{COLORS['success']}]\n"
                f"URL: [{COLORS['debug_value']}]{pr_response.get('html_url')}[/{COLORS['debug_value']}]",
                title="Success",
                border_style=COLORS['success'],
                width=TERMINAL_WIDTH
            ))
        except Exception as e:
            rprint(Panel(
                f"[{COLORS['error']}]Error creating pull request:[/{COLORS['error']}]\n{str(e)}\n\n"
                "Suggestion: Check your GitHub token and permissions.",
                title="Creation Failed",
                border_style=COLORS['error'],
                width=TERMINAL_WIDTH
            ))

    except KeyboardInterrupt:
        rprint(Panel(
            f"[{COLORS['error']}]Operation interrupted[/{COLORS['error']}]\n\n"
            "Suggestion: Run the command again when ready.",
            title="Operation Cancelled",
            border_style=COLORS['warning'],
            width=TERMINAL_WIDTH
        ))
        sys.exit(1)
    except Exception as e:
        rprint(Panel(
            f"[{COLORS['error']}]Critical error:[/{COLORS['error']}]\n{str(e)}\n\n"
            "Suggestion: Check your git repository and configuration.",
            title="Critical Error",
            border_style=COLORS['error'],
            width=TERMINAL_WIDTH
        ))
        sys.exit(1) 