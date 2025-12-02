"""User interaction abstraction for CLI.

This module provides a Protocol for user interaction, enabling dependency
injection for testing. Production code uses RichQuestionaryInteraction,
while tests can use TestInteraction.
"""

from __future__ import annotations

from typing import Protocol

import questionary
from rich import print as rprint
from rich.panel import Panel
from rich.prompt import Confirm

from git_acp.config import COLORS, QUESTIONARY_STYLE
from git_acp.git import CommitType, GitError
from git_acp.utils import GitConfig


class UserInteraction(Protocol):
    """Protocol for user interaction operations.

    This protocol defines the interface for all user-facing I/O operations,
    allowing the workflow to be tested without interactive prompts.
    """

    def select_files(self, changed_files: set[str]) -> str:
        """Present file selection and return selected files.

        Args:
            changed_files: Set of files with uncommitted changes.

        Returns:
            Space-separated list of selected files.

        Raises:
            GitError: If selection is cancelled or invalid.
        """
        ...

    def select_commit_type(
        self, suggested_type: CommitType, config: GitConfig
    ) -> CommitType:
        """Present commit type selection.

        Args:
            suggested_type: The suggested commit type based on changes.
            config: Configuration options.

        Returns:
            The selected commit type.

        Raises:
            GitError: If selection is cancelled.
        """
        ...

    def confirm(self, message: str) -> bool:
        """Ask user for confirmation.

        Args:
            message: The confirmation prompt.

        Returns:
            True if user confirms, False otherwise.
        """
        ...

    def print_message(self, message: str) -> None:
        """Print a message to the user.

        Args:
            message: Message to print (may contain Rich markup).
        """
        ...

    def print_error(self, error_msg: str, suggestion: str, title: str) -> None:
        """Print an error panel.

        Args:
            error_msg: The error message.
            suggestion: A suggestion for resolving the error.
            title: The panel title.
        """
        ...

    def print_panel(self, content: str, title: str, style: str) -> None:
        """Print a styled panel.

        Args:
            content: Panel content.
            title: Panel title.
            style: Border style.
        """
        ...


class RichQuestionaryInteraction:
    """Production implementation using Rich and Questionary."""

    def select_files(self, changed_files: set[str]) -> str:
        """Present an interactive selection menu for changed files.

        Args:
            changed_files: Set of files with uncommitted changes.

        Returns:
            Space-separated list of selected files, with proper quoting.

        Raises:
            GitError: If no files found, user cancels, or no selection made.
        """
        if not changed_files:
            raise GitError("No changed files found to commit.")

        if len(changed_files) == 1:
            selected_file = next(iter(changed_files))
            rprint(
                f"[{COLORS['warning']}]Adding file:[/{COLORS['warning']}] "
                f"{selected_file}"
            )
            return f'"{selected_file}"' if " " in selected_file else selected_file

        choices = []
        for file in sorted(list(changed_files)):
            choices.append({"name": file, "value": file})
        choices.append({"name": "All files", "value": "All files"})

        selected = questionary.checkbox(
            "Select files to commit:",
            choices=choices,
            style=questionary.Style(QUESTIONARY_STYLE),
            instruction=(
                "(Use arrow keys to move, <space> to select, <enter> to confirm)"
            ),
        ).ask()

        if selected is None:
            raise GitError("Operation cancelled by user.")
        elif not selected:
            raise GitError("No files selected.")

        # If "All files" is selected, stage and display all changed files.
        if "All files" in selected:
            selected_files = sorted(changed_files)
            rprint(f"[{COLORS['warning']}]Adding files:[/{COLORS['warning']}]")
            for file in selected_files:
                rprint(f"  - {file}")
            return " ".join(
                f'"{f}"' if " " in f else f for f in selected_files
            )

        rprint(f"[{COLORS['warning']}]Adding files:[/{COLORS['warning']}]")
        for file in selected:
            rprint(f"  - {file}")

        return " ".join(f'"{f}"' if " " in f else f for f in selected)

    def select_commit_type(
        self, suggested_type: CommitType, config: GitConfig
    ) -> CommitType:
        """Present an interactive selection menu for commit types.

        Args:
            suggested_type: The suggested commit type based on changes.
            config: Configuration options.

        Returns:
            The selected commit type.

        Raises:
            GitError: If no commit type is selected.
        """
        # Auto-select if skip_confirmation or if it's a valid type
        if config.skip_confirmation or suggested_type.value in [
            "feat", "fix", "docs", "style", "refactor", "test", "chore", "revert",
        ]:
            return suggested_type

        commit_type_choices = []
        for commit_type in CommitType:
            name = (
                f"{commit_type.value} (suggested)"
                if commit_type == suggested_type
                else commit_type.value
            )
            choice = {"name": name, "value": commit_type, "checked": False}
            if commit_type == suggested_type:
                commit_type_choices.insert(0, choice)
            else:
                commit_type_choices.append(choice)

        def validate_single(selected: list[CommitType]) -> str | bool:
            if len(selected) != 1:
                return "Please select exactly one commit type"
            return True

        selected_types = questionary.checkbox(
            "Select commit type (space to select, enter to confirm):",
            choices=commit_type_choices,
            style=questionary.Style(QUESTIONARY_STYLE),
            instruction=" (suggested type marked)",
            validate=validate_single,
        ).ask()

        if selected_types is None:
            raise GitError("Operation cancelled by user.")
        elif not selected_types or len(selected_types) != 1:
            raise GitError("No commit type selected.")

        return selected_types[0]

    def confirm(self, message: str) -> bool:
        """Ask user for confirmation using Rich Confirm.

        Args:
            message: The confirmation prompt.

        Returns:
            True if user confirms, False otherwise.
        """
        return Confirm.ask(message)

    def print_message(self, message: str) -> None:
        """Print a message using Rich.

        Args:
            message: Message to print (may contain Rich markup).
        """
        rprint(message)

    def print_error(self, error_msg: str, suggestion: str, title: str) -> None:
        """Print an error panel using Rich.

        Args:
            error_msg: The error message.
            suggestion: A suggestion for resolving the error.
            title: The panel title.
        """
        err = COLORS["error"]
        content = f"[{err}]{error_msg}[/{err}]\n\nSuggestion: {suggestion}"
        rprint(Panel(content, title=title, border_style="red"))

    def print_panel(self, content: str, title: str, style: str) -> None:
        """Print a styled panel using Rich.

        Args:
            content: Panel content.
            title: Panel title.
            style: Border style.
        """
        rprint(Panel(content, title=title, border_style=style))


class TestInteraction:
    """Test double for UserInteraction that returns canned responses.

    This class is used in tests to avoid interactive prompts while still
    exercising the workflow logic.
    """

    def __init__(
        self,
        files_response: str = ".",
        commit_type_response: CommitType = CommitType.CHORE,
        confirm_response: bool = True,
    ) -> None:
        """Initialize with canned responses.

        Args:
            files_response: Value to return from select_files.
            commit_type_response: Value to return from select_commit_type.
            confirm_response: Value to return from confirm.
        """
        self._files_response = files_response
        self._commit_type_response = commit_type_response
        self._confirm_response = confirm_response
        self.messages: list[str] = []
        self.errors: list[tuple[str, str, str]] = []
        self.panels: list[tuple[str, str, str]] = []

    def select_files(self, changed_files: set[str]) -> str:
        """Return canned file selection.

        Args:
            changed_files: Ignored in test double.

        Returns:
            The configured files_response.
        """
        return self._files_response

    def select_commit_type(
        self, suggested_type: CommitType, config: GitConfig
    ) -> CommitType:
        """Return canned commit type.

        Args:
            suggested_type: Ignored in test double.
            config: Ignored in test double.

        Returns:
            The configured commit_type_response.
        """
        return self._commit_type_response

    def confirm(self, message: str) -> bool:
        """Return canned confirmation.

        Args:
            message: Ignored in test double.

        Returns:
            The configured confirm_response.
        """
        return self._confirm_response

    def print_message(self, message: str) -> None:
        """Record message for assertions.

        Args:
            message: Message to record.
        """
        self.messages.append(message)

    def print_error(self, error_msg: str, suggestion: str, title: str) -> None:
        """Record error for assertions.

        Args:
            error_msg: Error message to record.
            suggestion: Suggestion to record.
            title: Title to record.
        """
        self.errors.append((error_msg, suggestion, title))

    def print_panel(self, content: str, title: str, style: str) -> None:
        """Record panel for assertions.

        Args:
            content: Panel content to record.
            title: Panel title to record.
            style: Border style to record.
        """
        self.panels.append((content, title, style))
