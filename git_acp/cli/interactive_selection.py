"""CLI prompts for interactive selection."""
import questionary
from git_acp.config.settings import TERMINAL_SETTINGS
from git_acp.git.classification import CommitType
from git_acp.git import GitError

def select_files(changed_files: set, verbose: bool = False) -> str:
    """
    Present an interactive selection for files.
    
    Args:
        changed_files: Set of changed files.
        verbose: Enable verbose output.
    
    Returns:
        A space-separated string of selected files.
    """
    if not changed_files:
        raise GitError("No changed files found to commit.")
    if len(changed_files) == 1:
        selected_file = next(iter(changed_files))
        print(f"Adding file: {selected_file}")
        return f'"{selected_file}"' if ' ' in selected_file else selected_file

    choices = [{"name": file, "value": file} for file in sorted(changed_files)]
    choices.append({"name": "All files", "value": "All files"})
    selected = questionary.checkbox(
        "Select files to commit (space to select, enter to confirm):",
        choices=choices,
        style=questionary.Style(TERMINAL_SETTINGS["questionary_style"])
    ).ask()
    
    if selected is None or not selected:
        raise GitError("No files selected or operation cancelled.")
    if "All files" in selected:
        print("Adding all files.")
        return "."
    return " ".join(f'"{f}"' if ' ' in f else f for f in selected)

def select_commit_type(config, suggested_type: CommitType) -> CommitType:
    """
    Present an interactive selection for commit type.
    
    Args:
        config: The GitConfig object.
        suggested_type: The suggested CommitType.
    
    Returns:
        The selected CommitType.
    """
    # If confirmation is skipped or a valid type is already provided, auto-select.
    if config.skip_confirmation or suggested_type.value in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'revert']:
        if config.verbose:
            print(f"Auto-selecting commit type: {suggested_type.value}")
        return suggested_type

    commit_type_choices = []
    for commit_type in CommitType:
        name = f"{commit_type.value} (suggested)" if commit_type == suggested_type else commit_type.value
        commit_type_choices.append({
            'name': name,
            'value': commit_type,
            'checked': False
        })

    selected_types = questionary.checkbox(
        "Select commit type (space to select, enter to confirm):",
        choices=commit_type_choices,
        style=questionary.Style(TERMINAL_SETTINGS["questionary_style"]),
        instruction="(suggested type marked)"
    ).ask()

    if selected_types is None or len(selected_types) != 1:
        raise GitError("No commit type selected or multiple selections made.")
    return selected_types[0] 