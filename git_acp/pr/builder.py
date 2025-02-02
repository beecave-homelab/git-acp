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
    
    system_prompt = """You are a PR title generator. Follow these rules exactly:
1. Output ONLY the title text, nothing else
2. Use exactly 5-10 words
3. Start with a verb in present tense
4. Be specific about what changed
5. NO formatting characters (#, `, ', ", etc.)
6. NO prefixes like 'PR:', 'Title:', etc.
7. NO explanatory text or meta-commentary
8. NO conventional commit prefixes (feat:, fix:, etc.)"""

    prompt = f"""Generate a title that captures the main changes from this information:

COMMIT MESSAGES:
{'\n'.join(commit_messages)}

CHANGES SUMMARY:
{diff_text}

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
    
    system_prompt = """You are a code change summarizer. Follow these rules exactly:
1. Output ONLY the description, nothing else
2. Use exactly 75-100 words
3. Focus on functional changes
4. Group related changes together
5. NO file paths or line numbers
6. NO implementation details
7. NO commit messages
8. NO technical jargon unless essential
9. Write in present tense
10. Use clear, professional language"""

    prompt = f"""Describe the functional changes in this diff:

CHANGES:
{diff_text}

Focus on:
- What functionality changed
- User-facing impacts
- System-level changes
- Dependencies affected"""

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


def generate_reason_for_changes(commit_messages: List[str], diff_text: str, verbose: bool = False) -> str:
    """Generate a clear explanation for the changes based on commit messages and diff."""
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    
    system_prompt = """You are a change rationale explainer. Follow these rules exactly:
1. Output ONLY the explanation, nothing else
2. Use exactly 75-100 words
3. Focus on WHY changes were needed
4. Include business context
5. NO implementation details
6. NO technical specifications
7. NO commit message quotes
8. Write in present tense
9. Use business-focused language
10. Explain benefits and impact"""

    prompt = f"""Explain why these changes were necessary:

CONTEXT:
Commit Messages: {commit_messages}
Changes: {diff_text}

Focus on:
- Business drivers
- Problems being solved
- Expected benefits
- Strategic alignment"""

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
    
    system_prompt = """You are a test plan generator. Follow these rules exactly:
1. Output ONLY the test plan, nothing else
2. Use exactly 75-100 words
3. Focus on verification steps
4. Include key test scenarios
5. NO implementation details
6. NO technical commands
7. NO specific test data
8. Write in imperative mood
9. Use clear, actionable language
10. Cover both happy and error paths"""

    prompt = f"""Create a test plan for these changes:

CHANGES:
{diff_text}

Include:
- Key scenarios to verify
- Important edge cases
- Required test environments
- Success criteria"""

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


def generate_additional_notes(commit_messages: List[str], diff_text: str, verbose: bool = False) -> str:
    """Generate any additional notes or comments for the PR."""
    context = {"commit_messages": commit_messages, "diff_text": diff_text}
    
    system_prompt = """You are a PR notes generator. Follow these rules exactly:
1. Output ONLY the notes, nothing else
2. Use exactly 25-50 words
3. Focus on important information not covered elsewhere
4. Include deployment considerations
5. NO duplicate information
6. NO implementation details
7. NO commit references
8. Write in present tense
9. Use clear, concise language
10. Only include if truly needed"""

    prompt = f"""Add any important notes not covered in other sections:

CONTEXT:
Commits: {commit_messages}
Changes: {diff_text}

Consider:
- Breaking changes
- Migration steps
- Dependencies
- Known limitations"""

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
    
    system_prompt = """You are a PR description generator. Follow these rules exactly:
1. Output ONLY markdown-formatted text
2. Use exactly 200-300 words total
3. Include these sections in order:
   - Title: Start with '# ' followed by 5-10 words that summarize the changes
   - Summary: A paragraph describing what changed and why (75-100 words)
   - Changes: Key functional changes and their impact (50-75 words)
   - Testing: Verification steps and test scenarios (25-50 words)
4. NO technical implementation details
5. NO file paths or line numbers
6. NO commit message quotes
7. NO lists of files or changes
8. Write in present tense
9. Use clear, business-focused language
10. Focus on value and impact, not technical details"""

    # Analyze commit messages for key themes
    commit_themes = "\n".join([f"- {msg}" for msg in commit_messages])

    prompt = f"""Create a concise pull request description that focuses on business value:

COMMIT MESSAGES:
{commit_themes}

CHANGES OVERVIEW:
{diff_text[:5000] if len(diff_text) > 5000 else diff_text}

FILES CHANGED:
Added: {len(added_files.split('\n')) if added_files else 0} files
Modified: {len(modified_files.split('\n')) if modified_files else 0} files
Deleted: {len(deleted_files.split('\n')) if deleted_files else 0} files

Requirements:
1. Start with a clear title that captures the main purpose of these changes
2. Explain the business value and impact of these changes
3. Describe key functional changes without technical details
4. Include specific verification steps
5. Keep the content professional and focused"""

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


def review_final_pr(markdown: str, verbose: bool = False) -> str:
    """Review and clean up the final PR markdown to remove duplicate or redundant information."""
    
    system_prompt = """You are a PR review specialist. Follow these rules exactly:
1. Output ONLY the cleaned markdown
2. Keep the existing structure and sections
3. Remove duplicate information
4. Remove redundant context
5. Ensure consistent formatting
6. Keep section headers unchanged
7. NO meta-commentary or explanations
8. NO additional sections
9. NO reformatting of existing content
10. Preserve the original title"""

    prompt = f"""Review and clean this PR description:

{markdown}

Requirements:
- Remove any duplicate information
- Keep all section headers
- Maintain existing formatting
- Preserve the original title
- Only remove truly redundant content"""

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