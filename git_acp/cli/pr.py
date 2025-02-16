"""
CLI command for PR workflow.
"""

import sys
from typing import Optional

import click
import questionary
from questionary import Style
from rich.console import Console

from git_acp.git.exceptions import GitError
from git_acp.utils.formatting import (
    debug_header,
    debug_item,
    debug_preview,
    success,
    warning,
    ai_message,
    ai_border_message,
    ProgressReporter,
)

from git_acp.config.constants import (
    DEFAULT_PR_AI_MODEL,
    DEFAULT_PROMPT_TYPE,
    QUESTIONARY_STYLE,
    COLORS,
    TERMINAL_WIDTH,
    DEFAULT_BRANCH,
    DEFAULT_PR_AI_CONTEXT_TYPE,
)
from git_acp.git.history import get_commit_messages, get_diff_between_branches
from git_acp.git.status import get_name_status_changes
from git_acp.git.branch import get_current_branch
from git_acp.pr.builder import (
    build_pr_markdown,
    _build_partial_markdown,
    generate_pr_title,
    generate_pr_summary,
    generate_code_changes,
    generate_reason_for_changes,
    generate_test_plan,
    generate_additional_notes,
    generate_pr_simple,
    review_final_pr,
)
from git_acp.pr.github import (
    create_pull_request,
    list_pull_requests,
    delete_pull_request,
)
from git_acp.utils.types import GitConfig, AIConfig

console = Console(width=TERMINAL_WIDTH)


def handle_draft_operations(
    config: GitConfig, list_drafts: bool, remove_draft: bool
) -> None:
    """Handle listing and removing draft PRs."""
    progress = ProgressReporter(config.verbose)
    progress.start_stage("Fetching draft pull requests...")

    prs = list_pull_requests("open")
    draft_prs = [
        pull_request for pull_request in prs if pull_request.get("draft", False)
    ]

    if not draft_prs:
        progress.end_stage("No draft pull requests found")
        return

    if list_drafts:
        if config.verbose:
            debug_header("Draft Pull Requests")
        for pull_request in draft_prs:
            # Break the long f-string into smaller pieces to meet the 88-character limit
            created_by = (
                f"[{COLORS['debug_value']}]Created by: "
                f"{pull_request['user']['login']}\n"
            )
            url_line = (
                f"URL: {pull_request['html_url']}" f"[/{COLORS['debug_value']}]\n\n"
            )
            description = (
                f"[{COLORS['bold']}]Description:[/{COLORS['bold']}]\n"
                "{pull_request['body']"
                "{' ' if pull_request['body'] else '(No description)'}"
            )
            pr_content = created_by + url_line + description
            ai_border_message(pr_content)
            progress.update("")

    if remove_draft:
        _handle_draft_deletion(config, draft_prs, progress)


def _handle_draft_deletion(
    config: GitConfig, draft_prs: list, progress: ProgressReporter
) -> None:
    """Handle the deletion of draft PRs."""
    if config.verbose:
        debug_header("Delete Draft Pull Requests")
    choices = [
        f"#{pull_request['number']} - {pull_request['title']}"
        for pull_request in draft_prs
    ]
    selected = questionary.checkbox(
        "Select draft PRs to delete:", choices=choices, style=Style(QUESTIONARY_STYLE)
    ).ask()

    if not selected:
        progress.end_stage("No drafts selected for deletion")
        return

    pr_map = {
        f"#{pull_request['number']} - {pull_request['title']}": pull_request
        for pull_request in draft_prs
    }
    for selection in selected:
        _delete_single_draft(config, pr_map[selection], progress)


def _delete_single_draft(
    config: GitConfig, pr_data: dict, progress: ProgressReporter
) -> None:
    """Delete a single draft PR."""
    pr_number = pr_data["number"]
    if config.verbose:
        debug_header(f"Preview PR #{pr_number}")
        _display_pr_preview(pr_data)

    if not config.skip_confirmation and not _confirm_deletion(pr_number):
        return

    try:
        progress.start_stage(f"Deleting PR #{pr_number}...")
        delete_pull_request(pr_number)
        progress.end_stage(f"Deleted PR #{pr_number}")
    except (RuntimeError, ValueError) as e:
        error_msg = (
            f"Failed to delete PR #{pr_number}:\n{str(e)}"
            + "\n\nSuggestion: Check your permissions and try again."
        )
        warning(error_msg)
    progress.update("")


def _display_pr_preview(pr_data: dict) -> None:
    """Display a preview of the PR."""
    title_line = f"[{COLORS['status']}]Title: {pr_data['title']}[/{COLORS['status']}]\n"
    created_by_line = (
        f"Created by: [{COLORS['debug_value']}]"
        f"{pr_data['user']['login']}[/{COLORS['debug_value']}]\n"
    )
    url_line = (
        f"URL: [{COLORS['debug_value']}]"
        f"{pr_data['html_url']}[/{COLORS['debug_value']}]\n\n"
    )
    description_line = (
        f"[{COLORS['bold']}]Description:[/{COLORS['bold']}]\n"
        f"{pr_data['body'] if pr_data['body'] else '(No description)'}"
    )

    preview_content = title_line + created_by_line + url_line + description_line

    ai_message("PR Content")
    ai_border_message(preview_content)


def _confirm_deletion(pr_number: int) -> bool:
    """Confirm PR deletion with user."""
    try:
        answer = questionary.confirm(
            f"Are you sure you want to delete PR #{pr_number}?",
            style=Style(QUESTIONARY_STYLE),
        ).ask()
        return bool(answer)
    except KeyboardInterrupt:
        warning("Operation interrupted")
        sys.exit(1)


def create_new_pr(
    config: GitConfig,
    source: str,
    target: str,
    draft: bool,
    ollama: bool,
    prompt_type: str,
    context_type: str,
) -> None:
    """Create a new pull request."""
    progress = ProgressReporter(config.verbose)
    current_stage = None

    if config.verbose:
        debug_header("Generating Pull Request with the below settings:")
        debug_item(config, "Source branch", source)
        debug_item(config, "Target branch", target)
        debug_item(config, "AI enabled", str(ollama))
        debug_item(config, "Draft PR", str(draft))
        if ollama and prompt_type == "advanced":
            debug_item(config, "AI Model", config.ai_config.model)

    try:
        # Initialize PR generation
        if ollama:
            current_stage = "PR generation"
            progress.start_stage(f"Initializing PR generation ({prompt_type} mode)...")
            progress.end_stage(f"PR generation initialized ({prompt_type} mode)")

        # Gather git data
        current_stage = "Git data gathering"
        progress.start_stage("Gathering git data...")
        git_data = _gather_git_data(target, source, progress)
        progress.end_stage(
            "Git data gathered successfully"
            if prompt_type == "simple"
            else "Git data and commit history gathered successfully"
        )

        # Generate PR content - removed progress stages here since they're handled
        # in the content generation functions
        current_stage = "PR content generation"
        pr_markdown, title = _generate_pr_content(
            config, git_data, ollama, prompt_type, context_type, progress
        )

        # Preview PR
        current_stage = "PR preview"
        progress.start_stage("Preparing PR preview...")
        _display_pr_creation_preview(
            title, source, target, draft, pr_markdown, progress
        )
        progress.end_stage(
            "PR preview ready"
            if prompt_type == "simple"
            else "Detailed PR preview ready"
        )

        if not config.skip_confirmation and not _confirm_pr_creation():
            return

        # Submit PR
        current_stage = "PR submission"
        _submit_pr_to_github(
            title, source, target, pr_markdown, draft, config.verbose, progress
        )

    except Exception as e:
        # Ensure we end any active stage before re-raising
        if current_stage:
            progress.end_stage(f"Failed during {current_stage}: {str(e)}")
        raise


def _gather_git_data(target: str, source: str, progress: ProgressReporter) -> dict:
    """Gather git data for PR creation."""
    try:
        progress.start_stage("Fetching commit messages...")
        commit_messages_data = get_commit_messages(target, source)
        progress.end_stage("Commit messages fetched")

        progress.start_stage("Getting diff between branches...")
        diff_text = get_diff_between_branches(target, source)
        progress.end_stage("Diff retrieved")

        progress.start_stage("Analyzing file changes...")
        changes = get_name_status_changes(target, source)
        progress.end_stage("File changes analyzed")

        return {
            "commit_messages_data": commit_messages_data,
            "diff_text": diff_text,
            "changes": changes,
            "added_files": "\n".join(f"- {f}" for f in changes.get("added", [])),
            "modified_files": "\n".join(f"- {f}" for f in changes.get("modified", [])),
            "deleted_files": "\n".join(f"- {f}" for f in changes.get("deleted", [])),
        }
    except KeyboardInterrupt:
        _handle_interrupt("Git data gathering interrupted")


def _generate_pr_content(
    config: GitConfig,
    git_data: dict,
    ollama: bool,
    prompt_type: str,
    context_type: str,
    progress: ProgressReporter,
) -> tuple:
    """Generate PR content using AI or basic template.

    Args:
        config: Git configuration object
        git_data: Dictionary containing git data for PR generation
        ollama: Whether to use AI for generation
        prompt_type: Type of prompt to use ('simple' or 'advanced')
        context_type: Type of context to include ('commits', 'diffs', or 'both')
        progress: ProgressReporter object for updating progress

    Returns:
        tuple: (pr_markdown, title)

    Raises:
        GitError: If PR generation fails
    """
    try:
        if ollama:
            result = _generate_ai_pr_content(
                config, git_data, prompt_type, context_type, progress
            )
            return result
        return _generate_basic_pr_content(git_data)
    except (GitError, ValueError, RuntimeError) as e:
        # If AI generation fails, fall back to basic template with a warning
        warning(
            "AI-assisted PR generation failed. Falling back to basic template.\n"
            f"Error: {str(e)}\n\n"
            "Suggestion: Try again with --verbose flag for more details, or:\n"
            "1. Check if Ollama server is running and responsive\n"
            "2. Consider using a simpler context type (--context-type commits)\n"
            "3. Try the basic template without AI (remove --ollama flag)"
        )
        return _generate_basic_pr_content(git_data)


def _generate_ai_pr_content(
    config: GitConfig,
    git_data: dict,
    prompt_type: str,
    context_type: str,
    progress: ProgressReporter,
) -> tuple:
    """Generate PR content using AI.

    Args:
        config: Git configuration object
        git_data: Dictionary containing git data for PR generation
        prompt_type: Type of prompt to use ('simple' or 'advanced')
        context_type: Type of context to include ('commits', 'diffs', or 'both')
        progress: ProgressReporter object for updating progress

    Returns:
        tuple: (pr_markdown, title)

    Raises:
        GitError: If PR generation fails
        ValueError: If input parameters are invalid
        RuntimeError: If GitHub API operations fail
    """
    try:
        if prompt_type == "advanced":
            result = _generate_advanced_ai_content(config, git_data, progress)
            return result
        return _generate_simple_ai_content(config, git_data, context_type, progress)
    except (GitError, ValueError, RuntimeError) as e:
        # If advanced mode fails, try falling back to simple mode
        if prompt_type == "advanced":
            warning(
                f"Advanced AI PR generation failed ({str(e)}). Trying simple mode.\n"
                "Suggestion: For complex PRs, try:\n"
                "1. Using simple mode (--prompt-type simple)\n"
                "2. Reducing context (--context-type commits)\n"
                "3. Breaking changes into smaller PRs"
            )
            return _generate_simple_ai_content(config, git_data, "commits", progress)
        raise


def _generate_advanced_ai_content(
    config: GitConfig, git_data: dict, progress: ProgressReporter
) -> tuple:
    """Generate advanced AI PR content."""
    try:
        # Code changes
        progress.start_stage("Analyzing code changes...")
        code_changes = generate_code_changes(
            git_data["diff_text"],
            config.verbose,
            progress.update,  # Pass progress.update directly
        )
        progress.end_stage("Code changes analyzed")

        # Change reasons
        progress.start_stage("Understanding change reasons...")
        reason_for_changes = generate_reason_for_changes(
            git_data["commit_messages_data"]["messages"],
            git_data["diff_text"],
            config.verbose,
            progress.update,  # Pass progress.update directly
        )
        progress.end_stage("Change reasons identified")

        # Test plan
        progress.start_stage("Creating test plan...")
        test_plan = generate_test_plan(
            git_data["diff_text"],
            config.verbose,
            progress.update,  # Pass progress.update directly
        )
        progress.end_stage("Test plan created")

        # Notes
        progress.start_stage("Compiling notes...")
        additional_notes = generate_additional_notes(
            git_data["commit_messages_data"]["messages"],
            config.verbose,
            progress.update,  # Pass progress.update directly
        )
        progress.end_stage("Notes compiled")

        # Build partial markdown before summary generation
        partial_pr_markdown = _build_partial_markdown(
            title="",  # Title will be generated later
            git_data=git_data,
            code_changes=code_changes,
            reason=reason_for_changes,
        )

        # Summary
        progress.start_stage("Generating summary...")
        summary = generate_pr_summary(
            partial_pr_markdown,
            config.verbose,
            progress.update,  # Pass progress.update directly
        )
        progress.end_stage("Summary generated")

        # Title
        progress.start_stage("Generating title...")
        # Prepare AI data for title generation
        ai_data = {
            "commit_messages": git_data["commit_messages_data"][
                "messages_with_details"
            ],
            "diff": git_data["diff_text"],
            "added_files": git_data["added_files"],
            "modified_files": git_data["modified_files"],
            "deleted_files": git_data["deleted_files"],
            "model": config.ai_config.model,
        }
        title = generate_pr_title(
            ai_data,
            verbose=config.verbose,
            progress_callback=progress.update,  # Pass progress.update directly
        )
        progress.end_stage("Title generated")

        # Build final PR markdown
        progress.start_stage("Building final PR markdown...")
        pr_markdown = build_pr_markdown(
            title=title,
            summary=summary,
            commit_messages="\n".join(
                f"- {msg}"
                for msg in git_data["commit_messages_data"]["messages_with_details"]
            ),
            added_files=git_data["added_files"],
            modified_files=git_data["modified_files"],
            deleted_files=git_data["deleted_files"],
            code_changes=code_changes,
            reason_for_changes=reason_for_changes,
            test_plan=test_plan,
            additional_notes=additional_notes,
        )
        progress.end_stage("PR markdown built")

        return pr_markdown, title

    except Exception as e:
        # Ensure we end any active stage before re-raising
        progress.end_stage(f"Failed to generate PR content: {str(e)}")
        raise


def _generate_simple_ai_content(
    config: GitConfig, git_data: dict, context_type: str, progress: ProgressReporter
) -> tuple:
    """Generate simple AI PR content."""
    if config.verbose:
        debug_header("Generating PR Content in Simple Mode with AI")
        debug_item(config, "Context Type", context_type)
        debug_item(config, "AI Model", config.ai_config.model or DEFAULT_PR_AI_MODEL)

    # Prepare AI data based on context type
    commit_messages = (
        git_data["commit_messages_data"]["messages_with_details"]
        if context_type in ["commits", "both"]
        else git_data["commit_messages_data"]["messages"]
    )
    diff_text = git_data["diff_text"] if context_type in ["diffs", "both"] else ""

    ai_data = {
        "commit_messages": commit_messages,
        "diff": diff_text,
        "added_files": git_data["added_files"],
        "modified_files": git_data["modified_files"],
        "deleted_files": git_data["deleted_files"],
        "model": config.ai_config.model,
    }

    if config.verbose:
        debug_header("AI Input Data Summary")
        debug_item(config, "Number of Commit Messages", str(len(commit_messages)))
        debug_item(
            config,
            "Diff Size",
            f"{len(diff_text)} characters" if diff_text else "Not included",
        )
        debug_item(
            config,
            "Files Changed",
            f"Added: {len(git_data['changes'].get('added', []))}, "
            f"Modified: {len(git_data['changes'].get('modified', []))}, "
            f"Deleted: {len(git_data['changes'].get('deleted', []))}",
        )
        if commit_messages:
            debug_header("Sample Commit Messages")
            debug_preview("\n".join(commit_messages[:3]))

    try:
        progress.start_stage("Generating PR content...")
        pr_markdown = generate_pr_simple(ai_data, config.verbose)
        progress.end_stage("Generated PR content successfully")

        first_line = pr_markdown.split("\n", maxsplit=1)[0]
        title = (
            first_line.lstrip("#").strip()
            if first_line.startswith("#")
            else "Pull Request"
        )

        if config.verbose:
            debug_header("PR Content")
            debug_item(config, "Title", title)
            debug_preview(pr_markdown)

        return pr_markdown, title

    except Exception as e:
        progress.end_stage(f"Failed to generate PR content: {str(e)}")
        raise


def _generate_basic_pr_content(git_data: dict) -> tuple:
    """Generate basic PR content without AI."""
    initial_title = (
        f"PR: {git_data['commit_messages_data']['messages_with_details'][0]}"
        if git_data["commit_messages_data"]["messages_with_details"]
        else "Pull Request"
    )

    pr_markdown = build_pr_markdown(
        title=initial_title,
        summary="Summary derived from commit messages.",
        commit_messages="\n".join(
            f"- {msg}"
            for msg in git_data["commit_messages_data"]["messages_with_details"]
        ),
        added_files=git_data["added_files"],
        modified_files=git_data["modified_files"],
        deleted_files=git_data["deleted_files"],
        code_changes=f"{git_data['diff_text'][:500]}\n...[diff excerpt]",
        reason_for_changes="Reason derived from commit messages.",
        test_plan="Describe your test plan here...",
        additional_notes="Additional notes here...",
    )

    pr_markdown = review_final_pr(pr_markdown, False)
    first_line = pr_markdown.split("\n", maxsplit=1)[0]
    title = (
        first_line.lstrip("#").strip() if first_line.startswith("#") else initial_title
    )

    return pr_markdown, title


def _display_pr_creation_preview(
    title: str,
    source: str,
    target: str,
    draft: bool,
    pr_markdown: str,
    progress: ProgressReporter,
) -> None:
    """Display preview of PR to be created."""
    progress.start_stage("Preparing PR preview...")
    preview_content = (
        f"Title: {title}\n"
        f"Source: {source}\n"
        f"Target: {target}\n"
        f"Draft: {str(draft)}\n\n"
        f"Content:\n{pr_markdown}"
    )
    ai_border_message(preview_content)
    progress.end_stage("PR preview ready")


def _confirm_pr_creation() -> bool:
    """Confirm PR creation with user."""

    try:
        answer = questionary.confirm(
            "Do you want to create this pull request?", style=Style(QUESTIONARY_STYLE)
        ).ask()
        return bool(answer)
    except KeyboardInterrupt:
        warning("Operation interrupted")
        return False


def _submit_pr_to_github(
    title: str,
    source: str,
    target: str,
    pr_markdown: str,
    draft: bool,
    verbose: bool,
    progress: ProgressReporter,
) -> None:
    """Submit the PR to GitHub."""
    progress.start_stage("Creating PR on GitHub...")
    if verbose:
        debug_header("Creating PR on GitHub")
    try:
        pr_response = create_pull_request(
            base_branch=target,
            head_branch=source,
            title=title,
            body=pr_markdown,
            draft=draft,
        )
        progress.end_stage("Pull Request created successfully!")
        success(f"URL: {pr_response}")
    except (RuntimeError, ValueError) as e:
        progress.end_stage("Failed to create pull request")
        warning(
            f"Error creating pull request:\n{str(e)}\n\n"
            "Suggestion: Check your GitHub token and permissions."
        )


def _handle_interrupt(message: str) -> None:
    """Handle keyboard interrupts."""
    warning(f"{message}\n\n" "Suggestion: Run the command again when ready.")
    sys.exit(1)


@click.command()
@click.option(
    "-s",
    "--source",
    help="Feature branch name (default: current branch)",
    default=get_current_branch(),
)
@click.option(
    "-t",
    "--target",
    help=(
        f"Target (base) branch (default: {DEFAULT_BRANCH}, "
        "from GIT_ACP_DEFAULT_BRANCH)"
    ),
    default=DEFAULT_BRANCH,
)
@click.option(
    "-o",
    "--ollama",
    is_flag=True,
    help=f"(default model: {DEFAULT_PR_AI_MODEL}, " "from GIT_ACP_PR_AI_MODEL)",
)
@click.option(
    "-d",
    "--draft",
    is_flag=True,
    help="Create as draft PR",
)
@click.option(
    "-ld",
    "--list-drafts",
    is_flag=True,
    help="List all draft PRs",
)
@click.option(
    "-rd",
    "--remove-draft",
    is_flag=True,
    help="Interactively select and remove draft PRs",
)
@click.option(
    "-nc",
    "--no-confirm",
    is_flag=True,
    help="Skip all confirmation prompts and proceed automatically",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose debug output")
@click.option(
    "-p",
    "--prompt-type",
    type=click.Choice(["simple", "advanced"]),
    default=DEFAULT_PROMPT_TYPE,
    show_default=True,
    help="Select prompt type for PR generation: 'simple' "
    "(single AI request) or 'advanced' (multiple AI requests).",
)
@click.option(
    "-ct",
    "--context-type",
    type=click.Choice(["commits", "diffs", "both"]),
    default=DEFAULT_PR_AI_CONTEXT_TYPE,
    help="Specify which context to include in simple PR generation"
    "mode (commits and/or diffs)",
)
@click.option(
    "-am",
    "--ai-model",
    help=f"Override AI model (requires --ollama) (default: {DEFAULT_PR_AI_MODEL})",
    default=DEFAULT_PR_AI_MODEL,
)
def pr(
    source: Optional[str],
    target: str,
    ollama: bool,
    draft: bool,
    list_drafts: bool,
    remove_draft: bool,
    no_confirm: bool,
    verbose: bool,
    prompt_type: str,
    context_type: str,
    ai_model: Optional[str],
) -> None:
    """
    Create or manage pull requests.

    This command helps you create and manage pull requests with optional
    AI-assisted description generation.
    """
    try:
        config = GitConfig(
            files="",
            message="",
            branch=source,
            ai_config=AIConfig(
                use_ollama=ollama,
                prompt_type=prompt_type,
                context_type=context_type,
                verbose=verbose,
                model=ai_model,
            ),
            skip_confirmation=no_confirm,
            verbose=verbose,
        )

        if list_drafts or remove_draft:
            handle_draft_operations(config, list_drafts, remove_draft)
            return

        if not source:
            error_text = (
                "Error: --source is required when creating a pull request.\n\n"
                "Suggestion: Specify the source branch using --source option."
            )
            warning(error_text)
            return

        create_new_pr(config, source, target, draft, ollama, prompt_type, context_type)

    except KeyboardInterrupt:
        _handle_interrupt("Operation interrupted")
    except (RuntimeError, ValueError) as e:
        warning(
            f"Critical error:\n{str(e)}\n\n"
            "Suggestion: Check your git repository and configuration."
        )
        sys.exit(1)
