"""CLI-specific formatting helpers."""
def format_commit_message(commit_type, message: str) -> str:
    """
    Format a commit message using conventional commits style.
    
    Args:
        commit_type: The commit type (e.g., CommitType enum).
        message: The raw commit message.
    
    Returns:
        A formatted commit message.
    """
    lines = message.split('\n')
    title = lines[0]
    description = '\n'.join(lines[1:])
    return f"{commit_type.value}: {title}\n\n{description}".strip() 