"""
Functions for building PR descriptions and generating content using AI.
"""

from typing import Dict, List, Optional

from git_acp.ai.client import AIClient
from git_acp.git.runner import GitError
from git_acp.utils.formatting import debug_header, debug_item
from git_acp.config.constants import DEFAULT_PR_AI_MODEL
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
    PR_REVIEW_USER_PROMPT
)


def generate_pr_title(git_data: Dict, config: Optional[Dict] = None, verbose: bool = False) -> str:
    """Generate a PR title using AI.

    Args:
        git_data: Dictionary containing commit messages, diff information, and model name
        config: Optional configuration dictionary
        verbose: Whether to log debug information

    Returns:
        Generated PR title

    Raises:
        GitError: If title generation fails
    """
    commit_messages = git_data.get("commit_messages", [])
    diff_text = git_data.get("diff", "")
    model = git_data.get("model", DEFAULT_PR_AI_MODEL)  # Get model from git_data or use PR default
    
    if verbose:
        debug_header("Title Generation Input")
        debug_item("Number of commit messages", len(commit_messages))
        debug_item("First commit message", commit_messages[0] if commit_messages else "None")
        debug_item("Diff length", len(diff_text))
        debug_item("Model", model)

    # Format the user prompt with the actual data
    prompt = ADVANCED_PR_TITLE_USER_PROMPT.format(
        commit_messages='\n'.join(commit_messages),
        diff_text=diff_text[:2000] if len(diff_text) > 2000 else diff_text
    )

    if verbose:
        debug_item("PR Title Prompt", prompt)
        debug_item("PR Title Context", git_data)

    debug_header("Generating PR Title")
    client = AIClient(config, use_pr_model=True)  # Always use PR model
    client.model = model  # Override with specific model if provided
    messages = [
         {"role": "system", "content": ADVANCED_PR_TITLE_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    try:
        title = client.chat_completion(messages).strip()
        # Remove any markdown formatting or quotes that might have been added
        title = title.replace('#', '').replace('`', '').replace('"', '').replace("'", '').strip()
        # Ensure it's a single line
        title = title.split('\n')[0].strip()
        if verbose:
            debug_item("Generated Raw Title", title)
        return title
    except Exception as e:
        raise GitError(f"Failed to generate PR title: {str(e)}") from e


def generate_pr_summary(partial_pr_markdown: str, commit_messages: list, verbose: bool = False) -> str:
    """Generate a comprehensive summary for the PR based on partial markdown and commit messages."""
    context = {"partial_pr_markdown": partial_pr_markdown, "commit_messages": commit_messages}
    
    prompt = ADVANCED_PR_SUMMARY_USER_PROMPT.format(partial_pr_markdown=partial_pr_markdown)

    if verbose:
        debug_item("PR Summary Prompt", prompt)
        debug_item("PR Summary Context", context)
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": ADVANCED_PR_SUMMARY_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_code_changes(diff_text: str, verbose: bool = False) -> str:
    """Generate a detailed description of the code changes from the diff."""
    
    prompt = ADVANCED_CODE_CHANGES_USER_PROMPT.format(diff_text=diff_text)

    if verbose:
        debug_item("Code Changes Prompt", prompt)
        debug_item("Code Changes Context", {"diff_text": diff_text})
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": ADVANCED_CODE_CHANGES_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_reason_for_changes(commit_messages: List, diff_text: str, verbose: bool = False) -> str:
    """Generate a clear explanation for the changes based on commit messages and diff."""
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    
    prompt = ADVANCED_REASON_CHANGES_USER_PROMPT.format(
        commit_types=[msg.split(':')[0] for msg in commit_messages],
        diff_text=diff_text[:1000]
    )

    if verbose:
        debug_item("Reason for Changes Prompt", prompt)
        debug_item("Reason for Changes Context", context)
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": ADVANCED_REASON_CHANGES_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_test_plan(diff_text: str, verbose: bool = False) -> str:
    """Generate a test plan for verifying the code changes."""
    
    prompt = ADVANCED_TEST_PLAN_USER_PROMPT.format(diff_text=diff_text)

    if verbose:
        debug_item("Test Plan Prompt", prompt)
        debug_item("Test Plan Context", {"diff_text": diff_text})
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": ADVANCED_TEST_PLAN_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_additional_notes(commit_messages: List, diff_text: str, verbose: bool = False) -> str:
    """Generate any additional notes or comments for the PR."""
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    
    prompt = ADVANCED_ADDITIONAL_NOTES_USER_PROMPT.format(commit_messages=commit_messages)

    if verbose:
        debug_item("Additional Notes Prompt", prompt)
        debug_item("Additional Notes Context", context)
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": ADVANCED_ADDITIONAL_NOTES_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_pr_simple(git_data: Dict, verbose: bool = False) -> str:
    """Generate a compact pull request description in markdown format using a single AI request.
    
    This function generates the entire PR description including title in a single AI call.
    The output is automatically formatted and cleaned up.
    
    Args:
        git_data: Dictionary containing commit messages, diff, file changes, and model name
        verbose: Whether to log debug information
        
    Returns:
        Complete PR description in markdown format with title
    """
    commit_messages = git_data.get("commit_messages", [])
    diff_text = git_data.get("diff", "")
    added_files = git_data.get("added_files", "")
    modified_files = git_data.get("modified_files", "")
    deleted_files = git_data.get("deleted_files", "")
    model = git_data.get("model", DEFAULT_PR_AI_MODEL)
    
    # Analyze commit messages for key themes
    commit_themes = "\n".join([f"- {msg}" for msg in commit_messages])
    
    # Prepare changes overview
    changes_overview = f'''## Overview of changes to analyze\n\n{diff_text[:10000] if len(diff_text) > 10000 else diff_text}''' if diff_text else '# Note: No diff information provided for analysis'
    
    prompt = SIMPLE_PR_USER_PROMPT.format(
        commit_themes=commit_themes,
        changes_overview=changes_overview
    )

    if verbose:
        debug_item("Simple PR Prompt", prompt)
        debug_item("Simple PR Context", git_data)
    
    client = AIClient(use_pr_model=True)
    client.model = model  # Use the model from git_data
    messages = [
         {"role": "system", "content": SIMPLE_PR_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return clean_markdown_formatting(result.strip())
    # return result


def extract_clean_title(content: str, verbose: bool = False) -> str:
    """Extract and clean up a title from PR content.
    
    Args:
        content: The PR content containing a title
        verbose: Whether to log debug information
        
    Returns:n
        A clean, single-line title
    """
    if verbose:
        debug_header("Extracting Clean Title")
        debug_item("Original Content", content)
    
    prompt = SIMPLE_TITLE_EXTRACTION_USER_PROMPT.format(content=content)

    if verbose:
        debug_item("Title Extraction Prompt", prompt)

    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": SIMPLE_TITLE_EXTRACTION_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
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
    additional_notes: str
) -> str:
    """Assemble a complete Markdown PR description.

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
{additional_notes}"""

    return clean_markdown_formatting(markdown)


def review_final_pr(markdown: str, verbose: bool = False) -> str:
    """Review and clean up the final PR markdown to remove duplicate or redundant information."""
    
    prompt = PR_REVIEW_USER_PROMPT.format(markdown=markdown)

    if verbose:
        debug_item("PR Review Prompt", prompt)
        debug_item("PR Review Context", {"markdown": markdown})
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": PR_REVIEW_SYSTEM_PROMPT},
         {"role": "user", "content": prompt}
    ]
    try:
        result = client.chat_completion(messages)
        return clean_markdown_formatting(result.strip())
    except Exception as e:
        # If review fails, return the original markdown after cleaning
        return clean_markdown_formatting(markdown)


def clean_markdown_formatting(markdown: str) -> str:
    """Clean up markdown formatting issues.
    
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
    lines = markdown.strip().split('\n')
    cleaned_lines = []
    in_code_block = False
    last_was_header = False
    
    for line in lines:
        # Skip empty lines after headers
        if last_was_header and not line.strip():
            continue
            
        # Track code block state
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
            
        # Clean up header formatting
        if line.strip().startswith('#'):
            # Add spacing before headers (except first)
            if cleaned_lines and not cleaned_lines[-1].strip() == '':
                cleaned_lines.append('')
            # Normalize header format
            header_level = len(line.split()[0])  # Count #s
            header_text = ' '.join(line.split()[1:])
            line = f"{'#' * header_level} {header_text}"
            last_was_header = True
        else:
            last_was_header = False
            
        # Skip lines that look like explanatory text
        if any(skip in line.lower() for skip in [
            'please output', 'generate', 'following format', 'important:', 
            'note:', 'instructions:', 'example:', 'template:'
        ]):
            continue
            
        # Add the cleaned line
        if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
            cleaned_lines.append(line)
    
    # Ensure single newline between sections
    result = '\n'.join(cleaned_lines)
    # Remove multiple consecutive newlines
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')
    
    return result.strip() 