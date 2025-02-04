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
    DEFAULT_PROMPT_TYPE,
    QUESTIONARY_STYLE,
    COLORS,
    TERMINAL_WIDTH,
    DEFAULT_BRANCH,
    DEFAULT_PR_AI_CONTEXT_TYPE
)
from git_acp.git.history import get_commit_messages, get_diff_between_branches
from git_acp.git.status import get_name_status_changes
from git_acp.git.branch import get_current_branch
from git_acp.pr.builder import (
    build_pr_markdown,
    generate_pr_title,
    generate_pr_summary,
    generate_code_changes,
    generate_reason_for_changes,
    generate_test_plan,
    generate_additional_notes,
    generate_pr_simple,
    review_final_pr,
    clean_markdown_formatting
)
from git_acp.pr.github import create_pull_request, list_pull_requests, delete_pull_request
from git_acp.utils.formatting import debug_header, debug_item
from git_acp.utils.types import GitConfig

console = Console(width=TERMINAL_WIDTH)

@click.command()
@click.option(
    "-s",
    "--source",
    help="Feature branch name (default: current branch)",
    default=lambda: get_current_branch()
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
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose debug output"
)
@click.option(
    "-p",
    "--prompt-type",
    type=click.Choice(["simple", "advanced"]),
    default=DEFAULT_PROMPT_TYPE,
    show_default=True,
    help="Select prompt type for PR generation: 'simple' (single AI request) or 'advanced' (multiple AI requests)."
)
@click.option(
    "-ct",
    "--context-type",
    type=click.Choice(["commits", "diffs", "both"]),
    default=DEFAULT_PR_AI_CONTEXT_TYPE,
    help="Specify which context to include in simple PR generation mode (commits and/or diffs)"
)
def pr(source: Optional[str], target: str, ollama: bool, draft: bool, list_drafts: bool, remove_draft: bool, no_confirm: bool, verbose: bool, prompt_type: str, context_type: str) -> None:
    """Create or manage pull requests.
    
    This command helps you create and manage pull requests with optional AI-assisted description generation.
    """

    # Create config object to match cli.py pattern
    config = GitConfig(
        files="",  # Not used in PR command
        message="",  # Not used in PR command
        branch=source,  # Use source branch
        use_ollama=ollama,
        interactive=False,  # Not used in PR command
        skip_confirmation=no_confirm,
        verbose=verbose,  # Add verbose flag to config
        prompt_type=prompt_type
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
                if verbose:
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
                if verbose:
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
                    if verbose:
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

        if verbose:
            debug_header("Creating Pull Request")
            debug_item("Source branch", source)
            debug_item("Target branch", target)
            debug_item("AI enabled", str(ollama))
            debug_item("Draft PR", str(draft))
            if ollama and prompt_type == "advanced":
                debug_item("AI Model", DEFAULT_PR_AI_MODEL)

        # 1. Gather git data
        try:
            commit_messages_data = get_commit_messages(target, source)
            commit_messages = "\n".join(f"- {msg}" for msg in commit_messages_data["messages_with_details"])
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
            if prompt_type == "advanced":
                if verbose:
                    debug_header("Generating PR Content with AI (Advanced Mode)")
                git_data = {
                    "commit_messages": commit_messages_data["messages"],  # Clean messages for title
                    "diff": diff_text,
                    "model": DEFAULT_PR_AI_MODEL
                }
                try:
                    # First generate title
                    title = generate_pr_title(git_data, verbose=verbose)
                    if verbose:
                        debug_item("Generated Title", title)
                    
                    # Generate all sections
                    code_changes = generate_code_changes(diff_text, verbose)
                    if verbose:
                        debug_item("Generated Code Changes", code_changes)
                    
                    reason = generate_reason_for_changes(commit_messages_data["messages"], diff_text, verbose)
                    if verbose:
                        debug_item("Generated Reason for Changes", reason)
                    
                    test_plan = generate_test_plan(diff_text, verbose)
                    if verbose:
                        debug_item("Generated Test Plan", test_plan)
                    
                    additional_notes = generate_additional_notes(commit_messages_data["messages"], diff_text, verbose)
                    if verbose:
                        debug_item("Generated Additional Notes", additional_notes)
                    
                    # Build a partial PR markdown to use as context for summary generation
                    partial_pr_markdown = f"""# {title}

## Files Changed
### Added
{added_files if added_files else "None"}

### Modified
{modified_files if modified_files else "None"}

### Deleted
{deleted_files if deleted_files else "None"}

## Code Changes
{code_changes}

## Reason for Changes
{reason}"""
                    
                    # Generate summary using the partial markdown
                    summary = generate_pr_summary(partial_pr_markdown, commit_messages_data["messages"], verbose)
                    if verbose:
                        debug_item("Generated PR Summary", summary)
                    
                    # Build complete markdown
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
                    
                    # Final review to remove any remaining duplicates
                    # pr_markdown = review_final_pr(pr_markdown, verbose)
                    
                except Exception as e:
                    raise e
            elif prompt_type == "simple":
                if verbose:
                    debug_header("Generating PR Content in Simple Mode with AI")
                try:
                    # Prepare git data for simple mode based on context_type
                    git_data = {
                        "commit_messages": commit_messages_data["messages_with_details"] if context_type in ["commits", "both"] else commit_messages_data["messages"],
                        "diff": diff_text if context_type in ["diffs", "both"] else "",
                        "added_files": added_files,
                        "modified_files": modified_files,
                        "deleted_files": deleted_files,
                        "model": DEFAULT_PR_AI_MODEL
                    }
                    
                    if verbose:
                        debug_item("Context Type Mode", context_type)
                        debug_item("Using Full Commit Messages", str(context_type in ["commits", "both"]))
                        debug_item("Including Diffs", str(context_type in ["diffs", "both"]))
                    
                    # Generate simple PR markdown with title included
                    pr_markdown = generate_pr_simple(git_data, verbose)
                    
                    # Extract title from the markdown
                    lines = pr_markdown.split('\n')
                    if lines and lines[0].startswith('#'):
                        title = lines[0].lstrip('#').strip()
                    else:
                        title = "Pull Request"  # Fallback
                except Exception as e:
                    raise e
        else:
            if verbose:
                debug_header("Using Basic PR Content")
            # Use first commit message as initial title
            initial_title = f"PR: {commit_messages_data['messages_with_details'][0]}" if commit_messages_data['messages_with_details'] else "Pull Request"
            summary = "Summary derived from commit messages."
            code_changes = diff_text[:500] + "\n...[diff excerpt]"
            reason = "Reason derived from commit messages."
            test_plan = "Describe your test plan here..."
            additional_notes = "Additional notes here..."
            
            # Build initial markdown
            pr_markdown = build_pr_markdown(
                title=initial_title,
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
            
            # Clean up and extract final title
            pr_markdown = review_final_pr(pr_markdown, verbose)
            lines = pr_markdown.split('\n')
            if lines and lines[0].startswith('#'):
                title = lines[0].lstrip('#').strip()
            else:
                title = initial_title

        # 3. Preview and confirmation
        if verbose:
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
        if verbose:
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