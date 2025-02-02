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
    
    prompt = f"""Based on the following commit messages and diff, generate a succinct and descriptive PR title.
The title should be 5-10 words and describe the main changes concisely.

Commit Messages:
{'\n'.join(commit_messages)}

Diff:
{diff_text}"""

    if verbose:
        debug_item("PR Title Prompt", prompt)
        debug_item("PR Title Context", git_data)

    debug_header("Generating PR Title")
    client = AIClient(config, use_pr_model=True)  # Always use PR model
    client.model = model  # Override with specific model if provided
    system_prompt = ("You are an AI that generates pull request titles. Output ONLY the title text, with no quotes, explanations, or formatting. "
                    "The title should be 5-10 words and describe the main changes concisely.")
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
        return title
    except Exception as e:
        raise GitError(f"Failed to generate PR title: {str(e)}") from e


def generate_pr_summary(partial_pr_markdown: str, commit_messages: list, verbose: bool = False) -> str:
    """
    Generate a comprehensive summary for the PR based on partial markdown and commit messages.
    """
    context = {"partial_pr_markdown": partial_pr_markdown, "commit_messages": commit_messages}
    prompt = (
        f"Using the following partial PR markdown, generate a concise PR summary in 100-200 words.\n"
        f"Important: Do not include detailed commit messages or file change data (these will be added later).\n"
        f"Partial Markdown: {partial_pr_markdown}"
    )
    if verbose:
        from git_acp.utils.formatting import debug_item
        debug_item("PR Summary Prompt", prompt)
        debug_item("PR Summary Context", context)
    
    system_prompt = "You are an AI that generates a pull request summary. Output only the summary in 100-200 words without any extra commentary."
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    client = AIClient(use_pr_model=True)  # Use PR model by default
    result = client.chat_completion(messages)
    return result.strip()


def generate_code_changes(diff_text: str, verbose: bool = False) -> str:
    """
    Generate a detailed description of the code changes from the diff.
    """
    prompt = (
        f"Provide a concise description of the code changes shown in the diff below in 50-100 words.\n"
        f"Focus on the main modifications without unnecessary details.\n"
        f"Diff:\n{diff_text}"
    )
    if verbose:
        from git_acp.utils.formatting import debug_item
        debug_item("Code Changes Prompt", prompt)
        debug_item("Code Changes Context", {"diff_text": diff_text})
    
    system_prompt = "You are an AI that summarizes code changes. Output only a concise description (50-100 words) with no additional notes."
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    client = AIClient(use_pr_model=True)  # Use PR model by default
    result = client.chat_completion(messages)
    return result.strip()


def generate_reason_for_changes(commit_messages: List[str], diff_text: str, verbose: bool = False) -> str:
    """
    Generate a clear explanation for the changes based on commit messages and diff.
    """
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    prompt = (
        f"Based on the provided commit messages and diff, explain the main reasons for these changes in 50-100 words.\n"
        f"Ensure your explanation is succinct and does not duplicate detailed commit data.\n"
        f"Commit Messages: {commit_messages}\nDiff: {diff_text}"
    )
    if verbose:
        from git_acp.utils.formatting import debug_item
        debug_item("Reason for Changes Prompt", prompt)
        debug_item("Reason for Changes Context", context)
    
    system_prompt = "You are an AI that explains the reasons for changes concisely. Output only the explanation (50-100 words) with no further commentary."
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    client = AIClient(use_pr_model=True)  # Use PR model by default
    result = client.chat_completion(messages)
    return result.strip()


def generate_test_plan(diff_text: str, verbose: bool = False) -> str:
    """
    Generate a test plan for verifying the code changes.
    """
    prompt = (
        f"Generate a concise test plan in 50-100 words for verifying the changes presented in the diff below.\n"
        f"Focus on key testing steps and considerations.\n"
        f"Diff:\n{diff_text}"
    )
    if verbose:
        from git_acp.utils.formatting import debug_item
        debug_item("Test Plan Prompt", prompt)
        debug_item("Test Plan Context", {"diff_text": diff_text})
    
    system_prompt = "You are an AI that produces a concise test plan. Output only the test plan (50-100 words) without extra commentary."
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    client = AIClient(use_pr_model=True)  # Use PR model by default
    result = client.chat_completion(messages)
    return result.strip()


def generate_additional_notes(commit_messages: List[str], diff_text: str, verbose: bool = False) -> str:
    """
    Generate any additional notes or comments for the PR.
    """
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    prompt = (
        f"Generate additional notes or comments for this PR in up to 50 words.\n"
        f"Focus on essential information that has not been covered in other sections.\n"
        f"Commit Messages: {commit_messages}\nDiff: {diff_text}"
    )
    if verbose:
        from git_acp.utils.formatting import debug_item
        debug_item("Additional Notes Prompt", prompt)
        debug_item("Additional Notes Context", context)
    
    system_prompt = "You are an AI that generates additional notes for a pull request. Output only the notes (up to 50 words) without any extra comments."
    messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": prompt}
    ]
    client = AIClient(use_pr_model=True)  # Use PR model by default
    result = client.chat_completion(messages)
    return result.strip()


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


def generate_pr_simple(commit_messages: list, diff_text: str, added_files: str, modified_files: str, deleted_files: str, verbose: bool = False) -> str:
    """Generate a compact pull request description in Markdown format using a single AI request.

    This prompt instructs the AI to generate a concise PR markdown that excludes commit messages and file change data,
    as these values will be loaded directly from git commands later.
    """
    # Limit the diff text to prevent overly large context
    limited_diff = diff_text if len(diff_text) <= 10000 else diff_text[:10000] + "\n...[truncated diff]"
    
    # Updated prompt with strict formatting requirements
    prompt = f"""Generate a pull request description in the following format:
# <title>

## Summary
<brief overview>

## Code Changes
<brief description of key changes>

## Reason for Changes
<why the changes were made>

## Test Plan
<brief testing overview>

## Additional Notes
<any other important information>

Use the following diff to generate the content:
{limited_diff}

Important:
- Output ONLY the markdown content
- Do not include explanatory text or meta-commentary
- Do not use nested code blocks
- Keep sections concise and focused
- Title should be 5-10 words
- Summary should be 100-200 words
- Other sections should be 50-100 words each"""
    
    if verbose:
        debug_item("Simple Mode Prompt", prompt)
    
    system_prompt = """You are a PR description generator. Generate a pull request description following these rules:
1. Use the exact section structure provided
2. Output only the markdown content
3. No explanatory text or meta-commentary
4. No nested code blocks
5. Keep sections concise and focused
6. Use clear, professional language"""
    
    client = AIClient(use_pr_model=True)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    result = client.chat_completion(messages)
    
    # Clean up the formatting
    cleaned_result = clean_markdown_formatting(result)
    
    if verbose:
        debug_item("Generated PR (Before Cleaning)", result)
        debug_item("Generated PR (After Cleaning)", cleaned_result)
    
    return cleaned_result


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
    
    system_prompt = """You are a PR title extractor. Your task is to:
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
    markdown = f"""# {title}

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


def review_final_pr(pr_markdown: str, verbose: bool = False) -> str:
    """Review and clean up the final PR markdown.
    
    1. Remove duplicate information between sections
    2. Ensure consistent formatting
    3. Clean up any markdown issues
    
    Args:
        pr_markdown: The PR markdown to review
        verbose: Whether to log debug information
        
    Returns:
        Cleaned and reviewed PR markdown
    """
    if verbose:
        debug_header("Reviewing Final PR")
        debug_item("Original PR", pr_markdown)
    
    # First clean up the formatting
    cleaned_markdown = clean_markdown_formatting(pr_markdown)
    
    # Extract a clean title from the entire content
    new_title = extract_clean_title(cleaned_markdown, verbose)
    
    # Replace the original title with the clean one
    lines = cleaned_markdown.split('\n')
    if lines and lines[0].startswith('#'):
        lines[0] = f"# {new_title}"
        cleaned_markdown = '\n'.join(lines)
    
    system_prompt = """You are a PR formatting engine. Your task is to:
1. Remove any duplicate information between sections
2. Ensure each section is concise and focused
3. Maintain the exact section structure:
   # Title (already cleaned up - do not modify)
   ## Summary
   ## Commits
   ## Files Changed
   ## Code Changes
   ## Reason for Changes
   ## Test Plan
   ## Additional Notes
4. Remove any explanatory text or meta-commentary
5. Fix any markdown formatting issues
6. Keep the content professional and clear
7. Output only the cleaned markdown with no additional text"""
    
    prompt = f"""Review and clean up this PR markdown, following the system instructions.
Remove any duplicate information between sections while maintaining the key content.
Keep the sections focused and concise.
Do not modify the title as it has already been cleaned up.

PR Markdown to clean:
{cleaned_markdown}"""
    
    if verbose:
        debug_item("Review Prompt", prompt)
    
    client = AIClient(use_pr_model=True)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    try:
        result = client.chat_completion(messages)
        final_result = clean_markdown_formatting(result)
        
        if verbose:
            debug_item("AI Review Result", result)
            debug_item("Final Cleaned PR", final_result)
        
        return final_result
    except Exception as e:
        if verbose:
            debug_item("Review Error", str(e))
        # If review fails, return the cleaned markdown
        return cleaned_markdown 