"""
Functions for building PR descriptions and generating content using AI.
"""

from typing import Dict, List, Optional, Callable

from git_acp.git.exceptions import GitError
from git_acp.git.history import (
    find_related_commits,
    get_commit_messages,
    analyze_commit_types,
    get_diff_between_branches,
)
from git_acp.git.branch import (
    get_current_branch,
    get_default_branch,
    get_branch_age,
    find_parent_branch,
)
from git_acp.git.status import get_name_status_changes, analyze_diff_hotspots
from git_acp.ai.client import AIClient
from git_acp.utils.formatting import (
    debug_header,
    debug_item,
    debug_json,
    warning,
    instruction_text,
)
from git_acp.ai.pr_prompts import (
    ADVANCED_PR_TITLE_SYSTEM_PROMPT,
    ADVANCED_PR_TITLE_USER_PROMPT,
    ADVANCED_PR_SUMMARY_SYSTEM_PROMPT,
    ADVANCED_PR_SUMMARY_USER_PROMPT,
    ADVANCED_CODE_CHANGES_SYSTEM_PROMPT,
    ADVANCED_CODE_CHANGES_USER_PROMPT,
    ADVANCED_REASON_CHANGES_SYSTEM_PROMPT,
    ADVANCED_REASON_CHANGES_USER_PROMPT,
    ADVANCED_TEST_PLAN_SYSTEM_PROMPT,
    ADVANCED_TEST_PLAN_USER_PROMPT,
    ADVANCED_ADDITIONAL_NOTES_SYSTEM_PROMPT,
    ADVANCED_ADDITIONAL_NOTES_USER_PROMPT,
    SIMPLE_PR_SYSTEM_PROMPT,
    SIMPLE_PR_USER_PROMPT,
    SIMPLE_TITLE_EXTRACTION_SYSTEM_PROMPT,
    SIMPLE_TITLE_EXTRACTION_USER_PROMPT,
    PR_REVIEW_SYSTEM_PROMPT,
    PR_REVIEW_USER_PROMPT,
)
from git_acp.utils.types import GitConfig, AIConfig


def generate_pr_title(
    git_data: Dict,
    verbose: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Generate a PR title using AI.

    Args:
        git_data: Dictionary containing commit messages,
        diff information, and model name
        verbose: Whether to log debug information
        progress_callback: Optional callback function to update progress status

    Returns:
        Generated PR title

    Raises:
        GitError: If title generation fails
    """
    # Create proper config first
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="advanced",
            context_type="both",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    # Update context handling
    context = build_pr_context()
    git_data.update(context)  # Merge context into existing git_data

    # Update prompt formatting with new context variables
    prompt = ADVANCED_PR_TITLE_USER_PROMPT.format(
        commit_types=", ".join(
            f"{k}({v})" for k, v in context["commits"]["types"].items()
        ),
        hot_files=", ".join([f[0] for f in context["diff"]["hotspots"]]),
        commit_messages="\n".join(context["commits"]["messages"]),
        diff_text=context["diff"]["text"][:2000],
    )

    if verbose:
        debug_item(
            config, "Number of commit messages", len(context["commits"]["messages"])
        )
        debug_item(
            config,
            "First commit message",
            (
                context["commits"]["messages"][0]
                if context["commits"]["messages"]
                else "None"
            ),
        )
        debug_item(config, "Diff length", len(context["diff"]["text"]))

        # Add branch metadata collection
        current_branch = get_current_branch()
        branch_meta = {
            "name": current_branch,
            "age_days": get_branch_age(current_branch),
            "parent": find_parent_branch(),
        }
        debug_json(branch_meta)

        # Add commit type analysis
        commit_types = analyze_commit_types(context["commits"]["messages"])
        debug_item(
            config,
            "Commit Type Distribution",
            ", ".join(f"{k}: {v}" for k, v in commit_types.items()),
        )

        # Add diff hotspot analysis
        hotspots = analyze_diff_hotspots(context["diff"]["text"])
        debug_item(config, "Code Change Hotspots", [f[0] for f in hotspots])

    if verbose:
        debug_item(config, "PR Title Prompt", prompt)
        debug_json(git_data)

    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": ADVANCED_PR_TITLE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    try:
        response = client.chat_completion(messages, progress_callback=progress_callback)

        # Handle reasoning LLM outputs
        if client.is_reasoning_llm(response):
            # Extract first non-thinking block content
            cleaned = client.clean_thinking_tags(response)
            title = cleaned.strip()
        else:
            title = response.strip()

        # Extract first line and clean formatting
        title = title.split("\n")[0].strip()
        title = (
            title.replace('"', "").replace("'", "").replace("#", "").replace("`", "")
        )
        title = title[:100]  # Truncate to 100 chars

        if not title:
            raise GitError("Empty title generated by AI")

        if verbose:
            debug_item(config, "Final Title", title)

        return title

    except Exception as e:
        warning(f"Title generation failed: {str(e)}")
        return "Untitled PR"


def generate_pr_summary(
    pr_content: str,
    verbose: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Generate a comprehensive summary for the PR based
    on partial markdown and commit messages.
    """
    # Create proper config
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="advanced",
            context_type="both",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    prompt = ADVANCED_PR_SUMMARY_USER_PROMPT.format(partial_pr_markdown=pr_content)

    if verbose:
        debug_item(config, "Prompt Length", str(len(prompt)))
        debug_item(config, "Markdown Length", str(len(pr_content)))
        if len(pr_content) > 0:
            preview = pr_content[:200] + "..." if len(pr_content) > 200 else pr_content
            debug_item(config, "Markdown Preview", preview)

    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": ADVANCED_PR_SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    result = client.chat_completion(messages, progress_callback=progress_callback)

    # Extract and log thinking blocks if present
    if verbose and client.is_reasoning_llm(result):
        debug_header("AI Reasoning Blocks")
        for block, position in client.extract_thinking_blocks(result):
            debug_item(config, f"Thinking Block ({position})", block)

    cleaned_result = client.clean_thinking_tags(result).strip()

    return cleaned_result


def generate_code_changes(
    diff_text: str,
    verbose: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """Generate code changes description using AI."""
    try:
        # Create proper config object first
        config = GitConfig(
            files="",
            message="",
            branch="",
            ai_config=AIConfig(
                use_ollama=True,
                prompt_type="advanced",
                context_type="diffs",
                verbose=verbose,
                model=None,
            ),
            skip_confirmation=False,
            verbose=verbose,
        )

        client = AIClient(config, use_pr_model=True)
        messages = [
            {"role": "system", "content": ADVANCED_CODE_CHANGES_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": ADVANCED_CODE_CHANGES_USER_PROMPT.format(
                    diff_text=diff_text
                ),
            },
        ]

        if verbose:
            debug_item(config, "Prompt Length", str(len(messages[1]["content"])))
            debug_item(config, "Diff Length", str(len(diff_text)))
            debug_preview = (
                diff_text[:200] + "..." if len(diff_text) > 200 else diff_text
            )
            debug_item(config, "Diff Preview", debug_preview)

        result = client.chat_completion(messages, progress_callback=progress_callback)

        if verbose and client.is_reasoning_llm(result):
            debug_header("AI Reasoning Blocks - Code Changes")
            for block, position in client.extract_thinking_blocks(result):
                debug_item(config, f"Thinking Block ({position})", block)
                debug_json({"position": position, "content": block})

        cleaned_result = client.clean_thinking_tags(result).strip()

        return cleaned_result
    except Exception as e:
        warning(f"Failed to generate code changes description: {str(e)}")
        return "Code changes description unavailable"


def generate_reason_for_changes(
    commit_messages: List,
    diff_text: str,
    verbose: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Generate a clear explanation for the changes
    based on commit messages and diff.
    """
    # Create proper config first
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="advanced",
            context_type="both",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    prompt = ADVANCED_REASON_CHANGES_USER_PROMPT.format(
        commit_types=[msg.split(":")[0] for msg in commit_messages],
        diff_text=diff_text[:1000],
    )

    if verbose:
        debug_item(config, "Number of Commit Messages", str(len(commit_messages)))
        if commit_messages:
            preview = (
                commit_messages[0][:200] + "..."
                if len(commit_messages[0]) > 200
                else commit_messages[0]
            )
            debug_item(config, "First Commit Message", preview)
        debug_item(config, "Prompt Length", str(len(prompt)))
        debug_item(config, "Diff Text Length", str(len(diff_text)))
        if len(diff_text) > 0:
            preview = diff_text[:200] + "..." if len(diff_text) > 200 else diff_text
            debug_item(config, "Diff Preview", preview)

    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": ADVANCED_REASON_CHANGES_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    result = client.chat_completion(messages, progress_callback=progress_callback)

    # Extract and log thinking blocks if present
    if verbose and client.is_reasoning_llm(result):
        debug_header("AI Reasoning Blocks")
        for block, position in client.extract_thinking_blocks(result):
            debug_item(config, f"Thinking Block ({position})", block)

    cleaned_result = client.clean_thinking_tags(result).strip()

    return cleaned_result


def generate_test_plan(
    diff_text: str,
    verbose: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Generate a test plan for verifying the code changes.
    """
    # Create proper config first
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="advanced",
            context_type="diffs",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": ADVANCED_TEST_PLAN_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": ADVANCED_TEST_PLAN_USER_PROMPT.format(diff_text=diff_text),
        },
    ]

    result = client.chat_completion(messages, progress_callback=progress_callback)

    if verbose and client.is_reasoning_llm(result):
        debug_header("AI Reasoning Blocks")
        for block, position in client.extract_thinking_blocks(result):
            debug_item(config, f"Thinking Block ({position})", block)

    cleaned_result = client.clean_thinking_tags(result).strip()

    return cleaned_result


def generate_additional_notes(
    commit_messages: List,
    verbose: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Generate any additional notes or comments for the PR.
    """
    # Create proper config first
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="advanced",
            context_type="both",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": ADVANCED_ADDITIONAL_NOTES_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": ADVANCED_ADDITIONAL_NOTES_USER_PROMPT.format(
                commit_messages=commit_messages
            ),
        },
    ]

    result = client.chat_completion(messages, progress_callback=progress_callback)

    if verbose and client.is_reasoning_llm(result):
        debug_header("AI Reasoning Blocks")
        for block, position in client.extract_thinking_blocks(result):
            debug_item(config, f"Thinking Block ({position})", block)

    cleaned_result = client.clean_thinking_tags(result).strip()

    return cleaned_result


def generate_pr_simple(git_data: Dict, verbose: bool = False) -> str:
    """Generate a simple PR description using AI.

    Args:
        git_data: Dictionary containing commit messages and diff information
        verbose: Whether to log debug information

    Returns:
        Generated PR description
    """
    # Create proper config first
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="simple",
            context_type="both",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    commit_messages = git_data.get("commit_messages", [])
    diff_text = git_data.get("diff", "")
    added_files = git_data.get("added_files", "")
    modified_files = git_data.get("modified_files", "")
    deleted_files = git_data.get("deleted_files", "")

    # Analyze commit messages for key themes
    commit_themes = "\n".join([f"- {msg}" for msg in commit_messages])

    # Prepare changes overview
    overview_text = diff_text[:2000] if len(diff_text) > 2000 else diff_text
    changes_overview = (
        f"## Overview of changes to analyze\n\n{overview_text}"
        if diff_text
        else "# Note: No changes to analyze"
    )

    instruction_text("Generating PR with the `simple` prompt-type")
    if verbose:
        debug_header("Simple PR Generation Input")
        debug_item(config, "Number of commit messages", len(commit_messages))
        debug_item(
            config,
            "First commit message",
            commit_messages[0] if commit_messages else "None",
        )
        debug_item(config, "Diff length", len(diff_text))
        debug_item(config, "Added files", added_files if added_files else "None")
        debug_item(
            config, "Modified files", modified_files if modified_files else "None"
        )
        debug_item(config, "Deleted files", deleted_files if deleted_files else "None")

    # Format the user prompt with the actual data
    prompt = SIMPLE_PR_USER_PROMPT.format(
        commit_themes=commit_themes,
        changes_overview=changes_overview,
        added_files=added_files if added_files else "None",
        modified_files=modified_files if modified_files else "None",
        deleted_files=deleted_files if deleted_files else "None",
    )

    if verbose:
        debug_item(config, "Simple PR Prompt", prompt)
        debug_json(git_data)

    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": SIMPLE_PR_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    result = client.chat_completion(messages)

    if verbose and client.is_reasoning_llm(result):
        debug_header("AI Reasoning Blocks - Simple PR")
        for block, position in client.extract_thinking_blocks(result):
            debug_item(config, f"Thinking Block ({position})", block)

    cleaned_result = client.clean_thinking_tags(result).strip()

    return cleaned_result


def extract_clean_title(content: str, verbose: bool = False) -> str:
    """
    Extract and clean up a title from PR content.

    Args:
        content: The PR content containing a title
        verbose: Whether to log debug information

    Returns:
        A clean, single-line title
    """
    # Create config first
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="advanced",
            context_type="both",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    if verbose:
        debug_header("Extracting Clean Title")
        debug_item(config, "Original Content", content)

    prompt = SIMPLE_TITLE_EXTRACTION_USER_PROMPT.format(content=content)

    if verbose:
        debug_item(config, "Title Extraction Prompt", prompt)

    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": SIMPLE_TITLE_EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    result = client.chat_completion(messages)

    return result.strip()


def build_pr_markdown(
    title: str,
    summary: str,
    commit_messages: str,
    added_files: str,
    modified_files: str,
    deleted_files: str,
    code_changes: str,
    reason_for_changes: str,
    test_plan: str,
    additional_notes: str,
) -> str:
    """
    Assemble a complete Markdown PR description.

    Args:
        title: PR title (will be cleaned up later)
        summary: PR summary
        commit_messages: Formatted commit messages
        added_files: List of added files
        modified_files: List of modified files
        deleted_files: List of deleted files
        code_changes: Description of code changes
        reason_for_changes: Reasoning behind changes
        test_plan: Testing strategy
        additional_notes: Any additional information

    Returns:
        Complete PR description in Markdown format
    """
    markdown = f"""
# {title}

## Summary
{summary}

## Commits
{commit_messages}

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
{reason_for_changes}

## Test Plan
{test_plan}

## Additional Notes
{additional_notes}
"""

    return clean_markdown_formatting(markdown)


def review_final_pr(markdown: str, verbose: bool = False) -> str:
    """
    Review and clean up the final PR markdown to remove duplicate or
    redundant information.
    """
    # Create proper config
    config = GitConfig(
        files="",
        message="",
        branch="",
        ai_config=AIConfig(
            use_ollama=True,
            prompt_type="advanced",
            context_type="both",
            verbose=verbose,
            model=None,
        ),
        skip_confirmation=False,
        verbose=verbose,
    )

    instruction_text("Reviewing final PR")
    client = AIClient(config, use_pr_model=True)
    messages = [
        {"role": "system", "content": PR_REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": PR_REVIEW_USER_PROMPT.format(markdown=markdown)},
    ]

    result = client.chat_completion(messages)

    if verbose and client.is_reasoning_llm(result):
        debug_header("AI Reasoning Blocks")
        for block, position in client.extract_thinking_blocks(result):
            debug_item(config, f"Thinking Block ({position})", block)

    return client.clean_thinking_tags(result).strip()


def clean_markdown_formatting(markdown: str) -> str:
    """
    Clean up markdown formatting issues.

    - Remove nested code blocks
    - Ensure consistent header formatting
    - Remove explanatory/meta text
    - Fix spacing between sections

    Args:
        markdown: The markdown text to clean

    Returns:
        Cleaned markdown text
    """
    # Split into lines for processing
    lines = markdown.strip().split("\n")
    cleaned_lines = []
    in_code_block = False
    last_was_header = False

    for line in lines:
        # Skip empty lines after headers
        if last_was_header and not line.strip():
            continue

        # Track code block state
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Clean up header formatting
        if line.strip().startswith("#"):
            # Add spacing before headers (except first)
            if cleaned_lines and not cleaned_lines[-1].strip() == "":
                cleaned_lines.append("")
            # Normalize header format
            header_level = len(line.split()[0])  # Count #s
            header_text = " ".join(line.split()[1:])
            line = f"{'#' * header_level} {header_text}"
            last_was_header = True
        else:
            last_was_header = False

        # Skip lines that look like explanatory text
        if any(
            skip in line.lower()
            for skip in [
                "please output",
                "generate",
                "following format",
                "important:",
                "note:",
                "instructions:",
                "example:",
                "template:",
            ]
        ):
            continue

        # Add the cleaned line
        if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
            cleaned_lines.append(line)

    # Ensure single newline between sections
    result = "\n".join(cleaned_lines)
    # Remove multiple consecutive newlines
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")

    return result.strip()


def _build_partial_markdown(
    title: str, git_data: dict, code_changes: str, reason: str
) -> str:
    """Build partial markdown for summary generation."""
    return f"""# {title}

## Files Changed
### Added
{git_data["added_files"] if git_data["added_files"] else "None"}

### Modified
{git_data["modified_files"] if git_data["modified_files"] else "None"}

### Deleted
{git_data["deleted_files"] if git_data["deleted_files"] else "None"}

## Code Changes
{code_changes}

## Reason for Changes
{reason}"""


def build_pr_description(config=None) -> str:
    """Build a pull request description.

    Args:
        config: Optional configuration

    Returns:
        str: Generated PR description

    Raises:
        GitError: If building PR description fails
    """
    try:
        # Get branch information
        current_branch = get_current_branch()
        default_branch = get_default_branch()

        # Get commit messages and changes
        commit_data = get_commit_messages(default_branch, current_branch)
        changes = get_name_status_changes(default_branch, current_branch)

        # Build context for AI
        context = {
            "commits": commit_data["messages"],
            "detailed_commits": commit_data["messages_with_details"],
            "changes": changes,
            "source_branch": current_branch,
            "target_branch": default_branch,
            # "commit_summaries": get_recent_commits(5),
            # "changed_files": get_name_status_changes(),
        }

        # Generate description using AI
        client = AIClient(config)
        if config and getattr(config, "prompt_type", "advanced") == "simple":
            messages = [
                {"role": "system", "content": SIMPLE_PR_SYSTEM_PROMPT},
                {"role": "user", "content": str(context)},
            ]
        else:
            messages = [
                {"role": "system", "content": ADVANCED_PR_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": str(context)},
            ]

        description = client.chat_completion(messages).strip()

        # Allow user to review and edit if interactive
        # if config and getattr(config, "interactive", False):
        #     # TODO Implement interactive review
        #     pass

        return description

    except Exception as e:
        raise GitError(f"Failed to build PR description: {str(e)}") from e


def build_pr_context() -> Dict:
    """Aggregate all PR context data from various sources.

    Returns:
        Dictionary containing branch metadata, commit analysis,
        diff insights, and related commits
    """
    current_branch = get_current_branch()
    default_branch = get_default_branch()

    # Get core data
    commit_data = get_commit_messages(default_branch, current_branch)
    diff_text = get_diff_between_branches(default_branch, current_branch)
    changes = get_name_status_changes(default_branch, current_branch)

    return {
        "branch": {  # From Phase 2
            "name": current_branch,
            "age_days": get_branch_age(current_branch),
            "parent": find_parent_branch(),
        },
        "commits": {  # From Phase 3
            "messages": commit_data["messages"],
            "types": analyze_commit_types(commit_data["messages"]),
            "count": len(commit_data["messages"]),
        },
        "diff": {  # From Phase 4
            "text": diff_text,
            "hotspots": analyze_diff_hotspots(diff_text),
            "added": changes["added"],
            "modified": changes["modified"],
            "deleted": changes["deleted"],
        },
        "relations": find_related_commits(
            changes["added"] + changes["modified"], num_commits=3
        ),
    }
