"""
Functions for building commit messages using AI.
"""

import json
from git_acp.utils import debug_header, debug_preview
from git_acp.ai.client import AIClient
from git_acp.ai.commit_prompts import (
    create_advanced_commit_message_prompt,
    create_simple_commit_message_prompt,
    ADVANCED_COMMIT_SYSTEM_PROMPT,
    SIMPLE_COMMIT_SYSTEM_PROMPT
)

def build_advanced_commit_message(context: dict, config=None) -> str:
    """
    Build an advanced commit message using repository context.
    
    Args:
        context: Dictionary containing git context.
        config: Optional configuration.
    
    Returns:
        A commit message string.
    """
    prompt = create_advanced_commit_message_prompt(context, config)
    
    if config and getattr(config, 'verbose', False):
        debug_header("Building Advanced Commit Message")
        debug_preview("Context", context)
        debug_preview("Generated Prompt", prompt)
    
    client = AIClient(config)
    messages = [
        {"role": "system", "content": ADVANCED_COMMIT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    try:
        commit_message = client.chat_completion(messages).strip()
        
        if config and getattr(config, 'verbose', False):
            debug_preview("Generated Commit Message", commit_message)
            
        return commit_message
    except Exception as e:
        if config and getattr(config, 'verbose', False):
            debug_preview("Error Generating Commit Message", str(e))
        # Fallback to a basic commit message
        return f"update: {context.get('staged_changes', '').split()[0]}"

def build_simple_commit_message(context: dict, config=None) -> str:
    """
    Build a simple commit message using repository context.
    
    Args:
        context: Dictionary containing git context.
        config: Optional configuration.
    
    Returns:
        A commit message string.
    """
    prompt = create_simple_commit_message_prompt(context, config)
    
    if config and getattr(config, 'verbose', False):
        debug_header("Building Simple Commit Message")
        debug_preview("Context", context)
        debug_preview("Generated Prompt", prompt)
    
    client = AIClient(config)
    messages = [
        {"role": "system", "content": SIMPLE_COMMIT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    try:
        commit_message = client.chat_completion(messages).strip()
        
        if config and getattr(config, 'verbose', False):
            debug_preview("Generated Commit Message", commit_message)
            
        return commit_message
    except Exception as e:
        if config and getattr(config, 'verbose', False):
            debug_preview("Error Generating Commit Message", str(e))
        # Fallback to a basic commit message
        return f"update: {context.get('staged_changes', '').split()[0]}" 