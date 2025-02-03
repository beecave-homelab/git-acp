"""
Prompts used for generating commit messages.
"""

import json
from git_acp.utils import debug_header, debug_preview

# System prompts for different commit message styles
ADVANCED_COMMIT_SYSTEM_PROMPT = """You are a commit message generator. Follow these rules exactly:
1. Use conventional commit format (type: description)
2. Be specific about what changed and why
3. Reference related work if relevant
4. Keep it concise but descriptive
5. Use present tense
6. Focus on the business value
7. Include scope if relevant
8. Add breaking change footer if needed"""

SIMPLE_COMMIT_SYSTEM_PROMPT = """You are a commit message generator. Follow these rules exactly:
1. Use conventional commit format (type: description)
2. Be specific about what changed
3. Keep it concise but descriptive
4. Use present tense"""

def create_advanced_commit_message_prompt(context: dict, config=None) -> str:
    """
    Create an advanced AI prompt using repository context.
    
    Args:
        context: Dictionary containing git context.
        config: Optional configuration.
    
    Returns:
        A prompt string.
    """
    commit_types = context['commit_patterns']['types']
    common_type = max(commit_types.items(), key=lambda x: x[1])[0] if commit_types else "feat"
    recent_messages = [c['message'] for c in context['recent_commits']]
    related_messages = [c['message'] for c in context['related_commits']]
    
    prompt = f"""Generate a concise and descriptive commit message for the following changes:

Changes to commit:
{context['staged_changes']}

Repository context:
- Most used commit type: {common_type}
- Recent commits:
{json.dumps(recent_messages, indent=2)}

Related commits:
{json.dumps(related_messages, indent=2) if related_messages else '[]'}

Requirements:
1. Follow the repository's commit style (type: description)
2. Be specific about what changed and why
3. Reference related work if relevant
4. Keep it concise but descriptive
"""
    if config and getattr(config, 'verbose', False):
        debug_header("Generated prompt preview:")
        debug_preview(prompt)
    return prompt

def create_simple_commit_message_prompt(context: dict, config=None) -> str:
    """
    Create a simple AI prompt using repository context.
    
    Args:
        context: Dictionary containing git context.
        config: Optional configuration.
    
    Returns:
        A prompt string.
    """
    prompt = f"""Generate a concise and descriptive commit message for the following changes:

{context['staged_changes']}

Requirements:
1. Follow conventional commit format (type: description)
2. Be specific about what changed
3. Keep it concise but descriptive
"""
    if config and getattr(config, 'verbose', False):
        debug_header("Generated simple prompt preview:")
        debug_preview(prompt)
    return prompt 