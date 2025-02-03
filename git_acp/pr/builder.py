"""
Functions for building PR descriptions and generating content using AI.
"""

from typing import Dict, List, Optional

from git_acp.ai.client import AIClient
from git_acp.git.runner import GitError
from git_acp.utils.formatting import debug_header, debug_item
from git_acp.config.constants import DEFAULT_PR_AI_MODEL


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
    
    system_prompt = """You are a PR title generator. Follow these rules exactly:
1. Output ONLY the title text, nothing else
2. Use exactly 5-10 words
3. Start with a verb in present tense
4. Be specific about what changed
5. NO formatting characters (#, `, ', ", etc.)
6. NO prefixes like 'PR:', 'Title:', etc.
7. NO explanatory text or meta-commentary
8. NO conventional commit prefixes (feat:, fix:, etc.)
9. Focus on the overall theme of changes, not individual commits
10. Be descriptive and meaningful"""

    prompt = f"""Generate a title that captures the main changes from this information:

COMMIT MESSAGES:
{'\n'.join(commit_messages)}

CHANGES SUMMARY:
{diff_text[:2000] if len(diff_text) > 2000 else diff_text}

Focus on:
- The overall theme or purpose of these changes
- What problem is being solved
- The main feature or improvement being added
- The area of the codebase being changed

Remember: Output only the title text, nothing else."""

    if verbose:
        debug_item("PR Title Prompt", prompt)
        debug_item("PR Title Context", git_data)

    debug_header("Generating PR Title")
    client = AIClient(config, use_pr_model=True)  # Always use PR model
    client.model = model  # Override with specific model if provided
    messages = [
         {"role": "system", "content": system_prompt},
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
    
    system_prompt = """You are a PR summary generator. Follow these rules exactly:
1. Output ONLY the summary text, nothing else
2. Use exactly 100-150 words
3. Focus on WHAT changed and WHY
4. Include impact and scope of changes
5. NO lists or bullet points
6. NO section headers
7. NO technical implementation details
8. NO commit message references
9. Write in present tense
10. Use professional, clear language"""

    prompt = f"""Generate a summary of these changes:

CONTEXT:
{partial_pr_markdown}

Requirements:
- Focus on business value and impact
- Explain what problems this solves
- Highlight key changes without technical details
- Write as a cohesive paragraph"""

    if verbose:
        debug_item("PR Summary Prompt", prompt)
        debug_item("PR Summary Context", context)
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_code_changes(diff_text: str, verbose: bool = False) -> str:
    """Generate a detailed description of the code changes from the diff."""
    
    system_prompt = """You are a code change analyst. Follow these rules:
1. Focus on specific changes in the diff
2. Reference actual filenames from changes
3. Group related file changes together
4. Use simple concrete examples
5. Avoid technical jargon"""

    prompt = f"""Describe these code changes in 3-5 bullet points:
{diff_text}

Format as:
- Updated [filename] to [specific change]
- Added [feature] in [filename]
- Fixed [issue] in [filepath]"""

    if verbose:
        debug_item("Code Changes Prompt", prompt)
        debug_item("Code Changes Context", {"diff_text": diff_text})
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_reason_for_changes(commit_messages: List, diff_text: str, verbose: bool = False) -> str:
    """Generate a clear explanation for the changes based on commit messages and diff."""
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    
    system_prompt = """Explain change reasons in 2-3 points:
1. Connect commits to user benefits
2. Reference specific commit types (feat/fix/chore)
3. Use simple cause-effect format"""

    prompt = f"""Why were these changes made?
Commit Types: {[msg.split(':')[0] for msg in commit_messages]}
Diff Summary: {diff_text[:1000]}

Format as:
1. [Commit type] changes to [achieve X]
2. [Commit type] updates to [solve Y]"""

    if verbose:
        debug_item("Reason for Changes Prompt", prompt)
        debug_item("Reason for Changes Context", context)
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_test_plan(diff_text: str, verbose: bool = False) -> str:
    """Generate a test plan for verifying the code changes."""
    
    system_prompt = """Create test scenarios that:
1. Map to actual code changes
2. Use real filenames from diff
3. Test specific added/modified features"""

    prompt = f"""Suggest test cases for:
{diff_text}

Examples:
- Verify [feature] in [filename] by [action]
- Check [scenario] using [modified component]"""

    if verbose:
        debug_item("Test Plan Prompt", prompt)
        debug_item("Test Plan Context", {"diff_text": diff_text})
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return result.strip()


def generate_additional_notes(commit_messages: List, diff_text: str, verbose: bool = False) -> str:
    """Generate any additional notes or comments for the PR."""
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    
    system_prompt = """List critical notes:
1. Focus on dependency changes
2. Warn about breaking changes
3. Mention required config updates"""

    prompt = f"""Important notes for these changes:
{commit_messages}

Examples:
❗ Update dependencies with 'pip install -r requirements.txt'
❗ Configuration change required in [file]"""

    if verbose:
        debug_item("Additional Notes Prompt", prompt)
        debug_item("Additional Notes Context", context)
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": system_prompt},
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
    
    system_prompt = """You are an expert developer, so you know how to read all kinds of code syntax.
    Write a PR description with title using this markdown template: 
    
    ```markdown
    # {{ Title (5-10 words) }}

    ## Summary

    {{ A paragraph describing what changed and why (200-250 words) }}

    ## Key Changes

    ### Added

    {{ Key functional changes and their impact (200-250 words) }}

    ### Modified

    {{ Key functional changes and their impact (200-250 words) }}

    ### Deleted

    {{ Key functional changes and their impact (200-250 words) }}

    ## Additional Notes

    {{ Any additional notes to concludes the PR message (100-200 words) }}

    ---

    ```
    """

    # Analyze commit messages for key themes
    commit_themes = "\n".join([f"- {msg}" for msg in commit_messages])

    prompt = f"""Create a concise pull request description by analyzing the below information:

## Commit messages to analyze

{commit_themes}

{f'''## Overview of changes to analyze

{diff_text[:10000] if len(diff_text) > 10000 else diff_text}''' if diff_text else '# Note: No diff information provided for analysis'}

## Output format to use

```markdown
# {{ Title that summarizes the changes (5-10 words) }}

## Summary

{{ A paragraph describing what changed and why (200-250 words) }}

## Key Changes

### Added

{{ Key functional changes and their impact (200-250 words) }}

### Modified

{{ Key functional changes and their impact (200-250 words) }}

### Deleted

{{ Key functional changes and their impact (200-250 words) }}

## Additional Notes

{{ Any additional notes to concludes the PR message (100-200 words) }}

---
```
"""

    if verbose:
        debug_item("Simple PR Prompt", prompt)
        debug_item("Simple PR Context", git_data)
    
    client = AIClient(use_pr_model=True)
    client.model = model  # Use the model from git_data
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    return clean_markdown_formatting(result.strip())


def extract_clean_title(content: str, verbose: bool = False) -> str:
    """Extract and clean up a title from PR content.
    
    Args:
        content: The PR content containing a title
        verbose: Whether to log debug information
        
    Returns:
        A clean, single-line title
    """
    if verbose:
        debug_header("Extracting Clean Title")
        debug_item("Original Content", content)
    
    system_prompt = """You are a PR title writer. Your task is to:
1. Extract the most important information from the PR content
2. Create a concise title (5-10 words) that summarizes the main changes
3. Output ONLY the title text with no formatting, quotes, or extra text
4. Focus on what changed, not how it changed
5. Be specific but brief"""

    prompt = f"""Based on this PR content, generate a concise title that captures the main changes:

{content}

Important:
- Output only the title text
- No quotes, formatting, or explanations
- 5-10 words maximum
- Focus on what changed"""

    if verbose:
        debug_item("Title Extraction Prompt", prompt)

    client = AIClient(use_pr_model=True)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    try:
        title = client.chat_completion(messages).strip()
        # Clean up any formatting
        title = title.replace('#', '').replace('`', '').replace('"', '').replace("'", '').strip()
        # Ensure single line
        title = title.split('\n')[0].strip()
        
        if verbose:
            debug_item("Extracted Title", title)
        
        return title
    except Exception as e:
        if verbose:
            debug_item("Title Extraction Error", str(e))
        # Fallback to first line of content that looks like a title
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and len(line.split()) <= 10:
                return line
        return "Pull Request"  # Last resort fallback


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
    
    system_prompt = """You are a PR quality assurance specialist. Follow these rules exactly:
1. Remove duplicate information across sections
2. Eliminate redundant commit message references
3. Consolidate similar technical details
4. Remove generic statements without concrete examples
5. Preserve all unique file references
6. Maintain the original section structure
7. Keep specific testing scenarios
8. Remove empty sections
9. Ensure each commit is only referenced once
10. Remove meta-commentary about the PR process"""

    prompt = f"""Clean this PR description by:
1. Removing duplicate file mentions (e.g., .env.example mentioned in multiple sections)
2. Consolidating similar technical changes
3. Removing generic statements like "No dependencies affected"
4. Keeping only one reference per commit hash
5. Preserving specific examples and test cases

PR Content:
{markdown}

Formatting Rules:
- Keep actual filenames from the diff
- Preserve specific test scenarios
- Remove empty bullet points
- Consolidate similar configuration changes
- Remove redundant explanations about the PR process"""

    if verbose:
        debug_item("PR Review Prompt", prompt)
        debug_item("PR Review Context", {"markdown": markdown})
    
    client = AIClient(use_pr_model=True)
    messages = [
         {"role": "system", "content": system_prompt},
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